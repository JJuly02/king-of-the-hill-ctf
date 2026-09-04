#!/bin/sh
# Restores the SUID find privesc (mcp_ctl) + server. Does NOT touch king.txt.
cp "$(command -v find)" /usr/local/bin/mcp_ctl
chown root:root /usr/local/bin/mcp_ctl; chmod 4755 /usr/local/bin/mcp_ctl
pgrep -f server.py >/dev/null || su mcp -c "python3 /opt/app/server.py &"
echo "[reset] SUID find (mcp_ctl) + server restored"
