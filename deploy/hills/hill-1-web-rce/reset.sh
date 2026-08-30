#!/bin/sh
# Revives the vuln + restores the planned privesc path from golden. Does NOT touch king.txt.
cp /opt/golden/sudoers.golden /etc/sudoers.d/www
chmod 440 /etc/sudoers.d/www
# if someone killed the www server, bring it back up
pgrep -f server.py >/dev/null || (su www -c "python3 /opt/app/server.py &")
echo "[reset] restored sudoers + www server"
