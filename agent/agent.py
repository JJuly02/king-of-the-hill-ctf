#!/usr/bin/env python3
"""KOTH beacon agent - reports which team holds a hill, on a timer every 1s.
Reads the hill's king.txt, validates it, signs the report, and sends it to the
collector.

Two read modes:
  - Local file (default): opens KOTH_KING directly with O_NOFOLLOW. Use when the
    agent runs on the same machine/box as king.txt (e.g. the local PoC).
  - Command (KOTH_READ_CMD): runs a command to fetch king.txt from inside the hill
    (e.g. "docker exec <cont> cat /root/king.txt"). Use this to run the agent ON
    THE HOST, so KOTH_HMAC_KEY never enters the container that players get root on.

Configuration via env:
  KOTH_HILL_ID     e.g. hill-1
  KOTH_OPS_URL     e.g. http://10.0.0.5:8000
  KOTH_HMAC_KEY    per-hill key (rotated on reset)   [harden: Ed25519 private key]
  KOTH_KING        default /root/king.txt (local file mode)
  KOTH_READ_CMD    if set, fetch the king token by running this command instead of
                   opening KOTH_KING locally (host-side agent; keeps the key off the box)
  KOTH_TOKENS      comma-separated list of known team tokens (exact match)
  KOTH_INTERVAL    default 1 (s)
  KOTH_NONCE_FILE  default <king_dir>/.agent_nonce
  KOTH_MAX_BYTES   default 64
  KOTH_REQUIRE_ROOT  "1" requires root:root mode 600 (local file mode); default 0
  KOTH_ONCE        "1" -> one iteration and exit (for a timer / systemd oneshot)

The signature (HMAC-SHA256) MUST match scoreboard/signing.py.
"""
import hmac
import hashlib
import json
import os
import stat
import subprocess
import sys
import time
import urllib.request

HILL_ID = os.environ.get("KOTH_HILL_ID", "hill-1")
OPS_URL = os.environ.get("KOTH_OPS_URL", "http://127.0.0.1:8000").rstrip("/")
HMAC_KEY = os.environ.get("KOTH_HMAC_KEY", "changeme")
KING = os.environ.get("KOTH_KING", "/root/king.txt")
READ_CMD = os.environ.get("KOTH_READ_CMD", "")
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


def _match(data):
    if data in TOKENS:
        return data, "ok"
    return None, ("empty" if not data else "unknown_token")


def read_king_cmd():
    """Read the king token by running KOTH_READ_CMD on the host (host-side agent).
    The command fetches king.txt from inside the hill (e.g. via docker exec), so
    KOTH_HMAC_KEY never enters the box that players get root on. Content is still
    validated by exact token match, which is the anti-impersonation control."""
    try:
        out = subprocess.run(READ_CMD, shell=True, capture_output=True, timeout=5)
    except Exception as e:
        return None, f"read_cmd_fail:{e}"
    if out.returncode != 0:
        return None, f"read_cmd_rc:{out.returncode}"
    raw = out.stdout
    if len(raw) > MAX_BYTES + 1:
        return None, "too_big"
    return _match(raw.decode("utf-8", "replace").strip())


def read_king():
    """Returns (token_or_None, reason). O_NOFOLLOW -> resistant to symlink swap."""
    if READ_CMD:
        return read_king_cmd()
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
    return _match(data)


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
