import contextlib
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic.json_schema import SkipJsonSchema
from pyiceberg.catalog import Catalog

from app import (
    GpkgLimiter,
    get_cache_catalog,
    get_cached_namespaces,
    get_catalog,
    get_gpkg_limiter,
    get_graphs,
)
from icefabric.modules import SmpModules, config_mapper, get_parameter_metadata
from icefabric.schemas import GeographicDomain, HydrofabricNamespace, HydrofabricSource
from icefabric.schemas.modules import (
    CFE,
    LASAM,
    LSTM,
    SFT,
    SMP,
    UEB,
    NoahOwpModular,
    SacSma,
    Snow17,
    Topmodel,
    Topoflow,
    TRoute,
)

logger = logging.getLogger(__name__)


def _resolve_module_namespace(
    domain: GeographicDomain | SkipJsonSchema[None],
    source: HydrofabricSource | SkipJsonSchema[None],
) -> HydrofabricNamespace:
    """Resolve namespace for module endpoints with error handling."""
    try:
        return HydrofabricNamespace.resolve(domain, source)
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


sft_router = APIRouter(prefix="/modules/sft")
snow17_router = APIRouter(prefix="/modules/snow17")
smp_router = APIRouter(prefix="/modules/smp")
lstm_router = APIRouter(prefix="/modules/lstm")
lasam_router = APIRouter(prefix="/modules/lasam")
noahowp_router = APIRouter(prefix="/modules/noahowp")
sacsma_router = APIRouter(prefix="/modules/sacsma")
troute_router = APIRouter(prefix="/modules/troute")
topmodel_router = APIRouter(prefix="/modules/topmodel")
topoflow_router = APIRouter(prefix="/modules/topoflow")
ueb_router = APIRouter(prefix="/modules/ueb")
cfe_router = APIRouter(prefix="/modules/cfe")
parameter_metadata_router = APIRouter(prefix="/modules/parameter_metadata")


@sft_router.get("/", tags=["NWM Modules"])
def get_sft_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    use_schaake: bool = Query(
        False,
        description="Whether to use Schaake for the Ice Fraction Scheme. Defaults to False to use Xinanjiang",
        openapi_examples={"sft_example": {"summary": "SFT Example", "value": False}},
    ),
    catalog: Catalog = Depends(get_catalog),
    network_graphs=Depends(get_graphs),
) -> list[SFT]:
    """
    An endpoint to return configurations for SFT.

    This endpoint traces upstream from a given gage ID to get all catchments
    and returns SFT (Soil Freeze-Thaw) parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gage ID to trace upstream from to get all catchments
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain to search for catchments from
    - **use_schaake**: Determines if we're using Schaake or Xinanjiang to calculate ice fraction

    **Returns:**
    A list of SFT pydantic objects for each catchment
    """
    namespace = _resolve_module_namespace(domain, source)

    # For HF v2.2 domains, prefix identifier with "gages-" and get graph
    if not namespace.is_nhf:
        formatted_identifier = f"gages-{identifier}"
        graph = network_graphs[namespace]
    else:
        formatted_identifier = identifier
        graph = None

    return config_mapper["sft"](
        catalog=catalog,
        namespace=namespace,
        identifier=formatted_identifier,
        graph=graph,
        use_schaake=use_schaake,
    )


