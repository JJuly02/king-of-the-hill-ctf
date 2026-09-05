#!/usr/bin/env python3
"""hill-18 Gringotts Vault (Harry Potter) + anti-AI decoys.

  repair  : the vault ledger is corrupt and the vault is sealed. Rebuild the ledger through
            the repair console before the vault door will accept requests.
  entry   : the vault door parses submitted YAML with an unsafe loader -> deserialization
            RCE  (user = goblin)
  privesc : a root cron installs sudoers fragments dropped into a goblin-writable dir
  flags   : /home/goblin/user.txt (foothold) and /root/root.txt (root)

The one clearly-marked vulnerability is yaml.unsafe_load on the request body.
"""
import os
import yaml
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROBOTS = ("User-agent: anthropic-ai\nDisallow: /\n\n"
          "User-agent: *\nAllow: /\nDisallow: /vault\n")
OPEN = "/opt/vault/state_open"


def landing():
    state = "OPEN" if os.path.exists(OPEN) else "SEALED (ledger corrupt)"
    return (
        "<!doctype html><meta charset=utf-8><title>Gringotts Wizarding Bank</title>"
        "<style>body{background:#0b0a06;color:#e8d9a0;font-family:Georgia,serif;margin:0}"
        ".wrap{max-width:700px;margin:8vh auto;padding:0 20px}h1{color:#c9a94a}"
        ".card{border:1px solid #6a4;padding:16px;margin:16px 0;border-radius:8px}"
        "code{color:#9cf;font-family:monospace}</style>"
        "<div class=wrap><h1>Gringotts Wizarding Bank</h1>"
        "<p>Vault door status: <b>" + state + "</b></p>"
        "<div class=card><h2>Vault door</h2>"
        "<p>Rebuild the ledger at <code>/repair?ledger=rebuilt&amp;seal=lifted</code>, then "
        "POST a vault manifest (YAML) to <code>/vault/open</code>.</p></div>"
        "<p style=color:#654>Goblin security wards are active and audited.</p></div>"
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
        if u.path == "/repair":
            if q.get("ledger", [""])[0] == "rebuilt" and q.get("seal", [""])[0] == "lifted":
                try:
                    open(OPEN, "w").write("ok")
                except Exception as e:
                    self._send(500, "repair failed: " + str(e)); return
                self._send(200, "vault open: ledger rebuilt")
            else:
                self._send(400, "repair rejected: set ledger=rebuilt and seal=lifted")
            return
        self._send(404, "not found")

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/vault/open":
            if not os.path.exists(OPEN):
                self._send(503, "vault sealed - rebuild the ledger first"); return
            n = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(n).decode("utf-8", "replace")
            try:
                obj = yaml.unsafe_load(body)  # PODATNOSC (unsafe YAML deserialization)
                self._send(200, "manifest: " + str(obj), "text/plain; charset=utf-8")
            except Exception as e:
                self._send(500, "manifest error: " + str(e))
            return
        self._send(404, "not found")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
