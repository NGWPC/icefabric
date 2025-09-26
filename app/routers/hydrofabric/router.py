import pathlib
import tempfile
import uuid

import geopandas as gpd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import Path as FastAPIPath
from fastapi.responses import FileResponse
from pyiceberg.expressions import EqualTo
from starlette.background import BackgroundTask

from app import get_catalog, get_graphs
from icefabric.hydrofabric.subset import subset_hydrofabric
from icefabric.schemas import (
    DivideAttributes,
    Divides,
    FlowpathAttributes,
    FlowpathAttributesML,
    Flowpaths,
    Hydrolocations,
    Lakes,
    Network,
    Nexus,
    POIs,
)
from icefabric.schemas.hydrofabric import HydrofabricDomains, IdType

api_router = APIRouter(prefix="/hydrofabric")


@api_router.get("/{identifier}/gpkg", tags=["Hydrofabric Services"])
async def get_hydrofabric_subset_gpkg(
    identifier: str = FastAPIPath(
        ...,
        description="Identifier to start tracing from (e.g., catchment ID, POI ID, HL_URI)",
        openapi_examples={
            "hl_uri": {"summary": "USGS Gauge", "value": "gages-01010000"},
            "wb-id": {"summary": "Watershed ID", "value": "wb-4581"},
        },
    ),
    id_type: IdType = Query(
        IdType.HL_URI,
        description="The type of identifier being used",
        openapi_examples={
            "hl_uri": {"summary": "USGS Gauge", "value": IdType.HL_URI},
            "wb-id": {"summary": "Watershed ID", "value": IdType.ID},
        },
    ),
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS, description="The iceberg namespace used to query the hydrofabric"
    ),
    layers: list[str] | None = Query(
        default=["divides", "flowpaths", "network", "nexus"],
        description="Layers to include in the geopackage. Core layers (divides, flowpaths, network, nexus) are always included.",
        examples=["divides", "flowpaths", "network", "nexus", "lakes", "pois", "hydrolocations"],
    ),
    catalog=Depends(get_catalog),
    network_graphs=Depends(get_graphs),
):
    """
    Get hydrofabric subset as a geopackage file (.gpkg)

    This endpoint creates a subset of the hydrofabric data by tracing upstream
    from a given identifier and returns all related geospatial layers as a
    downloadable geopackage file.

    **Parameters:**
    - **identifier**: The unique identifier to start tracing from
    - **id_type**: Type of identifier (hl_uri, id, poi_id)
    - **domain**: Hydrofabric domain/namespace to query
    - **layers**: Additional layers to include (core layers always included)

    **Returns:** Geopackage file (.gpkg) containing the subset data
    """
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = pathlib.Path(tempfile.gettempdir())
    tmp_path = temp_dir / f"subset_{identifier}_{unique_id}.gpkg"

    try:
        # Create the subset (same as CLI logic)
        output_layers = subset_hydrofabric(
            catalog=catalog,
            identifier=identifier,
            id_type=id_type,
            layers=layers or ["divides", "flowpaths", "network", "nexus"],
            namespace=domain.value,
            graph=network_graphs[domain],
        )

        # Check if we got any data
        if not output_layers:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for identifier '{identifier}' with type '{id_type.value}'",
            )

        # Write to geopackage (same as CLI logic)
        tmp_path.parent.mkdir(parents=True, exist_ok=True)

        layers_written = 0
        for table_name, layer_data in output_layers.items():
            if len(layer_data) > 0:  # Only save non-empty layers
                # Ensure we have a GeoDataFrame for spatial layers
                if not isinstance(layer_data, gpd.GeoDataFrame):
                    if hasattr(layer_data, "geometry") or "geometry" in layer_data.columns:
                        layer_data = gpd.GeoDataFrame(layer_data)
                    else:
                        # For non-spatial layers (like network), convert to GeoDataFrame with empty geometry
                        layer_data = gpd.GeoDataFrame(layer_data, geometry=[None] * len(layer_data))

                layer_data.to_file(tmp_path, layer=table_name, driver="GPKG")
                layers_written += 1
                print(f"Written layer '{table_name}' with {len(layer_data)} records")
            else:
                print(f"Warning: {table_name} layer is empty")

        if layers_written == 0:
            raise HTTPException(
                status_code=404, detail=f"No non-empty layers found for identifier '{identifier}'"
            )

        # Verify the file was created successfully
        if not tmp_path.exists():
            raise HTTPException(status_code=500, detail="Failed to create geopackage file")

        if tmp_path.stat().st_size == 0:
            tmp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail="Created geopackage file is empty")

        # Verify it's actually a file, not a directory
        if not tmp_path.is_file():
            raise HTTPException(status_code=500, detail="Expected file but got directory")

        print(f"Successfully created geopackage: {tmp_path} (size: {tmp_path.stat().st_size} bytes)")

        # Create download filename
        safe_identifier = identifier.replace("/", "_").replace("\\", "_")
        download_filename = f"hydrofabric_subset_{safe_identifier}_{id_type.value}.gpkg"

        return FileResponse(
            path=str(tmp_path),
            filename=download_filename,
            media_type="application/geopackage+sqlite3",
            headers={
                "Content-Description": "Hydrofabric Subset Geopackage",
                "X-Identifier": identifier,
                "X-ID-Type": id_type.value,
                "X-Domain": domain.value,
                "X-Layers-Count": str(layers_written),
            },
            background=BackgroundTask(lambda: tmp_path.unlink(missing_ok=True)),
        )

    except HTTPException:
        # Clean up temp file if it exists and re-raise HTTP exceptions
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
    except FileNotFoundError as e:
        # Clean up temp file if it exists
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail=f"Required file not found: {str(e)}") from None
    except ValueError as e:
        # Clean up temp file if it exists
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        if "No origin found" in str(e):
            raise HTTPException(
                status_code=404,
                detail=f"No origin found for {id_type.value}='{identifier}' in domain '{domain.value}'",
            ) from None
        else:
            raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}") from None


