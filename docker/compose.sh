#!/bin/bash
# Wrapper script for deploying the icefabric api/dashboard containers
SERVICE=${1:-full}
ICEFABRIC_DEPLOY_ENV=${2:-test}

if [ $SERVICE != "full" ] && [ $SERVICE != "api" ] && [ $SERVICE != "dashboard" ]; then
    echo "Invalid service specification. Use 'full', 'api', or 'dashboard'."
    exit 1
fi

if [ $ICEFABRIC_DEPLOY_ENV == "test" ]; then
    ICEFABRIC_CREDS_ENV_FILE=".env"
elif [ $ICEFABRIC_DEPLOY_ENV == "prod" ]; then
    ICEFABRIC_CREDS_ENV_FILE=".prod.env"
else
    echo "Invalid environment specified. Use 'test' or 'prod'."
    exit 1
fi

echo "Starting Icefabric ($SERVICE) in $ICEFABRIC_DEPLOY_ENV environment - using $ICEFABRIC_CREDS_ENV_FILE for credentials"

if [ $SERVICE == "full" ]; then
    SERVICE=""
fi

export ICEFABRIC_DEPLOY_ENV=$ICEFABRIC_DEPLOY_ENV
export ICEFABRIC_CREDS_ENV_FILE=$ICEFABRIC_CREDS_ENV_FILE
docker compose -f compose.yaml up $SERVICE
