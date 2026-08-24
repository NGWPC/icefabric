# Running the Dashboard

You can run the dashboard either locally or against the AWS Glue catalog.

## Requirements

- Python (all dependencies managed through UV)
- The Icefabric repo cloned locally
- AWS credentials in the project's `.env` file (only needed when using Glue with test catalog)
- AWS credentials in the project's `.prod.env` file (only needed when using Glue with prod (OE) catalog)
- Streamlit (installed automatically via project dependencies)
- Iceberg catalog available:
  - Either AWS Glue
  - Or local SQLite catalog
- S3 Icechunk catalog available (no local option yet)

## Getting Started

This repo is managed through UV and can be installed through:

```sh
uv sync --all-extras
source .venv/bin/activate
```

## Running Locally

To run the dashboard locally, ensure your `.env` file in your project root has the right credentials (`test`), then run the following:

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

### Running the Dashboard with a local Iceberg catalog (Advanced Use)

To run the dashboard locally against a local catalog, the catalog must first be exported from glue. You need to run the build script for the 'NHF', 'RAS XS' and 'CONUS Reference' namespaces, as these are the only necessary catalog namespaces for the dashboard to function. Ensure your `.env` file in your project root has the right credentials (`test`), then run the following:

```sh
uv python tools/iceberg/export_catalog.py --namespace nhf
uv python tools/iceberg/export_catalog.py --namespace ras_xs
uv python tools/iceberg/export_catalog.py --namespace conus_reference
```

Then, to run the dashboard locally using this newly exported SQL backend, add a `deploy-env` flag to the run command. The flag should be formatted as `deploy-env=local` to use the local SQL catalog. Run the following:

```sh
# Local deploy
uv run streamlit run app/streamlit/streamlit.py deploy-env=local
```

> [!IMPORTANT]
> At this time, the 'Streamflow Observations' dashboard page requires S3 access, as this page uses Icechunk (not Iceberg) to store and retrieve data. The Dashboard will still spin up as normal, and function fully, except the 'Streamflow Observations' dashboard page will not function (unless you have S3 credentials in your `.env` file.)

## Building/deploying the Dashboard through Docker

To run just Dashboard locally with Docker, ensure your `.env` file in your project root has the right credentials (`test`) (make sure to have your prod credentials in a `.prod.env` if deploying with the production env/catalog), then run the `compose.sh` wrapper script to spin up the dashboard:

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
