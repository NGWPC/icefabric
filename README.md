
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

### Running/deploying the services

The following sections detail how to run the Icefabric services locally (standalone) as well as how to build/deploy them through Docker (either standalone or together behind an nginx reverse-proxy)

#### Running the API locally
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

If you are running the API locally, you can run

```sh
python -m app.main --catalog sql
```

#### Building/deploying the API through Docker
To run the API locally with Docker, ensure your `.env` file (make sure to have your prod credentials in a `.prod.env` if deploying with the production env/catalog) in your project root has the right credentials, then run the `compose.sh` wrapper script to spin up the dashboard::
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

#### Running the dashboard locally

Besides the API, Icefabric also includes a frontend dashboard to interact with the Hydrofabric. The dashboard is implemented through `streamlit`.
To run the dashboard locally, ensure your `.env` file (make sure to have your prod credentials in a `.prod.env` if deploying with the production env/catalog) in your project root has the right credentials (as with the API), then run:

```sh
uv run streamlit run app/streamlit/streamlit.py
```

The dashboard will spin up, and can be accessed in a browser at `http://localhost:8501`. Please note that the port number may change depending on availability. The command output will tell you the port number.

To specify the deploy environment/iceberg catalog used (test or production (OE)), add a `deploy-env` flag to the run command. The flag should be formatted as `deploy-env=<value>`:

```sh
# Test deploy (default)
uv run streamlit run app/streamlit/streamlit.py deploy-env=test
# Prod (OE) deploy
uv run streamlit run app/streamlit/streamlit.py deploy-env=prod
```

#### Building/deploying the dashboard through Docker
To run just the Dashboard locally with Docker, ensure your `.env` file (make sure to have your prod credentials in a `.prod.env` if deploying with the production env/catalog) in your project root has the right credentials, then run the `compose.sh` wrapper script to spin up the dashboard:
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

#### Full deployment with reverse proxy

To run the api and dashboard together, you can specify this to the docker compose wrapper script. The services will be routed behind an nginx reverse-proxy, with the underlying services only directly accessible from the localhost.

The api will be accesible @ http://localhost:80/api

The dashboard will be accesible @ http://localhost:80/dashboard

ensure your `.env` file (make sure to have your prod credentials in a `.prod.env` if deploying with the production env/catalog) in your project root has the right credentials, then run the `compose.sh` wrapper script to spin up everyting:

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

### Development
To ensure that icefabric follows the specified structure, be sure to install the local dev dependencies and run `pre-commit install`

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
export API_BASE_URL="http://edfs.test.nextgenwaterprediction.com:8000/"
uv run pytest tests/smoke/ -v
```

The smoke tests currently verify:
- The API health endpoint is reachable
- Numeric fields (`initial_value`, `min`, `max`) in the `parameter_metadata` endpoint are never null
