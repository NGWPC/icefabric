"""Clone ALL icechunk streamflow snapshots to local filesystem."""

from pathlib import Path

import icechunk
import xarray as xr

# Remote source
BUCKET = "edfs-data"
PREFIX = "streamflow_observations/hourly_streamflow_observations"

# Local target
LOCAL_DIR = Path("/tmp/icefabric_streamflow_obs")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

print(f"Remote: s3://{BUCKET}/{PREFIX}")
print(f"Local:  {LOCAL_DIR}")

# Open remote repo
print("\nOpening remote icechunk repo...")
remote_store = icechunk.s3_storage(bucket=BUCKET, prefix=PREFIX, region="us-east-1", from_env=True)
remote_repo = icechunk.Repository.open(remote_store)

# Get all snapshots in history
ancestry = list(remote_repo.ancestry(branch="main"))
print(f"Found {len(ancestry)} snapshots in history")

# Remove existing local repo if it exists
if LOCAL_DIR.exists():
    import shutil

    shutil.rmtree(LOCAL_DIR, ignore_errors=True)
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)

# Create fresh local repo
print("Creating local icechunk repo...")
local_store = icechunk.local_filesystem_storage(str(LOCAL_DIR))
local_repo = icechunk.Repository.create(local_store)

# Process each snapshot from oldest to newest
print("\nCloning snapshots (oldest to newest)...")
for i, snap_info in enumerate(reversed(ancestry)):
    snap_id = snap_info.id
    message = snap_info.message
    print(f"\n  [{i + 1}/{len(ancestry)}] Snapshot {snap_id}")
    print(f"    Message: {message}")

    # Open readonly session for this snapshot on remote
    try:
        remote_session = remote_repo.readonly_session(snapshot_id=snap_id)
        ds = xr.open_zarr(remote_session.store, consolidated=False)
        print(f"    Data: {dict(ds.sizes)}")

        # Write to local repo
        if i == 0:
            # First snapshot - create branch
            local_repo.create_branch("main", snap_id)

        local_session = local_repo.writable_session("main")
        ds.to_zarr(local_session.store, consolidated=False)
        local_session.commit(f"Clone: {message}")
        print("    Cloned successfully")
    except Exception as e:  # noqa: BLE001 - broad catch intentional: gracefully skip any failed snapshot
        print(f"    ERROR: {e}")
        continue

print(f"\nDone! Local icechunk repo at: {LOCAL_DIR}")
