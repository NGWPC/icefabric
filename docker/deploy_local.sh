#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# icefabric Local Deploy Script
#
# Deploys the icefabric API and dashboard using a local catalog and icechunk
# store extracted from an S3 archive.
#
# Usage:
#   ./deploy_local.sh <s3_archive_path> <github_repo_url> <branch> [aws_profile]
#
# Example:
#   ./deploy_local.sh s3://edfs-data/tmp/icefabric_full_backup.tar \
#     https://github.com/NGWPC/icefabric.git main myprofile
# =============================================================================

# --- Colors for output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# --- Parse arguments ---
if [[ $# -lt 3 ]]; then
    echo "Usage: $0 <s3_archive_path> <github_repo_url> <branch> [aws_profile]"
    echo ""
    echo "Arguments:"
    echo "  s3_archive_path   S3 path to the icefabric backup tar file"
    echo "                    (e.g., s3://edfs-data/tmp/icefabric_full_backup.tar)"
    echo "  github_repo_url   GitHub repository URL"
    echo "                    (e.g., https://github.com/NGWPC/icefabric.git)"
    echo "  branch            Git branch to checkout"
    echo "  aws_profile       AWS profile name (optional, uses default if not set)"
    exit 1
fi

S3_ARCHIVE_PATH="$1"
GITHUB_REPO_URL="$2"
BRANCH="$3"
AWS_PROFILE="${4:-}"

# --- Validate inputs ---
if [[ ! "$S3_ARCHIVE_PATH" =~ ^s3:// ]]; then
    log_error "S3 archive path must start with s3://"
    exit 1
fi

if [[ -z "$GITHUB_REPO_URL" ]]; then
    log_error "GitHub repo URL cannot be empty"
    exit 1
fi

if [[ -z "$BRANCH" ]]; then
    log_error "Branch cannot be empty"
    exit 1
fi

# --- Check prerequisites ---
log_info "Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI is not installed. Please install it first."
    log_error "  See: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi
log_info "AWS CLI found: $(aws --version)"

# Check Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install it first."
    log_error "  See: https://docs.docker.com/engine/install/"
    exit 1
fi
log_info "Docker found: $(docker --version)"

# find docker compose version
DOCKER_COMPOSE=""
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
    log_info "Using: docker compose (v2 plugin)"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    log_info "Using: docker-compose (standalone)"
else
    log_error "Docker Compose is not installed."
    log_error "  Install Docker Compose v2: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check git
if ! command -v git &> /dev/null; then
    log_error "Git is not installed. Please install it first."
    exit 1
fi
log_info "Git found: $(git --version)"

# --- Setup AWS profile ---
AWS_CMD="aws"
if [[ -n "$AWS_PROFILE" ]]; then
    AWS_CMD="aws --profile $AWS_PROFILE"
    log_info "Using AWS profile: $AWS_PROFILE"
fi

# Verify AWS credentials
log_info "Verifying AWS credentials..."
if ! $AWS_CMD sts get-caller-identity &> /dev/null; then
    log_error "AWS credentials are not configured or have expired."
    log_error "  Run: aws configure --profile $AWS_PROFILE"
    exit 1
fi
ACCOUNT_ID=$($AWS_CMD sts get-caller-identity --query Account --output text)
log_info "AWS Account: $ACCOUNT_ID"

# --- Create working directory ---
DEPLOY_DIR="./icefabric_deploy_$(date +%Y%m%d_%H%M%S)"
log_info "Creating deployment directory: $DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# --- Clone repository ---
log_info "Cloning repository: $GITHUB_REPO_URL"
git clone --branch "$BRANCH" "$GITHUB_REPO_URL" repo
cd repo

log_info "Checked out branch: $(git branch --show-current)"
log_info "Commit: $(git rev-parse --short HEAD)"

# --- Extract archive ---
LOCAL_CATALOG="/tmp/icefabric_local_catalog"
LOCAL_ICECHUNK="/tmp/icefabric_streamflow_obs"

if [[ -d "$LOCAL_CATALOG" && -d "$LOCAL_ICECHUNK" ]]; then
    log_info "Archive already extracted, skipping download"
else
    log_info "Downloading and extracting archive from: $S3_ARCHIVE_PATH"
    ARCHIVE_FILENAME=$(basename "$S3_ARCHIVE_PATH")
    $AWS_CMD s3 cp "$S3_ARCHIVE_PATH" "/tmp/$ARCHIVE_FILENAME"

    log_info "Extracting archive..."
    tar -xf "/tmp/$ARCHIVE_FILENAME" -C /tmp/
    rm -f "/tmp/$ARCHIVE_FILENAME"
fi

# --- Verify extracted files ---

if [[ ! -d "$LOCAL_CATALOG" ]]; then
    log_error "Local catalog directory not found: $LOCAL_CATALOG"
    log_error "  Archive may not contain the expected structure."
    exit 1
fi

if [[ ! -d "$LOCAL_ICECHUNK" ]]; then
    log_error "Local icechunk directory not found: $LOCAL_ICECHUNK"
    log_error "  Archive may not contain the expected structure."
    exit 1
fi

log_info "Local catalog: $LOCAL_CATALOG ($(du -sh "$LOCAL_CATALOG" | cut -f1))"
log_info "Local icechunk: $LOCAL_ICECHUNK ($(du -sh "$LOCAL_ICECHUNK" | cut -f1))"

# --- Create .pyiceberg.yaml for local catalog ---
log_info "Creating .pyiceberg.yaml for local catalog..."
cat > .pyiceberg.yaml << EOF
catalog:
  sql:
    type: sql
    uri: sqlite:///${LOCAL_CATALOG}/pyiceberg_catalog.db
    warehouse: ${LOCAL_CATALOG}/warehouse
EOF

# --- Create .env for docker compose ---
log_info "Creating .env for docker compose..."
cat > .env << EOF
ICEFABRIC_DEPLOY_ENV=local
ICEFABRIC_ICECHUNK_PATH=${LOCAL_ICECHUNK}
ICEFABRIC_BUILD_CACHE=false
PYICEBERG_HOME=$(pwd)/.pyiceberg.yaml
EOF

# --- docker-compose.local.yaml is in docker/ directory ---

# --- Build and start services ---
COMPOSE_FILE="docker/compose.local.yaml"
log_info "Building Docker images..."
$DOCKER_COMPOSE -f "$COMPOSE_FILE" build

log_info "Starting services..."
$DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d

# --- Wait for health check ---
log_info "Waiting for API to become healthy..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log_info "API is healthy!"
        break
    fi
    if [[ $i -eq 30 ]]; then
        log_warn "API health check timed out. Check logs with: $DOCKER_COMPOSE -f $COMPOSE_FILE logs api"
    fi
    sleep 2
done

# --- Print summary ---
echo ""
echo "=========================================="
echo "  icefabric Local Deployment Complete"
echo "=========================================="
echo ""
echo "  API:       http://localhost:8000"
echo "  Dashboard: http://localhost:8501"
echo "  Nginx:     http://localhost:80"
echo ""
echo "  Catalog:   $LOCAL_CATALOG"
echo "  Icechunk:  $LOCAL_ICECHUNK"
echo ""
echo "  Logs:"
echo "    $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f api"
echo "    $DOCKER_COMPOSE -f $COMPOSE_FILE logs -f dashboard"
echo ""
echo "  Stop:"
echo "    $DOCKER_COMPOSE -f $COMPOSE_FILE down"
echo "=========================================="
