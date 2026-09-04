#!/bin/sh
# Restores the sudo python3 privesc + server. Does NOT touch king.txt.
cp /opt/golden/sudoers.golden /etc/sudoers.d/wizard; chmod 440 /etc/sudoers.d/wizard
pgrep -f server.py >/dev/null || su wizard -c "python3 /opt/app/server.py &"
echo "[reset] sudo python3 privesc + server restored"
