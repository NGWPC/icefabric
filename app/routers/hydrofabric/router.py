import pathlib
import tempfile
import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app import get_catalog
from icefabric.hydrofabric import subset
from icefabric.schemas import HydrofabricDomains, IdType

api_router = APIRouter(prefix="/hydrofabric")


@api_router.get("/{identifier}/gpkg")
async def get_hydrofabric_subset_gpkg(
    identifier: str = Path(
        ...,
        description="Identifier to start tracing from (e.g., catchment ID, POI ID)",
        examples=["01010000"],
        openapi_examples={"station_example": {"summary": "USGS Gauge", "value": "01010000"}},
    ),
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS, description="The iceberg namespace used to query the hydrofabric"
    ),
    catalog=Depends(get_catalog),
):
    """
    Get hydrofabric subset as a geopackage file (.gpkg)

    This endpoint creates a subset of the hydrofabric data by tracing upstream
    from a given identifier and returns all related geospatial layers as a
    downloadable geopackage file.
    """
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = pathlib.Path(tempfile.gettempdir())
    tmp_path = temp_dir / f"hydrofabric_subset_{identifier}_{unique_id}.gpkg"
    try:
        # Create the subset
        subset(
            catalog=catalog,
            identifier=f"gages-{identifier}",
            id_type=IdType.HL_URI,
            output_file=tmp_path,
            domain=domain,
        )

        if not tmp_path.exists():
            raise HTTPException(status_code=500, detail=f"Failed to create geopackage file at {tmp_path}")
        if tmp_path.stat().st_size == 0:
            tmp_path.unlink(missing_ok=True)  # Clean up empty file
            raise HTTPException(status_code=404, detail=f"No data found for identifier '{identifier}'")

        # Verify it's actually a file, not a directory
        if not tmp_path.is_file():
            raise HTTPException(status_code=500, detail=f"Expected file but got directory at {tmp_path}")

        print(f"Returning file: {tmp_path} (size: {tmp_path.stat().st_size} bytes)")

        download_filename = f"hydrofabric_subset_{identifier}.gpkg"

        return FileResponse(
            path=str(tmp_path),
            filename=download_filename,
            media_type="application/geopackage+sqlite3",
            headers={
                "Content-Description": "Hydrofabric Subset Geopackage",
                "X-Identifier": identifier,
            },
            background=BackgroundTask(lambda: tmp_path.unlink(missing_ok=True)),
        )

    except HTTPException:
        raise
    except Exception:
        # Clean up temp file if it exists
        if "tmp_path" in locals() and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
