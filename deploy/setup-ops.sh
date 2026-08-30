#!/usr/bin/env bash
# OPS VM: installs the scoreboard as a systemd service, generates per-hill keys.
# Run as root on the ops VM, from the repo directory. Prints the keys for setup-hill.sh.
set -euo pipefail
HILLS="${HILLS:-hill-1 hill-2 hill-3 hill-4}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST=/opt/koth
BIND="${KOTH_BIND:-0.0.0.0:8000}"

install -d "$DEST"
cp -r "$REPO/scoreboard" "$REPO/flags" "$DEST/"
install -d "$DEST/config"
cp "$REPO/config/teams.json" "$REPO/config/scoring.json" "$DEST/config/"

# Generate hills.json with random per-hill HMAC keys (to harden, swap in Ed25519).
echo "[" > "$DEST/config/hills.json"
first=1
declare -A KEYMAP
for h in $HILLS; do
  key="$(head -c24 /dev/urandom | base64 | tr -d '/+=' )"
  KEYMAP[$h]="$key"
  ip="HILL_IP_${h##*-}"   # placeholder: fill in the real service IP/host
  [ $first -eq 1 ] || echo "," >> "$DEST/config/hills.json"
  first=0
  printf '  {"id":"%s","name":"%s","service_host":"%s","service_port":80,"hmac_key":"%s"}' \
    "$h" "$h" "$ip" "$key" >> "$DEST/config/hills.json"
done
echo "" >> "$DEST/config/hills.json"; echo "]" >> "$DEST/config/hills.json"

cat > /etc/systemd/system/koth-scoreboard.service <<UNIT
[Unit]
Description=KOTH Scoreboard
After=network.target
[Service]
WorkingDirectory=$DEST
Environment=KOTH_CONFIG_DIR=$DEST/config KOTH_FLAGS=$DEST/flags/flags.json KOTH_DB=$DEST/koth.db KOTH_BIND=$BIND
ExecStart=/usr/bin/python3 $DEST/scoreboard/scoreboard.py
Restart=always
[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now koth-scoreboard.service
echo ">>> Scoreboard started on $BIND"
echo ">>> NOTE: fill in the real service_host in $DEST/config/hills.json (SLA prober)"
echo ">>> Per-hill HMAC keys (pass these to setup-hill.sh):"
for h in $HILLS; do echo "    $h  ${KEYMAP[$h]}"; done
