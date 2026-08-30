# Hill 2 - MathLab Compute (eval RCE → SUID bash)

An online calculator that evaluates arithmetic expressions server-side with no
sandbox, so the expression field is direct code execution.

- **Entry:** unsandboxed `eval()` of user input. Port 80 (published on 8082 locally).
- **Foothold:** service account `www`.
- **Privesc:** a SUID copy of bash at `/usr/local/bin/rootbash` (`rootbash -p` keeps euid 0). Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Run locally

    docker compose up -d --build
    # app: http://localhost:8082/

> The directory name is a legacy label; the challenge is a self-contained eval-RCE
> box, not a Drupal deployment.
