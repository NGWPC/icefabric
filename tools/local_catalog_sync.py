import glob
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import boto3
import fastavro
from botocore.exceptions import ClientError
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NamespaceAlreadyExistsError, NoSuchTableError, TableAlreadyExistsError


def download_s3(s3_uris: list[str], local_path: str) -> None:
    """Download files from s3.

    Parameters
    ----------
    s3_uris : list[str]
        A list of strings containing the s3 URI for each file
    local_path : str
        Local directory the files will be saved
    """
    s3 = boto3.client("s3")

    # loop through URIs
    for s3_uri in s3_uris:
        # get bucket, s3 object, and filename from URI
        parsed = urlparse(s3_uri)
        bucket = parsed.netloc
        object_key = parsed.path.lstrip("/")
        file_name = os.path.basename(parsed.path)

        # if the parquet file is partioned, get the VPU ID and
        # add the partition subdirectory
        if "vpu_id_partition" in object_key:
            match = re.search(r"\b(0[1-9]|1[0-9]|2[0-1])([NSWLU])?\b", object_key)
            if match:
                vpuid = match.group(1) + (match.group(2) or "")
                partition_str = f"vpu_id_partition={vpuid}"
                Path(os.path.join(local_path, partition_str)).mkdir(parents=True, exist_ok=True)
                full_local_path = os.path.join(local_path, partition_str, file_name)
        else:
            full_local_path = os.path.join(local_path, file_name)

        # download from s3 to local directory

        try:
            s3.download_file(Bucket=bucket, Key=object_key, Filename=full_local_path)
            print(f"Successfully downloaded {s3_uri} to {full_local_path}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            error_message = e.response.get("Error", {}).get("Message")

            if error_code == "404" or error_code == "NoSuchKey":
                print(f"Error: The file '{object_key}' does not exist.")
            else:
                print(f"AWS Error [{error_code}]: {error_message}")


def rewrite_metadata_paths(metadata_json_path: str, old_s3_prefix: str, new_local_prefix: str) -> None:
    """Replaces s3 URIs with local file paths in metadata JSON.

    Parameters
    ----------
    metadata_json_path : str
        Path and filename for local JSON file
    old_s3_prefix : str
        s3 prefix to be replaced
    new_local_prefix : str
        new local prefex
    """
    with open(metadata_json_path) as f:
        meta = json.load(f)

    # Serialize to string to do a global find-and-replace for paths
    meta_str = json.dumps(meta)
    meta_str = meta_str.replace(old_s3_prefix, new_local_prefix)

    # Save the mutated metadata back
    with open(metadata_json_path, "w") as f:
        f.write(meta_str)


def rewrite_avro_manifest(local_avro_path, s3_table_root, local_table_root):
    """Rewrite file paths inside manifest/manifest-list Avro files from S3 to local."""
    records = []
    with open(local_avro_path, "rb") as f:
        reader = fastavro.reader(f)
        schema = reader.writer_schema
        for record in reader:
            # Manifest list points to manifest files
            if "manifest_path" in record:
                if isinstance(record["manifest_path"], str) and record["manifest_path"].startswith("s3://"):
                    record["manifest_path"] = record["manifest_path"].replace(s3_table_root, local_table_root)
                    # record['manifest_path'] = s3_to_local(record['manifest_path'], s3_table_root, local_table_root)
            # Manifest file points to data/delete files
            if "data_file" in record and "file_path" in record["data_file"]:
                fp = record["data_file"]["file_path"]
                if fp.startswith("s3://"):
                    record["data_file"]["file_path"] = record["data_file"]["file_path"].replace(
                        s3_table_root, local_table_root
                    )
            records.append(record)

    # Write updated records back to the avro file
    with open(local_avro_path, "wb") as out:
        fastavro.writer(out, schema, records)
    print(f"Rewrote Avro paths in: {local_avro_path}")


# set local paths and create directories
local_catalog_root = "/var/tmp/icefabric_local_catalog"
warehouse_path = os.path.join(local_catalog_root, "warehouse")
Path(local_catalog_root).mkdir(parents=True, exist_ok=True)
Path(warehouse_path).mkdir(parents=True, exist_ok=True)

# load s3 catalog
try:
    glue_catalog = load_catalog("glue")
except ValueError as e:
    print(f"Error opening glue catalog:  {e}")
    raise

# load a new local sql catalog
try:
    sql_catalog = load_catalog("sql")
except ValueError as e:
    print(f"Error opening sql catalog:  {e}")
    raise

# get list of namespaces in catalog to process
namespaces = glue_catalog.list_namespaces()
if not namespaces:
    raise ValueError("no namespaces found in glue catalog")

for namespace in namespaces:
    namespace = namespace[0] if isinstance(namespace, tuple) else namespace

    print(f"Processing namespace: {namespace}\n")

    local_namespace_path = os.path.join(warehouse_path, namespace)
    Path(local_namespace_path=os.path.join(warehouse_path, namespace)).mkdir(parents=True, exist_ok=True)

    try:
        sql_catalog.create_namespace(namespace)
    except NamespaceAlreadyExistsError:
        pass  # Skip if already exists

    tables = glue_catalog.list_tables(namespace)
    if not tables:
        print(f"no tables found in namespace {namespace} in glue catalog")
        continue

    for table in tables:
        table_name = table[1]

        print(f"Processing table {namespace}.{table_name}")

        # load current namespace.table from the glue catalog
        try:
            glue_table = glue_catalog.load_table(f"{namespace}.{table_name}")
        except NoSuchTableError:
            print(f"Error loading table {table_name}")
            continue

        # define local paths for this table's metadata and data directories
        table_metadata_path = os.path.join(local_namespace_path, table_name, "metadata")
        table_data_path = os.path.join(local_namespace_path, table_name, "data")

        # create directories
        Path(table_metadata_path).mkdir(parents=True, exist_ok=True)
        Path(table_data_path).mkdir(parents=True, exist_ok=True)

        # get a list of snapshots for this table
        snapshots = glue_table.snapshots()

        if not snapshots:
            print(f"no snapshots found for {table_name}")
            continue

        # get s3 uri for this table's metadata JSON and download
        jsonfile = glue_table.metadata_location
        print("downloading metadata JSON file\n")
        download_s3([jsonfile], table_metadata_path)

        # loop through each snapshot
        for index, snapshot in enumerate(snapshots):
            print(f"processing snapshot {index} of {len(snapshots)}, snapshot id: {snapshot.snapshot_id}\n")

            # get the s3 uri for the snapshot's manifest list avro file
            manifest_list_file = snapshot.manifest_list

            # get the s3 uris for each manifest avro file
            manifests = snapshot.manifests(glue_table.io)

            if not manifests:
                print(f"no manifests found for snapshot id: {snapshot.snapshot_id}, skipping")
                continue

            manifest_paths = [manifest.manifest_path for manifest in manifests]

            # get all manifest entries
            entries = manifests[0].fetch_manifest_entry(glue_table.io)
            if not entries:
                print("no manifest entries found for ")

            # create empty list for storing parquet file URIs
            parquetfiles = []

            # loop through each entry and get the parquet file S3 URIs
            for entry in entries:
                parquetfiles.append(entry.data_file.file_path)

            # download all files for this snapshot from s3

            print("downloading manifest list avro file\n")
            download_s3([manifest_list_file], table_metadata_path)

            print("downloading manifest avro files\n")
            download_s3(manifest_paths, table_metadata_path)

            print("downloading data parquet filesfiles\n")
            download_s3(parquetfiles, table_data_path)

        # replace s3 paths with local file paths in metadata JSON
        parsed = urlparse(jsonfile)
        json_file_name = os.path.basename(parsed.path)
        json_full_local_path = os.path.join(table_metadata_path, json_file_name)
        rewrite_metadata_paths(
            json_full_local_path, "s3://edfs-data/icefabric_catalog", f"file://{warehouse_path}"
        )

        avrofiles = glob.glob(os.path.join(table_metadata_path, "*.avro"))
        for file in avrofiles:
            rewrite_avro_manifest(file, "s3://edfs-data/icefabric_catalog", f"file://{warehouse_path}")

        # register new table with this snapshot's metadata
        try:
            sql_catalog.register_table(
                identifier=f"{namespace}.{table_name}",
                metadata_location=json_full_local_path,
            )
        except TableAlreadyExistsError:
            print(f"table {table_name} already exists")
