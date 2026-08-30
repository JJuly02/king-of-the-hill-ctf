# Hill 1 - NetOps Console (command injection → sudo/find)

A network-diagnostics web panel that runs connectivity checks using a value you
supply. The value is passed to a shell, so it is a classic command-injection
foothold.

- **Entry:** command injection in a request parameter (`shell=True`). Port 80 (published on 8081 locally).
- **Foothold:** service account `www`.
- **Privesc:** `sudo NOPASSWD /usr/bin/find` (GTFOBins). Restored from a golden copy on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Run locally

    docker compose up -d --build
    # panel: http://localhost:8081/

Reset (revives the entry vuln and restores the privesc path) is `reset.sh` inside
the container; on a full deployment a timer runs it every 15 minutes.
