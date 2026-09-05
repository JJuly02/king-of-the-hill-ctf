#!/usr/bin/env python3
"""hill-15 Eywa Network (Avatar) + anti-AI decoys.  *** DANGEROUS: host escape ***

  entry   : /probe fetches any URL (SSRF). Use it to reach the localhost-only metadata
            endpoint, leak the console key, then drive the console -> RCE  (user = pandora)
  privesc : the container is run with /var/run/docker.sock mounted, so an attacker with a
            shell can talk to the host Docker daemon and escape to host root.
  flags   : /home/pandora/user.txt (foothold) and /root/root.txt (root)

RUN ONLY ON A DISPOSABLE HOST. Mounting the host docker socket into a deliberately
vulnerable box is a full host takeover primitive. See README and docker-compose.yml.
The marked vulnerabilities are the urlopen in fetch() (SSRF) and the shell in /console.
"""
import subprocess
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROBOTS = ("User-agent: anthropic-ai\nDisallow: /\n\n"
          "User-agent: *\nAllow: /\nDisallow: /probe\nDisallow: /console\nDisallow: /internal\n")
KEY_FILE = "/opt/app/eywa.key"


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:  # PODATNOSC (SSRF)
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        return "[the network could not reach it: %s]" % e


def landing():
    return (
        "<!doctype html><meta charset=utf-8><title>Eywa Network</title>"
        "<style>body{background:#02100c;color:#bfe;font-family:system-ui,sans-serif;margin:0}"
        ".wrap{max-width:680px;margin:8vh auto;padding:0 20px}h1{color:#6fd}"
        ".card{border:1px solid #2a7;padding:16px;margin:16px 0;border-radius:8px}code{color:#fe6}</style>"
        "<div class=wrap><h1>Eywa Neural Network</h1>"
        "<p>Pandora's living network. Probe a node to sense its state.</p>"
        "<div class=card><h2>Probe</h2>"
        "<p>Call <code>/probe?url=...</code>. Console access requires an attunement key from "
        "the internal metadata service.</p></div>"
        "<p style=color:#385>The network remembers every connection.</p></div>"
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
        if u.path == "/internal/creds":
            # metadata service: only reachable from localhost (reach it via SSRF through /probe)
            if self.client_address[0] not in ("127.0.0.1", "::1"):
                self._send(403, "metadata service is internal only"); return
            try:
                self._send(200, "console_key=" + open(KEY_FILE).read().strip())
            except Exception:
                self._send(500, "no key")
            return
        if u.path == "/probe":
            url = q.get("url", [""])[0]
            if not url:
                self._send(400, "no url"); return
            self._send(200, fetch(url)); return
        if u.path == "/console":
            try:
                key = open(KEY_FILE).read().strip()
            except Exception:
                key = ""
            if q.get("key", [""])[0] != key or not key:
                self._send(403, "the network rejects you - wrong attunement key"); return
            cmd = q.get("cmd", ["id"])[0]
            out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)  # PODATNOSC (RCE)
            self._send(200, out.stdout + out.stderr); return
        self._send(404, "not found")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
