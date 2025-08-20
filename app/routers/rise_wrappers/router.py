from fastapi import APIRouter, Depends, HTTPException

from icefabric.helpers import (
    EXT_RISE_BASE_URL,
    basemodel_to_query_string,
    make_get_req_to_rise,
)
from icefabric.schemas import (
    CatItemParams,
    CatRecParams,
    LocItemParams,
)

api_router = APIRouter(prefix="/rise")


@api_router.get("/catalog-item", tags=["RISE"])
async def get_catalog_item(query: CatItemParams = Depends()):
    """Retrieves the collection of CatalogItem resources."""
    query_url_portion = basemodel_to_query_string(query)
    rise_response = await make_get_req_to_rise(f"{EXT_RISE_BASE_URL}/catalog-item{query_url_portion}")
    if rise_response["status_code"] != 200:
        raise HTTPException(**rise_response)
    else:
        return rise_response["detail"]


@api_router.get("/catalog-item/{id}", tags=["RISE"])
async def get_catalog_item_by_id(id: str):
    """Retrieves a CatalogItem resource, per a given ID."""
    rise_response = await make_get_req_to_rise(f"{EXT_RISE_BASE_URL}/catalog-item/{id}")
    if rise_response["status_code"] != 200:
        raise HTTPException(**rise_response)
    else:
        return rise_response["detail"]


@api_router.get("/catalog-record", tags=["RISE"])
async def get_catalog_record(query: CatRecParams = Depends()):
    """Retrieves the collection of CatalogRecord resources."""
    query_url_portion = basemodel_to_query_string(query)
    rise_response = await make_get_req_to_rise(f"{EXT_RISE_BASE_URL}/catalog-record{query_url_portion}")
    if rise_response["status_code"] != 200:
        raise HTTPException(**rise_response)
    else:
        return rise_response["detail"]


@api_router.get("/catalog-record/{id}", tags=["RISE"])
async def get_catalog_record_by_id(id: str):
    """Retrieves a CatalogRecord resource, per a given ID."""
    rise_response = await make_get_req_to_rise(f"{EXT_RISE_BASE_URL}/catalog-record/{id}")
    if rise_response["status_code"] != 200:
        raise HTTPException(**rise_response)
    else:
        return rise_response["detail"]


@api_router.get("/location", tags=["RISE"])
async def get_location(query: LocItemParams = Depends()):
    """Retrieves the collection of Location resources."""
    query_url_portion = basemodel_to_query_string(query)
    rise_response = await make_get_req_to_rise(f"{EXT_RISE_BASE_URL}/location{query_url_portion}")
    if rise_response["status_code"] != 200:
        raise HTTPException(**rise_response)
    else:
        return rise_response["detail"]


@api_router.get("/location/{id}", tags=["RISE"])
async def get_location_by_id(id: str):
    """Retrieves a Location resource, per a given ID."""
    rise_response = await make_get_req_to_rise(f"{EXT_RISE_BASE_URL}/location/{id}")
    if rise_response["status_code"] != 200:
        raise HTTPException(**rise_response)
    else:
        return rise_response["detail"]


# TODO - Restore endpoint once the RISE api/result endpoint is no longer timing out
# @api_router.get("/result", tags=["RISE"])
# async def get_result(query: ResParams = Depends()):
#     """Retrieves the collection of Result resources."""
#     query_url_portion = basemodel_to_query_string(query)
#     rise_response = await make_get_req_to_rise(f"{EXT_RISE_BASE_URL}/result{query_url_portion}")
#     if rise_response["status_code"] != 200:
#         raise HTTPException(**rise_response)
#     else:
#         return rise_response["detail"]


@api_router.get("/result/{id}", tags=["RISE"])
async def get_result_by_id(id: str):
    """Retrieves a Result resource, per a given ID."""
    rise_response = await make_get_req_to_rise(f"{EXT_RISE_BASE_URL}/result/{id}")
    if rise_response["status_code"] != 200:
        raise HTTPException(**rise_response)
    else:
        return rise_response["detail"]
