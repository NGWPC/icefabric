#!/bin/bash
set -euo pipefail

# DEBUG logs everything to a file including secrets so only use for DEBUG
#exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
#set -x


# === Fetch instance metadata ===
TOKEN=$(curl -sX PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
LOCAL_IP=$(curl -sH "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/local-ipv4)
INSTANCE_ID=$(curl -sH "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id)

# === DNS and Hostname Configuration ===
AD_DNS_1="${ad_dns_1}"
AD_DNS_2="${ad_dns_2}"
DOMAIN_NAME="${directory_name}"
REALM_NAME=$(echo "$DOMAIN_NAME" | tr '[:lower:]' '[:upper:]')

# === Helper Functions ===
# Wait for APT: Implemented when I found intermittant user data failures
# due to apt being locked by cloud-init or unattended-upgrades
wait_for_apt_lock() {
  for i in {1..20}; do
    if ! fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; then
      return
    fi
    echo "Waiting for APT lock... ($i)"
    sleep 5
  done
  echo "APT lock timeout."
  exit 1
}

fetch_secret() {
  local arn="$1"
  for i in {1..10}; do
    secret=$(aws secretsmanager get-secret-value \
      --secret-id "$arn" \
      --region "${aws_region}" \
      --query SecretString \
      --output text 2>/dev/null) || true

    if [[ -n "$secret" ]]; then
      echo "$secret"
      return 0
    fi
    sleep 5
  done
  echo "Failed to fetch secret from $arn"
  exit 1
}

# Use netplan for persistent DNS configuration
INTERFACE=$(ip route | grep default | sed -e "s/^.*dev.//" -e "s/.proto.*//")
cat > /etc/netplan/99-custom-dns.yaml <<EOF
network:
  version: 2
  ethernets:
    $INTERFACE:
      nameservers:
        search: [$DOMAIN_NAME]
        addresses: [$AD_DNS_1, $AD_DNS_2]
EOF
netplan apply
sleep 5

# Set hostname
COMPUTER_NAME=$(echo "EC2-$(echo $INSTANCE_ID | tr '[:lower:]' '[:upper:]' | sed 's/I-//')" | cut -c1-15)
hostnamectl set-hostname "$COMPUTER_NAME"

# Update /etc/hosts
cat > /etc/hosts <<EOF
127.0.0.1 localhost
$LOCAL_IP $COMPUTER_NAME $COMPUTER_NAME.$DOMAIN_NAME
EOF

# === APT Updates and Dependencies ===
wait_for_apt_lock
apt-get update -y
wait_for_apt_lock
export DEBIAN_FRONTEND=noninteractive
apt-get install -y \
    awscli jq curl unzip gnupg2 ca-certificates \
    apt-transport-https software-properties-common \
    collectd systemd-timesyncd net-tools \
    realmd sssd sssd-tools libnss-sss libpam-sss \
    adcli samba-common-bin oddjob oddjob-mkhomedir \
    packagekit krb5-user

# === Configure Kerberos ===
cat > /etc/krb5.conf <<EOF
[libdefaults]
    default_realm = $REALM_NAME
    dns_lookup_realm = false
    dns_lookup_kdc = true
    ticket_lifetime = 24h
    renew_lifetime = 7d
    forwardable = true
    rdns = false

[realms]
    $REALM_NAME = {
        default_domain = $DOMAIN_NAME
    }

[domain_realm]
    .$DOMAIN_NAME = $REALM_NAME
    $DOMAIN_NAME = $REALM_NAME
EOF

# === Install Docker ===
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
wait_for_apt_lock
apt-get update -y
wait_for_apt_lock
apt-get install -y docker-ce docker-ce-cli containerd.io

# === Docker Compose v2 ===
curl -sSL "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# === Start Docker ===
systemctl enable docker
systemctl start docker

# === CloudWatch Agent ===
wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E amazon-cloudwatch-agent.deb

cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<EOF
{
  "metrics": {
    "namespace": "System/Linux",
    "metrics_collected": {
      "mem": {
        "measurement": [
          {"name": "mem_used_percent", "rename": "MemoryUtilization"}
        ],
        "metrics_collection_interval": 60
      }
    }
  }
}
EOF

systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent

# === CONFIGURE SSH FOR ACTIVE DIRECTORY LOGINS ===
echo "Configuring SSH to allow AD password authentication..."
# Set the desired values in the main sshd_config file
sed -i 's/^#?PasswordAuthentication .*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#?ChallengeResponseAuthentication .*/ChallengeResponseAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#?UsePAM .*/UsePAM yes/' /etc/ssh/sshd_config

# Find and disable cloud-init overrides
CONF_FILE=$(grep -l -r 'PasswordAuthentication no' /etc/ssh/sshd_config.d/ 2>/dev/null || true)
if [ -n "$CONF_FILE" ]; then
  echo "Found and disabled override in: $CONF_FILE"
  # Comment out line to disable override
  sed -i 's/^\s*PasswordAuthentication\s\+no/#&/' "$CONF_FILE"
fi

# Restart SSHD
echo "Restarting SSH service..."
systemctl restart sshd

# === Join Domain Configuration ===
#AD_OU = "OU=Computers,OU=nextgenwater,DC=nextgenwaterprediction,DC=com"
AD_SECRET_ARN="${ad_secret}"

# Group to grant ssh access (no sudo though, currently)
AD_GROUP="SoftwareEngineersFull"

# Fetch domain join credentials
echo "Fetching AD credentials..."
AD_CREDS=$(fetch_secret "$AD_SECRET_ARN")
AD_USER=$(echo "$AD_CREDS" | jq -r .UserID)
AD_PASS=$(echo "$AD_CREDS" | jq -r .Password)

# Use direct adcli join command.
# I couldn't get the realm commands to play nice with our DNS.
echo "Joining domain using adcli..."
echo "$AD_PASS" | adcli join \
    --verbose \
    --domain "$DOMAIN_NAME" \
    --domain-realm "$REALM_NAME" \
    --domain-controller "$AD_DNS_1" \
    --computer-name "$COMPUTER_NAME" \
    --login-type user \
    --login-user "$AD_USER" \
    --stdin-password

# === Configure Access and SSSD ===
# Configure SSSD for user/group lookups and authentication
cat > /etc/sssd/sssd.conf <<EOF
[sssd]
domains = $DOMAIN_NAME
config_file_version = 2
services = nss, pam

[domain/$DOMAIN_NAME]
id_provider = ad
auth_provider = ad
access_provider = ad
chpass_provider = ad
use_fully_qualified_names = True
ad_domain = $DOMAIN_NAME
krb5_realm = $REALM_NAME
default_shell = /bin/bash
fallback_homedir = /home/%u@%d
enumerate = false
cache_credentials = true
krb5_store_password_if_offline = true
ad_gpo_access_control = disabled
ldap_id_mapping = true
EOF

chmod 600 /etc/sssd/sssd.conf
systemctl restart sssd
systemctl enable sssd

# Allow only a specific AD group to log in
realm permit -g "$AD_GROUP"

# Enable automatic home directory creation for users
pam-auth-update --enable mkhomedir

# Test SSSD functionality
echo "Testing SSSD functionality..."
getent passwd "$AD_USER@$DOMAIN_NAME" || echo "SSSD user lookup failed"

echo "Domain join and configuration complete"


# === Setup Application Directory ===
mkdir -p /opt/icefabric /opt/icefabric/logs

# === .env File for Compose ===
cat > /opt/icefabric/.env <<EOF

APP_HOST=0.0.0.0
APP_PORT=8000
RELOAD=true
CATALOG_PATH=glue
LOG_DIR=/opt/icefabric/logs/
AWS_DEFAULT_REGION=${aws_region}
AWS_REGION=${aws_region}
ENVIRONMENT=${environment}
EOF

# === Docker Compose Application Stack ===
cat > /opt/icefabric/docker-compose.yml <<EOF
services:
  myapp:
    image: ${docker_image_uri}
    network_mode: "host"
    ports:
      - "8000:8000"
    env_file:
      - ./.env
    restart: always
    volumes:
      - /opt/icefabric/logs:/app/logs
    command: /bin/bash -c "uvicorn app.main:app --host 0.0.0.0 --port 8000 >> /app/logs/app.log 2>&1"
    healthcheck:
      test: ["CMD", "curl", "-f", "--head", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s
EOF

# === Compose Systemd Service ===
cat > /etc/systemd/system/icefabric.service <<EOF
[Unit]
Description=icefabric Docker Compose Service
Requires=docker.service
After=docker.service

[Service]
Restart=always
WorkingDirectory=/opt/icefabric
ExecStart=/usr/local/bin/docker-compose up
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable icefabric
systemctl start icefabric

# === Log Rotation ===
cat > /etc/logrotate.d/icefabric <<'EOF'
/opt/icefabric/logs/*.log {
    rotate 7
    daily
    compress
    size 50M
    missingok
    delaycompress
    copytruncate
}
EOF

echo "User data complete for ${environment} instance at $LOCAL_IP"