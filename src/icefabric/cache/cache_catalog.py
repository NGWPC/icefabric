"""Cache implementation for most commonly used domains"""

import os
from pathlib import Path

import pyarrow as pa
import yaml
from pyiceberg.catalog import load_catalog
from pyiceberg.transforms import IdentityTransform
from tqdm import tqdm

from icefabric.helpers import load_creds
from icefabric.schemas import HydrofabricSnapshot


def parse_namespaces(namespaces: set) -> set:
    """Parse optional namespace param"""
    parsed = []
    for ns in namespaces:
        if ":" in ns:
            split = ns.split(":")
            parsed.append((split[0], int(split[1])))
        else:
            parsed.append((ns, None))
    return set(parsed)


def build_cache(namespaces: set, deploy_env: str):
    """Exports the catalog to a local SQL file based on the .pyiceberg.yaml in the project root

    Parameters
    ----------
    namespaces : set
        The namespaces to be included in the cache
    """
    namespaces = parse_namespaces(namespaces)

    deploy_env = os.environ.get("ICEFABRIC_DEPLOY_ENV") or os.environ.get("ENVIRONMENT") or deploy_env
    load_creds(deploy_env.lower())

    # Creates the local dir for the warehouse if it does not exist
    with open(os.environ["PYICEBERG_HOME"]) as f:
        config = yaml.safe_load(f)

    warehouse = Path(config["catalog"]["sql"]["warehouse"].replace("file://", ""))
    warehouse.mkdir(parents=True, exist_ok=True)

    glue_catalog = load_catalog("glue")
    local_catalog = load_catalog("sql")

    for namespace, snapshot in namespaces:
        local_catalog.create_namespace_if_not_exists(namespace)

        namespace_tables = glue_catalog.list_tables(namespace=namespace)

        # Saving new snapshots for local
        snapshots = {}
        if "hf" in namespace:
            is_hf = True
            domain = namespace.split("_")[0]
            snapshots["domain"] = domain
        else:
            is_hf = False

        for _, table in tqdm(
            namespace_tables, desc=f"Exporting {namespace} tables", total=len(namespace_tables)
        ):
            _table = glue_catalog.load_table(f"{namespace}.{table}").scan(snapshot_id=snapshot)
            _arrow = _table.to_arrow()

            if local_catalog.table_exists(f"{namespace}.{table}"):
                print("Warning: overwriting existing table in local SQL catalog")
                local_catalog.drop_table(f"{namespace}.{table}")

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
            if is_hf:
                snapshots[table] = iceberg_table.current_snapshot().snapshot_id

        if is_hf:
            local_catalog.create_namespace_if_not_exists("hydrofabric_snapshots")
            if local_catalog.table_exists("hydrofabric_snapshots.id"):
                tbl = local_catalog.load_table("hydrofabric_snapshots.id")
            else:
                tbl = local_catalog.create_table(
                    "hydrofabric_snapshots.id",
                    schema=HydrofabricSnapshot.schema(),
                )
            df = pa.Table.from_pylist([snapshots], schema=HydrofabricSnapshot.arrow_schema())
            tbl.append(df)
        print(f"Exported {namespace} into local pyiceberg DB")
