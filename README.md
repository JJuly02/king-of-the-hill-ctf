# King of the Hill (KOTH)

A self-hostable **King of the Hill** CTF platform. Several machines ("hills") each
run a vulnerable service. Teams break in through the service, escalate to root,
write their team token to `/root/king.txt`, and then **defend** the box. Points
accrue for time spent holding a hill (a periodic tick) plus captured flags and
first bloods.

The entry vulnerability and privilege-escalation path on every hill are restored
on a schedule, so a box cannot be permanently patched shut. Defense has to be
active: monitor, kick other teams' sessions, and overwrite their `king.txt`.

Everything here is **intentionally vulnerable** and meant to run on an isolated
network or lab. Do not expose these services to the public internet or run them on
machines you care about.

## Two layers

**Scoring / anti-cheat core** (pure Python standard library, no dependencies):

- `scoreboard/` - collector for beacon reports, tick engine, flag service (with
  first blood), SLA prober, live dashboard, team portal, green-team admin panel,
  append-only audit log. SQLite + `http.server` + HMAC.
- `agent/` - the beacon agent that runs as root on a hill: it reads
  `/root/king.txt`, validates it, signs a report (HMAC), and sends it to the
  collector.
- `poc/` - local harnesses that stand up the scoreboard plus simulated hills and
  automatically exercise the whole scoring flow: taking a hill, first blood, SLA
  penalty, agent silence, and rejection of replay / symlink / bad-token reports.

**Hills** (the vulnerable boxes):

- `deploy/hills/` - one `docker-compose` project per hill (self-contained
  vulnerable box, an in-container beacon agent, and a `reset.sh`).
- `deploy/setup-ops.sh` / `deploy/setup-hill.sh` - deploy the scoreboard and the
  hills onto real VMs over SSH.
- `flags/flags.json` - the eight flags (`user.txt` + `root.txt` on four hills).

## The four hills

| Hill | Theme | Entry | Privesc |
| --- | --- | --- | --- |
| hill-1 | NetOps Console | command injection | `sudo find` (GTFOBins) |
| hill-2 | MathLab Compute | unsandboxed `eval()` | SUID bash |
| hill-3 | CacheCTL Admin | admin-login brute force → console RCE | world-writable root cron/hook |
| hill-4 | BuildHub CI | hidden console, weak creds | `sudo tar` (GTFOBins) |

Each hill's `README.md` describes it in detail. Full walkthroughs are in
[SOLUTIONS.md](SOLUTIONS.md).

## Quick start (local, one host with Docker)

Bring up the four hills:

```bash
for d in deploy/hills/*/; do (cd "$d" && docker compose up -d --build); done
```

Run the scoreboard against the sample config (hills reachable on 8081-8084):

```bash
cd scoreboard
KOTH_CONFIG_DIR=../config KOTH_FLAGS=../flags/flags.json \
KOTH_BIND=0.0.0.0:8000 KOTH_ADMIN_KEY=change-me KOTH_TEAM_PASS=change-me \
python3 scoreboard.py
```

Then open:

- `http://localhost:8000/` - scoreboard and team login (username = team name from
  `config/teams.json`, password = `KOTH_TEAM_PASS`).
- `http://localhost:8000/team` - team portal (reveal your beacon command by access code).
- `http://localhost:8000/admin?k=<KOTH_ADMIN_KEY>` - green-team control (pause,
  rotate keys, revert, manual point adjustment).

To claim a hill, get root on it and write your team token to `/root/king.txt`
(the portal gives you the exact command). The in-container agent reports it and the
tick engine starts scoring your team.

Want a fully scripted demo without deploying anything? See `poc/` - for example
`python3 poc/simulate.py` runs the scoring scenarios end to end.

## Verify the challenges

With the four hills running locally:

```bash
bash deploy/smoke-test.sh
```

This walks every hill from entry to root to `king.txt`, and checks that a reset
revives the entry vuln and restores the privesc path.

## Deploying to real machines

See [DEPLOY.md](DEPLOY.md).

## Configuration

- `config/teams.json` - teams, each with a beacon `token` and a portal `code`.
- `config/hills.json` - hill id, SLA probe host/port, per-hill HMAC key, dashboard URL.
- `config/scoring.json` - tick value, flag points, first-blood bonus, SLA penalty, timers.
- `flags/flags.json` - the flags (`CTF{...}`), one user and one root per hill.

The default flag format is `CTF{...}`.
