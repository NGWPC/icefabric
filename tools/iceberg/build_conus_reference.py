import argparse

import pyarrow.parquet as pq
from pyiceberg.catalog import load_catalog
from pyiceberg.transforms import IdentityTransform

from icefabric.helpers import load_creds
from icefabric.schemas import ReferenceDivides, ReferenceFlowpaths

load_creds()


def build_table(catalog_type: str, file_dir: str):
    """Builds the hydrofabric namespace and tables

    Parameters
    ----------
    file_dir : str
        The directory to hydrofabric parquet files
    """
    catalog = load_catalog(catalog_type)
    namespace = "conus_reference"
    catalog.create_namespace_if_not_exists(namespace)
    layers = [("reference_flowpaths", ReferenceFlowpaths), ("reference_divides", ReferenceDivides)]
    for layer, schema in layers:
        print(f"building layer: {layer}")
        try:
            table = pq.read_table(f"{file_dir}/{layer}.parquet", schema=schema.arrow_schema())
        except FileNotFoundError:
            print(f"Cannot find {layer} in the given file dir {file_dir}")
            continue
        if catalog.table_exists(f"{namespace}.{layer}"):
            print(f"Table {layer} already exists. Skipping build")
        else:
            iceberg_table = catalog.create_table(
                f"{namespace}.{layer}",
                schema=schema.schema(),
                location=f"s3://edfs-data/icefabric_catalog/{namespace.lower()}/{layer}",
            )
            partition_spec = iceberg_table.spec()
            if "vpuid" in table.column_names:
                col = "vpuid"
            else:
                col = "VPUID"
            if len(partition_spec.fields) == 0:
                with iceberg_table.update_spec() as update:
                    update.add_field(col, IdentityTransform(), "vpuid_partition")
            iceberg_table.append(table)

    print(f"Build complete. Files written into metadata store on {catalog.name} @ {namespace}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script to build a pyiceberg catalog for the conus reference fabric"
    )
    parser.add_argument(
        "--catalog",
        choices=["sql", "glue"],
        default="sql",
        help="Catalog type to use (default: sql for local build)",
    )
    parser.add_argument("--files", help="The directory containing the conus_reference parquet files")

    args = parser.parse_args()
    build_table(catalog_type=args.catalog, file_dir=args.files)
