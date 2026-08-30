#!/usr/bin/env python3
"""Green-team log/audit view for the KOTH scoreboard. Reads koth.db (append-only)."""
import sqlite3, json, time, os
BASE = os.environ.get("KOTH_DIR", "/opt/koth")
db = sqlite3.connect(BASE + "/koth.db"); db.row_factory = sqlite3.Row
def q(s, a=()): return db.execute(s, a).fetchall()
cfg = json.load(open(BASE + "/config/teams.json"))
sc = json.load(open(BASE + "/config/scoring.json"))
flags = json.load(open(BASE + "/flags/flags.json"))
tok2team = {v["token"]: n for n, v in cfg.items()}
def hms(t): return time.strftime("%H:%M:%S", time.localtime(t))

print("==== KOTH LOG  %s ====" % time.strftime("%Y-%m-%d %H:%M:%S"))
tk = {n: 0 for n in cfg}
for r in q("select team, coalesce(sum(points),0) n from ticks group by team"):
    nm = tok2team.get(r["team"], r["team"]); tk[nm] = tk.get(nm, 0) + r["n"]
adj = {n: 0 for n in cfg}
for r in q("select details t, coalesce(sum(points),0) p from events where type in ('SLA_PENALTY','ADJUST') group by details"):
    if r["t"] in adj: adj[r["t"]] += r["p"]
fp = {n: 0 for n in cfg}; fb = {n: 0 for n in cfg}
for f in flags:
    r = q("select team from flag_submissions where flag_id=? and correct=1 order by ts_server asc limit 1", (f["flag_id"],))
    if r:
        t = r[0]["team"]
        if t in fp:
            fp[t] += sc["root_flag"] if f["kind"] == "root" else sc["user_flag"]; fb[t] += sc["first_blood_bonus"]
print("\n-- SCORE per team --")
print("   %-8s %6s %6s %6s %7s %8s" % ("team", "ticks", "flags", "fblood", "adjust", "TOTAL"))
for total, n in sorted(((max(0, tk[n]+fp[n]+fb[n]+adj[n]), n) for n in cfg), reverse=True):
    print("   %-8s %6d %6d %6d %7d %8d" % (n, tk[n], fp[n], fb[n], adj[n], total))
print("\n-- OWNER per hill (last valid report) --")
for r in q("select hill_id, team_token from samples where sig_valid=1 and team_token is not null and id in "
           "(select max(id) from samples where sig_valid=1 and team_token is not null group by hill_id) order by hill_id"):
    print("   %s: %s" % (r["hill_id"], tok2team.get(r["team_token"], r["team_token"])))
print("\n-- ANOMALIES (last 10) --")
an = q("select ts_server,hill_id,details from events where type='ANOMALY' order by id desc limit 10")
if not an: print("   none")
for r in an: print("   %s %s %s" % (hms(r["ts_server"]), r["hill_id"], r["details"]))
print("\n-- EVENTS (last 15) --")
for r in q("select ts_server,hill_id,type,details,points from events order by id desc limit 15"):
    p = " (%d)" % r["points"] if r["points"] else ""
    print("   %s [%s] %s %s%s" % (hms(r["ts_server"]), r["type"], r["hill_id"], r["details"] or "", p))
