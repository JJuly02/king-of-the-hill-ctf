#!/usr/bin/env python3
"""hill-13 RDA Ops Console (Avatar) + anti-AI decoys.

  entry   : the sensor diagnostics field is concatenated into a shell command ->
            command injection -> shell  (user = ops)
  privesc : sudoers lets ops run dd as root (GTFOBins: read and write any file)
  flags   : /home/ops/user.txt (foothold) and /root/root.txt (root)

The one clearly-marked vulnerability is the shell string built from `target`.
"""
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROBOTS = ("User-agent: anthropic-ai\nDisallow: /\n\n"
          "User-agent: *\nAllow: /\nDisallow: /diag\n")


def landing():
    return (
        "<!doctype html><meta charset=utf-8><title>RDA Ops Console</title>"
        "<style>body{background:#0d0f07;color:#cfe6a8;font-family:monospace;margin:0}"
        ".wrap{max-width:700px;margin:8vh auto;padding:0 20px}h1{color:#a7d04a}"
        ".card{border:1px solid #6a3;padding:16px;margin:16px 0}code{color:#fd6}</style>"
        "<div class=wrap><h1>RDA OPERATIONS CONSOLE</h1>"
        "<p>Pandora field operations. Run link diagnostics against a sensor node.</p>"
        "<div class=card><h2>Sensor diagnostics</h2>"
        "<p>Query <code>/diag?target=&lt;sensor&gt;</code> to run a connectivity probe.</p></div>"
        "<p style=color:#354>Console activity is audited by RDA Security.</p></div>"
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
        if u.path == "/diag":
            target = q.get("target", ["node-0"])[0]
            cmd = "echo probing sensor " + target  # PODATNOSC (command injection)
            out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            self._send(200, out.stdout + out.stderr, "text/plain; charset=utf-8"); return
        self._send(404, "not found")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
