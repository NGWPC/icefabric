import gc
import logging
import pathlib
import sqlite3
import tempfile
import uuid

import geopandas as gpd
import pyogrio
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import Path as FastAPIPath
from fastapi.responses import FileResponse
from pydantic.json_schema import SkipJsonSchema
from pyiceberg.expressions import EqualTo
from starlette.background import BackgroundTask

from app import (
    GpkgCache,
    GpkgLimiter,
    get_cache_catalog,
    get_cached_namespaces,
    get_catalog,
    get_gpkg_cache,
    get_gpkg_limiter,
    get_graphs,
)
from icefabric.cli.streamflow import NoResultsFoundError
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
    HydrofabricNamespace,
    HydrofabricSource,
    IdType,
    QueryIdType,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

api_router = APIRouter(prefix="/hydrofabric")


def _cleanup_tmp(path: pathlib.Path) -> None:
    """Delete a temp file; safe to call multiple times."""
    try:
        path.unlink(missing_ok=True)
    except OSError as e:  # pragma: no cover - defensive
        logger.warning(f"cleanup: failed to delete {path}: {e}")


@api_router.get("/{identifier}/gpkg", tags=["Hydrofabric Services"])
def get_hydrofabric_subset_gpkg(
    identifier: str = FastAPIPath(
        ...,
        description="Identifier to start tracing from (e.g., catchment ID, POI ID, HL_URI)",
        openapi_examples={
            "NHF flowpath": {"summary": "NHF Flowpath ID (NHF)", "value": 3490271},
            "vpu-id": {"summary": "VPU ID (NHF)", "value": "01"},
            "gage id": {"summary": "USGS Gauge ID (HFv2.2, NHF)", "value": "01010000"},
            "2.2 flowpath": {"summary": "Watershed ID (HFv2.2)", "value": "wb-4581"},
        },
    ),
    id_type: QueryIdType = Query(
        ...,
        description="The type of identifier being used",
        openapi_examples={
            "NHF flowpath": {"summary": "NHF Flowpath ID (NHF)", "value": QueryIdType.FLOWPATH_ID},
            "vpu-id": {"summary": "VPU ID (NHF)", "value": QueryIdType.VPU_ID},
            "gage id": {"summary": "USGS Gauge (HFv2.2, NHF)", "value": QueryIdType.GAGE_ID},
            "2.2 flowpath": {"summary": "Watershed ID (HFv2.2)", "value": QueryIdType.FLOWPATH_ID},
        },
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes).",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (conus_hf, ak_hf, hi_hf, prvi_hf, gl_hf) for backwards compatibility.",
    ),
    layers: list[str] | None = Query(
        None,
        description="Layers to include in the geopackage. Core layers (divides, flowpaths, network, nexus) are always included.",
    ),
    catalog=Depends(get_catalog),
    cache_catalog=Depends(get_cache_catalog),
    cached_namespaces=Depends(get_cached_namespaces),
    network_graphs=Depends(get_graphs),
    gpkg_limiter: GpkgLimiter = Depends(get_gpkg_limiter),
    gpkg_cache: GpkgCache | None = Depends(get_gpkg_cache),
):
    """
    Get hydrofabric subset as a geopackage file (.gpkg)

    This endpoint creates a subset of the hydrofabric data by tracing upstream
    from a given identifier and returns all related geospatial layers as a
    downloadable geopackage file.

    **Parameters:**
    - **identifier**: The unique identifier to start tracing from
    - **id_type**: Type of identifier (gage_id, flowpath_id, vpu_id)
    - **domain**: Hydrofabric domain/namespace to query
    - **layers**: Additional layers to include (core layers always included)

    **Returns:** Geopackage file (.gpkg) containing the subset data
    """
    unique_id = str(uuid.uuid4())[:8]
    temp_dir = pathlib.Path(tempfile.gettempdir()).resolve()
    # Use only the UUID in the filename to avoid user-controlled data in path expressions
    tmp_path = temp_dir / f"subset_{unique_id}.gpkg"

    # Resolve namespace from domain/source combination (outside try block for error handling access)
    try:
        namespace = HydrofabricNamespace.resolve(domain, source)
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

    # swap catalog for cached catalog if appropriate
    catalog = cache_catalog if namespace in cached_namespaces else catalog

    # Build the response filename up-front so every exit path uses the same.
    safe_identifier = identifier.replace("/", "_").replace("\\", "_")
    download_filename = f"hydrofabric_subset_{safe_identifier}_{id_type.value}.gpkg"
    response_headers_base = {
        "Content-Description": "Hydrofabric Subset Geopackage",
        "X-Identifier": identifier,
        "X-ID-Type": id_type.value,
        "X-Domain": str(namespace),
    }

    # Cache lookup. Result is deterministic given (namespace, id_type,
    # identifier, snapshot_id). Hit -> return immediately, bypassing the
    # semaphore, the subset work, and the layer-streaming writes.
    cache_key: str | None = None
    if gpkg_cache is not None:
        try:
            snapshot_id = str(catalog.load_table(f"{namespace}.flowpaths").current_snapshot().snapshot_id)
            cache_key = gpkg_cache.key(str(namespace), id_type.value, str(identifier), snapshot_id)
            cached_path = gpkg_cache.get(cache_key)
            if cached_path is not None:
                # Defense-in-depth: verify the resolved path stays inside the
                # cache directory. The key is already a sha256 hex digest, so
                # this should always succeed; it silences CodeQL's
                # "Uncontrolled data used in path expression" alert.
                try:
                    resolved_path = cached_path.resolve()
                    resolved_path.relative_to(gpkg_cache.cache_dir.resolve())
                except (ValueError, OSError):
                    logger.warning(f"gpkg cache path escape detected for key {cache_key[:12]}")
                    cache_key = None
                else:
                    logger.info(f"gpkg cache HIT: {cache_key[:12]} ({cached_path.name})")
                    return FileResponse(
                        path=str(resolved_path),
                        filename=download_filename,
                        media_type="application/geopackage+sqlite3",
                        headers={**response_headers_base, "X-Cache": "HIT"},
                        # No background delete: this file IS the cache entry.
                    )
        except Exception as e:  # noqa: BLE001
            # Cache-lookup failures must never prevent serving the request.
            logger.warning(f"gpkg cache lookup skipped: {e}")
            cache_key = None

    # Cap concurrent heavy builds per worker. Each CONUS VPU subset peaks
    # at hundreds of MB of pandas/geopandas memory, so uncapped concurrency
    # can OOM the instance. ``admit()`` enforces queue-depth (429 fast-fail)
    # and timeout (503) in one step; shared with the param_metadata endpoint
    # so backlog accounting is correct across both heavy paths.
    slot = gpkg_limiter.admit(logger=logger, context=f"for {identifier}").__enter__()

    def _release_sem() -> None:
        slot.release()

    try:
        if namespace.is_nhf:
            if id_type == QueryIdType.VPU_ID:
                output_layers = subset_nhf(
                    vpu_id=identifier,
                    catalog=catalog,
                    namespace=namespace,
                )
            elif id_type == QueryIdType.FLOWPATH_ID:
                output_layers = subset_nhf(
                    flowpath_id=int(identifier),
                    catalog=catalog,
                    namespace=namespace,
                )
            elif id_type == QueryIdType.GAGE_ID:
                output_layers = subset_nhf(
                    gage_id=identifier,
                    catalog=catalog,
                    namespace=namespace,
                )
            else:
                raise ValueError(f"Incorrect ID type: {id_type} for the NHF")
        else:
            if id_type == QueryIdType.GAGE_ID:
                output_layers = subset_hydrofabric(
                    catalog=catalog,
                    identifier=f"gages-{identifier}",
                    id_type=IdType.HL_URI,
                    layers=layers or ["divides", "flowpaths", "network", "nexus"],
                    namespace=namespace,
                    graph=network_graphs[namespace],
                )
            elif id_type == QueryIdType.FLOWPATH_ID:
                output_layers = subset_hydrofabric(
                    catalog=catalog,
                    identifier=identifier,
                    id_type=IdType.ID,
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

        # Partition layers up front so we can pop + free as we write.
        # pyogrio handles spatial, sqlite handles tabular (incl. empty ones).
        spatial_names: list[str] = []
        nonspatial_names: list[str] = []
        for name, data in output_layers.items():
            if isinstance(data, gpd.GeoDataFrame) and len(data) > 0:
                spatial_names.append(name)
            elif not isinstance(data, gpd.GeoDataFrame):
                nonspatial_names.append(name)

        layers_written = 0

        # Stream spatial layers one at a time: pop -> write -> del. Refcounts
        # hit zero immediately so numpy/geopandas memory is freed without
        # needing gc.collect() between layers.
        for name in spatial_names:
            layer_data = output_layers.pop(name)
            n_rows = len(layer_data)
            pyogrio.write_dataframe(layer_data, tmp_path, layer=name)
            del layer_data
            layers_written += 1
            logger.info(f"Written spatial layer '{name}' with {n_rows} records")

        # Share one sqlite connection across tabular layers.
        if nonspatial_names:
            conn = sqlite3.connect(tmp_path)
            try:
                for name in nonspatial_names:
                    layer_data = output_layers.pop(name)
                    n_rows = len(layer_data)
                    layer_data.to_sql(name, conn, if_exists="replace", index=False)
                    del layer_data
                    layers_written += 1
                    logger.info(f"Written non-spatial layer '{name}' with {n_rows} records")
            finally:
                conn.close()

        # Single sweep at the end for any pandas/geopandas reference cycles.
        output_layers.clear()
        gc.collect()

        # Heavy work is done; release the slot before streaming to the client.
        _release_sem()

        if layers_written == 0:
            raise HTTPException(
                status_code=404, detail=f"No non-empty layers found for identifier '{identifier}'"
            )

        # Validate the freshly-built file BEFORE committing to cache — we
        # never want to cache garbage, and after os.replace() tmp_path no
        # longer exists so these checks must happen first.
        if not tmp_path.exists():
            raise HTTPException(status_code=500, detail="Failed to create geopackage file")
        if not tmp_path.is_file():
            raise HTTPException(status_code=500, detail="Expected file but got directory")
        if tmp_path.stat().st_size == 0:
            tmp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail="Created geopackage file is empty")

        # Install into the gpkg cache if available. os.replace() is atomic;
        # after commit, tmp_path no longer exists so BackgroundTask.unlink is
        # a no-op (safe via missing_ok=True).
        served_path = tmp_path
        cache_hit_header = "MISS"
        if gpkg_cache is not None and cache_key is not None:
            try:
                served_path = gpkg_cache.commit(cache_key, tmp_path)
                cache_hit_header = "STORE"
                logger.info(f"gpkg cache STORE: {cache_key[:12]}")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"gpkg cache store failed: {e}")

        logger.info(
            f"Successfully created geopackage: {served_path} (size: {served_path.stat().st_size} bytes)"
        )

        # If the file moved into the cache, don't delete it afterward.
        cleanup_path = tmp_path if served_path == tmp_path else None
        background = BackgroundTask(_cleanup_tmp, cleanup_path) if cleanup_path else None

        return FileResponse(
            path=str(served_path),
            filename=download_filename,
            media_type="application/geopackage+sqlite3",
            headers={
                **response_headers_base,
                "X-Layers-Count": str(layers_written),
                "X-Cache": cache_hit_header,
            },
            background=background,
        )

    except HTTPException:
        _cleanup_tmp(tmp_path)
        raise
    except FileNotFoundError as e:
        _cleanup_tmp(tmp_path)
        raise HTTPException(status_code=404, detail=f"Required file not found: {str(e)}") from None
    except NoResultsFoundError as e:
        _cleanup_tmp(tmp_path)
        raise HTTPException(status_code=404, detail=str(e)) from None
    except ValueError as e:
        _cleanup_tmp(tmp_path)
        if "No origin found" in str(e):
            raise HTTPException(
                status_code=404,
                detail=f"No origin found for {id_type.value}='{identifier}' in namespace '{namespace}'",
            ) from None
        else:
            raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}") from None
    finally:
        # Idempotent: no-op if already released on the happy path.
        _release_sem()


@api_router.get("/history", tags=["Hydrofabric Services"])
def get_hydrofabric_history(
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
