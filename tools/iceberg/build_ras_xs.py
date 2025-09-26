import argparse
import os
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from pyiceberg.catalog import load_catalog

from icefabric.helpers import load_creds
from icefabric.schemas import ConflatedRasXS, RepresentativeRasXS

load_creds()
with open(os.environ["PYICEBERG_HOME"]) as f:
    CONFIG = yaml.safe_load(f)
WAREHOUSE = Path(CONFIG["catalog"]["sql"]["warehouse"].replace("file://", ""))
WAREHOUSE.mkdir(parents=True, exist_ok=True)

LOCATION = {
    "glue": "s3://edfs-data/icefabric_catalog",
    "sql": CONFIG["catalog"]["sql"]["warehouse"],
}
NAMESPACE = "ras_xs"


def build_table(catalog_type: str, file_path: Path, schema_type: str, overwrite: bool) -> None:
    """Build the RAS XS table in a PyIceberg warehouse.

    Parameters
    ----------
    catalog : str
        The PyIceberg catalog type
    file_path : Path
        Path to the parquet file to upload to the warehouse
    schema_type : str
        The schema to validate against. Either representative XS or all conflated XS

    Raises
    ------
    FileNotFoundError
        If the parquet file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot find file: {file_path}")

    print(f"Processing file: {file_path}")
    catalog = load_catalog(catalog_type)
    catalog.create_namespace_if_not_exists(NAMESPACE)

    table_identifier = f"{NAMESPACE}.{schema_type}"
    if catalog.table_exists(table_identifier):
        if not overwrite:
            print(f"Table {table_identifier} already exists. Skipping build")
            return
        else:
            print(f"Table {table_identifier} will be overwritten.")

    print("Building XS table")

    if schema_type == "representative":
        schema = RepresentativeRasXS.schema()
        pa_schema = RepresentativeRasXS.arrow_schema()
    elif schema_type == "conflated":
        schema = ConflatedRasXS.schema()
        pa_schema = ConflatedRasXS.arrow_schema()
    else:
        raise ValueError("Schema not found for your inputted XS file")

    if not overwrite:
        iceberg_table = catalog.create_table(
            table_identifier,
            schema=schema,
            location=LOCATION[catalog_type],
        )
    else:
        iceberg_table = catalog.load_table(table_identifier)
        with iceberg_table.update_schema() as update:
            update.union_by_name(schema)

    # Load data and create table
    parquet_file = pq.ParquetFile(file_path)
    if not overwrite:
        for batch in parquet_file.iter_batches(batch_size=500000):
            print("Adding batch...")
            arrow_table = pa.Table.from_batches([batch])
            arrow_table = arrow_table.cast(pa_schema)
            iceberg_table.append(arrow_table)
            print("Batch appended to iceberg table...")
    else:
        first_thru = True
        for batch in parquet_file.iter_batches(batch_size=500000):
            print("Adding batch...")
            arrow_table = pa.Table.from_batches([batch])
            arrow_table = arrow_table.cast(pa_schema)
            if first_thru:
                print("Overwriting table with first batch...")
                iceberg_table.overwrite(arrow_table)
                first_thru = False
            else:
                iceberg_table.append(arrow_table)
                print("Batch appended to iceberg table...")

    print(f"Build successful. Files written to metadata store @ {catalog.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a PyIceberg catalog in the S3 Table for FEMA-BLE data"
    )
    parser.add_argument(
        "--catalog",
        choices=["sql", "glue"],
        default="sql",
        help="Catalog type to use (default: sql for local build)",
    )
    parser.add_argument(
        "--schema",
        type=str,
        choices=["representative", "conflated"],
        required=True,
        help="The schema to validate against. Either representative XS or all conflated XS",
    )
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to the parquet file containing processed cross sections",
    )
    parser.add_argument(
        "--overwrite",
        type=bool,
        required=False,
        default=False,
        help="Flag to indicate that it is okay to overwrite an existing table",
    )
    args = parser.parse_args()

    build_table(
        catalog_type=args.catalog, file_path=args.file, schema_type=args.schema, overwrite=args.overwrite
    )
