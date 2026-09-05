#!/bin/sh
# Ensures the server is alive. Does NOT touch king.txt. (The privesc is the mounted docker
# socket itself - a host-level primitive - so there is no in-container reset for it.)
pgrep -f server.py >/dev/null || su pandora -c "python3 /opt/app/server.py &"
echo "[reset] server restored"