@snow17_router.get("/", tags=["NWM Modules"])
def get_snow17_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    envca: bool = Query(
        False,
        description="If source is ENVCA, then set to True. Defaults to False.",
        openapi_examples={"sft_example": {"summary": "SNOW-17 Example", "value": False}},
    ),
    catalog: Catalog = Depends(get_catalog),
    network_graphs=Depends(get_graphs),
) -> list[Snow17]:
    """
    An endpoint to return configurations for SNOW-17.

    This endpoint traces upstream from a given gage ID to get all catchments
    and returns SNOW-17 (Snow Accumulation and Ablation Model) parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gage ID from which upstream catchments are traced.
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain used to filter catchments.
    - **envca**: Designates that the source is ENVCA.

    **Returns:**
    A list of SNOW-17 pydantic objects for each catchment.
    """
    namespace = _resolve_module_namespace(domain, source)

    if not namespace.is_nhf:
        formatted_identifier = f"gages-{identifier}"
        graph = network_graphs[namespace]
    else:
        formatted_identifier = identifier
        graph = None

    return config_mapper["snow17"](
        catalog=catalog,
        namespace=namespace,
        identifier=formatted_identifier,
        graph=graph,
        envca=envca,
    )


@smp_router.get("/", tags=["NWM Modules"])
def get_smp_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    module: SmpModules = Query(
        None,
        description="A setting to determine if a module should be specified to obtain additional SMP parameters.",
        openapi_examples={"smp_example": {"summary": "SMP Example", "value": None}},
    ),
    catalog: Catalog = Depends(get_catalog),
    network_graphs=Depends(get_graphs),
) -> list[SMP]:
    """
    An endpoint to return configurations for SMP.

    This endpoint traces upstream from a given gage ID to get all catchments
    and returns SMP (Soil Moisture Profile) parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gage ID from which upstream catchments are traced.
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain used to filter catchments.
    - **module**: Denotes if another module should be used to obtain additional SMP parameters. Confined to certain modules.

    **Returns:**
    A list of SMP pydantic objects for each catchment.
    """
    namespace = _resolve_module_namespace(domain, source)

    if not namespace.is_nhf:
        formatted_identifier = f"gages-{identifier}"
        graph = network_graphs[namespace]
    else:
        formatted_identifier = identifier
        graph = None

    return config_mapper["smp"](
        catalog=catalog,
        namespace=namespace,
        identifier=formatted_identifier,
        graph=graph,
        extra_module=module,
    )


@lstm_router.get("/", tags=["NWM Modules"])
def get_lstm_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    catalog: Catalog = Depends(get_catalog),
    network_graphs=Depends(get_graphs),
) -> list[LSTM]:
    """
    An endpoint to return configurations for LSTM.

    This endpoint traces upstream from a given gage ID to get all catchments
    and returns LSTM (Long Short-Term Memory) parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gage ID from which upstream catchments are traced.
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain used to filter catchments.

    **Returns:**
    A list of LSTM pydantic objects for each catchment.
    """
    namespace = _resolve_module_namespace(domain, source)

    if not namespace.is_nhf:
        formatted_identifier = f"gages-{identifier}"
        graph = network_graphs[namespace]
    else:
        formatted_identifier = identifier
        graph = None

    return config_mapper["lstm"](
        catalog=catalog,
        namespace=namespace,
        identifier=formatted_identifier,
        graph=graph,
    )


@lasam_router.get("/", tags=["NWM Modules"])
def get_lasam_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    sft_included: bool = Query(
        False,
        description='True if SFT is in the "dep_modules_included" definition as declared in HF API repo.',
        openapi_examples={"lasam_example": {"summary": "LASAM Example", "value": False}},
    ),
    soil_params_file: str = Query(
        "vG_default_params_HYDRUS.dat",
        description="Name of the Van Genuchton soil parameters file. Note: This is the filename that gets returned by HF API's utility script get_hydrus_data().",
        openapi_examples={
            "lasam_example": {"summary": "LASAM Example", "value": "vG_default_params_HYDRUS.dat"}
        },
    ),
    catalog: Catalog = Depends(get_catalog),
    network_graphs=Depends(get_graphs),
) -> list[LASAM]:
    r"""
    An endpoint to return configurations for LASAM.

    This endpoint traces upstream from a given gage ID to get all catchments
    and returns LASAM (Lumped Arid/Semi-arid Model) parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gage ID from which upstream catchments are traced.
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain used to filter catchments.
    - **sft_included**: Denotes that SFT is in the \"dep_modules_included\" definition as declared in the HF API repo.
    - **soil_params_file**: Name of the Van Genuchton soil parameters file.

    **Returns:**
    A list of LASAM pydantic objects for each catchment.
    """
    namespace = _resolve_module_namespace(domain, source)

    if not namespace.is_nhf:
        formatted_identifier = f"gages-{identifier}"
        graph = network_graphs[namespace]
    else:
        formatted_identifier = identifier
        graph = None

    return config_mapper["lasam"](
        catalog=catalog,
        namespace=namespace,
        identifier=formatted_identifier,
        graph=graph,
        sft_included=sft_included,
        soil_params_file=soil_params_file,
    )


