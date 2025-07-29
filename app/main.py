import argparse
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, status
from pydantic import BaseModel
from pyiceberg.catalog import load_catalog

from app.routers.hydrofabric.router import api_router as hydrofabric_api_router
from app.routers.nwm_modules.router import sft_router, topoflow_router
from app.routers.ras_xs.router import api_router as ras_api_router
from app.routers.rise_wrappers.router import api_router as rise_api_wrap_router
from app.routers.streamflow_observations.router import api_router as streamflow_api_router
from icefabric.helpers import load_creds


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads the iceberg catalog location from an environment variable

    Parameters
    ----------
    app: FastAPI
        The FastAPI app instance
    """
    catalog_path = os.getenv("CATALOG_PATH")
    app.state.catalog = load_catalog(catalog_path)
    yield


tags_metadata = [
    {
        "name": "RISE",
        "description": "An interface to the RISE API for querying reservoir outflow data",
        "externalDocs": {"description": "Link to the RISE API", "url": "https://data.usbr.gov/rise-api"},
    }
]


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
