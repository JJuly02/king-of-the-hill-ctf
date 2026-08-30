#!/bin/sh
# Reset the weak password (already in code) + restore sudo/tar privesc + server. Does NOT touch king.txt.
cp /opt/golden/sudoers.golden /etc/sudoers.d/jenkins; chmod 440 /etc/sudoers.d/jenkins
pgrep -f server.py >/dev/null || su jenkins -c "python3 /opt/app/server.py &"
echo "[reset] sudo tar privesc + server restored"
