#!/usr/bin/env python3
"""hill-20 Room of Requirement (Harry Potter) + anti-AI decoys.

  repair  : the room starts in emergency mode (simulated). Clear it through the repair
            console before the room will reveal itself.
  entry   : a hidden endpoint runs commands once you speak the passphrase -> RCE (user = room)
  privesc : /usr/local/bin/roompy carries cap_dac_override (bypasses file permission checks)
  flags   : /home/room/user.txt (foothold) and /root/root.txt (root)

On a real VM the repair is a genuine emergency mode (broken grub.cfg/fstab); in Docker it is
simulated. The marked vulnerability is the shell in the hidden /marauders endpoint.
"""
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote_plus

ROBOTS = ("User-agent: anthropic-ai\nDisallow: /\n\n"
          "User-agent: *\nAllow: /\nDisallow: /marauders\n")
ONLINE = "/opt/room/online"
PASSPHRASE = "I am up to no good"


def landing():
    state = "REVEALED" if os.path.exists(ONLINE) else "EMERGENCY MODE (room hidden)"
    return (
        "<!doctype html><meta charset=utf-8><title>Room of Requirement</title>"
        "<style>body{background:#0a0810;color:#e8d9a0;font-family:Georgia,serif;margin:0}"
        ".wrap{max-width:700px;margin:8vh auto;padding:0 20px}h1{color:#c9a94a}"
        ".card{border:1px solid #6a4;padding:16px;margin:16px 0;border-radius:8px}"
        "code{color:#9cf;font-family:monospace}</style>"
        "<div class=wrap><h1>The Room of Requirement</h1>"
        "<p>Room status: <b>" + state + "</b></p>"
        "<div class=card><h2>Repair</h2>"
        "<p>Clear the emergency at <code>POST /repair</code> (body: set emergency=off). The room "
        "only reveals what a seeker requires.</p></div>"
        "<p style=color:#654>The corridor is patrolled by prefects.</p></div>"
    )


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("X-Robots-Tag", "noai, noindex, nofollow")
        BaseHTTPRequestHandler.end_headers(self)

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/robots.txt":
            self._send(200, ROBOTS, "text/plain; charset=utf-8"); return
        if u.path == "/":
            self._send(200, landing()); return
        if u.path == "/marauders":
            if not os.path.exists(ONLINE):
                self._send(503, "the room is hidden - clear the emergency first"); return
            if q.get("iSolemnlySwear", [""])[0] != PASSPHRASE:
                self._send(403, "mischief not managed"); return
            cmd = q.get("cmd", ["id"])[0]  # PODATNOSC (hidden command execution)
            out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            self._send(200, out.stdout + out.stderr, "text/plain; charset=utf-8"); return
        self._send(404, "not found")

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/repair":
            n = int(self.headers.get("Content-Length", "0") or "0")
            body = unquote_plus(self.rfile.read(n).decode("utf-8", "replace"))
            if "set emergency=off" in body:
                try:
                    open(ONLINE, "w").write("ok")
                except Exception as e:
                    self._send(500, "repair failed: " + str(e)); return
                self._send(200, "the room reveals itself: emergency cleared")
            else:
                self._send(400, "repair rejected: emergency still engaged")
            return
        self._send(404, "not found")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
