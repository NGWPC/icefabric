"""A file to assist with querying data from the RISE app"""

from typing import Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

from icefabric.schemas.rise_parameters import PARAM_CONV

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
    rise_response = {}
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


def make_sync_get_req_to_rise(full_url: str) -> dict[str, Any]:
    """
    Makes a synchronous GET request to the RISE API.

    Returns a response dict with the status code and the message body. If
    the response is an error from RISE, the original code and message is
    returned as well.

    Parameters
    ----------
    full_url : str
        The complete URL to make the GET request to

    Returns
    -------
    dict[str, Any]
        Dictionary containing 'status_code' and 'detail' keys
    """
    rise_response = {}
    try:
        rise_response = {"status_code": 200, "detail": ""}
        print(f"Making GET request to RISE (full URL): {full_url}")

        resp = httpx.get(full_url, headers=RISE_HEADERS, timeout=15)
        resp.raise_for_status()
        rise_response["detail"] = resp.json()
    except httpx.HTTPError as err:
        print(f"RISE API returned an HTTP error: {err}")
        rise_response["status_code"] = int(err.response.status_code)
        rise_response["detail"] = err.response.text
    return rise_response
