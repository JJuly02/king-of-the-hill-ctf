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
- `agent/` - the beacon agent: it reads a hill's `/root/king.txt` from the host
  (so the signing key never enters the box players get root on), validates it,
  signs a report (HMAC), and sends it to the collector.
- `poc/` - local harnesses that stand up the scoreboard plus simulated hills and
  automatically exercise the whole scoring flow: taking a hill, first blood, SLA
  penalty, agent silence, and rejection of replay / symlink / bad-token reports.

**Hills** (the vulnerable boxes):

- `deploy/hills/` - one `docker-compose` project per hill (self-contained
  vulnerable box, an in-container beacon agent, and a `reset.sh`).
- `deploy/setup-ops.sh` / `deploy/setup-hill.sh` - deploy the scoreboard and the
  hills onto real VMs over SSH.
- `flags/flags.json` - the flags (`user.txt` + `root.txt` on each hill).

## The hills

| Hill | Theme | Entry | Privesc |
| --- | --- | --- | --- |
| hill-1 | NetOps Console | command injection | `sudo find` (GTFOBins) |
| hill-2 | MathLab Compute | unsandboxed `eval()` | SUID bash |
| hill-3 | CacheCTL Admin | admin-login brute force → console RCE | world-writable root cron/hook |
| hill-4 | BuildHub CI | hidden console, weak creds | `sudo tar` (GTFOBins) |
| hill-5 | Doors of Durin (LOTR) | repair boot → command injection | `sudo find` (GTFOBins) |
| hill-6 | Palantir of Orthanc (LOTR) | XXE file read → command console | `sudo awk` (GTFOBins) |
| hill-7 | Barad-dur Watchtower (LOTR) | JWT `alg:none` bypass → RCE | root-cron `PATH` hijack |
| hill-8 | Isengard Forge (LOTR) | weak-cred CI console → build RCE | capability `cap_setuid` |
| hill-9 | Grid Portal / I/O Tower (Tron) | server-side template injection | `sudo sed` (GTFOBins) |

Hills 5-9 are new and ship as an **alpha**: each is validated end to end by the smoke
test, but they have not yet been battle-tested in a live event. The
[design roadmap](docs/CHALLENGE-ROADMAP.md) sketches challenges 10-20.

Each hill's `README.md` describes it in detail. Full walkthroughs are in
[SOLUTIONS.md](SOLUTIONS.md).

The project wiki, including how to add your own hill and how to bring an existing
project onto KOTH, and how the integration with the RedutaCTF platform works, is at
**https://jjuly02.github.io/king-of-the-hill-ctf/**.

## Quick start (local, one host with Docker)

Bring up the hills:

```bash
for d in deploy/hills/*/; do (cd "$d" && docker compose up -d --build); done
```

Run the scoreboard against the sample config (hills reachable on 8081-8089):

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

With the hills running locally:

```bash
bash deploy/smoke-test.sh              # all hills that are up
HILLS="5 6 7 8 9" bash deploy/smoke-test.sh   # or just a subset
```

This walks every hill from entry to root to `king.txt`, and checks that a reset
revives the entry vuln and restores the privesc path.

## Deploying to real machines

See [DEPLOY.md](DEPLOY.md).

## Security model

Everything here is intentionally vulnerable, but the *scoring* is designed to resist
cheating:

- Players get root **inside a hill's container**, never on the host. The beacon agent
  and its per-hill HMAC key run on the **host** and read the container's `king.txt`
  from outside, so a team that roots a hill cannot read the key or forge ownership
  reports to the scoreboard.
- The scoreboard rejects unsigned or replayed ownership reports. Rotate a hill's key
  from the green-team panel if you suspect a leak.
- Set a strong `KOTH_ADMIN_KEY` and `KOTH_TEAM_PASS`, keep team tokens and access
  codes per-team, and replace the demo `hmac_key` values in `config/hills.json`
  (setup-ops.sh does this for you).

## Configuration

- `config/teams.json` - teams, each with a beacon `token` and a portal `code`.
- `config/hills.json` - hill id, SLA probe host/port, per-hill HMAC key, dashboard URL. The committed `hmac_key` values are demo placeholders; `deploy/setup-ops.sh` generates random keys for a real deployment.
- `config/scoring.json` - tick value, flag points, first-blood bonus, SLA penalty, timers.
- `flags/flags.json` - the flags (`CTF{...}`), one user and one root per hill.

The default flag format is `CTF{...}`.
