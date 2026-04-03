"""A file to create/build the NHF table and snapshots for a specific domain"""

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
from icefabric.schemas.iceberg_tables import nhf_layers
from icefabric.schemas.iceberg_tables.nhf_snapshots import NHFSnapshot

# Suppress threading cleanup warnings
warnings.filterwarnings("ignore", category=ResourceWarning)

S3_BUCKETS = {
    "test": "edfs-data",
    "prod": "iceberg-data-oe",
}


def _init(deploy_env: str = "test"):
    """Load credentials and resolve catalog locations."""
    load_creds(deploy_env)
    with open(os.environ["PYICEBERG_HOME"]) as f:
        config = yaml.safe_load(f)
    warehouse = Path(config["catalog"]["sql"]["warehouse"].replace("file://", ""))
    warehouse.mkdir(parents=True, exist_ok=True)
    s3_bucket = S3_BUCKETS.get(deploy_env, S3_BUCKETS["test"])
    return {
        "glue": f"s3://{s3_bucket}/icefabric_catalog",
        "sql": config["catalog"]["sql"]["warehouse"],
    }


DOMAIN_TO_NAMESPACE = {
    "conus": "nhf",
    "ak": "ak_nhf",
    "hi": "hi_nhf",
    "prvi": "prvi_nhf",
}


def tear_down_nhf(catalog_type: str, domain: str = "conus", deploy_env: str = "test"):
    """
    Tears down the hydrofabric Iceberg tables

    Parameters
    ----------
    catalog_type : str
        the type of catalog. sql is local, glue is production
    domain : str
        the NHF domain (conus, ak, hi, prvi)
    deploy_env : str
        the deploy environment (test or prod)
    """
    _init(deploy_env)
    catalog = load_catalog(catalog_type)
    namespace = DOMAIN_TO_NAMESPACE[domain]

    print(f"Tearing down existing NHF tables in {namespace}...")
    for layer in nhf_layers.keys():
        table_identifier = f"{namespace}.{layer}"
        if catalog.table_exists(table_identifier):
            catalog.purge_table(table_identifier)
            print(f"Purged NHF layer table: {table_identifier}")
        else:
            print(f"NHF layer table {table_identifier} does not exist. Skipping purge.")

    print("Tearing down existing NHF snapshot table...")
    snapshot_namespace = f"{namespace}_snapshots"
    snapshot_table_identifier = f"{snapshot_namespace}.id"
    if catalog.table_exists(snapshot_table_identifier):
        catalog.purge_table(snapshot_table_identifier)
        print(f"Purged snapshot table: {snapshot_table_identifier}")
    else:
        print(f"Snapshot table {snapshot_table_identifier} does not exist. Skipping purge.")


