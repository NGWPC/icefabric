import argparse
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pyiceberg.catalog import load_catalog
from pyiceberg.exceptions import NoSuchTableError
from pyprojroot import here

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
        "ak_nhf",
        "hi_nhf",
        "prvi_nhf",
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
    deploy_env = os.environ.get("ICEFABRIC_DEPLOY_ENV") or os.environ.get("ENVIRONMENT") or args.deploy_env
    deploy_env = deploy_env.lower()
    load_creds(deploy_env)
    if args.cache_catalog == "sql":
        app.state.main_logger.info("Building local SQL cache...")
        build_cache(set(args.cached_namespaces), deploy_env)
    catalog = load_catalog(args.catalog)
    cache_catalog = load_catalog(args.cache_catalog)
    hydrofabric_namespaces = ["conus_hf", "ak_hf", "hi_hf", "prvi_hf"]
    app.state.catalog = catalog
    app.state.cache_catalog = cache_catalog
    app.state.cached_namespaces = {e.split(":")[0] for e in args.cached_namespaces}
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
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
