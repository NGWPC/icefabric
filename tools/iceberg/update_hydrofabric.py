"""A file to update the hydrofabric table and snapshots for a specific domain"""

import argparse
import os
import warnings
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from pyiceberg.catalog import load_catalog
from pyiceberg.expressions import EqualTo

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
load_creds(dir=Path.cwd())
with open(os.environ["PYICEBERG_HOME"]) as f:
    CONFIG = yaml.safe_load(f)

LOCATION = {
    "glue": "s3://edfs-data/icefabric_catalog",
    "sql": CONFIG["catalog"]["sql"]["warehouse"],
}

# Suppress threading cleanup warnings
warnings.filterwarnings("ignore", category=ResourceWarning)


def update_hydrofabric(catalog_type: str, layer: str, file: Path, domain: str, tag: str | None = None):
    """A script to update the hydrofabric for a specific layer

    Parameters
    ----------
    catalog_type : str
        specifying either a local (sql) or remote (glue) endpoint
    layer : str
        The layer of the hydrofabric to update
    file : Path
        the path to the updated HF parquet file
    domain : str
        the domain to update
    tag : str | None, optional
        A tag to place on the updates, by default None

    Raises
    ------
    FileNotFoundError
        Cannot find inputted parquet file
    """
    catalog = load_catalog(catalog_type)
    namespace = f"{domain}_hf"
    layers = {
        "divide-attributes": DivideAttributes,
        "divides": Divides,
        "flowpath-attributes-ml": FlowpathAttributesML,
        "flowpath-attributes": FlowpathAttributes,
        "flowpaths": Flowpaths,
        "hydrolocations": Hydrolocations,
        "lakes": Lakes,
        "network": Network,
        "nexus": Nexus,
        "pois": POIs,
    }
    snapshots = {}
    snapshots["domain"] = domain
    schema = layers[layer]
    print(f"Updating layer: {layer}")
    try:
        table = pq.read_table(file, schema=schema.arrow_schema())
    except FileNotFoundError as e:
        print("Cannot find input file")
        raise FileNotFoundError from e
    if catalog.table_exists(f"{namespace}.{layer}"):
        iceberg_table = catalog.load_table(f"{namespace}.{layer}")
        iceberg_table.overwrite(table)  # TODO See issue #81 for support of upsert
        current_snapshot = iceberg_table.current_snapshot()
        snapshots[layer] = current_snapshot.snapshot_id
        print()
    else:
        print(f"{layer} not found in S3 Tables. Please run `build_hydrofabric.py` First prior to updating")

    snapshot_namespace = "hydrofabric_snapshots"
    tbl = catalog.load_table(f"{snapshot_namespace}.id")
    df = tbl.scan(row_filter=EqualTo("domain", domain)).to_pandas()
    df[layer] = snapshots[layer]
    table = pa.Table.from_pandas(df, preserve_index=False, schema=HydrofabricSnapshot.arrow_schema())
    tbl.upsert(table)
    if tag is not None:
        tbl.manage_snapshots().create_tag(tbl.current_snapshot().snapshot_id, tag).commit()
    print(f"Build complete. Files written into metadata store on {catalog.name} @ {namespace}")
    print(f"Snapshots written to: {snapshot_namespace}.id")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update a PyIceberg catalog in the S3 Table for the Hydrofabric"
    )

    parser.add_argument(
        "--catalog",
        choices=["sql", "glue"],
        default="sql",
        help="Catalog type to use (default: sql for local build)",
    )
    parser.add_argument(
        "--layer",
        type=str,
        required=True,
        help="the layer to be updated in S3 Tables",
    )
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="Path to the file for the updated Hydrofabric parquet file",
    )
    parser.add_argument(
        "--domain",
        type=str,
        required=True,
        choices=["conus", "ak", "hi", "prvi", "gl"],
        help="The hydrofabric domain to be used for the namespace",
    )
    parser.add_argument(
        "--tag",
        type=str,
        required=False,
        help="A tag to add to the snapshot table update",
    )

    args = parser.parse_args()

    update_hydrofabric(
        catalog_type=args.catalog, layer=args.layer, file=args.file, domain=args.domain, tag=args.tag
    )
    # update_hydrofabric(catalog_type="sql", layer="network", file="/Users/taddbindas/projects/NGWPC/icefabric/data/hydrofabric/update_tmp/network.parquet", domain="conus")
