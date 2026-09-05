#!/usr/bin/env python3
"""hill-16 Unobtainium Refinery (Avatar) + anti-AI decoys.

  repair  : the refinery boots offline (coolant mount down). Bring it online through the
            repair console before the calibration endpoint will run.
  entry   : the calibration formula is eval'd server-side -> RCE  (user = refiner)
  privesc : sudoers lets refiner run env as root (GTFOBins)
  flags   : /home/refiner/user.txt (foothold) and /root/root.txt (root)

The one clearly-marked vulnerability is the eval in /calibrate (reachable once repaired).
"""
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROBOTS = ("User-agent: anthropic-ai\nDisallow: /\n\n"
          "User-agent: *\nAllow: /\nDisallow: /calibrate\n")
ONLINE = "/opt/refinery/online"


def landing():
    state = "ONLINE" if os.path.exists(ONLINE) else "OFFLINE (coolant mount down)"
    return (
        "<!doctype html><meta charset=utf-8><title>Unobtainium Refinery</title>"
        "<style>body{background:#0a0c0d;color:#bfe;font-family:monospace;margin:0}"
        ".wrap{max-width:700px;margin:8vh auto;padding:0 20px}h1{color:#4fd0c0}"
        ".card{border:1px solid #297;padding:16px;margin:16px 0}code{color:#fd6}</style>"
        "<div class=wrap><h1>UNOBTAINIUM REFINERY</h1>"
        "<p>Refinery status: <b>" + state + "</b></p>"
        "<div class=card><h2>Repair console</h2>"
        "<p>Restore the coolant mount via <code>/repair?mount=core-7&amp;coolant=on</code>, "
        "then submit a calibration to <code>/calibrate?formula=...</code>.</p></div>"
        "<p style=color:#354>Refinery control is monitored by RDA Operations.</p></div>"
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
            if q.get("mount", [""])[0] == "core-7" and q.get("coolant", [""])[0] == "on":
                try:
                    open(ONLINE, "w").write("ok")
                except Exception as e:
                    self._send(500, "repair failed: " + str(e)); return
                self._send(200, "refinery online: coolant mount restored")
            else:
                self._send(400, "repair rejected: set mount=core-7 and coolant=on")
            return
        if u.path == "/calibrate":
            if not os.path.exists(ONLINE):
                self._send(503, "refinery offline - repair the coolant mount first"); return
            formula = q.get("formula", ["1+1"])[0]
            try:
                self._send(200, "calibration = " + str(eval(formula)))  # PODATNOSC (eval RCE)
            except Exception as e:
                self._send(500, "calibration error: " + str(e))
            return
        self._send(404, "not found")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
