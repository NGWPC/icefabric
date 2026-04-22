import argparse
import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
import uvicorn
from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NoSuchTableError
from pyprojroot import here

from app import GpkgCache, GpkgLimiter, StreamflowData
from app.routers.hydrofabric.router import api_router as hydrofabric_api_router
from app.routers.nwm_modules.router import (
    cfe_router,
    lasam_router,
    lstm_router,
    noahowp_router,
    parameter_metadata_router,
    sacsma_router,
    sft_router,
    smp_router,
    snow17_router,
    topmodel_router,
    topoflow_router,
    troute_router,
    ueb_router,
)
from app.routers.ras_xs.router import api_router as ras_api_router
from app.routers.rise_wrappers.router import api_router as rise_api_wrap_router
from app.routers.streamflow_observations.router import api_router as streamflow_api_router
from icefabric.builds import load_upstream_json
from icefabric.cache import build_cache
from icefabric.helpers import load_creds

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(asctime)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create a logger instance
main_logger = logging.getLogger(__name__)

tags_metadata = [
    {
        "name": "Streamflow Observations",
        "description": "Data querying functions for observational streamflow time series (USGS, local agencies, etc.)",
    },
    {
        "name": "Hydrofabric Services",
        "description": "Data Querying functions for the Hydrofabric",
    },
    {
        "name": "NWM Modules",
        "description": "Functions that interact with NWM modules. Mainly supports IPE generation.",
    },
    {
        "name": "HEC-RAS XS",
        "description": "Data querying functions for HEC-RAS cross-sectional data (i.e. per flowpath ID or geospatial queries)",
    },
    {
        "name": "RISE",
        "description": "An interface to the RISE API for querying reservoir outflow data",
        "externalDocs": {"description": "Link to the RISE API", "url": "https://data.usbr.gov/rise-api"},
    },
]

parser = argparse.ArgumentParser(description="The FastAPI App instance for querying versioned EDFS data")