def build_nhf(
    catalog_type: str,
    file_dir: str,
    domain: str = "conus",
    overwrite_existing: bool = False,
    deploy_env: str = "test",
):
    """
    Builds the hydrofabric Iceberg tables

    Parameters
    ----------
    catalog_type : str
        the type of catalog. sql is local, glue is production
    file_dir : str
        where the files are located
    domain : str
        the NHF domain (conus, ak, hi, prvi)
    overwrite_existing : bool
        if True, overwrite existing populated tables (preserves old snapshots for rollback)
    deploy_env : str
        the deploy environment (test or prod)
    """
    location = _init(deploy_env)
    catalog = load_catalog(catalog_type)
    namespace = DOMAIN_TO_NAMESPACE[domain]
    catalog.create_namespace_if_not_exists(namespace)
    snapshots = {}

    update_snapshots = False
    for layer, schema in nhf_layers.items():
        build_table = True
        print(f"Building layer: {layer}")
        try:
            table = pq.read_table(f"{file_dir}/{layer}.parquet", schema=schema.arrow_schema())
        except FileNotFoundError:
            print(f"Cannot find {layer} in the given file dir {file_dir}")
            continue
        if catalog.table_exists(f"{namespace}.{layer}"):
            current_snapshot = catalog.load_table(f"{namespace}.{layer}").current_snapshot()
            if current_snapshot is not None:
                if overwrite_existing:
                    print(f"Table {layer} already exists. Overwriting (old snapshots preserved)...")
                    iceberg_table = catalog.load_table(f"{namespace}.{layer}")
                    with iceberg_table.update_schema() as update:
                        update.union_by_name(schema.arrow_schema())
                    iceberg_table.overwrite(table)
                    snapshots[layer] = iceberg_table.current_snapshot().snapshot_id
                    update_snapshots = True
                    build_table = False
                else:
                    print(f"Table {layer} already exists, and is populated. Skipping build")
                    snapshots[layer] = current_snapshot.snapshot_id
                    build_table = False
            else:
                print(f"Table {layer} has no current snapshot (must be empty).")

        if build_table:
            update_snapshots = True
            iceberg_table = catalog.create_table_if_not_exists(
                f"{namespace}.{layer}",
                schema=schema.schema(),
                location=f"{location[catalog_type]}/{namespace.lower()}/{layer}",
            )

            # Bucket partitioning on the schema ID field
            # Additional partitioning on vpu_id if it exists in the schema
            schema_id_field = schema.schema().identifier_field_ids[0]
            schema_id_field = schema.schema().find_field(schema_id_field).name
            partition_spec = iceberg_table.spec()
            if len(partition_spec.fields) == 0:
                with iceberg_table.update_spec() as update:
                    # TODO - look into bucket partitioning during planning/innovation
                    # update.add_field(
                    #     schema_id_field, BucketTransform(100), f"{schema_id_field}_bucket_partition"
                    # )
                    try:
                        schema.schema().find_field("vpu_id")
                        update.add_field("vpu_id", IdentityTransform(), "vpu_id_partition")
                    except ValueError:
                        # No vpu_id field to partition on
                        pass

            iceberg_table.overwrite(table)
            current_snapshot = iceberg_table.current_snapshot()
            snapshots[layer] = current_snapshot.snapshot_id

    if update_snapshots:
        snapshot_namespace = f"{namespace}_snapshots"
        snapshot_table = f"{snapshot_namespace}.id"
        catalog.create_namespace_if_not_exists(snapshot_namespace)
        if catalog.table_exists(snapshot_table):
            tbl = catalog.load_table(snapshot_table)
            with tbl.update_schema() as update:
                update.union_by_name(NHFSnapshot.arrow_schema())
        else:
            tbl = catalog.create_table(
                snapshot_table,
                schema=NHFSnapshot.schema(),
                location=f"{location[catalog_type]}/{snapshot_namespace}",
            )
        df = pa.Table.from_pylist([snapshots], schema=NHFSnapshot.arrow_schema())
        tbl.append(df)
        tbl.manage_snapshots().create_tag(tbl.current_snapshot().snapshot_id, "base").commit()
        print(f"Build complete. Files written into metadata store on {catalog.name} @ {namespace}")
        print(f"Snapshots written to: {snapshot_namespace}.id")
    else:
        print("No table built. All tables were initialized and already had data records. Build skipped.")


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
        "--delete-old",
        action="store_true",
        default=False,
        help="Purges old catalog tables before building new ones - use with caution! This permanently deletes data with no rollback. Prefer --overwrite instead.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing populated tables. Preserves old snapshots for rollback via Iceberg time-travel.",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="conus",
        choices=["conus", "ak", "hi", "prvi"],
        help="The NHF domain (default: conus). Determines the namespace (e.g., ak -> ak_nhf).",
    )
    parser.add_argument(
        "--deploy-env",
        type=str,
        default="test",
        choices=["test", "prod"],
        help="Deploy environment (default: test). Controls AWS credentials and S3 bucket location.",
    )

    args = parser.parse_args()

    if args.delete_old:
        tear_down_nhf(catalog_type=args.catalog, domain=args.domain, deploy_env=args.deploy_env)
    build_nhf(
        catalog_type=args.catalog,
        file_dir=args.files,
        domain=args.domain,
        overwrite_existing=args.overwrite,
        deploy_env=args.deploy_env,
    )
