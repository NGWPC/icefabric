import argparse
from datetime import datetime

from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table


def open_table(namespace: str, table_name: str) -> Table:
    """Loads Iceberg catalog and table

    Parameters
    ----------
    namespace : str
       The namespace where the iceberg table is stored
    catalog_name : str
    table_name
        The name of the table.

    Returns
    -------
    Table
        The requested Pyiceberg table
    """
    catalog = load_catalog("glue")
    table = catalog.load_table(f"{namespace}.{table_name}")

    return table


def get_snapshots(table: Table):
    """Get a list of snapshot ids and timestamps

    Parameters
    ----------
    table : Table
        The table from the open_table function

    Returns
    -------
    None
    """
    snapshots = table.history()
    snapshots_list = []
    for snapshot in snapshots:
        snapshots_list.append(dict(snapshot))

    for snapshot in snapshots_list:
        id = snapshot["snapshot_id"]
        date_time = datetime.fromtimestamp(snapshot["timestamp_ms"] / 1000)
        print(f"{id}:  {date_time}")


def set_snapshot(table: Table, snapshot_id: int) -> None:
    """Updates the existing parameter metadata iceberg table using a Parquet file.

    Parameters
    ----------
    table : Table
       The table from open_table
    snapshot_id : int
       The snapshot ID to set as the current snapshot

    Returns
    -------
    None
    """
    try:
        with table.manage_snapshots() as ms:
            ms.set_current_snapshot(snapshot_id=snapshot_id)
            print(f"table successfully set to {snapshot_id}")

    except ValueError as e:
        # Triggered if the snapshot ID is invalid or not an ancestor of the current state
        print(f"Invalid snapshot or ancestor error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="View snapshots for a namespace and table.  Set current snapshot to snapshot ID if provided"
    )

    parser.add_argument("--namespace", help="The namespace where the Iceberg table is stored")
    parser.add_argument("--table_name", help="The name of the parquet file")
    parser.add_argument("--snapshot_id", help="If provided the current snapshot will be set to this ID")

    args = parser.parse_args()
    table = open_table(namespace=args.namespace, table_name=args.table_name)
    get_snapshots(table)

    if args.snapshot_id:
        set_snapshot(table=table, snapshot_id=int(args.snapshot_id))
