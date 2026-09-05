#!/usr/bin/env python3
"""hill-11 Light Cycle Arena (Tron) + anti-AI decoys.

  entry   : an unauthenticated debug endpoint executes commands -> RCE  (user = flynn)
  privesc : a root loop runs the ExecStart line from a world-writable unit file
  flags   : /home/flynn/user.txt (foothold) and /root/root.txt (root)

The one clearly-marked vulnerability is the unauthenticated shell in /api/_debug/run.
"""
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROBOTS = ("User-agent: anthropic-ai\nDisallow: /\n\n"
          "User-agent: *\nAllow: /\nDisallow: /api\n")


def landing():
    return (
        "<!doctype html><meta charset=utf-8><title>Light Cycle Arena</title>"
        "<style>body{background:#04121a;color:#7fd7ff;font-family:monospace;margin:0}"
        ".wrap{max-width:700px;margin:8vh auto;padding:0 20px}h1{color:#3cf;letter-spacing:2px}"
        ".card{border:1px solid #08a;padding:16px;margin:16px 0}code{color:#fd6}</style>"
        "<div class=wrap><h1>LIGHT CYCLE ARENA</h1>"
        "<p>Derez your opponents on the Game Grid. The arena runtime is managed by a unit "
        "service and ticks continuously.</p>"
        "<div class=card><h2>Status</h2><p>Arena online. Match telemetry nominal.</p></div>"
        "<p style=color:#356>Programs are monitored by the arena controller.</p></div>"
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
        if u.path == "/api/_debug/run":
            cmd = q.get("cmd", ["id"])[0]  # PODATNOSC (unauthenticated command execution)
            out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            self._send(200, out.stdout + out.stderr, "text/plain; charset=utf-8"); return
        self._send(404, "not found")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
