#!/bin/sh
# Re-applies cap_dac_override on roompy AND re-engages emergency mode. Does NOT touch king.txt.
[ -x /usr/local/bin/roompy ] || cp "$(readlink -f "$(command -v python3)")" /usr/local/bin/roompy
setcap cap_dac_override+ep /usr/local/bin/roompy
mkdir -p /opt/room; chown room:room /opt/room; rm -f /opt/room/online
pgrep -f server.py >/dev/null || su room -c "python3 /opt/app/server.py &"
echo "[reset] cap_dac_override on roompy + emergency re-engaged + server restored"
