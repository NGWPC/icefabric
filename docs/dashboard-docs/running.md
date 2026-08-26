# Running the Dashboard

You can run the dashboard either locally or against the AWS Glue catalog.

## Requirements

- Python v3.11 - v3.12.8 (all dependencies managed through UV)
- The Icefabric repo cloned locally
- AWS credentials in the project's `.env` file (only needed when using Glue with test catalog)
- AWS credentials in the project's `.prod.env` file (only needed when using Glue with prod (OE) catalog)
- Streamlit (installed automatically via project dependencies)
- Iceberg catalog available in one of either formats:
    - AWS Glue
    - SQLite catalog (local)
- S3 Icechunk catalog available

## Getting Started

This repo is managed through UV and can be installed through:

```sh
uv sync --all-extras
source .venv/bin/activate
```

## Running Locally

To run the dashboard locally, ensure your `.env` file in your project root has the right credentials if running with AWS glue catalog, then run the following:

```sh
uv run streamlit run app/streamlit/streamlit.py
```

The dashboard will spin up, and can be accessed in a browser at `http://localhost:8501`. Please note that the port number may change depending on availability. The command output will tell you the port number.

To specify the deploy environment/iceberg catalog used (test or production (OE)), add a `deploy-env` flag to the run command. The flag should be formatted as `deploy-env=<value>`. Also, make sure to have your prod credentials in a `.prod.env` file in your project root, if deploying with the production env/catalog. Run the following:

```sh
# Test deploy (default)
uv run streamlit run app/streamlit/streamlit.py deploy-env=test
# Prod (OE) deploy
uv run streamlit run app/streamlit/streamlit.py deploy-env=prod
```

### Running the Dashboard with a local catalog/store

To run the dashboard locally against a local Iceberg catalog and local Icechunk store, there's a shell script (`docker/deploy_local.sh`) to do so. It deploys the icefabric API and dashboard using a local catalog and icechunk store extracted from an S3 archive. The script automates everything from downloading the S3 archive, and extracting it locally, and spinning up the docker deployment.

For further information or troubleshooting, please reference [the script](https://github.com/NGWPC/icefabric/blob/main/docker/deploy_local.sh).

!!! warning "Important"
    The archive pulled from S3 is quite large. You will need ~100GB of free diskspace in the location where you are writing the archive. The script defaults to the root var/temp directory (`/var/tmp`)

## Building/deploying the Dashboard through Docker

To run just the Dashboard locally with Docker, ensure your `.env` file in your project root has the right credentials (`test`) (make sure to have your prod credentials in a `.prod.env` if deploying with the production env/catalog), then run the `compose.sh` wrapper script to spin up the dashboard:

```sh
# Build
docker compose -f docker/compose.yaml build dashboard --no-cache
# Run
./compose.sh dashboard
```

To specify the deploy environment/iceberg catalog used (test or production (OE)), pass it in as an argument to the wrapper script:

```sh
# Test deploy (default)
./compose.sh dashboard test
# Prod (OE) deploy
./compose.sh dashboard prod
```

## Full deployment with reverse proxy

To run the API and Dashboard together, you can specify this to the docker compose wrapper script. The services will be routed behind an nginx reverse-proxy, with the underlying services only directly accessible from the localhost.

The api will be accesible @ http://localhost:80/api

The dashboard will be accesible @ http://localhost:80/dashboard

Ensure your `.env` file (make sure to have your prod credentials in a `.prod.env` if deploying with the production env/catalog) in your project root has the right credentials, then run the `compose.sh` wrapper script to spin up everyting:

```sh
# Build
docker compose -f docker/compose.yaml build --no-cache
# Run
./compose.sh full
```

To specify the deploy environment/iceberg catalog used (test or production (OE)), pass it in as an argument to the wrapper script:

```sh
# Test deploy (default)
./compose.sh full test
# Prod (OE) deploy
./compose.sh full prod
```
