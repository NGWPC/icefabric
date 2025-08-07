import io
from datetime import datetime
from enum import Enum

from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import Response
from pyiceberg.catalog import load_catalog

api_router = APIRouter(prefix="/streamflow_observations")


# TODO add other gauges used by NWM
class DataSource(str, Enum):
    """All observational streamflow sources"""

    USGS = "usgs"


# Configuration for each data source
DATA_SOURCE_CONFIG = {
    DataSource.USGS: {
        "namespace": "streamflow_observations",
        "table": "usgs_hourly",
        "time_column": "time",
        "units": "cms",
        "description": "USGS stream gauge hourly data",
    },
}


def get_catalog_and_table(data_source: DataSource):
    """Get catalog and table for a given data source"""
    config = DATA_SOURCE_CONFIG[data_source]
    try:
        catalog = load_catalog("glue")
        table = catalog.load_table(f"{config['namespace']}.{config['table']}")
    except ClientError as e:
        msg = "AWS Test account credentials expired. Can't access remote S3 Table"
        print(msg)
        raise e
    return catalog, table, config


def validate_identifier(data_source: DataSource, identifier: str):
    """Check if identifier exists in the dataset"""
    catalog, table, config = get_catalog_and_table(data_source)
    schema = table.schema()
    available_columns = [field.name for field in schema.fields]

    if identifier not in available_columns:
        available_ids = [col for col in available_columns if col != config["time_column"]]
        raise HTTPException(
            status_code=404,
            detail=f"ID '{identifier}' not found in {data_source} dataset. Available IDs: {available_ids[:10]}...",
        )

    return catalog, table, config


@api_router.get("/{data_source}/available")
async def get_available_identifiers(
    data_source: DataSource = Path(..., description="Data source type"),
    limit: int = Query(100, description="Maximum number of IDs to return"),
):
    """
    Get list of available identifiers for a data source

    Examples
    --------
    GET /data/usgs/available
    GET /data/usgs/available?limit=50
    """
    try:
        _, table, config = get_catalog_and_table(data_source)

        schema = table.schema()
        # Get all columns except time column
        identifier_columns = [field.name for field in schema.fields if field.name != config["time_column"]]

        return {
            "data_source": data_source.value,
            "description": config["description"],
            "total_identifiers": len(identifier_columns),
            "identifiers": sorted(identifier_columns)[:limit],
            "showing": min(limit, len(identifier_columns)),
            "units": config["units"],
        }

    except HTTPException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@api_router.get("/{data_source}/csv")
async def get_data_csv(
    data_source: DataSource = Path(..., description="Data source type"),
    identifier: str = Query(
        ...,
        description="Station/gauge ID",
        examples=["01010000"],
        openapi_examples={"station_example": {"summary": "USGS Gauge", "value": "01010000"}},
    ),
    start_date: datetime | None = Query(
        None,
        description="Start Date",
        openapi_examples={"sample_date": {"summary": "Sample Date", "value": "2021-12-31T14:00:00"}},
    ),
    end_date: datetime | None = Query(
        None,
        description="End Date",
        openapi_examples={"sample_date": {"summary": "Sample Date", "value": "2022-01-01T14:00:00"}},
    ),
    include_headers: bool = Query(True, description="Include CSV headers"),
):
    """
    Get data as CSV file for any data source

    Examples
    --------
    GET /data/usgs_hourly/csv?identifier=01031500
    """
    try:
        _, table, config = validate_identifier(data_source, identifier)
        scan_builder = table.scan(selected_fields=[config["time_column"], identifier])
        if start_date:
            scan_builder = scan_builder.filter(f"{config['time_column']} >= '{start_date.isoformat()}'")
        if end_date:
            scan_builder = scan_builder.filter(f"{config['time_column']} <= '{end_date.isoformat()}'")

        df = scan_builder.to_pandas()

        if df.empty:
            return Response(
                content="Error: No data available for the specified parameters",
                status_code=404,
                media_type="text/plain",
            )

        df = df.rename(columns={config["time_column"]: "time", identifier: "q_cms"})

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, header=include_headers)
        csv_data = csv_buffer.getvalue()

        filename_parts = [data_source.value, identifier, "data"]
        if start_date:
            filename_parts.append(f"from_{start_date.strftime('%Y%m%d_%H%M')}")
        if end_date:
            filename_parts.append(f"to_{end_date.strftime('%Y%m%d_%H%M')}")
        filename = "_".join(filename_parts) + ".csv"

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Total-Records": str(len(df)),
                "X-Data-Source": data_source.value,
                "X-Units": config["units"],
            },
        )

    except HTTPException:
        raise


