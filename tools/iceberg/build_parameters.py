import argparse

from dotenv import load_dotenv
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NamespaceAlreadyExistsError

from icefabric.builds import build_iceberg_table

load_dotenv()


def build_table(file_dir):
    """Builds the divide parameters namespace and tables

    Parameters
    ----------
    file_dir : str
        The directory to hydrofabric parquet files
    """
    parquet_tables = {
        "CFE-X_params_Alaska_2.2.parquet": "CFE-X_Alaska",
        "CFE-X_params_GL_2.2.parquet": "CFE-X_GL",
        "CFE-X_params_Puerto_Rico_2.2.parquet": "CFE-X_Puerto_Rico",
        "snow17_params_2.2.parquet": "Snow-17_CONUS",
        "CFE-X_params_CONUS_2.2.parquet": "CFE-X_CONUS",
        "CFE-X_params_Hawaii_2.2.parquet": "CFE-X_Hawaii",
        "sac_sma_params_2.2.parquet": "Sac-SMA_CONUS",
        "ueb_params.parquet": "UEB_CONUS",
    }

    catalog = load_catalog("glue")  # Using an AWS Glue Endpoint
    namespace = "divide_parameters"
    try:
        catalog.create_namespace(namespace)
    except NamespaceAlreadyExistsError:
        print(f"Namespace {namespace} already exists")

    for file in parquet_tables.keys():
        build_iceberg_table(
            catalog=catalog,
            parquet_file=f"{file_dir}/{file}",
            namespace=namespace,
            table_name=parquet_tables[file],
            location=f"s3://edfs-data/icefabric_catalog/{namespace}{parquet_tables[file]}",
        )
        print(f"Build successful. Files written into metadata store @ {catalog.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script to build a pyiceberg catalog in the S3 Table")

    parser.add_argument("--files", help="The local file dir where the files are located")

    args = parser.parse_args()
    build_table(file_dir=args.files)
