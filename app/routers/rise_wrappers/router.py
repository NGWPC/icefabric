from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.routers.rise_wrappers.rise_parameters import (
    PARAM_CONV,
    CatItemParams,
    CatRecParams,
    LocItemParams,
)

api_router = APIRouter(prefix="/rise")
EXT_RISE_BASE_URL = "https://data.usbr.gov/rise/api"
RISE_HEADERS = {"accept": "application/vnd.api+json"}


def basemodel_to_query_string(model: BaseModel) -> str:
    """
    Encodes a basemodel into the querying string portion of a GET request.

    Also uses the PARAM_CONV definition to convert parameter names that are
    invalid in python.
    """
    filtered_params = model.model_dump(exclude_none=True)
    for k in PARAM_CONV.keys():
        if k in filtered_params:
            filtered_params[PARAM_CONV[k]] = filtered_params.pop(k)
    q_str = urlencode(filtered_params)
    if q_str != "":
        q_str = f"?{q_str}"
    return q_str


async def make_get_req_to_rise(full_url: str):
    """
    Makes an asynchronous GET request to the RISE API.

    Returns a response dict with the status code and the message body. If
    the response is an error from RISE, the original code and message is
    returned as well.
    """
    async with httpx.AsyncClient() as client:
        try:
            rise_response = {"status_code": 200, "detail": ""}
            print(f"Making GET request to RISE (full URL): {full_url}")
            resp = await client.get(full_url, headers=RISE_HEADERS, timeout=15)
            resp.raise_for_status()
            rise_response["detail"] = resp.json()
        except httpx.HTTPError as err:
            print(f"RISE API returned an HTTP error: {err}")
            rise_response["status_code"] = int(err.response.status_code)
            rise_response["detail"] = err.response.text
        return rise_response


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
