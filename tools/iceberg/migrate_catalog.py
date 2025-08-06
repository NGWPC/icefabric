from pathlib import Path

import pyarrow.parquet as pq
from pyiceberg.catalog import Catalog, load_catalog
from pyiceberg.table import Table

from icefabric.helpers import load_creds

load_creds(dir=Path.cwd())


def migrate_table_in_place(
    catalog: Catalog, table_name: str, new_location: str, backup_location: str | None = None
) -> Table:
    """A script to migrate/move pyiceberg tables to a new location and to save to disk

    Parameters
    ----------
    catalog : Catalog
        The pyiceberg catalog
    table_name : str
        The table name to be moved. Ex: conus_hf.network
    new_location : str
        the new S3 location in glue for the table data to reside
    backup_location : str | None, optional
        Where to save a backup parquet file in case the move goes wrong, by default None

    Returns
    -------
    Table
        The moved pyiceberg table in memory
    """
    print(f"WARNING: This will drop and recreate table {table_name}")
    print(f"New location will be: {new_location}")

    old_table = catalog.load_table(table_name)
    schema = old_table.schema()
    partition_spec = old_table.spec()
    sort_order = old_table.sort_order()
    properties = old_table.properties

    # Export all data
    print("Exporting data...")
    all_data = old_table.scan().to_arrow()
    row_count = len(all_data)
    print(f"Exported {row_count} rows")

    # Optional: Save to backup location first
    if backup_location:
        print(f"Saving backup to {backup_location}")
        # You could write to S3 or local file here
        Path(backup_location).parent.mkdir(exist_ok=True)
        pq.write_table(all_data, backup_location)

    print(f"Dropping table {table_name}")
    catalog.drop_table(table_name)

    try:
        # Create new table with new location
        print(f"Creating new table at {new_location}")
        new_table = catalog.create_table(
            identifier=table_name,  # Same name
            schema=schema,
            location=new_location,  # New location
            partition_spec=partition_spec,
            sort_order=sort_order,
            properties=properties,
        )
        # Import the data
        print("Importing data to new table...")

        # For Hydrofabric. Partition based on VPU
        # if len(partition_spec.fields) == 0:
        #     with new_table.update_spec() as update:
        #         update.add_field("vpuid", IdentityTransform(), "vpuid_partition")
        new_table.append(all_data)
        return new_table

    except Exception as e:
        print(f"CRITICAL ERROR during migration: {str(e)}")
        print("Table has been dropped but recreation failed!")
        print("You may need to restore from backup")
        raise


if __name__ == "__main__":
    catalog = load_catalog("glue")
    # namespace = "gl_hf"
    # layers = [
    #     "divide-attributes",
    #     "divides",
    #     "flowpath-attributes-ml",
    #     "flowpath-attributes",
    #     "flowpaths",
    #     "hydrolocations",
    #     "lakes",
    #     "network",
    #     "nexus",
    #     "pois",
    # ]
    namespace = "streamflow_observations"
    for _, table_name in catalog.list_tables(namespace):
        table_to_migrate = f"{namespace}.{table_name}"
        new_location = f"s3://edfs-data/icefabric_catalog/{namespace}/{table_name}"

        table = migrate_table_in_place(
            catalog=catalog,
            table_name=table_to_migrate,
            new_location=new_location,
            backup_location=f"/tmp/backup/{namespace}/{table_name}.parquet",
        )

        print(f"Successfully migrated {table_name} to {new_location}")
        print(f"Sample output: {table.scan().to_pandas().head()}")
