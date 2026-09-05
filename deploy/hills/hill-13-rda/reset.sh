#!/bin/sh
# Restores the sudo dd privesc + server. Does NOT touch king.txt.
cp /opt/golden/sudoers.golden /etc/sudoers.d/ops; chmod 440 /etc/sudoers.d/ops
pgrep -f server.py >/dev/null || su ops -c "python3 /opt/app/server.py &"
echo "[reset] sudo dd privesc + server restored"
