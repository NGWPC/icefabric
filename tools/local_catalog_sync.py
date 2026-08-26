"""Sync all Glue catalog namespaces/snapshots to a local SQLite + Parquet catalog."""

import io
import json
import os
import sys
from pathlib import Path

import boto3
import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv
from fastavro import reader as avro_reader

# Set up local catalog config BEFORE importing pyiceberg
LOCAL_BASE = Path("/tmp/icefabric_local_catalog")
LOCAL_BASE.mkdir(parents=True, exist_ok=True)
LOCAL_CATALOG_YAML = LOCAL_BASE / ".pyiceberg.yaml"


LOCAL_CATALOG_YAML.write_text(
    yaml.dump(
        {
            "catalog": {
                "local": {
                    "type": "sql",
                    "uri": f"sqlite:///{LOCAL_BASE}/pyiceberg_catalog.db",
                    "warehouse": str(LOCAL_BASE / "warehouse"),
                }
            }
        }
    )
)
os.environ["PYICEBERG_HOME"] = str(LOCAL_BASE)  # Must be directory, not file

from pyiceberg.catalog import load_catalog  # noqa: E402

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)
os.environ.pop("AWS_PROFILE", None)

BUCKET = "edfs-data"
CATALOG_PREFIX = "icefabric_catalog/"

s3 = boto3.client("s3", region_name="us-east-1")
glue = boto3.client("glue", region_name="us-east-1")


def extract_latest_meta_key(location: str) -> str | None:
    """Find the latest metadata.json key for a given table location on S3."""
    base = location.replace(f"s3://{BUCKET}/", "").rstrip("/")
    paginator = s3.get_paginator("list_objects_v2")
    latest_meta = None
    latest_num = -1
    try:
        for page in paginator.paginate(Bucket=BUCKET, Prefix=f"{base}/metadata/"):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".metadata.json"):
                    fname = key.split("/")[-1]
                    try:
                        num = int(fname.split("-")[0])
                    except ValueError:
                        num = 0
                    if num > latest_num:
                        latest_num = num
                        latest_meta = key
    except (ClientError, NoCredentialsError):
        pass
    return latest_meta


def read_metadata(meta_key: str) -> dict | None:
    """Read and parse a metadata.json file from S3."""
    try:
        meta_obj = s3.get_object(Bucket=BUCKET, Key=meta_key)
        return json.loads(meta_obj["Body"].read())
    except (ClientError, json.JSONDecodeError) as e:
        print(f"  WARN: Could not read {meta_key}: {e}", file=sys.stderr)
        return None


def get_snapshot_manifest_entries(meta: dict, snapshot_id: int) -> list[dict]:
    """Get all manifest entries for a specific snapshot."""
    ml_key = None
    for snap in meta.get("snapshots", []):
        if snap["snapshot-id"] == snapshot_id:
            ml_key = snap["manifest-list"].replace(f"s3://{BUCKET}/", "")
            break
    if not ml_key:
        return []

    entries = []
    ml_obj = s3.get_object(Bucket=BUCKET, Key=ml_key)
    manifests = list(avro_reader(io.BytesIO(ml_obj["Body"].read())))
    for m in manifests:
        man_path = m["manifest_path"].replace(f"s3://{BUCKET}/", "")
        man_obj = s3.get_object(Bucket=BUCKET, Key=man_path)
        man_entries = list(avro_reader(io.BytesIO(man_obj["Body"].read())))
        for entry in man_entries:
            if entry["status"] != 2:  # not deleted
                entries.append(entry)
    return entries


def download_parquet_from_s3(s3_path: str) -> pa.Table:
    """Download a Parquet file from S3 and return as PyArrow Table."""
    key = s3_path.replace(f"s3://{BUCKET}/", "")
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    data = obj["Body"].read()
    return pq.read_table(io.BytesIO(data))


def get_glue_table_schema(table_info: dict) -> pa.Schema:
    """Extract PyArrow schema from Glue table storage descriptor."""
    # We'll infer from the actual Parquet files instead
    return None


