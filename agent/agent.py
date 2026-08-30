#!/usr/bin/env python3
"""KOTH beacon agent - runs as root on a hill, on a systemd timer every 1s.
Reads /root/king.txt safely, validates, signs, and reports to the collector.

Configuration via env:
  KOTH_HILL_ID     e.g. hill-1
  KOTH_OPS_URL     e.g. http://10.0.0.5:8000
  KOTH_HMAC_KEY    per-hill key (rotated on reset)   [harden: Ed25519 private key]
  KOTH_KING        default /root/king.txt
  KOTH_TOKENS      comma-separated list of known team tokens (exact match)
  KOTH_INTERVAL    default 1 (s)
  KOTH_NONCE_FILE  default <king_dir>/.agent_nonce
  KOTH_MAX_BYTES   default 64
  KOTH_REQUIRE_ROOT  "1" requires root:root mode 600 (recommended); default 0
  KOTH_ONCE        "1" -> one iteration and exit (for a timer / systemd oneshot)

The signature (HMAC-SHA256) MUST match scoreboard/signing.py.
"""
import hmac
import hashlib
import json
import os
import stat
import sys
import time
import urllib.request

HILL_ID = os.environ.get("KOTH_HILL_ID", "hill-1")
OPS_URL = os.environ.get("KOTH_OPS_URL", "http://127.0.0.1:8000").rstrip("/")
HMAC_KEY = os.environ.get("KOTH_HMAC_KEY", "changeme")
KING = os.environ.get("KOTH_KING", "/root/king.txt")
TOKENS = set(t for t in os.environ.get("KOTH_TOKENS", "").split(",") if t)
INTERVAL = float(os.environ.get("KOTH_INTERVAL", "1"))
NONCE_FILE = os.environ.get("KOTH_NONCE_FILE", os.path.join(os.path.dirname(KING) or ".", ".agent_nonce"))
MAX_BYTES = int(os.environ.get("KOTH_MAX_BYTES", "64"))
REQUIRE_ROOT = os.environ.get("KOTH_REQUIRE_ROOT", "0") == "1"
ONCE = os.environ.get("KOTH_ONCE", "0") == "1"


def canonical_msg(hill_id, token, nonce, ts_agent):
    tok = token if token else ""
    return f"{hill_id}|{tok}|{int(nonce)}|{ts_agent:.3f}"


def sign(key, msg):
    return hmac.new(key.encode(), msg.encode(), hashlib.sha256).hexdigest()


def next_nonce():
    try:
        with open(NONCE_FILE) as f:
            n = int(f.read().strip()) + 1
    except Exception:
        n = int(time.time() * 1000)   # monotonic start, survives a restart
    try:
        with open(NONCE_FILE, "w") as f:
            f.write(str(n))
    except Exception:
        pass
    return n


def read_king():
    """Returns (token_or_None, reason). O_NOFOLLOW -> resistant to symlink swap."""
    try:
        fd = os.open(KING, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as e:
        return None, f"open_fail:{e.errno}"   # ELOOP on a symlink etc. -> no owner
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            return None, "not_regular_file"
        if REQUIRE_ROOT and (st.st_uid != 0 or (st.st_mode & 0o777) != 0o600):
            return None, "bad_owner_or_mode"
        if st.st_size > MAX_BYTES:
            return None, "too_big"
        data = os.read(fd, MAX_BYTES + 1).decode("utf-8", "replace").strip()
    finally:
        os.close(fd)
    if data in TOKENS:
        return data, "ok"
    return None, ("empty" if not data else "unknown_token")


def send(token, reason):
    nonce = next_nonce()
    ts = time.time()
    msg = canonical_msg(HILL_ID, token, nonce, ts)
    payload = json.dumps({"hill_id": HILL_ID, "token": token, "nonce": nonce,
                          "ts_agent": ts, "sig": sign(HMAC_KEY, msg)}).encode()
    req = urllib.request.Request(OPS_URL + "/ingest", data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.status, r.read().decode()
    except Exception as e:
        return -1, str(e)


def main():
    while True:
        token, reason = read_king()
        code, resp = send(token, reason)
        print(f"[agent {HILL_ID}] token={token} reason={reason} -> {code} {resp}", flush=True)
        if ONCE:
            break
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
