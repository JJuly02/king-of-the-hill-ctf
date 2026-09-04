#!/bin/sh
# Restores sudo awk privesc + server. Does NOT touch king.txt.
cp /opt/golden/sudoers.golden /etc/sudoers.d/palantir; chmod 440 /etc/sudoers.d/palantir
pgrep -f server.py >/dev/null || su palantir -c "python3 /opt/app/server.py &"
echo "[reset] sudo awk privesc + server restored"
