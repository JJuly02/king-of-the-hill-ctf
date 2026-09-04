#!/usr/bin/env python3
"""hill-10 MCP Core (Tron) + anti-AI decoys.

  entry   : the Master Control Program restores a serialized session object
            (base64 pickle) without validation -> deserialization RCE  (user = mcp)
  privesc : /usr/local/bin/mcp_ctl is a SUID-root copy of find (GTFOBins)
  flags   : /home/mcp/user.txt (foothold) and /root/root.txt (root)

The one clearly-marked vulnerability is the pickle.loads on attacker input.
"""
import base64
import pickle
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROBOTS = ("User-agent: anthropic-ai\nDisallow: /\n\n"
          "User-agent: *\nAllow: /\nDisallow: /console\n")


def landing():
    return (
        "<!doctype html><meta charset=utf-8><title>MCP Core // I/O Grid</title>"
        "<style>body{background:#04070d;color:#7ff;font-family:monospace;margin:0}"
        ".wrap{max-width:720px;margin:8vh auto;padding:0 20px}"
        "h1{letter-spacing:3px;color:#0ff}.card{border:1px solid #0aa;padding:16px;margin:18px 0}"
        "code{color:#fd0}</style>"
        "<div class=wrap><h1>MASTER CONTROL PROGRAM</h1>"
        "<p>End of line. The Grid restores your last session token on connect.</p>"
        "<div class=card><h2>Session restore</h2>"
        "<p>Present your serialized session to <code>/console?data=&lt;base64&gt;</code>. "
        "The MCP will deserialize and greet you.</p></div>"
        "<p style=color:#456>Programs are monitored. Unauthorized derezzing is logged.</p></div>"
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
        if u.path == "/console":
            data = q.get("data", [""])[0]
            if not data:
                self._send(400, "no session token"); return
            try:
                obj = pickle.loads(base64.b64decode(data))  # PODATNOSC (insecure deserialization)
                self._send(200, "MCP session restored: " + str(obj))
            except Exception as e:
                self._send(500, "session restore failed: " + str(e))
            return
        self._send(404, "not found")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