@noahowp_router.get("/", tags=["NWM Modules"])
def get_noahowp_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    catalog: Catalog = Depends(get_catalog),
    network_graphs=Depends(get_graphs),
) -> list[NoahOwpModular]:
    """
    An endpoint to return configurations for Noah-OWP-Modular.

    This endpoint traces upstream from a given gage ID to get all catchments
    and returns Noah-OWP-Modular parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gage ID from which upstream catchments are traced.
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain used to filter catchments.

    **Returns:**
    A list of Noah-OWP-Modular pydantic objects for each catchment.
    """
    namespace = _resolve_module_namespace(domain, source)

    if not namespace.is_nhf:
        formatted_identifier = f"gages-{identifier}"
        graph = network_graphs[namespace]
    else:
        formatted_identifier = identifier
        graph = None

    return config_mapper["noah_owp"](
        catalog=catalog,
        namespace=namespace,
        identifier=formatted_identifier,
        graph=graph,
    )


@sacsma_router.get("/", tags=["NWM Modules"])
def get_sacsma_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    envca: bool = Query(
        False,
        description="If source is ENVCA, then set to True. Defaults to False.",
        openapi_examples={"sacsma_example": {"summary": "SAC-SMA Example", "value": False}},
    ),
    catalog: Catalog = Depends(get_catalog),
    network_graphs=Depends(get_graphs),
) -> list[SacSma]:
    """
    An endpoint to return configurations for SAC-SMA.

    This endpoint traces upstream from a given gage ID to get all catchments
    and returns SAC-SMA (Sacramento Soil Moisture Accounting) parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gage ID from which upstream catchments are traced.
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain used to filter catchments.
    - **envca**: Designates that the source is ENVCA.

    **Returns:**
    A list of SAC-SMA pydantic objects for each catchment.
    """
    namespace = _resolve_module_namespace(domain, source)

    if not namespace.is_nhf:
        formatted_identifier = f"gages-{identifier}"
        graph = network_graphs[namespace]
    else:
        formatted_identifier = identifier
        graph = None

    return config_mapper["sacsma"](
        catalog=catalog,
        namespace=namespace,
        identifier=formatted_identifier,
        graph=graph,
        envca=envca,
    )


@troute_router.get("/", tags=["NWM Modules"])
def get_troute_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    catalog: Catalog = Depends(get_catalog),
    network_graphs=Depends(get_graphs),
) -> list[TRoute]:
    """
    An endpoint to return configurations for T-Route.

    This endpoint traces upstream from a given gage ID to get all catchments
    and returns T-Route (Tree-Based Channel Routing) parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gage ID from which upstream catchments are traced.
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain used to filter catchments.

    **Returns:**
    A list of T-Route pydantic objects for each catchment.
    """
    namespace = _resolve_module_namespace(domain, source)

    if not namespace.is_nhf:
        formatted_identifier = f"gages-{identifier}"
        graph = network_graphs[namespace]
    else:
        formatted_identifier = identifier
        graph = None

    return config_mapper["troute"](
        catalog=catalog,
        namespace=namespace,
        identifier=formatted_identifier,
        graph=graph,
    )


