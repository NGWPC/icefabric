import argparse
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, status
from pydantic import BaseModel
from pyiceberg.catalog import load_catalog

from app.routers.hydrofabric.router import api_router as hydrofabric_api_router
from app.routers.nwm_modules.router import (
    lasam_router,
    lstm_router,
    noahowp_router,
    sacsma_router,
    sft_router,
    smp_router,
    snow17_router,
    topmodel_router,
    topoflow_router,
    troute_router,
)
from app.routers.ras_xs.router import api_router as ras_api_router
from app.routers.rise_wrappers.router import api_router as rise_api_wrap_router
from app.routers.streamflow_observations.router import api_router as streamflow_api_router
from icefabric.builds import load_upstream_json
from icefabric.helpers import load_creds

tags_metadata = [
    {
        "name": "Hydrofabric Services",
        "description": "Data Querying functions for the Hydrofabric",
    },
    {
        "name": "RISE",
        "description": "An interface to the RISE API for querying reservoir outflow data",
        "externalDocs": {"description": "Link to the RISE API", "url": "https://data.usbr.gov/rise-api"},
    },
    {
        "name": "NWM Modules",
        "description": "Functions that interact with NWM modules. Mainly supports IPE generation.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads the iceberg catalog location from an environment variable

    Parameters
    ----------
    app: FastAPI
        The FastAPI app instance
    """
    catalog_path = os.getenv("CATALOG_PATH")
    catalog = load_catalog(catalog_path)
    hydrofabric_namespaces = ["conus_hf", "ak_hf", "gl_hf", "hi_hf", "prvi_hf"]
    app.state.catalog = catalog
    app.state.network_graphs = load_upstream_json(
        catalog=catalog,
        namespaces=hydrofabric_namespaces,
        output_path=Path(__file__).parents[1] / "data",
    )
    yield


app = FastAPI(
    title="Icefabric API",
    description="API for accessing iceberg or icechunk data from EDFS services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
app.include_router(ras_api_router, prefix="/v1")
app.include_router(rise_api_wrap_router, prefix="/v1")


@app.head(
    "/health",
    tags=["Health"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
)
def get_health() -> HealthCheck:
    """Returns a HeatlhCheck for the server"""
    return HealthCheck(status="OK")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="The FastAPI App instance for querying versioned EDFS data")

    # Glue = S3 Tables; Sql is a local iceberg catalog
    parser.add_argument(
        "--catalog",
        choices=["glue", "sql"],
        help="The catalog information for querying versioned EDFS data",
        default="glue",
    )  # Setting the default to read from S3

    args = parser.parse_args()

    os.environ["CATALOG_PATH"] = args.catalog

    load_creds(dir=Path.cwd())
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
