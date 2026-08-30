# DEPLOY - King of the Hill

Deploying to real machines: one VM per hill plus one "ops" VM for the scoreboard,
team portal, and green-team panel. Each hill runs as a container with the beacon
agent **inside** it; reset and monitoring run from the host / ops.

You can also run everything on a single host for testing - see the Quick start in
[README.md](README.md). This document covers a multi-VM deployment.

## 0. Requirements

Per VM: a recent Linux (e.g. Ubuntu 22.04), root over SSH, outbound internet, and
Docker. Suggested roles and ports:

| VM | Role | Player port | SLA prober checks |
| --- | --- | --- | --- |
| hill-1 | web-rce (command injection) | 8081 | hill-1:8081 |
| hill-2 | eval RCE | 8082 | hill-2:8082 |
| hill-3 | login brute → RCE | 8083 | hill-3:8083 |
| hill-4 | weak creds → RCE | 8084 | hill-4:8084 |
| ops | scoreboard + portal + panel | 8000 | - |

> You can standardize on port 80 per hill (one hill = one VM). If you do, change
> the mapping in `deploy/hills/*/docker-compose.yml` and `service_port` in
> `config/hills.json`.

## 1. Ops VM - scoreboard

```bash
git clone <repo> koth && cd koth
sudo KOTH_ADMIN_KEY='PICK-A-STRONG-KEY' KOTH_TEAM_PASS='PICK-A-TEAM-PASSWORD' \
     KOTH_BIND=0.0.0.0:8000 bash deploy/setup-ops.sh
```

The script:

- installs the scoreboard as a `systemd` service (`koth-scoreboard`),
- **generates a random per-hill HMAC key** and prints them at the end - save them,
  you need them in step 2,
- writes `/opt/koth/config/hills.json` with **IP placeholders** (`HILL_IP_1..4`).

After it runs, **edit `/opt/koth/config/hills.json`**: set the real `service_host`
(hill IPs) and `service_port` (8081..8084), then
`sudo systemctl restart koth-scoreboard`.

Check: `http://OPS_IP:8000/` (scoreboard), `/team` (portal),
`/admin?k=<KEY>` (green team).

## 2. Each hill VM - service + agent + reset

On hill-1 (repeat for 2/3/4 with the right type and key from step 1):

```bash
cd koth
sudo bash deploy/setup-hill.sh web-rce  <OPS_IP> hill-1 <HILL-1_KEY> 8081
# hill-2:  ... drupal  <OPS_IP> hill-2 <HILL-2_KEY> 8082
# hill-3:  ... redis   <OPS_IP> hill-3 <HILL-3_KEY> 8083
# hill-4:  ... jenkins <OPS_IP> hill-4 <HILL-4_KEY> 8084
```

(The first argument is the hill type; the `drupal` / `redis` / `jenkins` labels are
just the directory names for hill-2 / hill-3 / hill-4.)

The script does `docker compose up` for the hill, launches the in-container beacon
agent, and installs a `systemd` timer that resets every 15 minutes (revives the
vuln, keeps the agent alive, and **does not touch `king.txt`**).

## 3. Network

- players reach hills on 8081..8084 and ops on 8000,
- hills reach ops:8000 (beacon reports) - internal traffic,
- ops reaches hills:808x (SLA prober),
- SSH (22) restricted to your admin IP; everything else denied.

Run players over a controlled path (VPN or a source-IP allowlist). Keep the scoring
infrastructure (ops:8000) and management (SSH) off-limits to players.

## 4. Team onboarding

- Each team gets a **name + access code** from `config/teams.json` (the defaults are
  red/blue/purple - replace them with real teams and random codes).
- A team opens `http://OPS:8000/team`, reveals its beacon command by access code,
  and runs it as root on a hill it controls to write its token to `/root/king.txt`
  and start scoring.
- Teams log in to the scoreboard with their team name and the shared
  `KOTH_TEAM_PASS`.
- **Tokens and codes must not leak between teams** - that is the only anti-impersonation secret.

## 5. Green team - control panel

`http://OPS:8000/admin?k=<ADMIN_KEY>`:

- **Pause / Resume** scoring for a hill (dispute, outage).
- **Rotate** a hill's HMAC key (invalidates a stolen key).
- **Revert** - writes an audit-log entry; the real revert on the VM is
  `sudo systemctl start koth-reset` on that hill (or recreate the container).
- **Manual point adjustment** (± points) with a reason.
- Everything lands in the **audit log** for dispute resolution.

## 6. Reset levels

1. **Automatic, every 15 minutes** (`koth-reset.timer` on the hill): `reset.sh`
   inside the container restores the entry vulnerability and the privesc path from a
   golden copy, restarts the service if someone killed it, and keeps the agent
   alive. It does **not** touch `king.txt` (ownership stays). So the entry point
   cannot be patched shut for good.
2. **Hard reset to pristine state** (on demand): recreate the container from its
   image, which drops every attacker change and clears `king.txt`:
   ```bash
   cd deploy/hills/hill-1-web-rce && docker compose up -d --force-recreate
   /opt/koth/launch-agent.sh   # re-attach the beacon agent
   ```

Note: teams get root **inside the container**, not on the host (no docker socket,
no `NET_ADMIN`). They cannot firewall the port; the realistic denial vector is
killing the service, which the 15-minute reset restarts and which costs the last
owner an SLA penalty when the prober sees it go DOWN. The host stays under green-team
control over SSH.

## 7. Verify before start

```bash
# on ops (must reach the hills):
bash deploy/smoke-test.sh     # 4 chains + CTF flags + reset (adjust IPs/ports)
python3 poc/integration.py    # full beacon loop + SLA + panel
```

Checklist: every hill reaches root, `king.txt` is written, the agent reports, SLA is
UP, pause/adjust work, flags submit.

## 8. Teardown

- `docker compose down` on the hills, `systemctl disable --now koth-*`.
- Keep the audit log (`/opt/koth/koth.db`) if you want a record of the game.
