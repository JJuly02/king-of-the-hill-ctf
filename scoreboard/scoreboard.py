#!/usr/bin/env python3
"""KOTH scoreboard: collector + tick engine + SLA prober + flag service +
dashboard + team portal (beacon download) + admin panel (green team).
Pure standard library. Env:
  KOTH_CONFIG_DIR (config), KOTH_FLAGS (flags/flags.json), KOTH_DB (koth.db),
  KOTH_BIND (127.0.0.1:8000), KOTH_ADMIN_KEY (green-admin-changeme)
"""
import base64, hmac, json, os, socket, sys, threading, time, hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import signing
from db import DB
from ui import DASHBOARD, TEAM_PAGE, ADMIN_LOGIN, ADMIN_PAGE, LOGIN_PAGE

CFG_DIR = os.environ.get("KOTH_CONFIG_DIR", "config")
FLAGS_PATH = os.environ.get("KOTH_FLAGS", "flags/flags.json")
DB_PATH = os.environ.get("KOTH_DB", "koth.db")
BIND = os.environ.get("KOTH_BIND", "127.0.0.1:8000")
ADMIN_KEY = os.environ.get("KOTH_ADMIN_KEY", "green-admin-changeme")
REQUIRE_LOGIN = os.environ.get("KOTH_REQUIRE_LOGIN", "1") == "1"
TEAM_PASS = os.environ.get("KOTH_TEAM_PASS", "changeme")
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.svg")
# Cookie login: username = team name, shared password KOTH_TEAM_PASS. The signed
# cookie identifies the team (used to serve that team's beacon).
_LOGIN_PATHS = ("/", "/index.html", "/api/state", "/team", "/beacon", "/mybeacon")


def _sign(team):
    return hmac.new(ADMIN_KEY.encode(), team.encode(), hashlib.sha256).hexdigest()[:16]


def _current_team(headers):
    """Return the team from a valid session cookie, or None."""
    for part in headers.get("Cookie", "").split(";"):
        part = part.strip()
        if part.startswith("koth_sess="):
            team, _, sig = part[len("koth_sess="):].partition(".")
            if team in S.team_code and hmac.compare_digest(sig, _sign(team)):
                return team
    return None


def _need_login(path):
    return REQUIRE_LOGIN and path in _LOGIN_PATHS


def load_json(p):
    with open(p) as f:
        return json.load(f)


class State:
    def __init__(self):
        self.hills = {h["id"]: h for h in load_json(os.path.join(CFG_DIR, "hills.json"))}
        raw = load_json(os.path.join(CFG_DIR, "teams.json"))     # name -> {token, code}
        self.teams = raw
        self.team_by_token = {v["token"]: n for n, v in raw.items()}
        self.team_code = {n: v["code"] for n, v in raw.items()}
        self.token_by_team = {n: v["token"] for n, v in raw.items()}
        self.scoring = load_json(os.path.join(CFG_DIR, "scoring.json"))
        self.db = DB(DB_PATH)
        self.flags = load_json(FLAGS_PATH)
        for f in self.flags:
            self.db.load_flag(f["flag_id"], f["hill_id"], f["kind"],
                              hashlib.sha256(f["flag"].encode()).hexdigest())
        self._nonce = {hid: self.db.last_nonce(hid) for hid in self.hills}
        self._sla_prev = {hid: None for hid in self.hills}
        self._hill_state = {hid: None for hid in self.hills}
        self.paused = set()      # hills with scoring paused (admin)
        self._lock = threading.Lock()

    def key_for(self, hid):
        return self.hills[hid]["hmac_key"]


S = State()

# ---------------- collector ----------------

def handle_ingest(body, ip):
    try:
        r = json.loads(body)
        hid = r["hill_id"]; token = r.get("token"); nonce = int(r["nonce"])
        ts_agent = float(r["ts_agent"]); sig = r.get("sig", "")
    except Exception as e:
        return 400, {"error": f"bad_request:{e}"}
    if hid not in S.hills:
        return 404, {"error": "unknown_hill"}
    ts_server = time.time()
    msg = signing.canonical_msg(hid, token, nonce, ts_agent)
    if not signing.verify(S.key_for(hid), msg, sig):
        S.db.insert_sample(hid, None, 0, nonce, ts_agent, ts_server, ip, 0)
        S.db.insert_event(hid, "ANOMALY", "bad_signature")
        return 400, {"error": "bad_signature"}
    with S._lock:
        if nonce <= S._nonce.get(hid, -1):
            S.db.insert_event(hid, "ANOMALY", f"replay_nonce={nonce}")
            return 409, {"error": "replay"}
        S._nonce[hid] = nonce
    owner = None
    if token:
        if token in S.team_by_token:
            owner = token
        else:
            S.db.insert_event(hid, "ANOMALY", f"unknown_token={token[:16]}")
    skew_ms = int((ts_agent - ts_server) * 1000)
    if abs(skew_ms) > S.scoring["clock_skew_flag_ms"]:
        S.db.insert_event(hid, "ANOMALY", f"clock_skew_ms={skew_ms}")
    S.db.insert_sample(hid, owner, 1, nonce, ts_agent, ts_server, ip, skew_ms)
    return 200, {"ok": True, "owner": S.team_by_token.get(owner) if owner else None}

