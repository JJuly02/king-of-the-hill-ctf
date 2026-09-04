#!/usr/bin/env python3
"""hill-14 Avatar Link Unit (Avatar) + anti-AI decoys.

  entry   : the biometric link login builds its SQL by string formatting ->
            SQL injection auth bypass -> operator console -> shell  (user = navi)
  privesc : sudoers lets navi run /usr/bin/perl as root (GTFOBins)
  flags   : /home/navi/user.txt (foothold) and /root/root.txt (root)

The one clearly-marked vulnerability is the f-string SQL in do_login.
"""
import sqlite3
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROBOTS = ("User-agent: anthropic-ai\nDisallow: /\n\n"
          "User-agent: *\nAllow: /\nDisallow: /login\nDisallow: /run\n")
SESSION = "linked-9c3f"  # issued on a successful link

db = sqlite3.connect(":memory:", check_same_thread=False)
db.execute("CREATE TABLE operators(name TEXT, pass TEXT, clearance TEXT)")
db.execute("INSERT INTO operators VALUES('grace','h3llsg4te','admin')")
db.execute("INSERT INTO operators VALUES('navi','tsahaylu','user')")
db.commit()


def landing():
    return (
        "<!doctype html><meta charset=utf-8><title>Avatar Link Unit</title>"
        "<style>body{background:#02120e;color:#bfe;font-family:system-ui,sans-serif;margin:0}"
        ".wrap{max-width:680px;margin:8vh auto;padding:0 20px}h1{color:#6fd}"
        ".card{border:1px solid #2a7;padding:16px;margin:16px 0;border-radius:8px}"
        "code{color:#fe6}</style>"
        "<div class=wrap><h1>RDA Avatar Link Unit</h1>"
        "<p>Establish tsaheylu. Authenticate an operator to open the link.</p>"
        "<div class=card><h2>Operator link</h2>"
        "<p>POST <code>name</code> and <code>pass</code> to <code>/login</code>. "
        "A linked operator may drive the unit at <code>/run?cmd=</code>.</p></div>"
        "<p style=color:#385>Link activity is logged by RDA Ops.</p></div>"
    )


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("X-Robots-Tag", "noai, noindex, nofollow")
        BaseHTTPRequestHandler.end_headers(self)

    def _send(self, code, body, ctype="text/html; charset=utf-8", cookie=None):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _linked(self):
        return "sess=" + SESSION in self.headers.get("Cookie", "")

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/robots.txt":
            self._send(200, ROBOTS, "text/plain; charset=utf-8"); return
        if u.path == "/":
            self._send(200, landing()); return
        if u.path == "/run":
            if not self._linked():
                self._send(403, "no link established"); return
            cmd = q.get("cmd", ["id"])[0]
            out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            self._send(200, out.stdout + out.stderr); return
        self._send(404, "not found")

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/login":
            n = int(self.headers.get("Content-Length", "0") or "0")
            form = parse_qs(self.rfile.read(n).decode("utf-8", "replace"))
            name = form.get("name", [""])[0]
            passwd = form.get("pass", [""])[0]
            sql = "SELECT clearance FROM operators WHERE name='%s' AND pass='%s'" % (name, passwd)  # PODATNOSC (SQLi)
            try:
                row = db.execute(sql).fetchone()
            except Exception as e:
                self._send(500, "link error: " + str(e)); return
            if row:
                self._send(200, "link established (clearance: %s)" % row[0], cookie="sess=" + SESSION)
            else:
                self._send(401, "link rejected")
            return
        self._send(404, "not found")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
