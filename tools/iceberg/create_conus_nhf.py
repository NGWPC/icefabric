"""
Create conus_nhf namespace by registering tables from nhf namespace.

This creates the new namespace for explicit domain=CONUS&source=nhf requests
while preserving the original nhf namespace for backwards compatibility.

The tables are registered and not copied, meaning both namespaces point to the
same underlying data. Changes to one will be reflected in the other.

Usage:
    # Dry run to see what would happen
    python create_conus_nhf.py --catalog sql --dry-run

    # Run against local catalog
    python create_conus_nhf.py --catalog sql

    # Run against AWS Glue (test environment)
    python create_conus_nhf.py --catalog glue

    # Then migrate to production using existing tooling
    python catalog_migration/catalog_migration.py -n conus_nhf
"""

import argparse
import os

import yaml
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NamespaceAlreadyExistsError, TableAlreadyExistsError

from icefabric.helpers import load_creds
from icefabric.schemas.iceberg_tables import nhf_layers

# Load credentials and config
load_creds()
with open(os.environ["PYICEBERG_HOME"]) as f:
    CONFIG = yaml.safe_load(f)


def create_conus_nhf(catalog_type: str, dry_run: bool = False):
    """
    Create conus_nhf namespace by registering tables from nhf namespace.

    Parameters
    ----------
    catalog_type : str
        The type of catalog. 'sql' is local, 'glue' is production.
    dry_run : bool
        If True, print actions without executing them.
    """
    catalog = load_catalog(catalog_type)
    source_namespace = "nhf"
    dest_namespace = "conus_nhf"

    # 1. Create the new namespace
    print(f"Creating namespace: {dest_namespace}")
    if not dry_run:
        try:
            catalog.create_namespace(dest_namespace)
            print(f"  Created namespace: {dest_namespace}")
        except NamespaceAlreadyExistsError:
            print(f"  Namespace {dest_namespace} already exists, continuing...")

    # 2. For each table in nhf, register it in conus_nhf
    for layer in nhf_layers.keys():
        source_table = f"{source_namespace}.{layer}"
        dest_table = f"{dest_namespace}.{layer}"

        print(f"Registering {dest_table} from {source_table}")

        if dry_run:
            print(f"  [DRY RUN] Would register {dest_table}")
            continue

        # Check if source table exists
        if not catalog.table_exists(source_table):
            print(f"  WARNING: Source table {source_table} does not exist, skipping")
            continue

        # Check if destination table already exists
        if catalog.table_exists(dest_table):
            print(f"  Table {dest_table} already exists, skipping")
            continue

        try:
            # Load the source table to get its metadata location
            table = catalog.load_table(source_table)
            metadata_location = table.metadata_location

            # Register the same metadata location under the new namespace
            catalog.register_table(dest_table, metadata_location)
            print(f"  Registered {dest_table} -> {metadata_location}")
        except TableAlreadyExistsError:
            print(f"  Table {dest_table} already exists, skipping")
        except Exception as e:  # noqa: BLE001
            print(f"  ERROR registering {dest_table}: {e}")

    print("\nDone!")
    if dry_run:
        print("(This was a dry run - no changes were made)")


def tear_down_conus_nhf(catalog_type: str, dry_run: bool = False):
    """
    Remove the conus_nhf namespace and its table registrations.

    Note: This only removes the table registrations, not the underlying data
    (which is shared with the nhf namespace).

    Parameters
    ----------
    catalog_type : str
        The type of catalog. 'sql' is local, 'glue' is production.
    dry_run : bool
        If True, print actions without executing them.
    """
    catalog = load_catalog(catalog_type)
    namespace = "conus_nhf"

    print(f"Tearing down namespace: {namespace}")

    for layer in nhf_layers.keys():
        table_identifier = f"{namespace}.{layer}"
        if dry_run:
            print(f"  [DRY RUN] Would drop table: {table_identifier}")
            continue

        if catalog.table_exists(table_identifier):
            # Use drop_table (not purge_table) to remove registration without deleting data
            catalog.drop_table(table_identifier)
            print(f"  Dropped table registration: {table_identifier}")
        else:
            print(f"  Table {table_identifier} does not exist, skipping")

    # Drop the namespace
    if not dry_run:
        try:
            catalog.drop_namespace(namespace)
            print(f"  Dropped namespace: {namespace}")
        except Exception as e:  # noqa: BLE001
            print(f"  Could not drop namespace {namespace}: {e}")

    print("\nTeardown complete!")
    if dry_run:
        print("(This was a dry run - no changes were made)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create conus_nhf namespace by registering tables from nhf namespace"
    )

    parser.add_argument(
        "--catalog",
        choices=["sql", "glue"],
        default="sql",
        help="Catalog type to use (default: sql for local build)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print actions without executing them",
    )
    parser.add_argument(
        "--teardown",
        action="store_true",
        default=False,
        help="Remove the conus_nhf namespace (does not delete underlying data)",
    )

    args = parser.parse_args()

    if args.teardown:
        tear_down_conus_nhf(catalog_type=args.catalog, dry_run=args.dry_run)
    else:
        create_conus_nhf(catalog_type=args.catalog, dry_run=args.dry_run)
