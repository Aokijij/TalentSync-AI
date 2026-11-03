#!/usr/bin/env bash
# Public bootstrap only. Never put application secrets or personal data here.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates curl python3-venv python3-pip nginx certbot python3-certbot-nginx \
  libgl1 libglib2.0-0t64 fonts-dejavu-core unattended-upgrades
id talentsync >/dev/null 2>&1 || useradd --system --create-home --home-dir /var/lib/talentsync --shell /usr/sbin/nologin talentsync
install -d -m 0755 /opt/talentsync /opt/talentsync/releases /var/www/letsencrypt
install -d -m 0700 /etc/talentsync
install -d -m 0700 -o talentsync -g talentsync /var/lib/talentsync/uploads /var/lib/talentsync/models
python3 -m venv /opt/talentsync/venv
/opt/talentsync/venv/bin/python -m pip install --upgrade pip
timedatectl set-ntp true
install -d -m 0755 /etc/systemd/journald.conf.d
cat >/etc/systemd/journald.conf.d/talentsync-limits.conf <<'EOF'
[Journal]
SystemMaxUse=200M
MaxRetentionSec=14day
EOF
systemctl restart systemd-journald
# No application is started until credentials, migration and readiness are checked.
