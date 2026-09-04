#!/bin/sh
# Re-arms the writable-PATH misconfig + ensures cron loop and server. Does NOT touch king.txt.
rm -f /opt/watchbin/keeper 2>/dev/null
chown watch:watch /opt/watchbin; chmod 775 /opt/watchbin
pgrep -f watch-cron >/dev/null || (/usr/local/sbin/watch-cron &)
pgrep -f server.py  >/dev/null || su watch -c "python3 /opt/app/server.py &"
echo "[reset] writable PATH dir + cron loop + server restored"
