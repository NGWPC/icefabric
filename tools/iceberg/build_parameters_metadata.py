import argparse

import pyarrow.parquet as pq
from pyiceberg.catalog import load_catalog

from icefabric.helpers import load_creds
from icefabric.schemas import ParameterMetadata

load_creds()


def build_parameter_metadata(file_dir, filename):
    """Builds the parameter metadata namespace and table

    Parameters
    ----------
    file_dir : str
        The directory to parameter metadata parquet file
    filename: str
        The filename of the parquet file
    """
    try:
        table = pq.read_table(f"{file_dir}/{filename}", schema=ParameterMetadata.arrow_schema())
    except FileNotFoundError:
        print(f"Cannot find {file_dir}/{filename} in the given file dir {file_dir}")

    catalog = load_catalog("glue")  # Using an AWS Glue Endpoint
    namespace = "parameter_metadata"
    table_name = "parameter_metadata"

    if catalog.table_exists(f"{namespace}.{table_name}"):
        print(f"Table {table_name} already exists. Skipping build")
        return
    else:
        iceberg_table = catalog.create_table(
            f"{namespace}.{table_name}",
            schema=ParameterMetadata.schema(),
            location=f"s3://edfs-data/icefabric_catalog/{namespace}{table_name}",
        )

    print(iceberg_table.schema)
    iceberg_table.append(table)
    print(f"Build successful. Files written into metadata store @ {catalog.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script to build a pyiceberg catalog in the S3 Table")

    parser.add_argument("--path", help="The local file dir where the file is located")
    parser.add_argument("--file", help="The name of the parquet file")

    args = parser.parse_args()
    build_parameter_metadata(file_dir=args.path, filename=args.file)
