#!/bin/sh
# Restores the sudo perl privesc + server. Does NOT touch king.txt.
cp /opt/golden/sudoers.golden /etc/sudoers.d/navi; chmod 440 /etc/sudoers.d/navi
pgrep -f server.py >/dev/null || su navi -c "python3 /opt/app/server.py &"
echo "[reset] sudo perl privesc + server restored"
