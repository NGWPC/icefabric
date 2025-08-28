import icechunk
import xarray as xr
from dotenv import load_dotenv
from icechunk.xarray import to_icechunk

load_dotenv()

bucket = "edfs-data"
prefix = "streamflow_observations/usgs_observations"
storage_config = icechunk.s3_storage(bucket=bucket, prefix=prefix, region="us-east-1", from_env=True)
try:
    repo = icechunk.Repository.create(storage_config)
    session = repo.writable_session("main")
    ds = xr.open_zarr("usgs.zarr")
    to_icechunk(ds, session)
    snapshot = session.commit("Uploaded all USGS gages to the store")
    print(f"All data is uploaded. Commit: {snapshot}")
except icechunk.IcechunkError as e:
    if "repositories can only be created in clean prefixes" in e.message:
        print("usgs_observations icechunk store already exists. Pulling it down now...")
        repo = icechunk.Repository.open(storage_config)
        session = repo.writable_session("main")
        ds = xr.open_zarr(session.store, consolidated=False)
        print(ds)
    else:
        print(f"Unexpected Icechunk error: {e}")
