import os
import re
from datetime import datetime
from logging import Logger

import icechunk
import numpy as np
import xarray as xr
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.background import BackgroundTasks
from fastapi.responses import FileResponse
from werkzeug.utils import secure_filename

from app import get_logger
from icefabric.cli.streamflow import (
    BUCKET,
    PREFIX,
    TIME_FORMATS,
    NoResultsFoundError,
    streamflow_observations,
)
from icefabric.schemas.hydrofabric import StreamflowOutputFormats

api_router = APIRouter(prefix="/streamflow_observations")

STREAMFLOW_HEADERS = {
    "repo": "hourly_streamflow_observations",
    "description": "Stream gauge hourly data",
    "units": str(["cms", "cms_denoted_3"]),
}


def cleanup(file_path: str):
    """Background task helper to cleanup CSV/Parquet files"""
    try:
        os.remove(file_path)
    except OSError:
        pass


def validate_datetime(date_string: str, start_or_end: str):
    """Validation helper function to make sure datetimes are in an acceptable format"""
    for fmt in TIME_FORMATS:
        try:
            datetime_obj = datetime.strptime(date_string, fmt)
            return datetime_obj
        except ValueError:
            continue
    raise ValueError(
        f"Suggested date formatted incorrectly: {start_or_end} must match one of the following formats: {', '.join(TIME_FORMATS)}"
    )


def sanitize_filename_component(s: str) -> str:
    """
    Sanitize filename

    Remove unsafe characters from a string for safe filename use.
    Only allows Unicode alphanumerics and underscore.
    """
    return re.sub(r"[^A-Za-z0-9_]", "_", s)


def integrate_time_range(sd: str, ed: str, filename_parts: list, command_args: list, file_ext: str):
    """Takes a time range (start/end times) and injects them into a filename/command args list"""
    if sd:
        sd = validate_datetime(sd, "start_date")
        filename_parts.append(f"from_{sd.strftime('%Y%m%d_%H%M')}")
        command_args.append("-s")
        command_args.append(str(sd))
    if ed:
        ed = validate_datetime(ed, "end_date")
        filename_parts.append(f"to_{ed.strftime('%Y%m%d_%H%M')}")
        command_args.append("-e")
        command_args.append(str(ed))
    # Secure output directory
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)
    # Sanitize filename
    safe_filename = sanitize_filename_component("_".join(filename_parts))
    safe_ext = sanitize_filename_component(file_ext)
    safe_file = f"{safe_filename}.{safe_ext}"
    # Normalize path
    output_file = os.path.normpath(os.path.join(output_dir, safe_file))
    # Validate path is inside output_dir
    if not output_file.startswith(os.path.abspath(output_dir)):
        raise ValueError("Invalid filename/path.")
    command_args.append("-o")
    command_args.append(output_file)

    return command_args, output_file


def get_data_and_repo_hist():
    """Get repo/data from icechunk for a given data source"""
    try:
        storage_config = icechunk.s3_storage(bucket=BUCKET, prefix=PREFIX, region="us-east-1", from_env=True)
        repo = icechunk.Repository.open(storage_config)
        session = repo.writable_session("main")
        ds = xr.open_zarr(session.store, consolidated=False)
    except ClientError as e:
        msg = "AWS Test account credentials expired. Can't access remote S3 Table"
        raise ClientError(msg) from e
    return ds, repo


def validate_identifier(identifier: str):
    """Check if identifier exists in the dataset"""
    ds, repo = get_data_and_repo_hist()
    if identifier not in ds.coords["id"]:
        raise HTTPException(
            status_code=404,
            detail=f"ID '{identifier}' not found in dataset.",
        )
    return ds, repo


@api_router.get("/{identifier}/info", tags=["Streamflow Observations"])
async def get_identifier_info(
    identifier: str = Path(
        ...,
        description="Station/gauge ID",
        max_length=10,
        pattern=r"^[a-zA-Z0-9]+$",
        examples=["01010000"],
        openapi_examples={"station_example": {"summary": "USGS Gauge", "value": "01010000"}},
    ),
):
    """
    GET ID Full Dataset Overview

    Get information about dataset size for a specific gauge/station. Gives number of records,
    date range, and estimated sizes of CSV/Parquet representations.

    Examples
    --------
    - GET /v1/streamflow_observations/01010000/info
    - GET /v1/streamflow_observations/JBR/info
    - GET /v1/streamflow_observations/08102730/info
    """
    try:
        ds, _ = validate_identifier(identifier)
        df = ds.sel(id=identifier).to_dataframe().reset_index()
        df.dropna(subset=["q_cms"], inplace=True)

        return {
            **STREAMFLOW_HEADERS,
            "identifier": identifier,
            "total_records": len(df),
            "date_range": {
                "start": df["time"].min().isoformat() if not df.empty else None,
                "end": df["time"].max().isoformat() if not df.empty else None,
            },
            "estimated_sizes": {
                "csv_mb": round(len(df) * 25 / 1024 / 1024, 2),
                "parquet_mb": round(len(df) * 8 / 1024 / 1024, 2),
            },
        }
    except HTTPException:
        raise


