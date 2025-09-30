from fastapi import APIRouter, Depends, Query
from pyiceberg.catalog import Catalog

from app import get_catalog
from icefabric.modules import get_sft_parameters
from icefabric.schemas import SFT, Albedo, HydrofabricDomains

sft_router = APIRouter(prefix="/modules/sft")
topoflow_router = APIRouter(prefix="/modules/topoflow")


@sft_router.get("/")
async def get_sft_ipes(
    identifier: str = Query(
        ...,
        description="Gauge ID to trace upstream catchments from",
        examples=["01010000"],
        openapi_examples={"sft_example": {"summary": "SFT Example", "value": "01010000"}},
    ),
    domain: HydrofabricDomains = Query(
        HydrofabricDomains.CONUS,
        description="The iceberg namespace used to query the hydrofabric",
        openapi_examples={"sft_example": {"summary": "SFT Example", "value": "conus_hf"}},
    ),
    use_schaake: bool = Query(
        False,
        description="Whether to use Schaake for the Ice Fraction Scheme. Defaults to False to use Xinanjiang",
        openapi_examples={"sft_example": {"summary": "SFT Example", "value": False}},
    ),
    catalog: Catalog = Depends(get_catalog),
) -> list[SFT]:
    """
    An endpoint to return configurations for SFT.

    This endpoint traces upstream from a given gauge ID to get all catchments
    and returns SFT (Soil Freeze-Thaw) parameter configurations for each catchment.

    **Parameters:**
    - **identifier**: The Gauge ID to trace upstream from to get all catchments
    - **domain**: The geographic domain to search for catchments from
    - **use_schaake**: Determines if we're using Schaake or Xinanjiang to calculate ice fraction

    **Returns:**
    A list of SFT pydantic objects for each catchment
    """
    return get_sft_parameters(
        catalog=catalog,
        domain=domain,
        identifier=identifier,
        use_schaake=use_schaake,
    )


@topoflow_router.get("/albedo")
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
