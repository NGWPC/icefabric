import argparse
import os
from pathlib import Path

import pyarrow.parquet as pq
import yaml
from pyiceberg.catalog import load_catalog

from icefabric.helpers import load_creds
from icefabric.schemas import ConflatedRasXS, RepresentativeRasXS

load_creds(dir=Path.cwd())
with open(os.environ["PYICEBERG_HOME"]) as f:
    CONFIG = yaml.safe_load(f)
WAREHOUSE = Path(CONFIG["catalog"]["sql"]["warehouse"].replace("file://", ""))
WAREHOUSE.mkdir(parents=True, exist_ok=True)

LOCATION = {
    "glue": "s3://edfs-data/icefabric_catalog",
    "sql": CONFIG["catalog"]["sql"]["warehouse"],
}
NAMESPACE = "ras_xs"


def build_table(catalog_type: str, file_path: Path, schema_type: str) -> None:
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
        print(f"Table {table_identifier} already exists. Skipping build")
        return

    print("Building XS table")

    # Load data and create table
    arrow_table = pq.read_table(file_path)
    if schema_type == "representative":
        schema = RepresentativeRasXS.schema()
    elif schema_type == "conflated":
        schema = ConflatedRasXS.schema()
    else:
        raise ValueError("Schema not found for your inputted XS file")

    iceberg_table = catalog.create_table(
        table_identifier,
        schema=schema,
        location=LOCATION[catalog_type],
    )
    iceberg_table.append(arrow_table)

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

    args = parser.parse_args()

    build_table(catalog_type=args.catalog, file_path=args.file, schema_type=args.schema)
