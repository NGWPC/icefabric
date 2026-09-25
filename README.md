
# icefabric

<img src="docs/img/icefabric.png" alt="icefabric" width="50%"/>

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)


An [Apache Iceberg](https://py.iceberg.apache.org/) implementation of the Hydrofabric to disseminate continental hydrologic data

> [!NOTE]
> To run any of the functions in this repo your AWS test account credentials need to be in your `.env` file and your `.pyiceberg.yaml` settings need to up to date with `AWS_DEFAULT_REGION="us-east-1"` set
>> The `.env` file is used for deploying to the test environment. A `.prod.env` file is used in-place of that if you're deploying to the production environment. By default, when not deploying locally, the test env/catalog is the default; prod needs to be specified when the API/dashboard is launched.

### Getting Started
This repo is managed through [UV](https://docs.astral.sh/uv/getting-started/installation/) and can be installed through:
```sh
uv sync --all-extras
source .venv/bin/activate
```
Note: Functionality is split into `optional-dependencies` in `pyproject.toml`. If you only require base functionality, install as `uv sync`. If you require some extras (e.g. `icechunk`, `io`), you can specify `uv sync --extra icechunk --extra io` as needed. For local develpoment, `--all-extras` is recommended for complete functionality.

### Development
To ensure that icefabric follows the specified structure, be sure to install the local dev dependencies and run `pre-commit install`

### Running/deploying the services
The following sections detail how to:

- Run the Icefabric API locally (standalone)
- Deploy the API/Dashboard through a script that pulls down an S3 catalog archive, then spins up a unified docker setup routed behind an nginx proxy

For full information on API deployment, please see the full [user guide API deploy info page.](./docs/user_guide/deployment.md)
For full information on Streamlit Dashboard deployment, please see the [dashboard deploy info page.](./docs/dashboard-docs/running.md)

#### Running the API locally standalone
To run the API locally, ensure your `.env` file (make sure to have your prod credentials in a `.prod.env` if deploying with the production env/catalog) in your project root has the right credentials, then run

```sh
python -m app.main
```

This should spin up the API services at `localhost:8000/`.

To specify the deploy environment/iceberg catalog used (test or production (OE)), add a `deploy-env` flag to the command. The flag should be formatted as `--deploy-env <value>`:

```sh
# Test
python -m app.main --catalog glue --deploy-env test
# Prod
python -m app.main --catalog glue --deploy-env prod
```

##### SQL catalog deploy

If you are running the API locally (SQL) you first need to localize the Iceberg and Icechunk stores from S3. Information on this can be found in the User Guide - [details here](./docs/user_guide/icefabric_tools.md#localize-glue-catalog).

With the local SQL catalog created, run:

```sh
python -m app.main --catalog sql
```

#### Full API/dashboard local deployment (from archive file)

To run the api and dashboard together connected to a local iceberg catalog and icechunk data that has been extracted from an archive file synced from S3 please:

1\. Authenticate into an AWS profile that has access to the `ngwpc-data` S3 bucket using the command:
`aws sso login --profile your-profile-name`

If you haven't created a profile linked to the NGWPC Data AWS account please use the `aws configure sso` command using information associated with the NGWPC Data AWS account. Further instructions can be found at: https://d-90678ba0c3.awsapps.com/start/#/

2\. Run the following shell script to download the archived catalog, extract it, build the api, dashboard, and nginx docker images, and run docker compose up:

```sh
docker/deploy_local.sh s3://ngwpc-data/icefabric_catalog_archive.tar {aws_profile}
```

This process will take a while (10-30 minutes) because we need to download ~40 GB of data, extract a large archive, build 3 docker images, and then wait for the api to spin up.

The files will be saved to your `/var/tmp/`. If the both directories are present, the shell script will not re-download the archive. Delete `icefabric_local_catalog` and `icefabric_streamflow_obs` directories to force download.

The shell script will update your `.env` file to have the appropriate file paths.

### Documentation
To build the user guide documentation for Icefabric locally, run the following commands:
```sh
uv pip install ".[docs]"
mkdocs serve -a localhost:8080
```
Docs will be spun up at localhost:8080/

### Pytests

The `tests` folder is for all testing data so the global confest can pick it up. This allows all tests in the namespace packages to share the same scope without having to reference one another in tests

To run tests, run `pytest -s` from project root.

To run the subsetter tests, run `pytest --run-slow` as these tests take some time. Otherwise, they will be skipped

### Smoke Tests

Smoke tests validate the deployed test API. These tests are skipped when the `API_BASE_URL` environment variable is not set, so they won't run during normal CI.

To run smoke tests against a deployed environment:
```sh
export API_BASE_URL="[url]/api""
uv run pytest tests/smoke/ -v
```

The smoke tests currently verify:
- The API health endpoint is reachable
- Numeric fields (`initial_value`, `min`, `max`) in the `parameter_metadata` endpoint are never null
