"""A file to export the glue catalog to sqllite"""

import argparse
import os
from pathlib import Path

import yaml
from pyiceberg.catalog import load_catalog
from pyiceberg.transforms import IdentityTransform
from tqdm import tqdm

from icefabric.helpers import load_creds

load_creds(dir=Path.cwd())


def export(namespace: str, snapshot: int | None = None):
    """Exports the catalog to a local SQL file based on the .pyiceberg.yaml in the project root

    Parameters
    ----------
    namespace : str
        The namespace to be exported
    snapshot : str | None, optional
        The snapshot ID to export from, by default None and using the latest
    """
    # Creates the local dir for the warehouse if it does not exist
    with open(os.environ["PYICEBERG_HOME"]) as f:
        config = yaml.safe_load(f)

    warehouse = Path(config["catalog"]["sql"]["warehouse"].replace("file://", ""))
    warehouse.mkdir(parents=True, exist_ok=True)

    glue_catalog = load_catalog("glue")
    local_catalog = load_catalog("sql")
    local_catalog.create_namespace_if_not_exists(namespace)
    namespace_tables = glue_catalog.list_tables(namespace=namespace)
    for _, table in tqdm(namespace_tables, desc=f"Exporting {namespace} tables", total=len(namespace_tables)):
        _table = glue_catalog.load_table(f"{namespace}.{table}").scan(snapshot_id=snapshot)
        _arrow = _table.to_arrow()
        iceberg_table = local_catalog.create_table_if_not_exists(
            f"{namespace}.{table}",
            schema=_arrow.schema,
        )
        if namespace == "conus_hf":
            # Partitioning the CONUS HF data
            partition_spec = iceberg_table.spec()
            if len(partition_spec.fields) == 0:
                with iceberg_table.update_spec() as update:
                    update.add_field("vpuid", IdentityTransform(), "vpuid_partition")
        iceberg_table.append(_arrow)
    print(f"Exported {namespace} into local pyiceberg DB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A script to export the S3 tables catalog based on a namespace and snapshot id. If no snapshot, assuming the latest"
    )

    parser.add_argument("--namespace", help="The namespace repo that is being exported")
    parser.add_argument("--snapshot", help="The snapshot ID for the namespace")

    args = parser.parse_args()
    export(namespace=args.namespace, snapshot=args.snapshot)
