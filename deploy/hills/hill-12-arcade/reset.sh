#!/bin/sh
# Re-arms the PATH-hijack dir + root cron, re-breaks the boot (rescue mode), keeps server.
# Does NOT touch king.txt.
rm -f /opt/arcade/bin/keeper 2>/dev/null
mkdir -p /opt/arcade/bin; chown kevin:kevin /opt/arcade/bin; chmod 775 /opt/arcade/bin
rm -f /opt/arcade/online
pgrep -f arcade-cron >/dev/null || /usr/local/sbin/arcade-cron &
pgrep -f server.py >/dev/null || su kevin -c "python3 /opt/app/server.py &"
echo "[reset] writable PATH dir + root cron + boot re-broken (rescue) + server restored"
