import argparse
from pathlib import Path

import pandas as pd
import pyarrow as pa
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NamespaceAlreadyExistsError

from icefabric.helpers import load_creds

load_creds(dir=Path.cwd())


def clean_parquet_schema(parquet_file: str) -> pa.Table:
    """Clean parquet file to handle null types (ex: WaterbodyID and waterbody_nex_id)

    Parameters
    ----------
    parquet_file : str
        Path to the parquet file

    Returns
    -------
    pa.Table
        Cleaned Arrow table
    """
    # Read with pandas first to handle null types easily
    df = pd.read_parquet(parquet_file)
    null_columns = []
    for col in df.columns:
        if df[col].dtype == "object" and df[col].isna().all():
            df[col] = df[col].astype("string")
            null_columns.append(col)
    if null_columns:
        print(f"Converted null-type columns to string: {null_columns}")
    return pa.Table.from_pandas(df, preserve_index=False)


def build_table(file_dir: str, domain: str):
    """Builds the hydrofabric namespace and tables

    Parameters
    ----------
    file_dir : str
        The directory to hydrofabric parquet files
    """
    catalog = load_catalog("glue")  # Using an AWS Glue Endpoint
    namespace = f"{domain}_HF"
    try:
        catalog.create_namespace(namespace)
    except NamespaceAlreadyExistsError:
        print(f"Namespace {namespace} already exists")
    layers = [
        "divide-attributes",
        "divides",
        "flowpath-attributes-ml",
        "flowpath-attributes",
        "flowpaths",
        "hydrolocations",
        "lakes",
        "network",
        "nexus",
        "pois",
    ]
    for layer in layers:
        print(f"building layer: {layer}")
        try:
            cleaned_table = clean_parquet_schema(f"{file_dir}/{layer}.parquet")
            if catalog.table_exists(f"{namespace}.{layer}"):
                print(f"Table {layer} already exists. Skipping build")
            else:
                iceberg_table = catalog.create_table(
                    f"{namespace}.{layer}",
                    schema=cleaned_table.schema,
                    location="s3://fim-services-data-test/icefabric_metadata/",
                )
                iceberg_table.append(cleaned_table)
        except FileNotFoundError:
            print(f"Cannot find {layer} in the given file dir {file_dir}")
            pass

    print(f"Build successful. Files written into metadata store on {catalog.name} @ {namespace}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script to build a pyiceberg catalog in the S3 endpoint")

    parser.add_argument("--files", help="The local file dir where the files are located")
    parser.add_argument("--domain", help="The hydrofabric domain to be used for the namespace")

    args = parser.parse_args()
    build_table(file_dir=args.files, domain=args.domain)
