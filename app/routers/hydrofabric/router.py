import pathlib
import sqlite3
import tempfile
import uuid

import geopandas as gpd
import pyogrio
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import Path as FastAPIPath
from fastapi.responses import FileResponse
from pyiceberg.expressions import EqualTo
from starlette.background import BackgroundTask

from app import get_catalog, get_graphs
from icefabric.hydrofabric import subset_hydrofabric, subset_nhf
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
from icefabric.schemas.hydrofabric import (
    GeographicDomain,
    HydrofabricSource,
    IdType,
    resolve_namespace,
)

api_router = APIRouter(prefix="/hydrofabric")


@api_router.get("/{identifier}/gpkg", tags=["Hydrofabric Services"])
async def get_hydrofabric_subset_gpkg(
    identifier: str = FastAPIPath(
        ...,
        description="Identifier to start tracing from (e.g., catchment ID, POI ID, HL_URI)",
        openapi_examples={
            "fp_id": {"summary": "NHF Flowpath ID (NHF)", "value": 3490271},
            "site-no": {"summary": "UGSG Site no (NHF)", "value": "02374250"},
            "vpu-id": {"summary": "VPU ID (NHF)", "value": "01"},
            "hl_uri": {"summary": "USGS Gauge (HFv2.2)", "value": "gages-01010000"},
            "wb-id": {"summary": "Watershed ID (HFv2.2)", "value": "wb-4581"},
        },
    ),
    id_type: IdType = Query(
        ...,
        description="The type of identifier being used",
        openapi_examples={
            "fp_id": {"summary": "NHF Flowpath ID (NHF)", "value": IdType.FP_ID},
            "vpu-id": {"summary": "VPU ID (NHF)", "value": IdType.VPU_ID},
            "site-no": {"summary": "UGSG Site no (NHF)", "value": IdType.SITE_NO},
            "hl_uri": {"summary": "USGS Gauge (HFv2.2, NHF)", "value": IdType.HL_URI},
            "wb-id": {"summary": "Watershed ID (HFv2.2)", "value": IdType.ID},
        },
    ),
    source: HydrofabricSource | None = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes).",
    ),
    domain: GeographicDomain | str | None = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, ak_hf, hi_hf, prvi_hf, gl_hf) for backwards compatibility.",
    ),
    layers: list[str] | None = Query(
        None,
        description="Layers to include in the geopackage. Core layers (divides, flowpaths, network, nexus) are always included.",
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

    # Resolve namespace from domain/source combination (outside try block for error handling access)
    try:
        namespace, is_nhf, deprecation_warnings = resolve_namespace(domain, source)
    except NotImplementedError as e:
        raise HTTPException(
            status_code=501,
            detail={
                "error": "domain_not_available",
                "message": str(e),
                "available_domains": ["CONUS"],
                "requested_domain": domain.value if hasattr(domain, "value") else str(domain),
                "requested_source": source.value if source else None,
            },
        ) from None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}") from None

    try:
        if is_nhf:
            if id_type == IdType.VPU_ID:
                output_layers = subset_nhf(
                    vpu_id=identifier,
                    catalog=catalog,
                )
            elif id_type == IdType.FP_ID:
                output_layers = subset_nhf(
                    flowpath_id=int(identifier),
                    catalog=catalog,
                )
            elif id_type == IdType.SITE_NO:
                output_layers = subset_nhf(
                    gage_id=identifier,
                    catalog=catalog,
                )
            else:
                raise ValueError(f"Incorrect ID type: {id_type} for the NHF")
        else:
            if id_type in [
                IdType.HL_URI,
                IdType.ID,
            ]:
                output_layers = subset_hydrofabric(
                    catalog=catalog,
                    identifier=identifier,
                    id_type=id_type,
                    layers=layers or ["divides", "flowpaths", "network", "nexus"],
                    namespace=namespace,
                    graph=network_graphs[namespace],
                )
            else:
                raise ValueError(f"Incorrect ID type: {id_type} for the HFv2.2")

        # Check if we got any data
        if not output_layers:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for identifier '{identifier}' with type '{id_type.value}'",
            )

        tmp_path.parent.mkdir(parents=True, exist_ok=True)

        layers_written = 0
        spatial_layers = {}
        nonspatial_layers = {}

        # Separate spatial vs non-spatial
        for table_name, layer_data in output_layers.items():
            if len(layer_data) > 0:
                if isinstance(layer_data, gpd.GeoDataFrame):
                    spatial_layers[table_name] = layer_data
                else:
                    nonspatial_layers[table_name] = layer_data
            else:
                print(f"Warning: {table_name} layer is empty")

        # Write spatial layers first with pyogrio
        for table_name, layer_data in spatial_layers.items():
            pyogrio.write_dataframe(layer_data, tmp_path, layer=table_name)
            layers_written += 1
            print(f"Written spatial layer '{table_name}' with {len(layer_data)} records")

        # Then write non-spatial layers with sqlite3
        if nonspatial_layers:
            conn = sqlite3.connect(tmp_path)
            for table_name, layer_data in nonspatial_layers.items():
                layer_data.to_sql(table_name, conn, if_exists="replace", index=False)
                layers_written += 1
                print(f"Written non-spatial layer '{table_name}' with {len(layer_data)} records")
            conn.close()

            if layers_written == 0:
                raise HTTPException(status_code=404, detail=f"No non-empty layers found for identifier '{identifier}'")

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
                "X-Domain": namespace,
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
                detail=f"No origin found for {id_type.value}='{identifier}' in namespace '{namespace}'",
            ) from None
        else:
            raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}") from None


@api_router.get("/history", tags=["Hydrofabric Services"])
async def get_hydrofabric_history(
    domain: str = Query("conus_hf", description="The iceberg namespace used to query the hydrofabric"),
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
            detail=f"No snapshot history found for domain '{domain}'",
        )
    for e_in, entry in enumerate(domain_table.iter_rows()):
        return_dict["history"].append({"domain": entry[0], "layer_updates": []})
        for l_in, layer_id in enumerate(entry[1:]):
            layer_name = layers[l_in][0]
            tab = catalog.load_table(f"{domain}.{layer_name}")
            snap_obj = tab.snapshot_by_id(layer_id)
            layer_update = {"layer_name": layer_name, "snapshot_id": layer_id, "snapshot_summary": snap_obj}
            return_dict["history"][e_in]["layer_updates"].append(layer_update)

    return return_dict
