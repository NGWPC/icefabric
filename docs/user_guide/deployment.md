# Icefabric API Deployment

You can run the API either locally or against the AWS Glue catalog.

## Getting Started

This repo is managed through UV and can be installed through:

```sh
uv sync --all-extras
source .venv/bin/activate
```

## Running Locally

### Local Catalog (Full S3 Iceberg/Icechunk Archive)

To run the API connected to a local iceberg catalog/icechunk data, which has been extracted from an archive file synced from S3:

1\. Authenticate into an AWS profile that has access to the `ngwpc-data` S3 bucket using the command:
`aws sso login --profile your-profile-name`

If you haven't created a profile linked to the NGWPC Data AWS account please use the `aws configure sso` command using information associated with the NGWPC Data AWS account. Further instructions can be found at: https://d-90678ba0c3.awsapps.com/start/#/

You need AWS CLI 2.x. At time of writing this is not the version stored in the apt repository so build it from the AWS source.

2\. Run the following shell script to download the archived catalog, extract it, build the api, dashboard, and nginx docker images, and run docker compose up:

```sh
docker/deploy_local.sh s3://ngwpc-data/icefabric_catalog_archive.tar {aws_profile}
```

This process will take awhile (10-30 minutes) because we need to download ~40 GB of data, extract a large archive, build 3 docker images, and then wait for the api to spin up. The files will be saved to your `/tmp/`. If the both directories are present, the shell script will not re-download the archive. Delete `icefabric_local_catalog` and `icefabric_streamflow_obs` directories to force download. The shell script will update your `.env` file to have the appropriate file paths. Note that your `tmp` file system must be mounted to root and not a `tmpfs` file system tied to memory.  You can check this by running: `df -hT /tmp`.

The services will be routed behind an nginx reverse-proxy, with the underlying services only directly accessible from the localhost.

The api will be accesible @ `http://localhost:80/api`

The dashboard will be accesible @ `http://localhost:80/dashboard`

## Running with Glue/SQL Catalog

### Running Straight from Source

To run the API locally, ensure your `.env` file in your project root has the right credentials (`test`), then run

```sh
python -m app.main
```

This should spin up the API services at `localhost:8000/`

To specify the deploy environment/iceberg catalog used (test or production (OE)), add a `deploy-env` flag to the command. The flag should be formatted as `--deploy-env <value>`:

```sh
# Test
python -m app.main --catalog glue --deploy-env test
# Prod
python -m app.main --catalog glue --deploy-env prod
```

#### SQL Catalog Deploy

If you are running the API locally (SQL) you first need to localize the Iceberg and Icechunk stores from S3. Information on this can be found in the `Tools` section of the User Guide - [details here](./icefabric_tools.md#localize-glue-catalog).

With the local SQL catalog created, run:

```sh
python -m app.main --catalog sql
```

### Building/Running the Docker Image

To run the API locally with Docker, ensure your `.env` file (make sure to have your prod credentials in a `.prod.env` if deploying with the production env/catalog) in your project root has the right credentials, then build with `docker compose`, followed by running the image with the `compose.sh` wrapper script:

```sh
# Build
docker compose -f docker/compose.yaml build api --no-cache
# Run
./compose.sh api
```

To specify the deploy environment/iceberg catalog used (test or production (OE)), pass it in as an argument to the wrapper script:

```sh
# Test deploy (default)
./compose.sh api test
# Prod (OE) deploy
./compose.sh api prod
```

## Dashboard Deploy

For information specifically on deploying the Streamlit Dashboad, please check out the [documentation here.](../dashboard-docs/running.md)

## Pytests

The `tests` folder is for all testing data so the global confest can pick it up. This allows all tests in the namespace packages to share the same scope without having to reference one another in tests

To run tests, run `pytest -s` from project root.

To run the subsetter tests, run `pytest --run-slow` as these tests take some time. Otherwise, they will be skipped

### Smoke Tests

Smoke tests validate the deployed test API. These tests are skipped when the `API_BASE_URL` environment variable is not set, so they won't run during normal CI.

To run smoke tests against a deployed environment:
```sh
export API_BASE_URL="http://edfs.test.nextgenwaterprediction.com:8000/"
uv run pytest tests/smoke/ -v
```

For local (note no / following api):
```sh
export API_BASE_URL="http://localhost:8000/api"
uv run pytest tests/smoke/ -v
```

The smoke tests currently verify:
- The API health endpoint is reachable
- Numeric fields (`initial_value`, `min`, `max`) in the `parameter_metadata` endpoint are never null
