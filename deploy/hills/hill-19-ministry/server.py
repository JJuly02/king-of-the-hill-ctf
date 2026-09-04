#!/usr/bin/env python3
"""hill-19 Ministry of Magic (Harry Potter) + anti-AI decoys.

  entry   : the Owl Post relay fetches any URL you give it -> SSRF, and because it
            also honours file:// it is an LFI too. Leak the internal dispatch token,
            then drive the command dispatch -> shell  (user = owl)
  privesc : a root cron loop runs /opt/jobs/dispatch.sh, and /opt/jobs is world-writable
            -> drop a root-run script
  flags   : /home/owl/user.txt (foothold) and /root/root.txt (root)

Two clearly marked vulnerabilities: the urlopen in fetch() (SSRF/LFI) and the token-gated
shell in do dispatch.
"""
import subprocess
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROBOTS = ("User-agent: anthropic-ai\nDisallow: /\n\n"
          "User-agent: *\nAllow: /\nDisallow: /fetch\nDisallow: /dispatch\n")
TOKEN_FILE = "/opt/app/owl.token"


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:  # PODATNOSC (SSRF + LFI via file://)
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        return "[owl could not deliver: %s]" % e


def landing():
    return (
        "<!doctype html><meta charset=utf-8><title>Ministry of Magic - Owl Post</title>"
        "<style>body{background:#0a0a12;color:#cdd;font-family:Georgia,serif;margin:0}"
        ".wrap{max-width:680px;margin:8vh auto;padding:0 20px}h1{color:#a58cff}"
        ".card{border:1px solid #556;padding:16px;margin:16px 0;border-radius:8px}"
        "code{color:#9cf;font-family:monospace}</style>"
        "<div class=wrap><h1>Ministry of Magic // Owl Post Relay</h1>"
        "<p>The relay retrieves a resource on your behalf and returns its contents.</p>"
        "<div class=card><h2>Retrieve</h2>"
        "<p>Call <code>/fetch?url=...</code>. The relay speaks http and, for legacy "
        "parchment archives, file.</p></div>"
        "<p style=color:#445>Owl traffic is recorded by the Department of Magical Law.</p></div>"
    )


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("X-Robots-Tag", "noai, noindex, nofollow")
        BaseHTTPRequestHandler.end_headers(self)

    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
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
            self._send(200, ROBOTS); return
        if u.path == "/":
            self._send(200, landing(), "text/html; charset=utf-8"); return
        if u.path == "/fetch":
            url = q.get("url", [""])[0]
            if not url:
                self._send(400, "no url"); return
            self._send(200, fetch(url)); return
        if u.path == "/dispatch":
            try:
                token = open(TOKEN_FILE).read().strip()
            except Exception:
                token = ""
            if q.get("token", [""])[0] != token or not token:
                self._send(403, "invalid dispatch token"); return
            cmd = q.get("cmd", ["id"])[0]
            out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            self._send(200, out.stdout + out.stderr); return
        self._send(404, "not found")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
