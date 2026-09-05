#!/bin/sh
# Restores sudo env privesc AND re-breaks the refinery (back offline). Does NOT touch king.txt.
cp /opt/golden/sudoers.golden /etc/sudoers.d/refiner; chmod 440 /etc/sudoers.d/refiner
mkdir -p /opt/refinery; chown refiner:refiner /opt/refinery; rm -f /opt/refinery/online
pgrep -f server.py >/dev/null || su refiner -c "python3 /opt/app/server.py &"
echo "[reset] sudo env privesc + refinery re-set offline + server restored"
