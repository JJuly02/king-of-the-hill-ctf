#!/usr/bin/env python3
"""PoC harness (scoring/anti-cheat + portal + admin panel).
Stands up the scoreboard + dummy TCP services + agents, exercises scenarios 1-12.
Run:  python3 poc/simulate.py [--serve]
"""
import json, os, shutil, socket, subprocess, sys, tempfile, threading, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scoreboard"))
import signing  # noqa

BIND_HOST, BIND_PORT = "127.0.0.1", 18000
BASE = f"http://{BIND_HOST}:{BIND_PORT}"
ADMIN_KEY = "test-green-key"
SVC = {"hill-1": ("127.0.0.1", 19001), "hill-2": ("127.0.0.1", 19002)}
KEYS = {"hill-1": "key-hill-1-aaa", "hill-2": "key-hill-2-bbb"}
TEAMS = {"red": {"token": "TOK-RED-7f3a9c", "code": "red-4f2a91"},
         "blue": {"token": "TOK-BLUE-2e8b41", "code": "blue-9c1d33"},
         "purple": {"token": "TOK-PURPLE-9a1d55", "code": "purple-77b3ee"}}
TOK = {n: v["token"] for n, v in TEAMS.items()}
CODE = {n: v["code"] for n, v in TEAMS.items()}
ALL_TOKENS = ",".join(TOK.values())
PASS = FAIL = 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  \033[32mPASS\033[0m  {name} {extra}")
    else:
        FAIL += 1; print(f"  \033[31mFAIL\033[0m  {name} {extra}")


class Dummy:
    def __init__(self, host, port):
        self.host, self.port, self.sock, self.run = host, port, None, False

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port)); self.sock.listen(16); self.run = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.run:
            try:
                c, _ = self.sock.accept(); c.close()
            except OSError:
                break

    def stop(self):
        self.run = False
        try:
            self.sock.close()
        except Exception:
            pass


def http(path, method="GET", data=None, raw=False):
    url = BASE + path
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            b = r.read()
            return r.status, (b.decode() if raw else json.loads(b.decode()))
    except urllib.error.HTTPError as e:
        b = e.read()
        return e.code, (b.decode() if raw else json.loads(b.decode()))


def state():
    return http("/api/state")[1]


def hill(s, hid):
    return next(h for h in s["hills"] if h["hill"] == hid)


def team_row(s, name):
    return next((r for r in s["board"] if r["team"] == name), {"ticks": 0, "total": 0, "adjust": 0})


def ingest_raw(hid, token, nonce):
    ts = time.time(); msg = signing.canonical_msg(hid, token, nonce, ts)
    return http("/ingest", "POST", {"hill_id": hid, "token": token, "nonce": nonce,
                                    "ts_agent": ts, "sig": signing.sign(KEYS[hid], msg)})


def run_agent_once(king_path, hill_id):
    env = dict(os.environ, KOTH_HILL_ID=hill_id, KOTH_OPS_URL=BASE, KOTH_HMAC_KEY=KEYS[hill_id],
               KOTH_KING=king_path, KOTH_TOKENS=ALL_TOKENS, KOTH_ONCE="1",
               KOTH_NONCE_FILE=king_path + ".nonce")
    return subprocess.run([sys.executable, os.path.join(ROOT, "agent", "agent.py")],
                          env=env, capture_output=True, text=True).stdout.strip()


