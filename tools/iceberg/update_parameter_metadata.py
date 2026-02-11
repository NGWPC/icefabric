import argparse

import pyarrow.parquet as pq
from pyiceberg.catalog import load_catalog

from icefabric.schemas import ParameterMetadata


def update_parameter_metadata(file_dir: str, filename: str) -> None:
    """Updates the existing parameter metadata iceberg table using a Parquet file.

    Parameters
    ----------
    file_dir : str
       Path to the location of the Parquet file
    filename : str
       Filename of Parquet file
    """
    try:
        table_data = pq.read_table(f"{file_dir}/{filename}", schema=ParameterMetadata.arrow_schema())
    except FileNotFoundError:
        print(f"Cannot find {file_dir}/{filename} in the given file dir {file_dir}")

    table_name = "parameter_metadata.parameter_metadata"
    catalog = load_catalog("glue")

    if catalog.table_exists(table_name):
        table = catalog.load_table(table_name)
        print(f"overwriting {table_name} with {filename}")
        table.overwrite(table_data)
        print(table.snapshots)
    else:
        print(f"table {table_name} does not exist")
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script to update the parameter metadata table from a Parquet file"
    )

    parser.add_argument("--path", help="The local file dir where the file is located")
    parser.add_argument("--file", help="The name of the parquet file")

    args = parser.parse_args()
    update_parameter_metadata(file_dir=args.path, filename=args.file)
