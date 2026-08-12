"""Create or safely update NHF Iceberg tables for a specific namespace."""

import argparse
import json
import os
import warnings
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml  # type: ignore[import-untyped]
from pyiceberg.catalog import Catalog, load_catalog  # pyright: ignore[reportMissingImports]
from pyiceberg.schema import Schema
from pyiceberg.table import Table
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

DOMAIN_TO_NAMESPACE = {
    "conus": "conus_nhf",
    "ak": "ak_nhf",
    "hi": "hi_nhf",
    "prvi": "prvi_nhf",
}


def _init(deploy_env: str = "test") -> dict[str, str]:
    """Load credentials and resolve catalog locations."""
    load_creds(deploy_env)
    try:
        config_path = os.environ["PYICEBERG_HOME"]
        with open(config_path) as f:
            config = yaml.safe_load(f)
        warehouse_uri = config["catalog"]["sql"]["warehouse"]
        glue_region = config["catalog"]["glue"].get("region", "us-east-1")
    except (KeyError, OSError, TypeError, yaml.YAMLError) as exc:
        raise RuntimeError("Could not load the PyIceberg catalog configuration") from exc
    os.environ.setdefault("AWS_DEFAULT_REGION", glue_region)
    os.environ.setdefault("AWS_REGION", glue_region)
    warehouse = Path(warehouse_uri.replace("file://", ""))
    warehouse.mkdir(parents=True, exist_ok=True)
    s3_bucket = S3_BUCKETS.get(deploy_env, S3_BUCKETS["test"])
    return {
        "glue": f"s3://{s3_bucket}/icefabric_catalog",
        "sql": config["catalog"]["sql"]["warehouse"],
    }


def _table_state(table: Table) -> dict[str, str | int | None]:
    """Record the metadata pointer and snapshot needed for a full rollback."""
    current_snapshot = table.current_snapshot()
    return {
        "metadata_location": table.metadata_location,
        "current_snapshot_id": current_snapshot.snapshot_id if current_snapshot else None,
    }