# ---------------- flag service ----------------

def handle_flag(body, ip):
    try:
        r = json.loads(body)
        team = str(r["team"]); code = str(r.get("code", "")); flag = str(r["flag"])
    except Exception as e:
        return 400, {"error": f"bad_request:{e}"}
    if team not in S.teams or code != S.team_code.get(team):
        return 403, {"error": "bad_team_or_code"}
    now = time.time()
    if S.db.recent_submissions(team, now - 60) >= S.scoring["flag_submit_ratelimit_per_min"]:
        return 429, {"error": "rate_limited"}
    h = hashlib.sha256(flag.encode()).hexdigest()
    rec = S.db.flag_by_hash(h)
    if not rec:
        S.db.insert_submission(team, "UNKNOWN", False)
        return 200, {"correct": False}
    flag_id = rec["flag_id"]
    first_blood = S.db.first_correct(flag_id) is None
    S.db.insert_submission(team, flag_id, True)
    if first_blood:
        S.db.insert_event(rec["hill_id"], "FIRST_BLOOD", f"{team}:{flag_id}")
    return 200, {"correct": True, "flag_id": flag_id, "kind": rec["kind"],
                 "hill": rec["hill_id"], "first_blood": first_blood}

# ---------------- tick engine ----------------

def tick_engine():
    sc = S.scoring
    while True:
        now = time.time(); sec = int(now)
        for hid in S.hills:
            if hid in S.paused:
                if S._hill_state.get(hid) != "PAUSED":
                    S._hill_state[hid] = "PAUSED"
                continue
            sla = S.db.latest_sla(hid, now - 3 * sc["sla_prober_interval_s"])
            owner = S.db.latest_valid_owner(hid, now - sc["silence_warn_s"])
            last_ts = S.db.last_any_sample_ts(hid)
            silent = (now - last_ts) if last_ts else 1e9
            if last_ts == 0:
                new_state = "NO_AGENT"          # never reported yet: no revert event at startup
            elif silent > sc["silence_crit_s"]:
                new_state = "EMERGENCY_REVERT"
            elif silent > sc["silence_warn_s"]:
                new_state = "AGENT_SILENT"
            elif sla == "DOWN":
                new_state = "SLA_DOWN"
            elif owner:
                new_state = f"OWNED:{owner}"
                if sec % int(sc.get("tick_award_interval_s", 1)) == 0:
                    S.db.award_tick(sec, hid, owner, int(sc.get("tick", 1)))
            else:
                new_state = "NEUTRAL"
            prev = S._hill_state.get(hid)
            if new_state != prev:
                if new_state == "AGENT_SILENT":
                    S.db.insert_event(hid, "AGENT_SILENT", f"silent>{sc['silence_warn_s']}s")
                elif new_state == "EMERGENCY_REVERT":
                    S.db.insert_event(hid, "EMERGENCY_REVERT",
                                      f"silent>{sc['silence_crit_s']}s -> forced revert")
                S._hill_state[hid] = new_state
        time.sleep(0.25)

# ---------------- SLA prober ----------------

def sla_prober():
    sc = S.scoring
    while True:
        for hid, h in S.hills.items():
            host, port = h["service_host"], int(h["service_port"])
            t0 = time.time(); status = "DOWN"; lat = -1
            try:
                with socket.create_connection((host, port), timeout=1.0):
                    status = "UP"; lat = int((time.time() - t0) * 1000)
            except Exception:
                status = "DOWN"
            S.db.insert_sla(hid, status, lat)
            prev = S._sla_prev.get(hid)
            if prev == "UP" and status == "DOWN":
                owner = S.db.latest_valid_owner(hid, time.time() - 30)
                team = S.team_by_token.get(owner) if owner else "?"
                S.db.insert_event(hid, "SLA_DOWN", f"service {host}:{port} down")
                if owner:
                    S.db.insert_event(hid, "SLA_PENALTY", team, points=-sc["sla_penalty"])
            elif prev == "DOWN" and status == "UP":
                S.db.insert_event(hid, "SLA_UP", f"service {host}:{port} up")
            S._sla_prev[hid] = status
        time.sleep(sc["sla_prober_interval_s"])

