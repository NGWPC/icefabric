# Welcome to Icefabric

# Icefabric

An [Apache Iceberg](https://py.iceberg.apache.org/)/[Icechunk](https://icechunk.io/en/latest/) implementation of the Hydrofabric to disseminate continental hydrologic data

!!! note
    To run any of the functions in this repo your AWS test account credentials + `AWS_DEFAULT_REGION="us-east-1"` need to be in your `.env` file and your `.pyiceberg.yaml` settings need to up to date

### Getting Started
This repo is managed through [UV](https://docs.astral.sh/uv/getting-started/installation/) and can be installed through:

```sh
uv sync --all-extras
source .venv/bin/activate
```

Note: Functionality is split into `optional-dependencies` in `pyproject.toml`. If you only require base functionality, install as `uv sync`. For local develpoment, `--all-extras` is recommended for complete functionality.

### Deployment

You can run the API either locally or against the AWS Glue catalog. Please see the full [deployment information page.](./user_guide/deployment.md)

### Development
To ensure that icefabric follows the specified structure, be sure to install the local dev dependencies and run `pre-commit install`

### Documentation
To build the user guide documentation for Icefabric locally, run the following commands:

```sh
uv sync --extra docs
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
export API_BASE_URL="[url]/api"
uv run pytest tests/smoke/ -v
```


### Streamlit Dashboard

Also included alongisde the API is the Icefabric Dashboard. The dashboard is a Streamlit-based frontend that works separately from the API. It allows users to explore, subset, and visualize hydrologic datasets stored in the Icefabric ecosystem.

Further info can be found [here](./dashboard-docs/index.md).