def main():
    serve = "--serve" in sys.argv
    work = tempfile.mkdtemp(prefix="koth-poc-")
    cfg = os.path.join(work, "config"); os.makedirs(cfg)
    kings = os.path.join(work, "kings"); os.makedirs(kings)
    hills = [{"id": h, "name": h, "service_host": SVC[h][0], "service_port": SVC[h][1],
              "hmac_key": KEYS[h]} for h in SVC]
    json.dump(hills, open(os.path.join(cfg, "hills.json"), "w"))
    json.dump(TEAMS, open(os.path.join(cfg, "teams.json"), "w"))
    json.dump({"tick": 1, "user_flag": 50, "root_flag": 100, "first_blood_bonus": 50,
               "sla_penalty": 30, "hold_threshold_ticks": 600, "agent_beacon_interval_s": 0.5,
               "silence_warn_s": 2, "silence_crit_s": 4, "sla_prober_interval_s": 1,
               "clock_skew_flag_ms": 2000, "max_king_bytes": 64,
               "flag_submit_ratelimit_per_min": 1000}, open(os.path.join(cfg, "scoring.json"), "w"))

    svcs = {h: Dummy(*SVC[h]) for h in SVC}
    for d in svcs.values():
        d.start()
    env = dict(os.environ, KOTH_CONFIG_DIR=cfg, KOTH_DB=os.path.join(work, "koth.db"),
               KOTH_FLAGS=os.path.join(ROOT, "flags", "flags.json"),
               KOTH_BIND=f"{BIND_HOST}:{BIND_PORT}", KOTH_ADMIN_KEY=ADMIN_KEY)
    sb = subprocess.Popen([sys.executable, os.path.join(ROOT, "scoreboard", "scoreboard.py")],
                          env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    for _ in range(50):
        try:
            if http("/healthz")[0] == 200:
                break
        except Exception:
            time.sleep(0.1)
    print(f"\n=== KOTH PoC === work={work}\n")
    agents = []

    def start_agent(hid, king):
        e = dict(os.environ, KOTH_HILL_ID=hid, KOTH_OPS_URL=BASE, KOTH_HMAC_KEY=KEYS[hid],
                 KOTH_KING=king, KOTH_TOKENS=ALL_TOKENS, KOTH_INTERVAL="0.5",
                 KOTH_NONCE_FILE=king + ".nonce")
        p = subprocess.Popen([sys.executable, os.path.join(ROOT, "agent", "agent.py")],
                             env=e, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        agents.append(p); return p

    try:
        print("[1] Red takes a hill")
        k1 = os.path.join(kings, "hill-1.king"); open(k1, "w").write(TOK["red"])
        start_agent("hill-1", k1); time.sleep(3); s = state()
        check("hill-1 owned by red", hill(s, "hill-1")["owner"] == "red")
        check("red has ticks > 0", team_row(s, "red")["ticks"] > 0)

        print("[2] blue overwrites king.txt")
        open(k1, "w").write(TOK["blue"]); time.sleep(3); s = state()
        check("hill-1 owned by blue", hill(s, "hill-1")["owner"] == "blue")

        print("[3] Flag CTF + first blood (with team code)")
        _, r1 = http("/flag", "POST", {"team": "red", "code": CODE["red"], "flag": "CTF{w3b_rc3_1gn1t10n_f00th0ld}"})
        _, r2 = http("/flag", "POST", {"team": "blue", "code": CODE["blue"], "flag": "CTF{w3b_rc3_1gn1t10n_f00th0ld}"})
        _, r3 = http("/flag", "POST", {"team": "purple", "code": CODE["purple"], "flag": "CTF{wrong}"})
        check("red: correct + first blood", r1.get("correct") and r1.get("first_blood"))
        check("blue: correct, NOT first blood", r2.get("correct") and not r2.get("first_blood"))
        check("purple: wrong flag rejected", r3.get("correct") is False)

        print("[4] SLA down -> freeze + penalty")
        before = team_row(state(), "blue")["ticks"]; svcs["hill-1"].stop(); time.sleep(4); s = state()
        check("hill-1 SLA_DOWN", hill(s, "hill-1")["status"] == "SLA_DOWN")
        check("blue ticks frozen", team_row(s, "blue")["ticks"] - before <= 1)
        check("blue got an SLA penalty", team_row(s, "blue")["adjust"] < 0)
        svcs["hill-1"].start(); time.sleep(3)
        check("ticks grow again after SLA UP", team_row(state(), "blue")["ticks"] > before)

        print("[5] Agent silence -> emergency revert")
        k2 = os.path.join(kings, "hill-2.king"); open(k2, "w").write(TOK["purple"])
        a2 = start_agent("hill-2", k2); time.sleep(3); s = state()
        check("hill-2 owned by purple", hill(s, "hill-2")["owner"] == "purple")
        gb = team_row(s, "purple")["ticks"]; a2.terminate(); a2.wait(); time.sleep(6); s = state()
        check("hill-2 NO_AGENT/UNKNOWN", hill(s, "hill-2")["status"] in ("NO_AGENT", "UNKNOWN"))
        check("EMERGENCY_REVERT in events", "EMERGENCY_REVERT" in [e["type"] for e in s["events"]])

        print("[6] Replay rejected")
        c, r = ingest_raw("hill-1", TOK["red"], 1)
        check("replay -> 409", c == 409)

        print("[7] Symlink swap (O_NOFOLLOW)")
        secret = os.path.join(kings, "secret"); open(secret, "w").write(TOK["purple"])
        sym = os.path.join(kings, "sym.king"); os.path.exists(sym) and os.remove(sym); os.symlink(secret, sym)
        check("agent did not follow the symlink", "token=None" in run_agent_once(sym, "hill-1"))

        print("[8] Token fragment rejected (exact match)")
        part = os.path.join(kings, "part.king"); open(part, "w").write("TOK-RED")
        check("fragment rejected", "token=None" in run_agent_once(part, "hill-1"))

        print("[9] Portal: fetch the beacon by code")
        c, txt = http("/beacon?code=" + CODE["red"], raw=True)
        check("beacon red = token red", c == 200 and txt.strip() == TOK["red"], f"({txt.strip()})")
        c2, _ = http("/beacon?code=bad-code", raw=True)
        check("bad beacon code -> 403", c2 == 403)

        print("[10] Flag submit requires a code")
        c, r = http("/flag", "POST", {"team": "red", "code": "zly", "flag": "CTF{x}"})
        check("bad flag code -> 403", c == 403)

        print("[11] Green team: pause a hill -> freeze")
        open(k1, "w").write(TOK["red"]); time.sleep(2)
        http("/admin/pause?k=" + ADMIN_KEY, "POST", {"hill_id": "hill-1", "paused": True})
        s = state(); check("hill-1 PAUSED", hill(s, "hill-1")["status"] == "PAUSED")
        pb = team_row(s, "red")["ticks"]; time.sleep(3)
        check("ticks frozen while paused", team_row(state(), "red")["ticks"] - pb <= 1)
        http("/admin/pause?k=" + ADMIN_KEY, "POST", {"hill_id": "hill-1", "paused": False})
        check("hill-1 resumed", hill(state(), "hill-1")["status"] != "PAUSED")

        print("[12] Green team: manual point adjustment")
        a_before = team_row(state(), "red")["adjust"]
        http("/admin/adjust?k=" + ADMIN_KEY, "POST", {"team": "red", "points": 100})
        check("adjustment +100 applied", team_row(state(), "red")["adjust"] - a_before == 100)
        c, _ = http("/admin/adjust", "POST", {"team": "red", "points": 999})  # without the key
        check("admin without key -> 403", c == 403)

        print(f"\n=== RESULT: {PASS} PASS / {FAIL} FAIL ===\n")
        if serve:
            open(k1, "w").write(TOK["red"])
            print(f"Dashboard:   {BASE}/\nPortal:      {BASE}/team\nGreen team:  {BASE}/admin  (key: {ADMIN_KEY})")
            while True:
                time.sleep(1)
    finally:
        if not serve:
            for p in agents:
                try:
                    p.terminate()
                except Exception:
                    pass
            sb.terminate()
            try:
                sb.wait(timeout=3)
            except Exception:
                sb.kill()
            for d in svcs.values():
                d.stop()
            shutil.rmtree(work, ignore_errors=True)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