# Glue = S3 Tables; Sql is a local iceberg catalog
parser.add_argument(
    "--catalog",
    choices=["glue", "sql"],
    help="The catalog information for querying versioned EDFS data",
    default="glue",
)  # Setting the default to read from S3
parser.add_argument(
    "--cache-catalog",
    choices=["glue", "sql"],
    help="Optional local catalog to use for most common requests",
    default="sql",
)  # Setting the default to use local SQL cache
parser.add_argument(
    "--cached-namespaces",
    nargs="+",
    help="List of namespaces to include in local cache. Optionally specified as <namespace>:<snapshot>",
    default=[
        "conus_nhf",
        "conus_hf",
        "prvi_hf",
        "hi_hf",
        "ak_hf",
        "parameter_metadata",
        "divide_parameters",
    ],
)
parser.add_argument(
    "--deploy-env",
    choices=["t", "test", "p", "prod", "production"],
    help="The glue deploy environment",
    default="test",
)
args, _ = parser.parse_known_args()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads the iceberg catalog location from an environment variable

    Parameters
    ----------
    app: FastAPI
        The FastAPI app instance
    """
    app.state.main_logger = main_logger
    app.state.main_logger.info("Application starting up.")
    # Cap per-worker sync-handler concurrency. Hydrofabric/ras_xs/nwm handlers
    # can spike to hundreds of MB of pandas/geopandas memory per in-flight
    # request, so on a t3.large (8 GB / 2 workers) we keep this low to avoid
    # OOM. Effective per-instance concurrency = workers * total_tokens.
    thread_limiter = anyio.to_thread.current_default_thread_limiter()
    thread_limiter.total_tokens = 20
    app.state.main_logger.info(f"AnyIO threadpool limit set to {thread_limiter.total_tokens}")
    deploy_env = os.environ.get("ICEFABRIC_DEPLOY_ENV") or os.environ.get("ENVIRONMENT") or args.deploy_env
    deploy_env = deploy_env.lower()
    load_creds(deploy_env)
    if args.cache_catalog == "sql" and not os.environ.get("ICEFABRIC_CACHE_BUILT"):
        app.state.main_logger.info("Building local SQL cache...")
        build_cache(set(args.cached_namespaces), deploy_env)
    else:
        app.state.main_logger.info(
            "Skipping local SQL cache build (already built by parent process or disabled)."
        )
    catalog = load_catalog(args.catalog)
    cache_catalog = load_catalog(args.cache_catalog)
    hydrofabric_namespaces = ["conus_hf", "ak_hf", "hi_hf", "prvi_hf"]

    # Cache pyiceberg Table objects for the local SQL catalog. Data in the
    # SQL warehouse is frozen for this worker's lifetime (parent built it),
    # so repeated load_table() calls can safely return the same metadata
    # object. Each call otherwise round-trips SQLite + re-parses manifest
    # JSON (~5-20ms); per-request we hit 11 tables for hydrofabric gpkg.
    _sql_table_cache: dict = {}
    _sql_table_cache_lock = threading.Lock()
    _sql_original_load_table = cache_catalog.load_table

    def _cached_load_table(identifier):
        key = str(identifier)
        with _sql_table_cache_lock:
            cached = _sql_table_cache.get(key)
            if cached is None:
                cached = _sql_original_load_table(identifier)
                _sql_table_cache[key] = cached
            return cached

    cache_catalog.load_table = _cached_load_table  # type: ignore[method-assign]

    app.state.catalog = catalog
    app.state.cache_catalog = cache_catalog
    app.state.cached_namespaces = {e.split(":")[0] for e in args.cached_namespaces}
    # Per-worker concurrency cap for the heavy gpkg endpoint. Tunable via env.
    gpkg_concurrency = int(os.environ.get("ICEFABRIC_HF_GPKG_CONCURRENCY", "1"))
    gpkg_queue_timeout_s = float(os.environ.get("ICEFABRIC_HF_GPKG_QUEUE_TIMEOUT_S", "300"))
    # Queue-depth admission: reject with 429 once this many requests are
    # already waiting for a semaphore slot. Chosen so the worst-case wait
    # (max_queue_depth * expected build time) stays under queue_timeout_s.
    gpkg_max_queue_depth = int(os.environ.get("ICEFABRIC_HF_GPKG_MAX_QUEUE_DEPTH", "15"))
    app.state.gpkg_limiter = GpkgLimiter(
        semaphore=threading.BoundedSemaphore(gpkg_concurrency),
        queue_timeout_s=gpkg_queue_timeout_s,
        max_queue_depth=gpkg_max_queue_depth,
    )
    app.state.main_logger.info(
        f"gpkg concurrency cap per worker = {gpkg_concurrency} "
        f"(queue timeout {gpkg_queue_timeout_s:.0f}s, max queue depth {gpkg_max_queue_depth})"
    )

    # Disk-based result cache for hydrofabric gpkg. A given (namespace,
    # id_type, identifier, snapshot_id) is deterministic, so repeat requests
    # can skip the subset entirely. Disk-only -> zero RAM cost. Set max
    # entries conservatively; at ~200 MB per CONUS VPU, 30 entries ~= 6 GiB.
    gpkg_cache_enabled = os.environ.get("ICEFABRIC_GPKG_CACHE_ENABLED", "1") != "0"
    if gpkg_cache_enabled:
        gpkg_cache_dir = Path(os.environ.get("ICEFABRIC_GPKG_CACHE_DIR", "/tmp/hf_gpkg_cache"))
        gpkg_cache_max = int(os.environ.get("ICEFABRIC_GPKG_CACHE_MAX_ENTRIES", "30"))
        app.state.gpkg_cache = GpkgCache(cache_dir=gpkg_cache_dir, max_entries=gpkg_cache_max)
        app.state.main_logger.info(f"gpkg result cache at {gpkg_cache_dir} (max {gpkg_cache_max} entries)")
    else:
        app.state.gpkg_cache = None
    try:
        app.state.network_graphs = load_upstream_json(
            catalog=catalog,
            namespaces=hydrofabric_namespaces,
            output_path=here() / "data",
        )
    except NoSuchTableError:
        raise NotImplementedError(
            "Cannot load API as the Hydrofabric Database/Namespace cannot be connected to. Please ensure you are have access to the correct hydrofabric namespaces"
        ) from None

    # Open the streamflow icechunk repo + zarr dataset once per worker.
    # zarr reads are lazy so RAM cost is metadata only.
    try:
        import icechunk
        import xarray as xr

        from icefabric.cli.streamflow import PREFIX, get_bucket

        storage_config = icechunk.s3_storage(
            bucket=get_bucket(), prefix=PREFIX, region="us-east-1", from_env=True
        )
        _streamflow_repo = icechunk.Repository.open(storage_config)
        _streamflow_session = _streamflow_repo.writable_session("main")
        _streamflow_ds = xr.open_zarr(_streamflow_session.store, consolidated=False)
        app.state.streamflow_data = StreamflowData(dataset=_streamflow_ds, repo=_streamflow_repo)
        app.state.main_logger.info("Opened streamflow icechunk dataset.")
    except Exception as e:  # noqa: BLE001
        app.state.main_logger.warning(f"Could not open streamflow dataset: {e}")
        app.state.streamflow_data = None

    yield
    app.state.main_logger.info("Application shutting down.")


app = FastAPI(
    root_path="/api",
    title="Icefabric API",
    description="API for accessing iceberg or icechunk data from EDFS services",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
)


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


# Include routers
app.include_router(hydrofabric_api_router, prefix="/v1")
app.include_router(streamflow_api_router, prefix="/v1")
app.include_router(sft_router, prefix="/v1")
app.include_router(snow17_router, prefix="/v1")
app.include_router(smp_router, prefix="/v1")
app.include_router(lstm_router, prefix="/v1")
app.include_router(lasam_router, prefix="/v1")
app.include_router(noahowp_router, prefix="/v1")
app.include_router(sacsma_router, prefix="/v1")
app.include_router(troute_router, prefix="/v1")
app.include_router(topmodel_router, prefix="/v1")
app.include_router(topoflow_router, prefix="/v1")
app.include_router(ueb_router, prefix="/v1")
app.include_router(cfe_router, prefix="/v1")
app.include_router(ras_api_router, prefix="/v1")
app.include_router(rise_api_wrap_router, prefix="/v1")
app.include_router(parameter_metadata_router, prefix="/v1")


@app.get(
    "/health",
    tags=["Health"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
@app.head(
    "/health",
    tags=["Health"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
)
def get_health() -> HealthCheck:
    """Returns a HealthCheck for the server"""
    return HealthCheck(status="OK")


# Mount static files for mkdocs at the root
# This tells FastAPI to serve the static documentation files at the '/' URL
# We only mount the directory if it exists (only after 'mkdocs build' has run)
# This prevents the app from crashing during tests or local development.
docs_dir = Path("static/docs")
if docs_dir.is_dir():
    app.mount("/", StaticFiles(directory=docs_dir, html=True), name="static")
else:
    print("INFO: Documentation directory 'static/docs' not found. Docs will not be served.")

if __name__ == "__main__":
    # One-time setup in the parent before forking workers. With workers>1,
    # doing this in lifespan races: concurrent SQL cache builds clobber the
    # warehouse, and concurrent load_upstream_json() calls have one worker
    # reading a partially-written graph JSON (-> EOF). Pre-building here
    # means workers only hit the safe "read existing" paths.
    _deploy_env = (
        os.environ.get("ICEFABRIC_DEPLOY_ENV") or os.environ.get("ENVIRONMENT") or args.deploy_env
    ).lower()
    load_creds(_deploy_env)

    if args.cache_catalog == "sql":
        main_logger.info("Building local SQL cache (parent process, one-time)...")
        build_cache(set(args.cached_namespaces), _deploy_env)
        os.environ["ICEFABRIC_CACHE_BUILT"] = "1"

    # Prewarm hydrofabric graph JSON files so workers only read, never write.
    _hf_namespaces = ["conus_hf", "ak_hf", "hi_hf", "prvi_hf"]
    try:
        main_logger.info("Prewarming hydrofabric network graphs (parent process)...")
        _prewarm_catalog = load_catalog(args.catalog)
        load_upstream_json(
            catalog=_prewarm_catalog,
            namespaces=_hf_namespaces,
            output_path=here() / "data",
        )
    except NoSuchTableError:
        main_logger.warning(
            "Hydrofabric namespaces not reachable at prewarm time; workers will attempt at startup."
        )

    # Recycle each worker after this many requests. Resets per-process RSS
    # that otherwise creeps from glibc/numpy fragmentation over time. The
    # supervisor respawns the worker; new workers skip the heavy one-time
    # setup (cache + graphs are already on disk), so churn is ~seconds.
    max_requests_per_worker = int(os.environ.get("ICEFABRIC_MAX_REQUESTS_PER_WORKER", "200"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=2,
        log_level="info",
        limit_max_requests=max_requests_per_worker,
    )