@api_router.get("/history", tags=["Hydrofabric Services"])
async def get_hydrofabric_history(
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS, description="The iceberg namespace used to query the hydrofabric"
    ),
    catalog=Depends(get_catalog),
):
    """
    Get Hydrofabric domain snapshot history from Iceberg

    This endpoint takes a domain of hydrofabric data and querys for the
    hydrofabric snapshot history from Iceberg. Returns each layer's
    history for the chosen domain. Each snapshot is summarized.

    **Parameters:**
    - **domain**: Hydrofabric domain/namespace to query

    **Returns:** A JSON representation of the domain's snapshot history
    """
    return_dict = {"history": []}
    layers = [
        ("divide-attributes", DivideAttributes),
        ("divides", Divides),
        ("flowpath-attributes-ml", FlowpathAttributesML),
        ("flowpath-attributes", FlowpathAttributes),
        ("flowpaths", Flowpaths),
        ("hydrolocations", Hydrolocations),
        ("lakes", Lakes),
        ("network", Network),
        ("nexus", Nexus),
        ("pois", POIs),
    ]
    snapshots_table = catalog.load_table("hydrofabric_snapshots.id")
    domain_table = snapshots_table.scan(row_filter=EqualTo("domain", domain.replace("_hf", ""))).to_polars()
    if domain_table.is_empty():
        raise HTTPException(
            status_code=404,
            detail=f"No snapshot history found for domain '{domain.value}'",
        )
    for e_in, entry in enumerate(domain_table.iter_rows()):
        return_dict["history"].append({"domain": entry[0], "layer_updates": []})
        for l_in, layer_id in enumerate(entry[1:]):
            layer_name = layers[l_in][0]
            tab = catalog.load_table(f"{domain.value}.{layer_name}")
            snap_obj = tab.snapshot_by_id(layer_id)
            layer_update = {"layer_name": layer_name, "snapshot_id": layer_id, "snapshot_summary": snap_obj}
            return_dict["history"][e_in]["layer_updates"].append(layer_update)

    return return_dict
