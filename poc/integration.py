#!/usr/bin/env python3
"""Integration test: real hill containers + an agent in each + the scoreboard.
Checks the full loop: fetch the beacon -> plant it on a hill (king.txt) ->
scoreboard shows the owner + ticks; SLA against a live container; green-team control.
Requires the koth-hill-1..4 containers running (docker compose up in each).
"""
import json, os, subprocess, sys, tempfile, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIND_PORT = 18001
BASE = f"http://127.0.0.1:{BIND_PORT}"
ADMIN_KEY = "test-green-key"
HILLS = {"hill-1": 8081, "hill-2": 8082, "hill-3": 8083, "hill-4": 8084}
CONT = {h: f"koth-{h}" for h in HILLS}
KEYS = {h: f"itest-key-{h}" for h in HILLS}
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


def http(path, method="GET", data=None, raw=False):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=4) as r:
            b = r.read(); return r.status, (b.decode() if raw else json.loads(b.decode()))
    except urllib.error.HTTPError as e:
        b = e.read(); return e.code, (b.decode() if raw else json.loads(b.decode()))


def state():
    return http("/api/state")[1]


def hill(s, hid):
    return next(h for h in s["hills"] if h["hill"] == hid)


def team_row(s, name):
    return next((r for r in s["board"] if r["team"] == name), {"ticks": 0})


def dexec(cont, *cmd, detach=False):
    base = ["docker", "exec"] + (["-d"] if detach else []) + [cont]
    return subprocess.run(base + list(cmd), capture_output=True, text=True)


def containers_up():
    out = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True).stdout
    return all(CONT[h] in out for h in HILLS)


def main():
    if not containers_up():
        print("!! Containers koth-hill-1..4 are not running. Start them: for d in deploy/hills/*/; do (cd $d && docker compose up -d --build); done")
        sys.exit(2)

    work = tempfile.mkdtemp(prefix="koth-itest-")
    cfg = os.path.join(work, "config"); os.makedirs(cfg)
    hills = [{"id": h, "name": h, "service_host": "127.0.0.1", "service_port": HILLS[h],
              "hmac_key": KEYS[h]} for h in HILLS]
    json.dump(hills, open(os.path.join(cfg, "hills.json"), "w"))
    json.dump(TEAMS, open(os.path.join(cfg, "teams.json"), "w"))
    json.dump({"tick": 1, "user_flag": 50, "root_flag": 100, "first_blood_bonus": 50,
               "sla_penalty": 30, "hold_threshold_ticks": 600, "agent_beacon_interval_s": 1,
               "silence_warn_s": 3, "silence_crit_s": 8, "sla_prober_interval_s": 2,
               "clock_skew_flag_ms": 2000, "max_king_bytes": 64,
               "flag_submit_ratelimit_per_min": 1000}, open(os.path.join(cfg, "scoring.json"), "w"))

    env = dict(os.environ, KOTH_CONFIG_DIR=cfg, KOTH_DB=os.path.join(work, "koth.db"),
               KOTH_FLAGS=os.path.join(ROOT, "flags", "flags.json"),
               KOTH_BIND=f"0.0.0.0:{BIND_PORT}", KOTH_ADMIN_KEY=ADMIN_KEY, KOTH_REQUIRE_LOGIN="0")
    sb = subprocess.Popen([sys.executable, os.path.join(ROOT, "scoreboard", "scoreboard.py")],
                          env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    for _ in range(50):
        try:
            if http("/healthz")[0] == 200:
                break
        except Exception:
            time.sleep(0.1)
    print(f"\n=== KOTH INTEGRATION TEST === scoreboard {BASE}\n")

    agents = []
    try:
        # run one beacon agent per hill ON THE HOST (HMAC key stays off the box);
        # each agent reads the container's king.txt via docker exec
        print("[A] Starting host-side beacon agents (key never enters the container)")
        for h in HILLS:
            e = dict(os.environ, KOTH_HILL_ID=h, KOTH_OPS_URL=BASE, KOTH_HMAC_KEY=KEYS[h],
                     KOTH_TOKENS=ALL_TOKENS, KOTH_INTERVAL="1",
                     KOTH_READ_CMD=f"docker exec {CONT[h]} cat /root/king.txt",
                     KOTH_NONCE_FILE=os.path.join(work, f"nonce-{h}"))
            agents.append(subprocess.Popen([sys.executable, os.path.join(ROOT, "agent", "agent.py")],
                                           env=e, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        time.sleep(5)
        s = state()
        check("SLA: all 4 hills UP (not SLA_DOWN)",
              all(hill(s, h)["status"] != "SLA_DOWN" for h in HILLS))
        check("agents reporting (hills not NO_AGENT)",
              all(hill(s, h)["status"] != "NO_AGENT" for h in HILLS),
              f'({[(h,hill(s,h)["status"]) for h in HILLS]})')

        # FULL BEACON LOOP: fetch the beacon -> plant it on a hill -> scoreboard sees the owner
        print("[B] Full beacon loop (fetch -> plant -> take)")
        placement = {"hill-1": "red", "hill-2": "blue", "hill-3": "purple", "hill-4": "red"}
        for h, team in placement.items():
            code = CODE[team]
            c, token = http("/beacon?code=" + code, raw=True)   # team fetches its own beacon
            token = token.strip()
            check(f"{team} fetched beacon = its own token", c == 200 and token == TOK[team])
            # the team plants the beacon on the compromised host (as root)
            dexec(CONT[h], "sh", "-c", f"echo {token} > /root/king.txt")
        time.sleep(4)
        s = state()
        for h, team in placement.items():
            check(f"{h}: scoreboard shows owner {team}", hill(s, h)["owner"] == team,
                  f'(owner={hill(s,h)["owner"]}, status={hill(s,h)["status"]})')
        check("red collects ticks from 2 hills", team_row(s, "red")["ticks"] > 0,
              f'(ticks={team_row(s,"red")["ticks"]})')

        # ownership change on a live hill
        print("[C] Overwrite beacon (owner change hill-1 red->purple)")
        dexec(CONT["hill-1"], "sh", "-c", f"echo {TOK['purple']} > /root/king.txt")
        time.sleep(4)
        check("hill-1 taken by purple", hill(state(), "hill-1")["owner"] == "purple")

        # green team: pause a real hill
        print("[D] Green team: pause hill-2 -> freeze ticks")
        http("/admin/pause?k=" + ADMIN_KEY, "POST", {"hill_id": "hill-2", "paused": True})
        s = state(); check("hill-2 PAUSED", hill(s, "hill-2")["status"] == "PAUSED")
        pb = team_row(s, "blue")["ticks"]; time.sleep(3)
        check("blue ticks frozen while paused", team_row(state(), "blue")["ticks"] - pb <= 1)
        http("/admin/pause?k=" + ADMIN_KEY, "POST", {"hill_id": "hill-2", "paused": False})

        # SLA on a live container: stop the container -> SLA_DOWN
        print("[E] SLA: docker stop hill-4 -> SLA_DOWN, then start")
        subprocess.run(["docker", "stop", CONT["hill-4"]], capture_output=True)
        time.sleep(6)
        check("hill-4 SLA_DOWN after stopping the container",
              hill(state(), "hill-4")["status"] in ("SLA_DOWN", "NO_AGENT"),
              f'(status={hill(state(),"hill-4")["status"]})')
        subprocess.run(["docker", "start", CONT["hill-4"]], capture_output=True)

        print(f"\n=== INTEGRATION RESULT: {PASS} PASS / {FAIL} FAIL ===\n")
    finally:
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
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