@api_router.get("/{identifier}/{output_format}", tags=["Streamflow Observations"])
async def get_data_time_range(
    identifier: str = Path(
        ...,
        description="Station/gauge ID",
        max_length=10,
        pattern=r"^[a-zA-Z0-9]+$",
        examples=["01010000"],
        openapi_examples={"station_example": {"summary": "USGS Gauge", "value": "01010000"}},
    ),
    output_format: StreamflowOutputFormats = Path(
        ...,
        description="Output/return format of the data",
    ),
    start_date: str | None = Query(
        None,
        description="Start Date",
        openapi_examples={"sample_date": {"summary": "Sample Date", "value": "2021-12-31 14:00:00"}},
    ),
    end_date: str | None = Query(
        None,
        description="End Date",
        openapi_examples={"sample_date": {"summary": "Sample Date", "value": "2022-01-01 14:00:00"}},
    ),
    include_headers: bool | None = Query(
        True, description="Include CSV headers. Only applies if return format is CSV. Defaults to True."
    ),
    logger: Logger = Depends(get_logger),
):
    """
    GET ID Data in Time Range

    Returns hourly streamflow data for a specific gauge/station, over a specified time range. Returned
    file can be either CSV or Parquet file format.

    Examples
    --------
    - GET /v1/streamflow_observations/01031500/csv?include_headers=true
    - GET /v1/streamflow_observations/02GC002/csv?start_date=2010&end_date=2011
    - GET /v1/streamflow_observations/08102730/parquet?start_date=2023-06&end_date=2023-11
    """
    secure_identifier = secure_filename(identifier)
    try:
        # Construct filename and arg list for output file construction
        filename_parts = [
            "hourly_streamflow_data",
            sanitize_filename_component(secure_identifier),
        ]
        command_args = ["-g", secure_identifier, "-h", include_headers]
        command_args, output_path = integrate_time_range(
            start_date, end_date, filename_parts, command_args, output_format.value
        )
        output_file = output_path.split("/")[-1]
        logger.info(f"Output file: {output_file}")

        # Call click command to create output file
        total_records = streamflow_observations(command_args, standalone_mode=False)
        logger.info(f"Total records received for {identifier}: {total_records}")

        return_headers = {
            **STREAMFLOW_HEADERS,
            "Content-Disposition": f"attachment; filename={output_file}",
            "X-Total-Records": str(total_records),
        }
        if output_format.value == "parquet":
            return_headers["X-Compression"] = "lz4"

        # Generate response
        response = FileResponse(
            output_path, media_type=output_format.media_type(), filename=output_file, headers=return_headers
        )

        # Cleanup file after delivery
        background_tasks = BackgroundTasks()
        background_tasks.add_task(cleanup, output_path)
        response.background = background_tasks

        return response
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Problem with inputs - {e}") from e
    except NoResultsFoundError as e:
        raise HTTPException(status_code=404, detail=f"No records found - {e}") from e


@api_router.get("/history", tags=["Streamflow Observations"])
async def get_repo_history():
    """
    GET Repo History/Snapshots

    Get information about repo history. Includes latest snapshot and snapshot history.

    Example
    --------
    - GET /v1/streamflow_observations/history
    """
    try:
        _, repo = get_data_and_repo_hist()
        snapshots = []
        hist = repo.ancestry(branch="main")
        for ancestor in hist:
            snapshots.append(
                {
                    "snapshot_id": ancestor.id,
                    "commit_message": ancestor.message,
                    "timestamp": ancestor.written_at,
                }
            )

        return {
            **STREAMFLOW_HEADERS,
            "latest_snapshot": snapshots[0]["snapshot_id"],
            "snapshots": snapshots,
        }
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@api_router.get("/available", tags=["Streamflow Observations"])
async def get_available_identifiers(
    limit: int = Query(100, description="Maximum number of IDs to return"),
):
    """
    GET All Available IDs

    Get the list of available identifiers for querying the dataset. Can optionally
    limit output.

    Examples
    --------
    - GET /v1/streamflow_observations/available
    - GET /v1/streamflow_observations/available?limit=50
    """
    try:
        ds, _ = get_data_and_repo_hist()
        ds = ds.drop_vars(["q_cms", "q_cms_denoted_3"])
        ids = np.unique(ds.coords["id"]).tolist()

        return {
            **STREAMFLOW_HEADERS,
            "total_identifiers": len(ids),
            "identifiers": sorted(ids)[:limit],
            "showing": min(limit, len(ids)),
        }
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