@topmodel_router.get("/", tags=["NWM Modules"])
def get_topmodel_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    catalog: Catalog = Depends(get_catalog),
    network_graphs=Depends(get_graphs),
) -> list[Topmodel]:
    """
    An endpoint to return configurations for TOPMODEL.

    This endpoint traces upstream from a given gage ID to get all catchments
    and returns TOPMODEL parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gage ID from which upstream catchments are traced.
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain used to filter catchments.

    **Returns:**
    A list of TOPMODEL pydantic objects for each catchment.
    """
    namespace = _resolve_module_namespace(domain, source)

    if not namespace.is_nhf:
        formatted_identifier = f"gages-{identifier}"
        graph = network_graphs[namespace]
    else:
        formatted_identifier = identifier
        graph = None

    return config_mapper["topmodel"](
        catalog=catalog,
        namespace=namespace,
        identifier=formatted_identifier,
        graph=graph,
    )


@topoflow_router.get("/", tags=["NWM Modules"])
def get_topoflow_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    catalog: Catalog = Depends(get_catalog),
    network_graphs=Depends(get_graphs),
) -> list[Topoflow]:
    """
    An endpoint to return configurations for TopoFlow.

    This endpoint traces upstream from a given gage ID to get all catchments
    and returns TopoFlow parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gage ID from which upstream catchments are traced.
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain used to filter catchments.

    **Returns:**
    A list of TopoFlow pydantic objects for each catchment.
    """
    namespace = _resolve_module_namespace(domain, source)

    if not namespace.is_nhf:
        formatted_identifier = f"gages-{identifier}"
        graph = network_graphs[namespace]
    else:
        formatted_identifier = identifier
        graph = None

    return config_mapper["topoflow"](
        catalog=catalog,
        namespace=namespace,
        identifier=formatted_identifier,
        graph=graph,
    )


'''
@topoflow_router.get("/albedo", tags=["NWM Modules"])
def get_albedo(
    landcover_state: Albedo = Query(
        ...,
        description="The landcover state of a catchment for albedo classification",
        examples=["snow"],
        openapi_examples={"albedo_example": {"summary": "Albedo Example", "value": "snow"}},
    ),
) -> float:
    """
    An endpoint to return albedo values for TopoFlow Glacier module.

    This endpoint matches a catchment's land cover class ("snow", "ice", "other) with an albedo value [0, 1]

    **Parameters:**
    - **landcover_state**: Land cover state: "snow", "ice", or "other"

    **Returns:**
    A float albedo value [0, 1]
    """
    return Albedo.get_landcover_albedo(landcover_state.landcover).value
'''


@ueb_router.get("/", tags=["NWM Modules"])
def get_ueb_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    envca: bool = Query(
        False,
        description="If source is ENVCA, then set to True. Defaults to False.",
        openapi_examples={"ueb_example": {"summary": "UEB Example", "value": False}},
    ),
    catalog: Catalog = Depends(get_catalog),
    network_graphs=Depends(get_graphs),
) -> list[UEB]:
    """
    An endpoint to return configurations for UEB.

    This endpoint traces upstream from a given gage ID to get all catchments
    and returns UEB parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gage ID from which upstream catchments are traced.
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain used to filter catchments.
    - **envca**:  Designates that the source is ENVCA.

    **Returns:**
    A list of UEB pydantic objects for each catchment.
    """
    namespace = _resolve_module_namespace(domain, source)

    if not namespace.is_nhf:
        formatted_identifier = f"gages-{identifier}"
        graph = network_graphs[namespace]
    else:
        formatted_identifier = identifier
        graph = None

    return config_mapper["ueb"](
        catalog=catalog,
        namespace=namespace,
        identifier=formatted_identifier,
        graph=graph,
        envca=envca,
    )


