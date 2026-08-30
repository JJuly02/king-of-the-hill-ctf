#!/usr/bin/env bash
# HILL VM: brings up the vulnerable hill (container) + beacon agent IN THE CONTAINER + reset timer (host).
# This model is tested by poc/integration.py.
# Usage: sudo bash deploy/setup-hill.sh <web-rce|drupal|redis|jenkins> <OPS_IP> <HILL_ID> <HMAC_KEY> [SLA_PORT]
set -euo pipefail
VULN="${1:?vuln: web-rce|drupal|redis|jenkins}"; OPS="${2:?OPS_IP}"; HID="${3:?HILL_ID np. hill-1}"
KEY="${4:?HMAC_KEY z setup-ops}"; PORT="${5:-80}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
CONT="koth-$HID"
TOKENS="$(python3 -c 'import json,sys;print(",".join(v["token"] for v in json.load(open(sys.argv[1])).values()))' "$REPO/config/teams.json")"
case "$VULN" in
  web-rce) D=hill-1-web-rce;; drupal) D=hill-2-drupal;; redis) D=hill-3-redis;; jenkins) D=hill-4-jenkins;;
  *) echo "unknown vuln: $VULN"; exit 1;; esac

echo ">>> [1/4] vulnerable hill ($VULN) as container $CONT"
(cd "$REPO/deploy/hills/$D" && docker compose up -d --build)

echo ">>> [2/4] beacon agent inside the container"
docker cp "$REPO/agent/agent.py" "$CONT:/opt/koth_agent.py"
install -d /opt/koth
cat > /opt/koth/launch-agent.sh <<LA
#!/bin/sh
docker exec "$CONT" sh -c 'pgrep -f koth_agent.py >/dev/null 2>&1 && exit 0; \
  KOTH_HILL_ID=$HID KOTH_OPS_URL=http://$OPS:8000 KOTH_HMAC_KEY=$KEY \
  KOTH_KING=/root/king.txt KOTH_TOKENS=$TOKENS KOTH_INTERVAL=1 KOTH_REQUIRE_ROOT=1 \
  KOTH_NONCE_FILE=/var/koth_nonce nohup python3 /opt/koth_agent.py >/tmp/agent.log 2>&1 &'
LA
chmod +x /opt/koth/launch-agent.sh
/opt/koth/launch-agent.sh

echo ">>> [3/4] reset timer every 15 min (revives the vuln + keeps the agent alive; does NOT touch king.txt)"
cat > /etc/systemd/system/koth-reset.service <<UNIT
[Unit]
Description=KOTH reset ($HID)
[Service]
Type=oneshot
ExecStart=/bin/sh -c 'docker exec $CONT /opt/app/reset.sh; /opt/koth/launch-agent.sh'
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
echo ">>> The SLA prober will probe this host on the service port (see compose: $D)."
echo ">>> TIP: snapshot this VM now for fast recovery during the game."
