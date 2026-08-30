#!/usr/bin/env bash
# HILL VM: brings up the vulnerable hill (container) + beacon agent ON THE HOST + reset timer (host).
# The agent runs on the host (not in the container) so the HMAC signing key never
# enters the box that players get root on. This model is tested by poc/integration.py.
# Usage: sudo bash deploy/setup-hill.sh <web-rce|drupal|redis|jenkins> <OPS_IP> <HILL_ID> <HMAC_KEY> [SLA_PORT]
set -euo pipefail
VULN="${1:?vuln: web-rce|drupal|redis|jenkins}"; OPS="${2:?OPS_IP}"; HID="${3:?HILL_ID e.g. hill-1}"
KEY="${4:?HMAC_KEY from setup-ops}"; PORT="${5:-80}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
CONT="koth-$HID"
TOKENS="$(python3 -c 'import json,sys;print(",".join(v["token"] for v in json.load(open(sys.argv[1])).values()))' "$REPO/config/teams.json")"
case "$VULN" in
  web-rce) D=hill-1-web-rce;; drupal) D=hill-2-drupal;; redis) D=hill-3-redis;; jenkins) D=hill-4-jenkins;;
  *) echo "unknown vuln: $VULN"; exit 1;; esac

echo ">>> [1/4] vulnerable hill ($VULN) as container $CONT"
(cd "$REPO/deploy/hills/$D" && docker compose up -d --build)

echo ">>> [2/4] beacon agent on the HOST (HMAC key stays off the box)"
install -d /opt/koth
cp "$REPO/agent/agent.py" /opt/koth/agent.py
cat > /etc/systemd/system/koth-agent.service <<UNIT
[Unit]
Description=KOTH beacon agent ($HID)
After=docker.service
[Service]
Environment=KOTH_HILL_ID=$HID KOTH_OPS_URL=http://$OPS:8000 KOTH_HMAC_KEY=$KEY KOTH_TOKENS=$TOKENS
Environment=KOTH_READ_CMD=docker exec $CONT cat /root/king.txt
Environment=KOTH_INTERVAL=1
Environment=KOTH_NONCE_FILE=/var/lib/koth/nonce
ExecStartPre=/bin/mkdir -p /var/lib/koth
ExecStart=/usr/bin/python3 /opt/koth/agent.py
Restart=always
[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now koth-agent.service

echo ">>> [3/4] reset timer every 15 min (revives the vuln; does NOT touch king.txt)"
cat > /etc/systemd/system/koth-reset.service <<UNIT
[Unit]
Description=KOTH reset ($HID)
[Service]
Type=oneshot
ExecStart=/bin/sh -c 'docker exec $CONT /opt/app/reset.sh'
UNIT
cat > /etc/systemd/system/koth-reset.timer <<UNIT
[Unit]
Description=KOTH reset every 15 min ($HID)
[Timer]
OnBootSec=2min
OnUnitActiveSec=15min
[Install]
WantedBy=timers.target
UNIT
systemctl daemon-reload
systemctl enable --now koth-reset.timer

echo ">>> [4/4] done. Hill $HID ($VULN) -> scoreboard http://$OPS:8000"
echo ">>> The beacon agent runs on the host (koth-agent.service); the HMAC key never enters the container."
echo ">>> The SLA prober will probe this host on the service port (see compose: $D)."
echo ">>> TIP: snapshot this VM now for fast recovery during the game."
