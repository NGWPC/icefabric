import argparse
from pathlib import Path

from dotenv import load_dotenv
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NamespaceAlreadyExistsError

from icefabric.builds import build_iceberg_table

load_dotenv()


def build_table(file_dir: str):
    """Builds the FEMA BLE XS tables

    Parameters
    ----------
    file_dir : str
        The directory to hydrofabric parquet files
    """
    catalog = load_catalog("glue")  # Using an AWS Glue Endpoint
    namespace = "ble_xs"
    try:
        catalog.create_namespace(namespace)
    except NamespaceAlreadyExistsError:
        print(f"Namespace {namespace} already exists")
    for folder in Path(file_dir).glob("ble_*"):
        huc_number = folder.name.split("_", 1)[1]
        print(f"building HUC XS: {huc_number}")
        build_iceberg_table(
            catalog=catalog,
            parquet_file=f"{file_dir}/ble_{huc_number}/huc_{huc_number}.parquet",
            namespace=namespace,
            table_name=huc_number,
            location=f"s3://edfs-data/icefabric_catalog/{namespace}/{huc_number}",
        )
    print(f"Build successful. Files written into metadata store @ {catalog.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script to build a pyiceberg catalog in the S3 Table for the FEMA-BLE data"
    )

    parser.add_argument("--files", help="The local file dir where the files are located")

    args = parser.parse_args()
    build_table(file_dir=args.files)
