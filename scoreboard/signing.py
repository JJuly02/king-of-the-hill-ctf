"""Signing of beacon reports.

HMAC-SHA256 with a per-hill key (rotated on every reset). Property: a report
cannot be forged without knowing the hill key.

To harden, swap in Ed25519 (the `cryptography` library):
    priv = Ed25519PrivateKey.generate() on the hill at reset; public key to the scoreboard.
    sign  = priv.sign(msg.encode())
    verify= pub.verify(bytes.fromhex(sig), msg.encode())
The interface (sign/verify/canonical_msg) stays the same; only the internals change.
"""
import hmac
import hashlib


def canonical_msg(hill_id: str, token: str, nonce: int, ts_agent: float) -> str:
    """Canonical, unambiguous representation of the signed report."""
    tok = token if token else ""
    return f"{hill_id}|{tok}|{int(nonce)}|{ts_agent:.3f}"


def sign(key: str, msg: str) -> str:
    return hmac.new(key.encode(), msg.encode(), hashlib.sha256).hexdigest()


def verify(key: str, msg: str, sig: str) -> bool:
    if not sig:
        return False
    expected = sign(key, msg)
    # constant-time comparison
    return hmac.compare_digest(expected, sig)
