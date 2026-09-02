#!/bin/sh
# Revives the planned privesc path from golden. Does NOT touch king.txt.
cp /opt/golden/sudoers.golden /etc/sudoers.d/arena
chmod 440 /etc/sudoers.d/arena
# if someone killed the arena server, bring it back up
pgrep -f server.py >/dev/null || (su arena -c "python3 /opt/app/server.py &")
echo "[reset] restored sudoers + arena server"