@api_router.get("/{data_source}/parquet")
async def get_data_parquet(
    data_source: DataSource = Path(..., description="Data source type"),
    identifier: str = Query(
        ...,
        description="Station/gauge ID",
        examples=["01010000"],
        openapi_examples={"station_example": {"summary": "USGS Gauge", "value": "01010000"}},
    ),
    start_date: datetime | None = Query(
        None,
        description="Start Date",
        openapi_examples={"sample_date": {"summary": "Sample Date", "value": "2021-12-31T14:00:00"}},
    ),
    end_date: datetime | None = Query(
        None,
        description="End Date",
        openapi_examples={"sample_date": {"summary": "Sample Date", "value": "2022-01-01T14:00:00"}},
    ),
):
    """
    Get data as Parquet file for any data source

    Examples
    --------
    GET /data/usgs/parquet?identifier=01031500
    GET /data/usgs/parquet?identifier=01031500&start_date=2023-01-01T00:00:00&compression=gzip
    """
    try:
        _, table, config = validate_identifier(data_source, identifier)

        scan_builder = table.scan(selected_fields=[config["time_column"], identifier])

        if start_date:
            scan_builder = scan_builder.filter(f"{config['time_column']} >= '{start_date.isoformat()}'")
        if end_date:
            scan_builder = scan_builder.filter(f"{config['time_column']} <= '{end_date.isoformat()}'")

        df = scan_builder.to_pandas()
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available for the specified parameters")

        # Prepare output with metadata
        df = df.rename(columns={config["time_column"]: "time", identifier: "q_cms"}).copy()
        df["data_source"] = data_source.value
        df["identifier"] = identifier
        df["units"] = config["units"]

        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False, compression="lz4", engine="pyarrow")
        parquet_data = parquet_buffer.getvalue()

        # Fix filename generation with proper datetime formatting
        filename_parts = [data_source.value, identifier, "data"]
        if start_date:
            filename_parts.append(f"from_{start_date.strftime('%Y%m%d_%H%M')}")
        if end_date:
            filename_parts.append(f"to_{end_date.strftime('%Y%m%d_%H%M')}")
        filename = "_".join(filename_parts) + ".parquet"

        return Response(
            content=parquet_data,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Total-Records": str(len(df)),
                "X-Data-Source": data_source.value,
                "X-Compression": "lz4",
                "X-Units": config["units"],
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        Response(content=f"Error: {str(e)}", status_code=500, media_type="text/plain")


@api_router.get("/{data_source}/info")
async def get_data_source_info(
    data_source: DataSource = Path(..., description="Data source type"),
):
    """
    Get information about dataset size and recommendations

    Examples
    --------
    GET /data/usgs/info
    """
    try:
        _, table, config = get_catalog_and_table(data_source)

        df = table.inspect.snapshots().to_pandas()

        # Converting to an int rather than a numpy.int64
        latest_snapshot_id = int(df.loc[df["committed_at"].idxmax(), "snapshot_id"])
        snapshots = table.inspect.snapshots().to_pydict()

        snapshots = dict(snapshots)
        # Converting to an int rather than a numpy.int64
        if "snapshot_id" in snapshots and snapshots["snapshot_id"]:
            snapshots["snapshot_id"] = [int(sid) for sid in snapshots["snapshot_id"]]

        return {
            "data_source": data_source.value,
            "latest_snapshot": latest_snapshot_id,
            "description": config["description"],
            "units": config["units"],
            "snapshots": snapshots,
        }
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@api_router.get("/{data_source}/{identifier}/info")
async def get_data_info(
    data_source: DataSource = Path(..., description="Data source type"),
    identifier: str = Path(..., description="Station/gauge ID", examples=["01031500"]),
):
    """
    Get information about dataset size and recommendations

    Examples
    --------
    GET /data/usgs/01031500/info
    """
    try:
        _, table, config = validate_identifier(data_source, identifier)

        # Get data info
        df = table.scan(selected_fields=[config["time_column"], identifier]).to_pandas()
        df_clean = df.dropna(subset=[identifier])  # Droping NA to determine full date range

        return {
            "data_source": data_source.value,
            "identifier": identifier,
            "description": config["description"],
            "total_records": len(df_clean),
            "units": config["units"],
            "date_range": {
                "start": df_clean[config["time_column"]].min().isoformat() if not df_clean.empty else None,
                "end": df_clean[config["time_column"]].max().isoformat() if not df_clean.empty else None,
            },
            "estimated_sizes": {
                "csv_mb": round(len(df_clean) * 25 / 1024 / 1024, 2),
                "parquet_mb": round(len(df_clean) * 8 / 1024 / 1024, 2),
            },
        }

    except HTTPException:
        raise
    except ValueError as e:
        Response(content=f"Error: {str(e)}", status_code=500, media_type="text/plain")


@api_router.get("/sources")
async def get_available_sources():
    """
    Get list of all available data sources

    Examples
    --------
    GET /data/sources
    """
    sources = []
    for source, config in DATA_SOURCE_CONFIG.items():
        sources.append(
            {
                "name": source.value,
                "description": config["description"],
                "namespace": config["namespace"],
                "table": config["table"],
                "units": config["units"],
            }
        )

    return {"available_sources": sources, "total_sources": len(sources)}
