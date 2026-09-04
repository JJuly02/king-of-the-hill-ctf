#!/bin/sh
# Re-applies the cap_setuid capability + server. Does NOT touch king.txt.
[ -x /usr/local/bin/forgepy ] || cp "$(readlink -f "$(command -v python3)")" /usr/local/bin/forgepy
setcap cap_setuid+ep /usr/local/bin/forgepy
pgrep -f server.py >/dev/null || su orc -c "python3 /opt/app/server.py &"
echo "[reset] cap_setuid on forgepy + server restored"
