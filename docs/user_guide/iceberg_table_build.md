# Building Iceberg Tables for Icefabric

The Icefabric API is a FastAPI-based service that provides access to EDFS data stored in both Apache Iceberg & Icechunk format. The service includes code to build additional Iceberg tables to be added to the catalog.

## Loading the Catalog

The Icefabric API data is stored in both Apache Iceberg & Icechunk. Depending on how the app is started up, the API can point to either the AWS-hosted Glue catalog, or a local SQLite-backed catalog. When creating new tables for the Iceberg catalog, you should load and specify which backend you'll be using.

### AWS Glue Catalog

First, ensure your `.env` file in your project root has the right credentials (`test`). Load the environment before loading the catalog. To load the namespaces/tables hosted on glue, you can run the following commands in your Python code:

```python
from dotenv import load_dotenv
from pyiceberg.catalog import load_catalog

# Loads credentials from .env in the project root
load_dotenv()

# Load the AWS glue catalog
catalog = load_catalog("glue")
```

The resulting `catalog` variable is a `pyiceberg.catalog.Catalog` object that will allow modifications/additions to the defined catalog.

### Local SQLite Catalog

To run the API locally against a local catalog, the catalog must first be exported from glue. Then run the build script, and flag as many catalog namespaces as you need from the Glue catalog. Ensure your `.env` file in your project root has the right credentials (`test`), as with the Glue method directly above.

Running the following in a bash terminal will copy down the SQLite catalog from the Glue catalog:

```sh
uv sync
source .venv/bin/activate
python tools/pyiceberg/export_catalog.py --namespace conus_hf
# Run additional tool times with other namespaces as necessary
```

The SQLite catalog will be located locally in the directory defined in the `<project_root>/.pyiceberg.yaml` file. Default is `<project_root>/tmp/warehouse`

You can load up the SQLite catalog much like the Glue catalog:

```python
from dotenv import load_dotenv
from pyiceberg.catalog import load_catalog

# Loads credentials from .env in the project root
load_dotenv()

# Load the SQLite catalog
catalog = load_catalog("sql")
```

## Building a Table

### Namespace

Iceberg tables exist inside namespaces - you can view these with the `pyiceberg.catalog.Catalog.list_namespaces()` function. Make sure to check if the namespace exists before you build a table.

```python
from pyiceberg.exceptions import NamespaceAlreadyExistsError

namespace = "streamflow_observations"
try:
    # Catalog instance can be from Glue or SQLite - see previous sections on how to load the catalog
    catalog.create_namespace(namespace)
except NamespaceAlreadyExistsError:
    print(f"Namespace {namespace} already exists")
```

### Table Name

You need to specify a table name - the table must not have the name of an existing table: otherwise the code will skip building the table.

```python
table_name = "your_table_name"
```

### Parquet File

The table you build is based on a parquet file you provide. The schema of the resulting table is based on the parquet file, and will infer that schema automatically.

```python
from pathlib import Path

dir_path = Path("/path/to/directory")
parquet_path = dir_path / "my_data.parquet"

if not parquet_path.exists() or not parquet_path.is_file():
    print("Parquet file doesn't exist")
```

### Catalog Storage Location

The resulting Iceberg table will be created and stored in some location on the filesystem - be that Glue or SQLite. The warehouse defined in `<project_root>/.pyiceberg.yaml` will be the location, and the path you provide will be in that context.

```python
# If catalog is AWS-hosted GLue, specify an AWS S3 filepath
table_loc = "s3://path/to/table"
```
```python
# If catalog is local SQLite, specify a standard filepath
table_loc = "/path/to/table"
```

### Pass in Arguments

The function that handles the table build is `icefabric.builds.build_iceberg_table`. Provide the catalog, namespace, table name, parquet file and storage location. Run the function and check that the table has been created!

```python
from icefabric.builds import build_iceberg_table

# Build table
build_iceberg_table(
    catalog=catalog,
    parquet_file=str(parquet_path)
    namespace=namespace,
    table_name=table_name,
    location=table_loc,
)

# Verify the new table exists
table_def = (namespace, table_name)
if table_def not in catalog.list_tables(namespace):
    print("Something may have went wrong - the new table is not currently in the catalog")
```
