# Hill 3 - CacheCTL Admin (admin login brute force → console RCE → writable cron/hook)

An internal admin panel behind an administrator login. The admin account uses a
weak password from common wordlists; once in, the maintenance console runs commands.

- **Entry:** brute-force the `admin` login (rockyou-style wordlist), then the console executes commands as `svc`. Port 80 (published on 8083 locally).
- **Foothold:** service account `svc` (console requires a valid session cookie; `/run` returns 403 without it).
- **Privesc:** `/opt/hook.sh` is world-writable and executed by root every ~3 seconds - overwrite it with your payload.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Run locally

    docker compose up -d --build
    # panel: http://localhost:8083/

> The directory name is a legacy label; the challenge is a self-contained login /
> console-RCE box, not a Redis deployment.
