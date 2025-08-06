This folder is set up to build remote iceberg catalogs to the S3 endpoints. The following template can be used to easily create a build script:

The following variables must always be set when building

`namespace` which is the location of the namespace package to be used
`table_name` the name of each table
`parquet_file` the parquet file we're building into the S3 Glue catalog

Below contains an argparse script that can be easily manipulated to build an iceberg catalog:
```python
import argparse

from dotenv import load_dotenv
from pyiceberg.catalog import load_catalog

from icefabric_manage import build

load_dotenv()

def build_table(file_dir: str):
    """Builds the hydrofabric namespace and tables

    Parameters
    ----------
    file_dir : str
        The directory to hydrofabric parquet files
    """
    catalog = load_catalog("glue")  # Using an AWS Glue Endpoint
    namespace = "<INSERT NAMESPACE HERE>"
    try:
        catalog.create_namespace(namespace)
    except NamespaceAlreadyExistsError:
        print(f"Namespace {namespace} already exists")
    .
    .
    build(
        catalog=catalog,
        parquet_file=<PARQUET_FILE>,
        namespace=namespace,
        table_name=<TABLE_NAME>,
        location="s3://fim-services-data-test/icefabric_metadata/"
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script to build a pyiceberg catalog in the S3 endpoint"
    )

    parser.add_argument("--files", help="The local file dir where the files are located")

    args = parser.parse_args()
    build_table(file_dir=args.files)

```
