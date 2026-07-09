#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# icefabric Local Deploy Script
#
# Deploys the icefabric API and dashboard using a local catalog and icechunk
# store extracted from an S3 archive.
#
# Usage:
#   Run from the repo root on the correct branch:
#   ./docker/deploy_local.sh <s3_archive_path> [aws_profile]
#
# Example:
#   ./docker/deploy_local.sh s3://edfs-data/tmp/icefabric_full_backup.tar myprofile
# =============================================================================

# --- Parse arguments ---
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <s3_archive_path> [aws_profile]"
    echo ""
    echo "Arguments:"
    echo "  s3_archive_path   S3 path to the icefabric backup tar file"
    echo "                    (e.g., s3://edfs-data/tmp/icefabric_full_backup.tar)"
    echo "  aws_profile       AWS profile name (optional, uses default if not set)"
    exit 1
fi

S3_ARCHIVE_PATH="$1"
AWS_PROFILE="${2:-}"

# --- Validate inputs ---
if [[ ! "$S3_ARCHIVE_PATH" =~ ^s3:// ]]; then
    echo "[ERROR] S3 archive path must start with s3://" >&2
    exit 1
fi

# --- Check prerequisites ---
echo "[INFO] Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "[ERROR] AWS CLI is not installed. Please install it first." >&2
    echo "[ERROR]   See: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html" >&2
    exit 1
fi
echo "[INFO] AWS CLI found: $(aws --version)"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed. Please install it first." >&2
    echo "[ERROR]   See: https://docs.docker.com/engine/install/" >&2
    exit 1
fi
echo "[INFO] Docker found: $(docker --version)"

# find docker compose version
DOCKER_COMPOSE=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    echo "[INFO] Using: docker compose (v2 plugin)"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo "[INFO] Using: docker-compose (standalone)"
else
    echo "[ERROR] Docker Compose is not installed." >&2
    echo "[ERROR]   Install Docker Compose v2: https://docs.docker.com/compose/install/" >&2
    exit 1
fi

# --- Setup AWS profile ---
AWS_CMD="aws"
if [[ -n "$AWS_PROFILE" ]]; then
    AWS_CMD="aws --profile $AWS_PROFILE"
    echo "[INFO] Using AWS profile: $AWS_PROFILE"
fi

# Verify AWS credentials
echo "[INFO] Verifying AWS credentials..."
if ! $AWS_CMD sts get-caller-identity &> /dev/null; then
    echo "[ERROR] AWS credentials are not configured or have expired." >&2
    echo "[ERROR]   Run: aws configure --profile $AWS_PROFILE" >&2
    exit 1
fi
ACCOUNT_ID=$($AWS_CMD sts get-caller-identity --query Account --output text)
echo "[INFO] AWS Account: $ACCOUNT_ID"

# --- Verify we're in a repo with the compose file ---
if [[ ! -f "docker/compose.local.yaml" ]]; then
    echo "[ERROR] docker/compose.local.yaml not found. Are you in the repo root on the correct branch?" >&2
    exit 1
fi
echo "[INFO] Branch: $(git branch --show-current 2>/dev/null || echo 'not a git repo')"
echo "[INFO] Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"

# --- Extract archive ---
WAREHOUSE_DIR="/tmp/warehouse"
LOCAL_ICECHUNK="/tmp/icefabric_streamflow_obs"
ARCHIVE_DIR="/tmp/icefabric_local_catalog"

if [[ -f "$WAREHOUSE_DIR/pyiceberg_catalog.db" && -d "$LOCAL_ICECHUNK" ]]; then
    echo "[INFO] Archive already extracted, skipping download"
else
    echo "[INFO] Downloading and extracting archive from: $S3_ARCHIVE_PATH"
    ARCHIVE_FILENAME=$(basename "$S3_ARCHIVE_PATH")
    $AWS_CMD s3 cp "$S3_ARCHIVE_PATH" "/tmp/$ARCHIVE_FILENAME"

    echo "[INFO] Extracting archive..."
    tar -xf "/tmp/$ARCHIVE_FILENAME" -C /tmp/
    rm -f "/tmp/$ARCHIVE_FILENAME"
fi

# --- Move extracted files to expected locations ---
mkdir -p "$WAREHOUSE_DIR"
if [[ ! -f "$WAREHOUSE_DIR/pyiceberg_catalog.db" && -f "$ARCHIVE_DIR/pyiceberg_catalog.db" ]]; then
    echo "[INFO] Moving catalog to $WAREHOUSE_DIR..."
    mv "$ARCHIVE_DIR/pyiceberg_catalog.db" "$WAREHOUSE_DIR/"
    if [[ -d "$ARCHIVE_DIR/warehouse" ]]; then
        cp -r "$ARCHIVE_DIR/warehouse/"* "$WAREHOUSE_DIR/"
    fi
    rm -rf "$ARCHIVE_DIR"
fi

# --- Verify extracted files ---
if [[ ! -f "$WAREHOUSE_DIR/pyiceberg_catalog.db" ]]; then
    echo "[ERROR] SQLite catalog not found at $WAREHOUSE_DIR/pyiceberg_catalog.db" >&2
    exit 1
fi

if [[ ! -d "$LOCAL_ICECHUNK" ]]; then
    echo "[ERROR] Local icechunk directory not found: $LOCAL_ICECHUNK" >&2
    echo "[ERROR]   Archive may not contain the expected structure." >&2
    exit 1
fi

echo "[INFO] Local catalog: $WAREHOUSE_DIR ($(du -sh "$WAREHOUSE_DIR" | cut -f1))"
echo "[INFO] Local icechunk: $LOCAL_ICECHUNK ($(du -sh "$LOCAL_ICECHUNK" | cut -f1))"

# --- Create .env for docker compose ---
# .pyiceberg.yaml is already in the repo root pointing to /tmp/warehouse/
echo "[INFO] Creating .env for docker compose..."
cat > .env << EOF
ICEFABRIC_DEPLOY_ENV=local
ICEFABRIC_ICECHUNK_PATH=${LOCAL_ICECHUNK}
ICEFABRIC_BUILD_CACHE=false
PYICEBERG_HOME=$(pwd)/.pyiceberg.yaml
EOF

# --- Build and start services ---
COMPOSE_FILE="docker/compose.local.yaml"
echo "[INFO] Building Docker images..."
$DOCKER_COMPOSE -f "$COMPOSE_FILE" build

echo "[INFO] Starting services..."
$DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d

# --- Wait for health check ---
echo "[INFO] Waiting for API to become healthy..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "[INFO] API is healthy!"
        break
    fi
    if [[ $i -eq 30 ]]; then
        echo "[WARN] API health check timed out. Check logs with: $DOCKER_COMPOSE -f $COMPOSE_FILE logs api"
    fi
    sleep 2
done

echo ""
echo "=========================================="
echo "  icefabric Local Deployment Complete"
echo "=========================================="
echo ""
echo "  API:       http://localhost:8000"
echo "  Dashboard: http://localhost:8501"
echo "  Nginx:     http://localhost:80"
echo ""
echo "  Catalog:   $WAREHOUSE_DIR"
echo "  Icechunk:  $LOCAL_ICECHUNK"
echo ""
echo "  Logs:"
echo "    $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f api"
echo "    $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f dashboard"
echo ""
echo "  Stop:"
echo "    $DOCKER_COMPOSE -f $COMPOSE_FILE down"
echo "=========================================="
