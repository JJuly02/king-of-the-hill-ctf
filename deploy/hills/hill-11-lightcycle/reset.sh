#!/bin/sh
# Re-arms the world-writable unit (benign ExecStart) + root loop + server. Does NOT touch king.txt.
mkdir -p /opt/units
cat > /opt/units/arena.service <<'UNIT'
[Unit]
Description=Light Cycle Arena tick
[Service]
ExecStart=/bin/true
UNIT
chown root:root /opt/units/arena.service; chmod 666 /opt/units/arena.service
pgrep -f arena-cron >/dev/null || /usr/local/sbin/arena-cron &
pgrep -f server.py >/dev/null || su flynn -c "python3 /opt/app/server.py &"
echo "[reset] world-writable unit + root loop + server restored"
