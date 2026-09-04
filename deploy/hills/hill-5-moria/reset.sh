#!/bin/sh
# Restores privesc (sudo find) AND re-breaks the boot so entry is fresh again.
# Does NOT touch king.txt.
cp /opt/golden/sudoers.golden /etc/sudoers.d/moria; chmod 440 /etc/sudoers.d/moria
# re-arm the repair puzzle: back to rescue mode with the marred record
printf 'broken' > /opt/boot/state
cat > /opt/boot/durin.cfg <<'CFG'
# Doors of Durin - boot configuration  [RESCUE MODE]
# The Watcher stirred and the record was marred. Repair it to open the gate.
set gatename="West-gate of Moria"
set root=(hd0,gpt9)      # ??? the gate cannot find the first hall
set passphrase=""        # ??? the word of power is missing
set boot=off
CFG
chown -R moria:moria /opt/boot 2>/dev/null || true
pgrep -f server.py >/dev/null || su moria -c "python3 /opt/app/server.py &"
echo "[reset] sudo find privesc + boot re-broken (rescue mode) + server restored"
