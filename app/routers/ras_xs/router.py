import pathlib
import tempfile
import uuid

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import FileResponse
from pyiceberg.catalog import load_catalog
from starlette.background import BackgroundTask

from icefabric.ras_xs import subset_xs
from icefabric.schemas import XsType

api_router = APIRouter(prefix="/ras_xs")


@api_router.get("/{identifier}/")
async def get_xs_subset_gpkg(
    identifier: str = Path(
        ...,
        description="HUC-8 identifier to filter by huc ID",
        examples=["02040106"],
        openapi_examples={"huc": {"summary": "XS Example", "value": "02040106"}},
    ),
    xstype: XsType = Query(XsType.MIP, description="The iceberg namespace used to query the cross-sections"),
):
    """
    Get geopackage subset from the mip xs iceberg catalog by table identifier (aka huc ID).

    This endpoint will query cross-sections from the mip xs iceberg catalog by huc & return
    the data subset as a downloadable geopackage file.

    """
    catalog = load_catalog("glue")
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = pathlib.Path(tempfile.gettempdir())
    tmp_path = temp_dir / f"ras_xs_{identifier}_{unique_id}.gpkg"
    try:
        # Create data subset
        data_gdf = subset_xs(catalog=catalog, identifier=f"{identifier}", output_file=tmp_path, xstype=xstype)

        if not tmp_path.exists():
            raise HTTPException(status_code=500, detail=f"Failed to create geopackage file at {tmp_path}.")
        if tmp_path.stat().st_size == 0:
            tmp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=404, detail=f"No data found for HUC {identifier}.")

        # Verify it's actually a file, not a directory
        if not tmp_path.is_file():
            raise HTTPException(status_code=500, detail=f"Expected file, but got directory at {tmp_path}.")

        print(f"Returning file: {tmp_path} (size: {tmp_path.stat().st_size} bytes)")

        download_filename = f"ras_xs_huc{identifier}.gpkg"

        return FileResponse(
            path=str(tmp_path),
            filename=download_filename,
            media_type="application/geopackage+sqlite3",
            headers={
                "Data_Source": f"{xstype}_xs",
                "HUC Identifier": identifier,
                "Description": f"{xstype} RAS Cross-Section Geopackage",
                "Total Records": f"{len(data_gdf)}",
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


@api_router.get("/{identifier}/dsreachid={ds_reach_id}")
async def get_xs_subset_by_huc_reach_gpkg(
    identifier: str = Path(
        ...,
        description="Identifier to filter data by huc ID",
        examples=["02040106"],
        openapi_examples={"xs": {"summary": "XS Example", "value": "02040106"}},
    ),
    ds_reach_id: str = Path(
        ...,
        description="Identifier to filter data by downstream reach ID)",
        examples=["4188251"],
        openapi_examples={"xs": {"summary": "XS Example", "value": "4188251"}},
    ),
    xstype: XsType = Query(XsType.MIP, description="The iceberg namespace used to query the cross-sections"),
):
    """
    Get geopackage subset from the mip xs iceberg catalog by reach ID at huc ID.

    This endpoint will query cross-sections from the mip xs iceberg catalog by
    downstream reach ID at given huc ID -- returning the data subset as a downloadable geopackage file.

    """
    catalog = load_catalog("glue")
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = pathlib.Path(tempfile.gettempdir())
    tmp_path = temp_dir / f"ras_xs_{identifier}_{ds_reach_id}_{unique_id}.gpkg"
    try:
        # Create data subset
        data_gdf = subset_xs(
            catalog=catalog,
            identifier=f"{identifier}",
            ds_reach_id=f"{ds_reach_id}",
            output_file=tmp_path,
            xstype=xstype,
        )

        if not tmp_path.exists():
            raise HTTPException(status_code=500, detail=f"Failed to create geopackage file at {tmp_path}.")
        if tmp_path.stat().st_size == 0:
            tmp_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=404,
                detail=f"No data found for downstream reach id {ds_reach_id} @ HUC{identifier}.",
            )

        # Verify it's actually a file, not a directory
        if not tmp_path.is_file():
            raise HTTPException(status_code=500, detail=f"Expected file, but got directory at {tmp_path}.")

        print(f"Returning file: {tmp_path} (size: {tmp_path.stat().st_size} bytes)")

        download_filename = f"ras_xs_huc{identifier}_dsreachid{ds_reach_id}.gpkg"

        return FileResponse(
            path=str(tmp_path),
            filename=download_filename,
            media_type="application/geopackage+sqlite3",
            headers={
                "Data_Source": f"{xstype}_xs",
                "HUC Identifier": identifier,
                "DS Reach Identifier": ds_reach_id,
                "Description": f"{xstype} RAS Cross-Section Geopackage",
                "Total Records": f"{len(data_gdf)}",
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