def main() -> None:
    """Sync all Glue catalog namespaces/snapshots to a local SQLite + Parquet catalog."""
    local_catalog = load_catalog("sql")
    databases = glue.get_databases()["DatabaseList"]
    databases.sort(key=lambda d: d["Name"])

    for db in databases:
        db_name = db["Name"]
        print(f"\n{'=' * 60}")
        print(f"Namespace: {db_name}")
        print(f"{'=' * 60}")

        tables_resp = glue.get_tables(DatabaseName=db_name)
        table_list = tables_resp.get("TableList", [])

        for t in sorted(table_list, key=lambda x: x["Name"]):
            table_name = t["Name"]
            loc = t.get("StorageDescriptor", {}).get("Location", "").rstrip("/")
            if not loc:
                print(f"  {table_name}: no location, skipping")
                continue

            print(f"\n  Table: {table_name}")

            # Use metadata_location from Glue table params (avoids dedup issues when tables share Location)
            params = t.get("Parameters", {})
            meta_loc = params.get("metadata_location", "")
            if meta_loc:
                meta_key = meta_loc.replace(f"s3://{BUCKET}/", "")
            else:
                meta_key = extract_latest_meta_key(loc)

            if not meta_key:
                print("    No metadata found, skipping")
                continue

            meta = read_metadata(meta_key)
            if not meta:
                continue

            snapshots = meta.get("snapshots", [])
            current_snap_id = meta.get("current-snapshot-id")
            print(f"    Snapshots: {len(snapshots)}")

            # Find the most recent total delete - only sync snapshots after it
            last_delete_idx = -1
            for i, snap in enumerate(snapshots):
                if snap.get("summary", {}).get("operation") == "delete":
                    try:
                        deleted_files = int(snap.get("summary", {}).get("deleted-data-files", 0))
                        total_files = int(snap.get("summary", {}).get("total-data-files", 0))
                    except (ValueError, TypeError):
                        continue
                    # Total delete = deleted all files and total is now 0
                    if deleted_files > 0 and total_files == 0:
                        last_delete_idx = i

            if last_delete_idx >= 0:
                print(f"    Last total delete at snapshot {last_delete_idx + 1}, syncing after it")
                snapshots_to_process = snapshots[last_delete_idx + 1 :]
                offset = last_delete_idx + 1
            else:
                print("    No total delete found, syncing all snapshots")
                snapshots_to_process = snapshots
                offset = 0

            # Create local table namespace
            full_table_name = f"{db_name}.{table_name}"

            # Process each snapshot in chronological order
            for i, snap in enumerate(snapshots_to_process):
                snap_id = snap["snapshot-id"]
                operation = snap.get("summary", {}).get("operation", "append")
                is_current = snap_id == current_snap_id

                print(
                    f"    Snapshot {offset + i + 1}/{len(snapshots)} (id={snap_id}, op={operation}){'*' if is_current else ''}",
                    end="",
                    flush=True,
                )

                if operation == "delete":
                    print(" (skipping delete)")
                    continue

                # Get manifest entries for this snapshot
                entries = get_snapshot_manifest_entries(meta, snap_id)
                if not entries:
                    print(" (no entries)")
                    continue

                print(f" ({len(entries)} files)", end="", flush=True)

                # Download all Parquet files and combine
                tables = []
                for entry in entries:
                    s3_path = entry["data_file"]["file_path"]
                    try:
                        arrow_table = download_parquet_from_s3(s3_path)
                        tables.append(arrow_table)
                    except (ClientError, OSError, pa.ArrowException) as e:
                        print(f"\n      WARN: Could not download {s3_path}: {e}", file=sys.stderr)
                        continue

                if not tables:
                    print(" (no data)")
                    continue

                combined = pa.concat_tables(tables)

                # Create or append to local table
                try:
                    if not local_catalog.table_exists(full_table_name):
                        local_catalog.create_namespace_if_not_exists(db_name)
                        local_table = local_catalog.create_table(
                            full_table_name,
                            schema=combined.schema,
                        )
                        local_table.append(combined)
                        print(f" created ({combined.num_rows} rows)")
                    else:
                        local_table = local_catalog.load_table(full_table_name)
                        local_table.append(combined)
                        print(f" appended ({combined.num_rows} rows)")
                except (ClientError, OSError, pa.ArrowException) as e:
                    print(f"\n      ERROR: {e}", file=sys.stderr)
                    continue

    print(f"\n{'=' * 60}")
    print(f"Local catalog created at: {LOCAL_BASE}")
    print(f"SQLite DB: {LOCAL_BASE}/pyiceberg_catalog.db")
    print(f"Data: {LOCAL_BASE}/warehouse/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
