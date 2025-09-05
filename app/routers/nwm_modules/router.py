from fastapi import APIRouter, Depends, Query
from pyiceberg.catalog import Catalog

from app import get_catalog, get_graphs
from icefabric.modules import SmpModules, config_mapper
from icefabric.schemas import HydrofabricDomains
from icefabric.schemas.modules import (
    Albedo,
    LASAM,
    LSTM,
    NoahOwpModular,
    SacSma,
    SFT,
    SMP,
    Snow17,
    Topmodel,
    TRoute,
)

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


@sft_router.get("/", tags=["HF Modules"])
async def get_sft_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"sft_example": {"summary": "SFT Example", "value": "01010000"}},
    ),
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS,
        description="The iceberg namespace used to query the hydrofabric.",
        openapi_examples={"sft_example": {"summary": "SFT Example", "value": "conus_hf"}},
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
    - **domain**: The geographic domain to search for catchments from
    - **use_schaake**: Determines if we're using Schaake or Xinanjiang to calculate ice fraction

    **Returns:**
    A list of SFT pydantic objects for each catchment
    """
    return config_mapper["sft"](
        catalog=catalog,
        namespace=domain.value,
        identifier=f"gages-{identifier}",
        graph=network_graphs[domain],
        use_schaake=use_schaake,
    )


@snow17_router.get("/", tags=["NWM Modules"])
async def get_snow17_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"snow17_example": {"summary": "SNOW-17 Example", "value": "01010000"}},
    ),
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS,
        description="The iceberg namespace used to query the hydrofabric.",
        openapi_examples={"snow17_example": {"summary": "SNOW-17 Example", "value": "conus_hf"}},
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
    - **domain**: The geographic domain used to filter catchments.
    - **envca**: Designates that the source is ENVCA.

    **Returns:**
    A list of SNOW-17 pydantic objects for each catchment.
    """
    return config_mapper["snow17"](
        catalog=catalog,
        namespace=domain.value,
        identifier=f"gages-{identifier}",
        graph=network_graphs[domain],
        envca=envca,
    )


@smp_router.get("/", tags=["NWM Modules"])
async def get_smp_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"smp_example": {"summary": "SMP Example", "value": "01010000"}},
    ),
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS,
        description="The iceberg namespace used to query the hydrofabric.",
        openapi_examples={"smp_example": {"summary": "SMP Example", "value": "conus_hf"}},
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
    - **domain**: The geographic domain used to filter catchments.
    - **module**: Denotes if another module should be used to obtain additional SMP parameters. Confined to certain modules.

    **Returns:**
    A list of SMP pydantic objects for each catchment.
    """
    return config_mapper["smp"](
        catalog=catalog,
        namespace=domain.value,
        identifier=f"gages-{identifier}",
        graph=network_graphs[domain],
        module=module,
    )


@lstm_router.get("/", tags=["NWM Modules"])
async def get_lstm_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"lstm_example": {"summary": "LSTM Example", "value": "01010000"}},
    ),
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS,
        description="The iceberg namespace used to query the hydrofabric.",
        openapi_examples={"lstm_example": {"summary": "LSTM Example", "value": "conus_hf"}},
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
    - **domain**: The geographic domain used to filter catchments.

    **Returns:**
    A list of LSTM pydantic objects for each catchment.
    """
    return config_mapper["lstm"](
        catalog=catalog,
        namespace=domain.value,
        identifier=f"gages-{identifier}",
        graph=network_graphs[domain],
    )


@lasam_router.get("/", tags=["NWM Modules"])
async def get_lasam_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"lasam_example": {"summary": "LASAM Example", "value": "01010000"}},
    ),
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS,
        description="The iceberg namespace used to query the hydrofabric.",
        openapi_examples={"lasam_example": {"summary": "LASAM Example", "value": "conus_hf"}},
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
    - **domain**: The geographic domain used to filter catchments.
    - **sft_included**: Denotes that SFT is in the \"dep_modules_included\" definition as declared in the HF API repo.
    - **soil_params_file**: Name of the Van Genuchton soil parameters file.

    **Returns:**
    A list of LASAM pydantic objects for each catchment.
    """
    return config_mapper["lasam"](
        catalog=catalog,
        namespace=domain.value,
        identifier=f"gages-{identifier}",
        graph=network_graphs[domain],
        sft_included=sft_included,
        soil_params_file=soil_params_file,
    )


@noahowp_router.get("/", tags=["NWM Modules"])
async def get_noahowp_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"noahowp_example": {"summary": "Noah-OWP-Modular Example", "value": "01010000"}},
    ),
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS,
        description="The iceberg namespace used to query the hydrofabric.",
        openapi_examples={"noahowp_example": {"summary": "Noah-OWP-Modular Example", "value": "conus_hf"}},
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
    - **domain**: The geographic domain used to filter catchments.

    **Returns:**
    A list of Noah-OWP-Modular pydantic objects for each catchment.
    """
    return config_mapper["noah_owp"](
        catalog=catalog,
        namespace=domain.value,
        identifier=f"gages-{identifier}",
        graph=network_graphs[domain],
    )