# ---------------- view / leaderboard ----------------

def compute_state(admin=False):
    sc = S.scoring
    now = time.time()
    names = list(S.teams)
    tk = {n: 0 for n in names}
    for row in S.db.ticks_per_team():
        n = S.team_by_token.get(row["team"], row["team"]); tk[n] = tk.get(n, 0) + row["n"]
    hold = {}
    for row in S.db.ticks_per_team_hill():
        n = S.team_by_token.get(row["team"], row["team"])
        hold.setdefault(n, {})[row["hill_id"]] = row["n"]
    flag_pts = {n: 0 for n in names}; fb = {n: 0 for n in names}
    for f in S.flags:
        fc = S.db.first_correct(f["flag_id"])
        if fc:
            n = fc["team"]; flag_pts[n] = flag_pts.get(n, 0) + (sc["root_flag"] if f["kind"] == "root" else sc["user_flag"])
            fb[n] = fb.get(n, 0) + sc["first_blood_bonus"]
    adj = {n: 0 for n in names}
    for row in S.db.adjustments_per_team():
        if row["team"] in adj:
            adj[row["team"]] += (row["pts"] or 0)
    board = []
    for n in names:
        total = max(0, tk[n] + flag_pts[n] + fb[n] + adj[n])  # tk[n] already sums per-tick points; never negative
        board.append({"team": n, "ticks": tk[n], "flag_pts": flag_pts[n],
                      "first_blood": fb[n], "adjust": adj[n], "total": total})
    board.sort(key=lambda x: -x["total"])
    hills = []
    for hid in S.hills:
        sla = S.db.latest_sla(hid, now - 10)
        owner = S.db.latest_valid_owner(hid, now - sc["silence_warn_s"])
        last_ts = S.db.last_any_sample_ts(hid)
        silent = (now - last_ts) if last_ts else 1e9
        if hid in S.paused:
            st = "PAUSED"
        elif sla == "DOWN":
            st = "SLA_DOWN"
        elif silent > sc["silence_crit_s"]:
            st = "NO_AGENT"
        elif silent > sc["silence_warn_s"]:
            st = "UNKNOWN"
        elif owner:
            st = "OWNED"
        else:
            st = "NEUTRAL"
        hills.append({"hill": hid, "status": st, "url": S.hills[hid].get("url", ""),
                      "owner": S.team_by_token.get(owner) if owner else None})
    out = {"board": board, "hills": hills, "hold": hold, "threshold": sc["hold_threshold_ticks"],
           "now": now, "events": [dict(hill=e["hill_id"], type=e["type"], details=e["details"],
                                        points=e["points"], ts=e["ts_server"]) for e in S.db.all_events(60)]}
    return out

# ---------------- HTTP ----------------

