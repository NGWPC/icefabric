"""A file to create/build the hydrofabric table and snapshots for a specific domain"""

import argparse
import os
import warnings
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from pyiceberg.catalog import load_catalog
from pyiceberg.transforms import IdentityTransform

from icefabric.helpers import load_creds
from icefabric.schemas import (
    DivideAttributes,
    Divides,
    FlowpathAttributes,
    FlowpathAttributesML,
    Flowpaths,
    HydrofabricSnapshot,
    Hydrolocations,
    Lakes,
    Network,
    Nexus,
    POIs,
)

# Loading credentials, setting path to save outputs
load_creds()
with open(os.environ["PYICEBERG_HOME"]) as f:
    CONFIG = yaml.safe_load(f)
WAREHOUSE = Path(CONFIG["catalog"]["sql"]["warehouse"].replace("file://", ""))
WAREHOUSE.mkdir(parents=True, exist_ok=True)

LOCATION = {
    "glue": "s3://edfs-data/icefabric_catalog",
    "sql": CONFIG["catalog"]["sql"]["warehouse"],
}

# Suppress threading cleanup warnings
warnings.filterwarnings("ignore", category=ResourceWarning)


def build_hydrofabric(catalog_type: str, file_dir: str, domain: str):
    """Builds the hydrofabric Iceberg tables

    Parameters
    ----------
    catalog_type : str
        the type of catalog. sql is local, glue is production
    file_dir : str
        where the files are located
    domain : str
        the HF domain to be built
    """
    catalog = load_catalog(catalog_type)
    namespace = f"{domain}_hf"
    catalog.create_namespace_if_not_exists(namespace)
    layers = [
        ("divide-attributes", DivideAttributes),
        ("divides", Divides),
        ("flowpath-attributes-ml", FlowpathAttributesML),
        ("flowpath-attributes", FlowpathAttributes),
        ("flowpaths", Flowpaths),
        ("hydrolocations", Hydrolocations),
        ("lakes", Lakes),
        ("network", Network),
        ("nexus", Nexus),
        ("pois", POIs),
    ]
    snapshots = {}
    snapshots["domain"] = domain
    for layer, schema in layers:
        print(f"Building layer: {layer}")
        try:
            table = pq.read_table(f"{file_dir}/{layer}.parquet", schema=schema.arrow_schema())
        except FileNotFoundError:
            print(f"Cannot find {layer} in the given file dir {file_dir}")
            continue
        if catalog.table_exists(f"{namespace}.{layer}"):
            print(f"Table {layer} already exists. Skipping build")
            current_snapshot = catalog.load_table(f"{namespace}.{layer}").current_snapshot()
            snapshots[layer] = current_snapshot.snapshot_id
        else:
            iceberg_table = catalog.create_table(
                f"{namespace}.{layer}",
                schema=schema.schema(),
                location=f"{LOCATION[catalog_type]}/{namespace.lower()}/{layer}",
            )
            partition_spec = iceberg_table.spec()
            if len(partition_spec.fields) == 0:
                with iceberg_table.update_spec() as update:
                    update.add_field("vpuid", IdentityTransform(), "vpuid_partition")
            iceberg_table.append(table)
            current_snapshot = iceberg_table.current_snapshot()
            snapshots[layer] = current_snapshot.snapshot_id

    snapshot_namespace = "hydrofabric_snapshots"
    snapshot_table = f"{snapshot_namespace}.id"
    catalog.create_namespace_if_not_exists(snapshot_namespace)
    if catalog.table_exists(snapshot_table):
        tbl = catalog.load_table(snapshot_table)
    else:
        tbl = catalog.create_table(
            snapshot_table,
            schema=HydrofabricSnapshot.schema(),
            location=f"{LOCATION[catalog_type]}/{snapshot_namespace}",
        )
    df = pa.Table.from_pylist([snapshots], schema=HydrofabricSnapshot.arrow_schema())
    tbl.append(df)
    tbl.manage_snapshots().create_tag(tbl.current_snapshot().snapshot_id, "base").commit()
    print(f"Build complete. Files written into metadata store on {catalog.name} @ {namespace}")
    print(f"Snapshots written to: {snapshot_namespace}.id")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build a PyIceberg catalog in the S3 Table for the Hydrofabric"
    )

    parser.add_argument(
        "--catalog",
        choices=["sql", "glue"],
        default="sql",
        help="Catalog type to use (default: sql for local build)",
    )
    parser.add_argument(
        "--files",
        type=Path,
        required=True,
        help="Path to the folder containing Hydrofabric parquet files",
    )
    parser.add_argument(
        "--domain",
        type=str,
        required=True,
        choices=["conus", "ak", "hi", "prvi", "gl"],
        help="The hydrofabric domain to be used for the namespace",
    )

    args = parser.parse_args()

    build_hydrofabric(catalog_type=args.catalog, file_dir=args.files, domain=args.domain)
