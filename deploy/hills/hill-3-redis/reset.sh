#!/bin/sh
# Restores the writable hook (misconfig) + perms + service. Does NOT touch king.txt.
echo ':' > /opt/hook.sh; chmod 666 /opt/hook.sh
pgrep -f server.py >/dev/null || su svc -c "python3 /opt/app/server.py &"
echo "[reset] hook.sh (666) + server restored"
