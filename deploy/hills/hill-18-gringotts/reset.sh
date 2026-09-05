#!/bin/sh
# Re-arms the goblin-writable grants dir + root installer, clears attacker grants, and
# re-seals the vault (back to the repair puzzle). Does NOT touch king.txt.
rm -f /opt/vault/grants/*.sudo 2>/dev/null
rm -f /etc/sudoers.d/pwn* /etc/sudoers.d/goblin* 2>/dev/null
mkdir -p /opt/vault/grants; chown -R goblin:goblin /opt/vault; rm -f /opt/vault/state_open
pgrep -f vault-cron >/dev/null || /usr/local/sbin/vault-cron &
pgrep -f server.py >/dev/null || su goblin -c "python3 /opt/app/server.py &"
echo "[reset] grants dir + root installer + vault re-sealed + server restored"