def write_backup_manifest(
    catalog: Catalog,
    namespace: str,
    output_path: Path,
    *,
    release_tag: str,
    file_dir: Path,
) -> None:
    """Write all existing namespace metadata before any catalog mutation."""
    identifiers = sorted(catalog.list_tables(namespace)) if catalog.namespace_exists(namespace) else []
    snapshot_identifier = (f"{namespace}_snapshots", "id")
    if catalog.table_exists(snapshot_identifier):
        identifiers.append(snapshot_identifier)

    manifest = {
        "captured_at": datetime.now(UTC).isoformat(),
        "catalog": catalog.name,
        "namespace": namespace,
        "release_tag": release_tag,
        "parquet_directory": str(file_dir.resolve()),
        "tables": {
            ".".join(identifier): _table_state(catalog.load_table(identifier)) for identifier in identifiers
        },
        "rollback_note": (
            "Data snapshots can be restored with tools/iceberg/set_snapshot.py. "
            "If an incompatible schema change must also be reverted, restore the table registration "
            "to the recorded metadata_location; setting a snapshot alone does not restore a schema."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Pre-update catalog manifest written to {output_path}")


def _tag_snapshot(table: Table, tag: str) -> None:
    """Protect the current snapshot with a uniquely named rollback tag."""
    snapshot = table.current_snapshot()
    if snapshot is None:
        return
    existing = table.refs().get(tag)
    if existing is not None:
        if existing.snapshot_id != snapshot.snapshot_id:
            raise ValueError(
                f"Tag {tag!r} already points to {existing.snapshot_id} on {'.'.join(table.name())}, "
                f"not current snapshot {snapshot.snapshot_id}"
            )
        return
    table.manage_snapshots().create_tag(snapshot.snapshot_id, tag).commit()


def _schema_changes(current: Schema, desired: Schema) -> dict[str, list[str]]:
    """Return a concise, printable top-level schema diff."""
    current_fields = {field.name: field for field in current.fields}
    desired_fields = {field.name: field for field in desired.fields}
    return {
        "add": [name for name in desired_fields if name not in current_fields],
        "drop": [name for name in current_fields if name not in desired_fields],
        "type": [
            f"{name}: {current_fields[name].field_type} -> {field.field_type}"
            for name, field in desired_fields.items()
            if name in current_fields and current_fields[name].field_type != field.field_type
        ],
        "required": [
            f"{name}: {current_fields[name].required} -> {field.required}"
            for name, field in desired_fields.items()
            if name in current_fields and current_fields[name].required != field.required
        ],
    }


def _print_schema_changes(identifier: str, changes: dict[str, list[str]]) -> None:
    if not any(changes.values()):
        print(f"  Schema already matches {identifier}")
        return
    print(f"  Schema changes for {identifier}:")
    for change_type, values in changes.items():
        if values:
            print(f"    {change_type}: {', '.join(values)}")


def _sync_schema(table: Table, desired: Schema) -> None:
    """Make top-level columns, types, nullability, and order match ``desired``."""
    current_fields = {field.name: field for field in table.schema().fields}
    desired_fields = {field.name: field for field in desired.fields}
    changes = _schema_changes(table.schema(), desired)
    if not any(changes.values()) and [field.name for field in table.schema().fields] == [
        field.name for field in desired.fields
    ]:
        return

    # Some NHF source changes (for example lakes.lake_id long -> string) are
    # intentionally incompatible. The pre-update metadata manifest and tags
    # provide the complete rollback path for these changes.
    with table.update_schema(allow_incompatible_changes=True) as update:
        for name in changes["drop"]:
            update.delete_column(name)
        for name in changes["add"]:
            field = desired_fields[name]
            update.add_column(name, field.field_type, doc=field.doc, required=field.required)
        for name, desired_field in desired_fields.items():
            current_field = current_fields.get(name)
            if current_field is None:
                continue
            field_type = (
                desired_field.field_type if current_field.field_type != desired_field.field_type else None
            )
            required = desired_field.required if current_field.required != desired_field.required else None
            if field_type is not None or required is not None:
                update.update_column(name, field_type=field_type, required=required)

        desired_names = [field.name for field in desired.fields]
        if desired_names:
            update.move_first(desired_names[0])
            for previous, name in zip(desired_names, desired_names[1:], strict=False):
                update.move_after(name, previous)


def _preflight_parquet_files(file_dir: Path, require_all: bool) -> dict[str, Path]:
    """Validate the available Parquet files before changing any table."""
    available: dict[str, Path] = {}
    errors: list[str] = []
    for layer, schema_class in nhf_layers.items():
        path = file_dir / f"{layer}.parquet"
        if not path.exists():
            if require_all:
                errors.append(f"missing {path}")
            continue
        actual_schema = pq.read_schema(path)
        desired_schema = schema_class.arrow_schema()
        if actual_schema != desired_schema:
            errors.append(
                f"schema mismatch for {path}:\n  actual: {actual_schema}\n  expected: {desired_schema}"
            )
            continue
        available[layer] = path
    if errors:
        raise ValueError("Parquet preflight failed:\n" + "\n".join(errors))
    return available


def build_nhf(
    catalog_type: str,
    file_dir: str | Path,
    domain: str = "conus",
    overwrite_existing: bool = False,
    deploy_env: str = "test",
    *,
    namespace_override: str | None = None,
    require_all: bool = False,
    dry_run: bool = False,
    release_tag: str | None = None,
    backup_manifest: Path | None = None,
) -> None:
    """Create or update NHF tables without purging existing table history."""
    location = _init(deploy_env)
    catalog = load_catalog(catalog_type)
    namespace = namespace_override or DOMAIN_TO_NAMESPACE[domain]
    file_dir = Path(file_dir)
    available = _preflight_parquet_files(file_dir, require_all=require_all)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    release_tag = release_tag or f"nhf_update_{timestamp}"
    rollback_tag = f"pre_{release_tag}"
    backup_manifest = backup_manifest or Path.cwd() / f"{namespace}_{rollback_tag}.json"
    write_backup_manifest(
        catalog,
        namespace,
        backup_manifest,
        release_tag=release_tag,
        file_dir=file_dir,
    )

    if not catalog.namespace_exists(namespace):
        print(f"Namespace {namespace} will be created")
        if not dry_run:
            catalog.create_namespace(namespace)

    snapshots: dict[str, int | None] = {}
    changed = False
    for layer, schema_class in nhf_layers.items():
        path = available.get(layer)
        if path is None:
            print(f"Skipping {layer}: no Parquet file")
            continue

        identifier = f"{namespace}.{layer}"
        desired_schema = schema_class.schema()
        exists = catalog.table_exists(identifier)
        if exists:
            iceberg_table = catalog.load_table(identifier)
            current_snapshot = iceberg_table.current_snapshot()
            changes = _schema_changes(iceberg_table.schema(), desired_schema)
            _print_schema_changes(identifier, changes)
            if current_snapshot is not None and not overwrite_existing:
                print(f"Skipping populated table {identifier}; pass --overwrite to update it")
                snapshots[layer] = current_snapshot.snapshot_id
                continue
            print(f"{'Would overwrite' if dry_run else 'Overwriting'} {identifier}")
            if dry_run:
                continue
            if current_snapshot is not None:
                _tag_snapshot(iceberg_table, rollback_tag)
            _sync_schema(iceberg_table, desired_schema)
            arrow_table = pq.read_table(path, schema=schema_class.arrow_schema())
            iceberg_table.overwrite(
                arrow_table,
                snapshot_properties={"icefabric.release": release_tag},
            )
        else:
            print(f"{'Would create' if dry_run else 'Creating'} {identifier}")
            if dry_run:
                continue
            iceberg_table = catalog.create_table(
                identifier,
                schema=desired_schema,
                location=f"{location[catalog_type]}/{namespace.lower()}/{layer}",
            )
            if not iceberg_table.spec().fields:
                try:
                    desired_schema.find_field("vpu_id")
                except ValueError:
                    pass
                else:
                    with iceberg_table.update_spec() as update:
                        update.add_field("vpu_id", IdentityTransform(), "vpu_id_partition")
            arrow_table = pq.read_table(path, schema=schema_class.arrow_schema())
            iceberg_table.overwrite(
                arrow_table,
                snapshot_properties={"icefabric.release": release_tag},
            )

        current_snapshot = iceberg_table.current_snapshot()
        if current_snapshot is None:
            raise RuntimeError(f"No snapshot was created for {identifier}")
        snapshots[layer] = current_snapshot.snapshot_id
        changed = True
        print(f"  Current snapshot: {current_snapshot.snapshot_id}")

    if dry_run:
        print("Dry run complete; no catalog or S3 changes were made")
        return
    if not changed:
        print("No tables changed")
        return

    snapshot_namespace = f"{namespace}_snapshots"
    snapshot_identifier = f"{snapshot_namespace}.id"
    catalog.create_namespace_if_not_exists(snapshot_namespace)
    if catalog.table_exists(snapshot_identifier):
        snapshot_table = catalog.load_table(snapshot_identifier)
        _tag_snapshot(snapshot_table, rollback_tag)
        with snapshot_table.update_schema() as update:
            update.union_by_name(NHFSnapshot.arrow_schema())
    else:
        snapshot_table = catalog.create_table(
            snapshot_identifier,
            schema=NHFSnapshot.schema(),
            location=f"{location[catalog_type]}/{snapshot_namespace}",
        )

    snapshot_row = pa.Table.from_pylist([snapshots], schema=NHFSnapshot.arrow_schema())
    snapshot_table.append(snapshot_row, snapshot_properties={"icefabric.release": release_tag})
    new_snapshot = snapshot_table.current_snapshot()
    if new_snapshot is None:
        raise RuntimeError(f"No snapshot was created for {snapshot_identifier}")
    if release_tag not in snapshot_table.refs():
        snapshot_table.manage_snapshots().create_tag(new_snapshot.snapshot_id, release_tag).commit()

    print(f"Build complete. Files written into {catalog.name} @ {namespace}")
    print(f"Snapshots written to {snapshot_identifier}")
    print(f"Rollback tag on pre-update snapshots: {rollback_tag}")
    print(f"Rollback manifest: {backup_manifest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or safely update an NHF PyIceberg catalog")
    parser.add_argument(
        "--catalog",
        choices=["sql", "glue"],
        default="sql",
        help="Catalog type (default: sql)",
    )
    parser.add_argument(
        "--files",
        type=Path,
        required=True,
        help="Directory containing NHF Parquet files",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite populated tables while retaining prior snapshots and rollback tags",
    )
    parser.add_argument(
        "--domain",
        default="conus",
        choices=["conus", "ak", "hi", "prvi"],
        help="NHF domain used to derive the namespace",
    )
    parser.add_argument(
        "--namespace",
        choices=["nhf", "conus_nhf", "ak_nhf", "hi_nhf", "prvi_nhf"],
        help="Explicit namespace override (use nhf to update the legacy CONUS namespace)",
    )
    parser.add_argument(
        "--deploy-env",
        default="test",
        choices=["test", "prod"],
        help="Credential and S3 environment (default: test)",
    )
    parser.add_argument(
        "--release-tag",
        help="Unique release label used for snapshot tags (for example nhf_1_2_2)",
    )
    parser.add_argument(
        "--backup-manifest",
        type=Path,
        help="Path for the pre-update catalog/snapshot manifest",
    )
    parser.add_argument(
        "--require-all",
        action="store_true",
        help="Fail preflight unless every supported NHF layer has a Parquet file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate files and print catalog changes without modifying Glue or S3",
    )

    args = parser.parse_args()
    build_nhf(
        catalog_type=args.catalog,
        file_dir=args.files,
        domain=args.domain,
        overwrite_existing=args.overwrite,
        deploy_env=args.deploy_env,
        namespace_override=args.namespace,
        require_all=args.require_all,
        dry_run=args.dry_run,
        release_tag=args.release_tag,
        backup_manifest=args.backup_manifest,
    )
