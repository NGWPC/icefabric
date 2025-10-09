
# icefabric

<img src="docs/img/icefabric.png" alt="icefabric" width="50%"/>

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)


An [Apache Iceberg](https://py.iceberg.apache.org/) implementation of the Hydrofabric to disseminate continental hydrologic data

> [!NOTE]
> To run any of the functions in this repo your AWS test account credentials need to be in your `.env` file and your `.pyiceberg.yaml` settings need to up to date with `AWS_DEFAULT_REGION="us-east-1"` set

### Getting Started
This repo is managed through [UV](https://docs.astral.sh/uv/getting-started/installation/) and can be installed through:
```sh
uv sync --all-extras
source .venv/bin/activate
```
Note: Functionality is split into `optional-dependencies` in `pyproject.toml`. If you only require base functionality, install as `uv sync`. If you require some extras (e.g. `icechunk`, `io`), you can specify `uv sync --extra icechunk --extra io` as needed. For local develpoment, `--all-extras` is recommended for complete functionality.

### Running the API locally
To run the API locally, ensure your `.env` file in your project root has the right credentials, then run
```sh
python -m app.main
```
This should spin up the API services at `localhost:8000/`.

If you are running the API locally, you can run
```sh
python -m app.main --catalog sql
```

### Building the API through Docker
To run the API locally with Docker, ensure your `.env` file in your project root has the right credentials, then run
```sh
docker compose -f docker/compose.yaml build --no-cache
docker compose -f docker/compose.yaml up
```
This should spin up the API services


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