@cfe_router.get("/", tags=["NWM Modules"])
def get_cfe_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    cfe_version: str = Query(
        ...,
        description="Select which version of CFE to use: CFE-S or CFE-X.",
        openapi_examples={"cfe_example": {"summary": "CFE Example", "value": "CFE-S"}},
    ),
    sft_included: bool = Query(
        False,
        description="True if SFT is in the 'dep_modules_included' definition as declared in HF API repo.",
        openapi_examples={"cfe_example": {"summary": "CFE Example", "value": False}},
    ),
    rootzone_aet: bool = Query(
        False,
        description="Turn on rootzone AET",
        openapi_examples={"cfe_example": {"summary": "CFE Example", "value": False}},
    ),
    catalog: Catalog = Depends(get_catalog),
    network_graphs=Depends(get_graphs),
) -> list[CFE]:
    """
    An endpoint to return configurations for CFE.

    This endpoint traces upstream from a given gage ID to get all catchments
    and returns CFE parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gage ID from which upstream catchments are traced.
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain used to filter catchments.
    - **cfe_version**:  Select which version of CFE to use: CFE-S or CFE-X.
    - **sft_included**: True if SFT is in the 'dep_modules_included' definition as declared in HF API repo.
    - **rootzone_aet**: Turn on rootzone AET if True.

    **Returns:**
    A list of CFE pydantic objects for each catchment.
    """
    namespace = _resolve_module_namespace(domain, source)

    if not namespace.is_nhf:
        formatted_identifier = f"gages-{identifier}"
        graph = network_graphs[namespace]
    else:
        formatted_identifier = identifier
        graph = None

    return config_mapper["cfe"](
        catalog=catalog,
        namespace=namespace,
        identifier=formatted_identifier,
        graph=graph,
        cfe_version=cfe_version,
        sft_included=sft_included,
        rootzone_aet=rootzone_aet,
    )