def is_admin(qs, headers):
    return qs.get("k", [""])[0] == ADMIN_KEY or headers.get("X-Admin-Key", "") == ADMIN_KEY


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj, ctype="application/json", extra=None):
        body = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _read(self):
        n = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(n).decode() if n else ""

    def do_GET(self):
        u = urlparse(self.path); qs = parse_qs(u.query)
        if u.path == "/assets/logo.svg":
            try:
                with open(LOGO_PATH, "rb") as f:
                    self._send(200, f.read(), "image/svg+xml")
            except Exception:
                self._send(404, {"error": "no_logo"})
            return
        if u.path == "/healthz":
            self._send(200, {"ok": True}); return
        if u.path == "/logout":
            self.send_response(302)
            self.send_header("Set-Cookie", "koth_sess=; Path=/; Max-Age=0")
            self.send_header("Location", "/")
            self.send_header("Content-Length", "0"); self.end_headers()
            return
        if u.path == "/whoami":
            self._send(200, {"team": _current_team(self.headers)}); return
        if _need_login(u.path) and not _current_team(self.headers):
            if u.path in ("/", "/index.html"):
                self._send(200, LOGIN_PAGE.encode(), "text/html; charset=utf-8")
            else:
                self._send(401, {"error": "login_required"})
            return
        if u.path == "/mybeacon":
            user = _current_team(self.headers)
            if not user or user not in S.token_by_team:
                self._send(403, {"error": "no_team"}); return
            self._send(200, (S.token_by_team[user] + "\n").encode(),
                       "text/plain; charset=utf-8",
                       {"Content-Disposition": 'attachment; filename="king.txt"'})
            return
        if u.path in ("/", "/index.html"):
            self._send(200, DASHBOARD.encode(), "text/html; charset=utf-8")
        elif u.path == "/team":
            self._send(200, TEAM_PAGE.encode(), "text/html; charset=utf-8")
        elif u.path == "/admin":
            if not is_admin(qs, self.headers):
                self._send(200, ADMIN_LOGIN.encode(), "text/html; charset=utf-8"); return
            self._send(200, ADMIN_PAGE.encode(), "text/html; charset=utf-8")
        elif u.path == "/api/state":
            self._send(200, compute_state())
        elif u.path == "/api/admin/state":
            if not is_admin(qs, self.headers):
                self._send(403, {"error": "forbidden"}); return
            st = compute_state(admin=True); st["paused"] = list(S.paused)
            st["hill_keys"] = {h: S.hills[h]["hmac_key"][:6] + "..." for h in S.hills}
            self._send(200, st)
        elif u.path == "/beacon":
            code = qs.get("code", [""])[0]
            team = next((n for n, c in S.team_code.items() if c == code), None)
            if not team:
                self._send(403, {"error": "bad_code"}); return
            token = S.token_by_team[team]
            self._send(200, (token + "\n").encode(), "text/plain; charset=utf-8",
                       {"Content-Disposition": 'attachment; filename="king.txt"'})
        elif u.path == "/healthz":
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not_found"})

    def do_POST(self):
        u = urlparse(self.path); qs = parse_qs(u.query)
        ip = self.client_address[0]; body = self._read()
        if u.path == "/login":
            form = parse_qs(body)
            team = form.get("team", [""])[0].strip()
            pw = form.get("password", [""])[0]
            self.send_response(302)
            if team in S.team_code and pw == TEAM_PASS:
                self.send_header("Set-Cookie",
                                 f"koth_sess={team}.{_sign(team)}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400")
                self.send_header("Location", "/")
            else:
                self.send_header("Location", "/?e=1")
            self.send_header("Content-Length", "0"); self.end_headers()
            return
        if u.path == "/ingest":
            self._send(*handle_ingest(body, ip))
        elif u.path == "/flag":
            self._send(*handle_flag(body, ip))
        elif u.path.startswith("/admin/"):
            if not is_admin(qs, self.headers):
                self._send(403, {"error": "forbidden"}); return
            self._admin(u.path, body)
        else:
            self._send(404, {"error": "not_found"})

    def _admin(self, path, body):
        try:
            r = json.loads(body) if body else {}
        except Exception as e:
            self._send(400, {"error": str(e)}); return
        if path == "/admin/pause":
            hid = r["hill_id"]
            if r.get("paused"):
                S.paused.add(hid); S.db.insert_event(hid, "ADMIN_PAUSE", "scoring paused")
            else:
                S.paused.discard(hid); S.db.insert_event(hid, "ADMIN_RESUME", "scoring resumed")
            self._send(200, {"ok": True, "paused": list(S.paused)})
        elif path == "/admin/rotate":
            hid = r["hill_id"]; S.hills[hid]["hmac_key"] = r["new_key"]
            S.db.insert_event(hid, "KEY_ROTATED", "reset / key rotation")
            self._send(200, {"ok": True})
        elif path == "/admin/adjust":
            team = r["team"]; pts = int(r["points"])
            if team not in S.teams:
                self._send(400, {"error": "unknown_team"}); return
            S.db.insert_event(r.get("hill_id", "-"), "ADJUST", team, points=pts)
            self._send(200, {"ok": True})
        elif path == "/admin/revert":
            hid = r["hill_id"]
            S.db.insert_event(hid, "MANUAL_REVERT", r.get("reason", "green team"))
            self._send(200, {"ok": True, "note": "on the VM: run reset.sh / systemctl on the hill"})
        else:
            self._send(404, {"error": "unknown_admin_action"})



def main():
    threading.Thread(target=tick_engine, daemon=True).start()
    threading.Thread(target=sla_prober, daemon=True).start()
    host, port = BIND.split(":")
    srv = ThreadingHTTPServer((host, int(port)), H)
    print(f"[scoreboard] http://{host}:{port}  db={DB_PATH}  hills={list(S.hills)}  admin_key={ADMIN_KEY}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