@sacsma_router.get("/", tags=["NWM Modules"])
async def get_sacsma_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"sacsma_example": {"summary": "SAC-SMA Example", "value": "01010000"}},
    ),
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS,
        description="The iceberg namespace used to query the hydrofabric.",
        openapi_examples={"sacsma_example": {"summary": "SAC-SMA Example", "value": "conus_hf"}},
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
    - **domain**: The geographic domain used to filter catchments.
    - **envca**: Designates that the source is ENVCA.

    **Returns:**
    A list of SAC-SMA pydantic objects for each catchment.
    """
    return config_mapper["sacsma"](
        catalog=catalog,
        namespace=domain.value,
        identifier=f"gages-{identifier}",
        graph=network_graphs[domain],
        envca=envca,
    )


@troute_router.get("/", tags=["NWM Modules"])
async def get_troute_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"troute_example": {"summary": "T-Route Example", "value": "01010000"}},
    ),
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS,
        description="The iceberg namespace used to query the hydrofabric.",
        openapi_examples={"troute_example": {"summary": "T-Route Example", "value": "conus_hf"}},
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
    - **domain**: The geographic domain used to filter catchments.

    **Returns:**
    A list of T-Route pydantic objects for each catchment.
    """
    return config_mapper["troute"](
        catalog=catalog,
        namespace=domain.value,
        identifier=f"gages-{identifier}",
        graph=network_graphs[domain],
    )


@topmodel_router.get("/", tags=["NWM Modules"])
async def get_topmodel_ipes(
    identifier: str = Query(
        ...,
        description="Gage ID from which to trace upstream catchments.",
        examples=["01010000"],
        openapi_examples={"topmodel_example": {"summary": "TOPMODEL Example", "value": "01010000"}},
    ),
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS,
        description="The iceberg namespace used to query the hydrofabric.",
        openapi_examples={"topmodel_example": {"summary": "TOPMODEL Example", "value": "conus_hf"}},
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
    - **domain**: The geographic domain used to filter catchments.

    **Returns:**
    A list of TOPMODEL pydantic objects for each catchment.
    """
    return config_mapper["topmodel"](
        catalog=catalog,
        namespace=domain.value,
        identifier=f"gages-{identifier}",
        graph=network_graphs[domain],
    )


# TODO - Restore endpoint once the generation of IPEs for TopoFlow is possible/implemented
# @topoflow_router.get("/", tags=["NWM Modules"])
# async def get_topoflow_ipes(
#     identifier: str = Query(
#         ...,
#         description="Gage ID from which to trace upstream catchments.",
#         examples=["01010000"],
#         openapi_examples={"topoflow_example": {"summary": "TopoFlow Example", "value": "01010000"}},
#     ),
#     domain: HydrofabricDomains = Query(
#         HydrofabricDomains.CONUS,
#         description="The iceberg namespace used to query the hydrofabric.",
#         openapi_examples={"topoflow_example": {"summary": "TopoFlow Example", "value": "conus_hf"}},
#     ),
#     catalog: Catalog = Depends(get_catalog),
# ) -> list[Topoflow]:
#     """
#     An endpoint to return configurations for TopoFlow.
#
#     This endpoint traces upstream from a given gage ID to get all catchments
#     and returns TopoFlow parameter configurations for each catchment.
#
#     **Parameters:**
#     - **identifier**: The Gage ID from which upstream catchments are traced.
#     - **domain**: The geographic domain used to filter catchments.
#
#     **Returns:**
#     A list of TopoFlow pydantic objects for each catchment.
#     """
#     return config_mapper["topoflow"](
#         catalog=catalog,
#         namespace=domain.value,
#         identifier=f"gages-{identifier}",
#         graph=network_graphs[domain],
#     )


@topoflow_router.get("/albedo", tags=["NWM Modules"])
async def get_albedo(
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
