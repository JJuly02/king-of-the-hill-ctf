#!/bin/sh
# Restores SUID (privesc) + server. Does NOT touch king.txt.
chmod 4755 /usr/local/bin/rootbash
pgrep -f server.py >/dev/null || su www -c "python3 /opt/app/server.py &"
echo "[reset] SUID rootbash + server restored"
