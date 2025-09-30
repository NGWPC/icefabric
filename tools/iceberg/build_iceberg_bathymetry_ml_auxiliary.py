import argparse
from pathlib import Path

from dotenv import load_dotenv
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NamespaceAlreadyExistsError

from icefabric.builds import build_iceberg_table

load_dotenv()


def build_table(file_dir: Path):
    """Builds the bathymetric channel data for the Hydrofabric

    Parameters
    ----------
    file_dir : str
        The directory to hydrofabric parquet files
    """
    catalog = load_catalog("glue")  # Using an AWS Glue Endpoint
    namespace = "bathymetry_ml_auxiliary"
    try:
        catalog.create_namespace(namespace)
    except NamespaceAlreadyExistsError:
        print(f"Namespace {namespace} already exists")

    layers = [
        "vpuid=01",
        "vpuid=02",
        "vpuid=03N",
        "vpuid=03S",
        "vpuid=03W",
        "vpuid=04",
        "vpuid=05",
        "vpuid=06",
        "vpuid=07",
        "vpuid=08",
        "vpuid=09",
        "vpuid=10L",
        "vpuid=10U",
        "vpuid=11",
        "vpuid=12",
        "vpuid=13",
        "vpuid=14",
        "vpuid=15",
        "vpuid=16",
        "vpuid=17",
    ]

    for layer in layers:
        print(f"building layer: {layer}")
        # The following warning is expected:
        # Iceberg does not have a dictionary type. <class 'pyarrow.lib.DictionaryType'> will be inferred as int32 on read.
        # Arrow will make columns with a single, non-unique, value into a dictionary for ease of writing/loading
        # Thus, when writing to pyiceberg it needs to remove that.
        build_iceberg_table(
            catalog=catalog,
            parquet_file=f"{file_dir}/{layer}/ml_auxiliary_data.parquet",
            namespace=namespace,
            table_name=layer,
            location=f"s3://edfs-data/icefabric_catalog/{namespace}/{layer}",
        )
    print(f"Build successful. Files written into metadata store @ {catalog.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script to build a pyiceberg catalog for bathymetric data in the S3 Table"
    )

    parser.add_argument("--files", help="The local file dir where the files are located")

    args = parser.parse_args()
    build_table(file_dir=args.files)
