import argparse
import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
import uvicorn
import yaml
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


# Read icefabric config from .pyiceberg.yaml (for build_cache default).
_pyiceberg_home = os.environ.get("PYICEBERG_HOME", str(here() / ".pyiceberg.yaml"))
try:
    with open(_pyiceberg_home) as _f:
        _cfg = yaml.safe_load(_f) or {}
except FileNotFoundError:
    _cfg = {}
_icefabric_cfg = _cfg.get("icefabric", {})


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

parser.add_argument(
    "--catalog",
    choices=["glue", "sql"],
    help="The catalog for querying versioned EDFS data",
    default="glue",
)
parser.add_argument(
    "--cached-namespaces",
    nargs="+",
    help="Namespaces to include in local cache. Optionally <namespace>:<snapshot>",
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
parser.add_argument(
    "--local-icechunk-path",
    type=str,
    default=None,
    help="Path to a local icechunk store (overrides ICEFABRIC_ICECHUNK_PATH)",
)
args, _ = parser.parse_known_args()

# Resolve config with precedence: CLI > env > yam
local_icechunk_path = args.local_icechunk_path or os.environ.get("ICEFABRIC_ICECHUNK_PATH")
# build_cache: yaml default, env var overrides
_should_build = str(_icefabric_cfg.get("build_cache", "true")).lower()
if os.environ.get("ICEFABRIC_BUILD_CACHE") is not None:
    _should_build = os.environ["ICEFABRIC_BUILD_CACHE"].lower()
should_build_cache = _should_build in ("true", "1", "yes")

# --catalog sql  + build_cache=true  → query SQL, refresh from Glue on startup
# --catalog sql  + build_cache=false → query SQL as-is (fully offline)
# --catalog glue                     → query Glue (build_cache ignored)
_local_mode = args.catalog == "sql"
_refresh_from_glue = _local_mode and should_build_cache


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
    # Cap per-worker sync-handler concurrency.
    thread_limiter = anyio.to_thread.current_default_thread_limiter()
    thread_limiter.total_tokens = 20
    app.state.main_logger.info(f"AnyIO threadpool limit set to {thread_limiter.total_tokens}")
    deploy_env = os.environ.get("ICEFABRIC_DEPLOY_ENV") or os.environ.get("ENVIRONMENT") or args.deploy_env
    deploy_env = deploy_env.lower()

    # --catalog glue always needs AWS creds.
    # --catalog sql needs creds only when refreshing from Glue.
    if not _local_mode or _refresh_from_glue:
        load_creds(deploy_env)
    else:
        app.state.main_logger.info("Local mode: skipping AWS credential loading.")

    # Refresh SQL from Glue on startup (only when --catalog sql).
    if _refresh_from_glue and not os.environ.get("ICEFABRIC_CACHE_BUILT"):
        app.state.main_logger.info("Refreshing SQL catalog from Glue...")
        build_cache(set(args.cached_namespaces), deploy_env)
    elif _refresh_from_glue:
        app.state.main_logger.info("SQL already refreshed by parent process.")
    elif _local_mode:
        app.state.main_logger.info("SQL catalog: build_cache=false, using local data.")
    else:
        app.state.main_logger.info("Using Glue catalog directly.")

    catalog = load_catalog(args.catalog)
    # cache_catalog: same as catalog (no namespace routing needed anymore).
    cache_catalog = catalog
    hydrofabric_namespaces = ["conus_hf", "ak_hf", "hi_hf", "prvi_hf"]

    # When using SQL, cache pyiceberg Table objects to avoid repeated
    # SQLite round-trips (~5-20ms each).
    if _local_mode:
        _sql_table_cache: dict = {}
        _sql_table_cache_lock = threading.Lock()
        _sql_original_load_table = catalog.load_table

        def _cached_load_table(identifier):
            key = str(identifier)
            with _sql_table_cache_lock:
                cached = _sql_table_cache.get(key)
                if cached is None:
                    cached = _sql_original_load_table(identifier)
                    _sql_table_cache[key] = cached
                return cached

        catalog.load_table = _cached_load_table  # type: ignore[method-assign]

    app.state.catalog = catalog
    app.state.cache_catalog = cache_catalog
    app.state.cached_namespaces = set()  # no namespace routing
    # Per-worker concurrency cap for the heavy gpkg endpoint.
    gpkg_concurrency = int(os.environ.get("ICEFABRIC_HF_GPKG_CONCURRENCY", "1"))
    gpkg_queue_timeout_s = float(os.environ.get("ICEFABRIC_HF_GPKG_QUEUE_TIMEOUT_S", "300"))
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

    # Disk-based result cache for hydrofabric gpkg.
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
        app.state.main_logger.warning(
            "HF v2.2 namespaces not found in the catalog "
            "(expected when using local NHF-only catalog). "
            "Hydrofabric v2.2 endpoints will not be available."
        )
        app.state.network_graphs = {}

    # Open the streamflow icechunk repo + zarr dataset once per worker.
    # Supports both S3-backed and local filesystem icechunk stores.
    try:
        import icechunk
        import xarray as xr

        if local_icechunk_path:
            app.state.main_logger.info(f"Opening local icechunk store: {local_icechunk_path}")
            storage_config = icechunk.local_filesystem_storage(local_icechunk_path)
        else:
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
docs_dir = Path("static/docs")
if docs_dir.is_dir():
    app.mount("/", StaticFiles(directory=docs_dir, html=True), name="static")
else:
    print("INFO: Documentation directory 'static/docs' not found. Docs will not be served.")

if __name__ == "__main__":
    # One-time setup in the parent before forking workers.
    _deploy_env = (
        os.environ.get("ICEFABRIC_DEPLOY_ENV") or os.environ.get("ENVIRONMENT") or args.deploy_env
    ).lower()
    if not _local_mode or _refresh_from_glue:
        load_creds(_deploy_env)
    else:
        main_logger.info("Local mode: skipping AWS credential loading.")

    if _refresh_from_glue and not os.environ.get("ICEFABRIC_CACHE_BUILT"):
        main_logger.info("Refreshing SQL catalog from Glue (parent process)...")
        build_cache(set(args.cached_namespaces), _deploy_env)
        os.environ["ICEFABRIC_CACHE_BUILT"] = "1"
    elif _refresh_from_glue:
        main_logger.info("SQL already refreshed by parent process.")
    elif _local_mode:
        main_logger.info("SQL catalog: build_cache=false, using local data.")
    else:
        main_logger.info("Using Glue catalog directly.")

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

    max_requests_per_worker = int(os.environ.get("ICEFABRIC_MAX_REQUESTS_PER_WORKER", "100"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=2,
        log_level="info",
        limit_max_requests=max_requests_per_worker,
    )
