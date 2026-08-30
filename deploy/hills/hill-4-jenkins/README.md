# Hill 4 - BuildHub CI (weak creds → script console eval → sudo/tar)

A CI build server whose operator script console is not linked from the UI and sits
behind weak HTTP auth. Discover it, authenticate, and you have authenticated eval RCE.

- **Entry:** hidden `/script` console (listed in `/robots.txt`, or found by fuzzing) behind Basic auth `admin:admin`. Port 80 (published on 8084 locally).
- **Foothold:** service account `jenkins`.
- **Privesc:** `sudo NOPASSWD /usr/bin/tar` (GTFOBins `--checkpoint-action=exec`). Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Run locally

    docker compose up -d --build
    # app: http://localhost:8084/

> The directory name is a legacy label; the challenge is a self-contained
> weak-creds / eval-RCE box, not a Jenkins deployment.
