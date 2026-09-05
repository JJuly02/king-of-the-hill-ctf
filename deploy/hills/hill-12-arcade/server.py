#!/usr/bin/env python3
"""hill-12 Flynn's Arcade (Tron) + anti-AI decoys.

  repair  : the arcade cabinet boots into a rescue shell (simulated grub). Fix the boot
            record before the retro-CMS comes online.
  entry   : /view is a local file include; every request's User-Agent is written to the
            access log, and /render evaluates template markers in a file it reads -> classic
            LFI + log-poisoning -> RCE  (user = kevin)
  privesc : a root cron runs `keeper` with a kevin-writable dir first on PATH (PATH hijack)
  flags   : /home/kevin/user.txt (foothold) and /root/root.txt (root)

On a real VM the repair is a genuine broken grub.cfg / emergency mode; in Docker the boot
record is faithfully simulated so it runs anywhere. Marked vulnerabilities: the open() in
/view and the eval in render().
"""
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote_plus

ROBOTS = ("User-agent: anthropic-ai\nDisallow: /\n\n"
          "User-agent: *\nAllow: /\nDisallow: /view\nDisallow: /render\n")
ONLINE = "/opt/arcade/online"
LOG = "/var/log/arcade/access.log"


def render(t):
    def ev(m):
        try:
            return str(eval(m.group(1).strip()))  # PODATNOSC (template eval -> log poisoning to RCE)
        except Exception as e:
            return "[glitch: %s]" % e
    return re.sub(r"\{\{(.*?)\}\}", ev, t, flags=re.S)


def landing():
    state = "ONLINE" if os.path.exists(ONLINE) else "RESCUE MODE (boot record marred)"
    return (
        "<!doctype html><meta charset=utf-8><title>Flynn's Arcade</title>"
        "<style>body{background:#08040f;color:#f6c;font-family:monospace;margin:0}"
        ".wrap{max-width:700px;margin:8vh auto;padding:0 20px}h1{color:#f39}"
        ".card{border:1px solid #a2a;padding:16px;margin:16px 0}code{color:#6cf}</style>"
        "<div class=wrap><h1>FLYNN'S ARCADE</h1>"
        "<p>Cabinet status: <b>" + state + "</b></p>"
        "<div class=card><h2>Rescue console</h2>"
        "<p>Fix the boot record via <code>POST /rescue</code> (cfg=set boot=on), then browse "
        "the CMS at <code>/view?page=...</code> and render pages at <code>/render?page=...</code>.</p>"
        "</div><p style=color:#639>Cabinet telemetry is monitored by the arcade controller.</p></div>"
    )


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _log_ua(self):
        try:
            os.makedirs("/var/log/arcade", exist_ok=True)
            with open(LOG, "a") as f:
                f.write(self.headers.get("User-Agent", "-") + "\n")
        except Exception:
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
        self._log_ua()
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/robots.txt":
            self._send(200, ROBOTS, "text/plain; charset=utf-8"); return
        if u.path == "/":
            self._send(200, landing()); return
        if u.path == "/view":
            if not os.path.exists(ONLINE):
                self._send(503, "cabinet in rescue mode - repair the boot record first"); return
            page = q.get("page", ["/etc/hostname"])[0]
            try:
                self._send(200, open(page).read(), "text/plain; charset=utf-8")  # PODATNOSC (LFI)
            except Exception as e:
                self._send(500, "read error: " + str(e))
            return
        if u.path == "/render":
            if not os.path.exists(ONLINE):
                self._send(503, "cabinet in rescue mode - repair the boot record first"); return
            page = q.get("page", ["/etc/hostname"])[0]
            try:
                self._send(200, render(open(page).read()), "text/plain; charset=utf-8")
            except Exception as e:
                self._send(500, "render error: " + str(e))
            return
        self._send(404, "not found")

    def do_POST(self):
        self._log_ua()
        u = urlparse(self.path)
        if u.path == "/rescue":
            n = int(self.headers.get("Content-Length", "0") or "0")
            body = unquote_plus(self.rfile.read(n).decode("utf-8", "replace"))
            if "set boot=on" in body:
                try:
                    open(ONLINE, "w").write("ok")
                except Exception as e:
                    self._send(500, "repair failed: " + str(e)); return
                self._send(200, "cabinet online: boot record restored")
            else:
                self._send(400, "repair rejected: the boot record still reads boot=off")
            return
        self._send(404, "not found")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), H).serve_forever()
