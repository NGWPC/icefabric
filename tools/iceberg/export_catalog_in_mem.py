import argparse
import os
import subprocess
from pathlib import Path

import yaml
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NamespaceAlreadyExistsError
from tqdm import tqdm

from icefabric.helpers import load_creds


def create_tmpfs_ramdisk(mount_point: Path):
    """Given a mount point, creates a tmpfs ramdisk

    Parameters
    ----------
    mount_point : Path
        The path where the mount point is created
    """
    mount_point = str(mount_point).replace("file://", "")
    subprocess.run(["sudo", "mkdir", "-p", mount_point], check=True)
    subprocess.run(["sudo", "mount", "-o", "size=6G", "-t", "tmpfs", "none", mount_point], check=True)
    print(f"tmpfs mounted at {mount_point}")


def export_catalog(namespace: str, export_catalog_dest: str, in_ram: bool):
    """Exports the catalog to a local SQL file based on the .pyiceberg.yaml in the project root

    Parameters
    ----------
    namespace : str
        The namespace to be exported
    export_catalog_dest : str
        The local catalog that is receiving the exported repo
    in_ram : bool
        If the catalog will live inside a tmpfs mount (in RAM)

    Raises
    ------
    NamespaceAlreadyExistsError
        If the namespace already exists in the destination catalog
    """
    # Creates the local dir for the warehouse if it does not exist
    with open(os.environ["PYICEBERG_HOME"]) as f:
        config = yaml.safe_load(f)

    warehouse = Path(config["catalog"][export_catalog_dest]["warehouse"].replace("file://", ""))
    if in_ram:
        create_tmpfs_ramdisk(warehouse)
    else:
        warehouse.mkdir(parents=True, exist_ok=True)

    glue_catalog = load_catalog("glue")
    dest_catalog = load_catalog(export_catalog_dest)
    try:
        dest_catalog.create_namespace(namespace)
    except NamespaceAlreadyExistsError as e:
        print("Cannot Export Catalog. Already exists")

        # Unmount warehouse after error
        if in_ram:
            subprocess.run(["sudo", "umount", warehouse], check=True)
            print("Warehouse tmpfs location unmounted from RAM")

        raise NamespaceAlreadyExistsError from e
    namespace_tables = glue_catalog.list_tables(namespace=namespace)

    for _, table in tqdm(namespace_tables, desc=f"Exporting {namespace} tables", total=len(namespace_tables)):
        _table = glue_catalog.load_table(f"{namespace}.{table}").scan()
        _arrow = _table.to_arrow()
        iceberg_table = dest_catalog.create_table_if_not_exists(
            f"{namespace}.{table}",
            schema=_arrow.schema,
        )
        iceberg_table.append(_arrow)
    print(f"Exported {namespace} into local pyiceberg DB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script to export the S3 tables catalog based on a namespace and snapshot id. If no snapshot, assuming the latest"
    )

    parser.add_argument(
        "-n",
        "--namespace",
        type=str,
        required=True,
        help="The namespace repo that is being exported",
    )
    parser.add_argument(
        "-c",
        "--catalog",
        type=str,
        required=True,
        help="The local catalog that is receiving the exported repo",
    )
    parser.add_argument(
        "-r",
        "--in-ram",
        action="store_true",
        help="The catalog will live inside a tmpfs mount (in RAM)",
    )

    args = parser.parse_args()

    load_creds()
    export_catalog(
        namespace=args.namespace,
        export_catalog_dest=args.catalog,
        in_ram=args.in_ram,
    )
