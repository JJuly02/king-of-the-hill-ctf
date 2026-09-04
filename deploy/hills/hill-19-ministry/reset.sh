#!/bin/sh
# Re-arms the world-writable job dir + root cron loop + server. Does NOT touch king.txt.
rm -f /opt/jobs/dispatch.sh 2>/dev/null
mkdir -p /opt/jobs; chown root:root /opt/jobs; chmod 777 /opt/jobs
pgrep -f owl-cron >/dev/null || /usr/local/sbin/owl-cron &
pgrep -f server.py >/dev/null || su owl -c "python3 /opt/app/server.py &"
echo "[reset] world-writable /opt/jobs + root cron loop + server restored"
