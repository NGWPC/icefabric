import argparse
import os
from pathlib import Path

import pyarrow.parquet as pq
import yaml
from pyiceberg.catalog import Catalog, load_catalog

from icefabric.helpers import load_creds
from icefabric.schemas import ExtractedRasXS

load_creds(dir=Path.cwd())

LOCATION = "s3://edfs-data/icefabric_catalog/extracted_ras_xs"
NAMESPACE = "ras_xs"
TABLE_NAME = "extracted"


def build_table(catalog: Catalog, file_path: Path) -> None:
    """Build the RAS XS table in a PyIceberg warehouse.

    Parameters
    ----------
    catalog : Catalog
        The PyIceberg catalog object
    file_path : Path
        Path to the parquet file to upload to the warehouse

    Raises
    ------
    FileNotFoundError
        If the parquet file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot find file: {file_path}")

    print(f"Processing file: {file_path}")

    catalog.create_namespace_if_not_exists(NAMESPACE)

    table_identifier = f"{NAMESPACE}.{TABLE_NAME}"

    if catalog.table_exists(table_identifier):
        print(f"Table {table_identifier} already exists. Skipping build")
        return

    print("Building XS table")

    # Load data and create table
    arrow_table = pq.read_table(file_path)
    schema = ExtractedRasXS.schema()

    iceberg_table = catalog.create_table(
        table_identifier,
        schema=schema,
        location=LOCATION,
    )
    iceberg_table.append(arrow_table)

    print(f"Build successful. Files written to metadata store @ {catalog.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a PyIceberg catalog in the S3 endpoint for FEMA-BLE data"
    )

    parser.add_argument(
        "--catalog",
        choices=["sql", "glue"],
        default="sql",
        help="Catalog type to use (default: sql for local build)",
    )
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to the parquet file containing processed cross sections",
    )

    args = parser.parse_args()

    if args.catalog == "sql":
        with open(os.environ["PYICEBERG_HOME"]) as f:
            config = yaml.safe_load(f)
        warehouse = Path(config["catalog"]["sql"]["warehouse"].replace("file://", ""))
        warehouse.mkdir(parents=True, exist_ok=True)

    catalog = load_catalog(args.catalog)
    build_table(catalog=catalog, file_path=args.file)
