#!/bin/sh
# Restores sudo sed privesc + server. Does NOT touch king.txt.
cp /opt/golden/sudoers.golden /etc/sudoers.d/program; chmod 440 /etc/sudoers.d/program
pgrep -f server.py >/dev/null || su program -c "python3 /opt/app/server.py &"
echo "[reset] sudo sed privesc + server restored"
