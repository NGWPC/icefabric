import argparse
from pathlib import Path

import pyarrow.parquet as pq
from dotenv import load_dotenv
from pyiceberg.catalog import Catalog, load_catalog

from icefabric.schemas import ExtractedRasXS

load_dotenv(Path.cwd())

LOCATION = "s3://edfs-data/icefabric_catalog/extracted_ras_xs"
NAMESPACE = "ras_xs"
TABLE_NAME = "extracted"


def update_table(catalog: Catalog, file_path: Path) -> None:
    """Updates the RAS XS table in a PyIceberg warehouse using an upsert. Only new data is uploaded

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
    table_identifier = f"{NAMESPACE}.{TABLE_NAME}"
    table = catalog.load_table(table_identifier)
    arrow_table = pq.read_table(file_path, schema=ExtractedRasXS.arrow_schema())
    table.overwrite(arrow_table)
    print(f"Overwrote table at {table_identifier} with new data")


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

    catalog = load_catalog(args.catalog)
    update_table(catalog=catalog, file_path=args.file)
