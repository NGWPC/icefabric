"""Build scripts for pyiceberg"""

import pyarrow.parquet as pq
from pyiceberg.catalog import Catalog


def build_iceberg_table(
    catalog: Catalog, parquet_file: str, namespace: str, table_name: str, location: str
) -> None:
    """Builds the hydrofabric catalog based on the .pyiceberg.yaml config and defined parquet files.

    Creates a new Iceberg table from a parquet file if the table doesn't already exist.
    If the table exists, the function will skip the build process and print a message.

    Parameters
    ----------
    catalog : Catalog
        The Apache Iceberg Catalog instance used to manage tables
    parquet_file : str
        Path to the parquet file to be loaded into the Iceberg table
    namespace : str
        The namespace (database/schema) where the table will be created
    table_name : str
        The name of the table to be created in the catalog
    location : str
        The storage location where the Iceberg table data will be stored

    Notes
    -----
    - The function will automatically infer the schema from the parquet file
    - If the table already exists, no action is taken and a message is printed
    - The parquet data is appended to the newly created Iceberg table
    """
    if catalog.table_exists(f"{namespace}.{table_name}"):
        print(f"Table {table_name} already exists. Skipping build")
    else:
        arrow_table = pq.read_table(parquet_file)
        iceberg_table = catalog.create_table(
            f"{namespace}.{table_name}",
            schema=arrow_table.schema,
            location=location,
        )
        iceberg_table.append(arrow_table)