@parameter_metadata_router.get("/", tags=["NWM Modules"])
def get_calibratable_parameter_metadata(
    modules: list[str] = Query(
        ...,
        description="module name",
        openapi_examples={
            "CFE-S": {"summary": "CFE-S", "value": "CFE-S"},
            "CFE-X": {"summary": "CFE-X", "value": "CFE-X"},
            "LASAM": {"summary": "LASAM", "value": "LASAM"},
            "LSTM": {"summary": "LSTM", "value": "LSTM"},
            "Noah-OWP-Modular": {"summary": "Noah-OWP-Modular", "value": "Noah-OWP-Modular"},
            "PET": {"summary": "PET", "value": "PET"},
            "Sac-SMA": {"summary": "Sac-SMA", "value": "Sac-SMA"},
            "SFT": {"summary": "SFT", "value": "SFT"},
            "SMP": {"summary": "SMP", "value": "SMP"},
            "Snow-17": {"summary": "Snow-17", "value": "Snow-17"},
            "T-Route": {"summary": "T-Route", "value": "T-Route"},
            "TopModel": {"summary": "TopModel", "value": "TopModel"},
            "Topoflow-Glacier": {"summary": "Topoflow-Glacier", "value": "Topoflow-Glacier"},
            "UEB": {"summary": "UEB", "value": "UEB"},
        },
    ),
    gage_id: str = Query(
        None,
        description="Gage ID for averaging calibratable parameter values over all catchments in the subset.",
        examples=["01010000"],
        openapi_examples={"Sample Gage": {"summary": "Sample Gage", "value": "01010000"}},
    ),
    source: HydrofabricSource | SkipJsonSchema[None] = Query(
        None,
        description="Hydrofabric source: 'nhf' (National Hydrofabric) or 'hf' (Hydrofabric v2.2). "
        "Required when using geographic domain names.",
    ),
    domain: GeographicDomain | SkipJsonSchema[None] = Query(
        None,
        description="Geographic domain (CONUS, Alaska, Hawaii, Puerto_Rico, Great_Lakes) with source param, "
        "or legacy values (nhf, conus_hf, etc.) for backwards compatibility.",
    ),
    catalog: Catalog = Depends(get_catalog),
    cache_catalog: Catalog = Depends(get_cache_catalog),
    cached_namespaces=Depends(get_cached_namespaces),
    network_graphs=Depends(get_graphs),
    gpkg_limiter: GpkgLimiter = Depends(get_gpkg_limiter),
):
    """
    An endpoint to return calibratable parameter metadata for a module.

    **Parameters:**
    - **modules**: a list of modules.
    - **gage_id**: The Gage ID for averaging calibratable parameter values over all catchments in the subset.
    - **source**: Hydrofabric source ('nhf' or 'hf')
    - **domain**: The geographic domain to search for catchments from.

    **Returns:**
    A JSON containing metadata for a module's calibratable parameters.
    """
    # Map the NWM module names to the icefabric module names
    nwm_icefabric_module_mapping = {
        "CFE-S": "cfe-s",
        "CFE-X": "cfe-x",
        "LASAM": "lasam",
        "LSTM": "lstm",
        "Noah-OWP-Modular": "noahowp",
        "PET": "pet",
        "Sac-SMA": "sacsma",
        "SFT": "sft",
        "SMP": "smp",
        "Snow-17": "snow17",
        "T-Route": "troute",
        "TopModel": "topmodel",
        "Topoflow-Glacier": "topoflow",
        "UEB": "ueb",
    }

    # Map the icefabric module names back to the NWM module names
    icefabric_nwm_module_mapping = {
        "cfe-s": "CFE-S",
        "cfe-x": "CFE-X",
        "lasam": "LASAM",
        "lstm": "LSTM",
        "noahowp": "Noah-OWP-Modular",
        "pet": "PET",
        "sacsma": "Sac-SMA",
        "sft": "SFT",
        "smp": "SMP",
        "snow17": "Snow-17",
        "troute": "T-Route",
        "topmodel": "TopModel",
        "topoflow": "Topoflow-Glacier",
        "ueb": "UEB",
    }
    modules = [nwm_icefabric_module_mapping.get(mod, mod) for mod in modules]

    # Resolve namespace - for parameter_metadata, gage_id is optional
    # If gage_id is provided along with domain/source, resolve the namespace
    namespace = None
    graph = None
    formatted_gage_id = gage_id

    if gage_id and (domain is not None or source is not None):
        namespace = _resolve_module_namespace(domain, source)
        if not namespace.is_nhf:
            formatted_gage_id = f"gages-{gage_id}"
            graph = network_graphs[namespace]
    elif domain is not None:
        # Legacy mode - domain only without source
        namespace = _resolve_module_namespace(domain, source)
        if not namespace.is_nhf and gage_id:
            formatted_gage_id = f"gages-{gage_id}"
            graph = network_graphs[namespace]

    # Use cache catalog if parameter_metadata namespace is cached
    active_catalog = (
        cache_catalog
        if "parameter_metadata" in cached_namespaces and namespace in cached_namespaces
        else catalog
    )

    # With gage_id, runs same hydrofabric subset as /gpkg -> share the
    # limiter (concurrency cap + queue-depth admission + timeout) so a
    # burst of param_metadata requests can't starve the /gpkg endpoint
    # (or vice versa). Cheap metadata-only calls (no gage_id) skip admission.
    needs_subset = formatted_gage_id is not None
    admission = (
        gpkg_limiter.admit(logger=logger, context=f"for gage {gage_id}")
        if needs_subset
        else contextlib.nullcontext()
    )
    with admission:
        parameter_metadata = get_parameter_metadata(
            modules=modules,
            catalog=active_catalog,
            gage_id=formatted_gage_id,
            domain=namespace,
            graph=graph,
        )

    for module in parameter_metadata:
        module_name = module["module_name"]
        NWM_module_name = icefabric_nwm_module_mapping.get(module_name, module_name)
        module["module_name"] = NWM_module_name

    return {"modules": parameter_metadata}
