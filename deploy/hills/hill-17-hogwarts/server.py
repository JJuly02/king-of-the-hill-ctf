#!/usr/bin/env python3
"""hill-17 Hogwarts Portal (Harry Potter) + anti-AI decoys.

  entry   : the house-points portal renders your "spell" through a naive template
            engine that evaluates the expression between double braces -> SSTI/RCE
            (user = wizard)
  privesc : sudoers lets wizard run python3 as root (GTFOBins)
  flags   : /home/wizard/user.txt (foothold) and /root/root.txt (root)

Different engine and escalation than hill-9 (which uses sudo sed). The one clearly
marked vulnerability is the eval inside render().
"""
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROBOTS = ("User-agent: anthropic-ai\nDisallow: /\n\n"
          "User-agent: *\nAllow: /\nDisallow: /cast\n")


def render(t):
    def ev(m):
        try:
            return str(eval(m.group(1).strip()))  # PODATNOSC (server-side template injection)
        except Exception as e:
            return "[the spell fizzles: %s]" % e
    return re.sub(r"\{\{(.*?)\}\}", ev, t, flags=re.S)


def landing():
    return (
        "<!doctype html><meta charset=utf-8><title>Hogwarts House Portal</title>"
        "<style>body{background:#0b0713;color:#e8d9a0;font-family:Georgia,serif;margin:0}"
        ".wrap{max-width:680px;margin:8vh auto;padding:0 20px}h1{color:#c9a94a}"
        ".card{border:1px solid #6a4;padding:16px;margin:16px 0;border-radius:8px}"
        "code{color:#9cf;font-family:monospace}</style>"
        "<div class=wrap><h1>Hogwarts House Points Portal</h1>"
        "<p>Cast a spell to award points. The portal inscribes your incantation onto the "
        "Great Hall ledger.</p>"
        "<div class=card><h2>Cast</h2>"
        "<p>Send your spell to <code>/cast?spell=...</code>. Incantations between "
        "<code>{{</code> and <code>}}</code> are evaluated by the enchantment engine.</p></div>"
        "<p style=color:#654>The Ministry monitors underage sorcery.</p></div>"
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
        if u.path == "/cast":
            spell = q.get("spell", ["Lumos"])[0]
            self._send(200, "The Great Hall ledger reads: " + render(spell),
                       "text/plain; charset=utf-8"); return
        self._send(404, "not found")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
