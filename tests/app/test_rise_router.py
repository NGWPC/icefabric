import json

import pytest

from app.routers.rise_wrappers.router import EXT_RISE_BASE_URL, make_get_req_to_rise

resources = ["catalog-item", "catalog-record", "location", "result"]

good_ids = ["10835", "4462", "3672", "3672"]

bad_ids = ["0", "0", "0", "0"]

RISE_TIMEOUT_CODE = 504


def _skip_if_rise_unavailable(response):
    """Skip the test if RISE API is down or timing out."""
    if response.status_code == RISE_TIMEOUT_CODE:
        pytest.skip("RISE API is unavailable (timeout)")


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("resource_type,id", list(zip(resources, good_ids, strict=False)))
async def test_get_item_by_id_good(client, resource_type, id):
    """Test all per-ID endpoints for IDs that exist"""
    response = client.get(f"/v1/rise/{resource_type}/{id}")
    _skip_if_rise_unavailable(response)
    assert response.status_code == 200
    rise_direct_response = await make_get_req_to_rise(f"{EXT_RISE_BASE_URL}/{resource_type}/{id}")
    assert json.loads(response.text) == rise_direct_response["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("resource_type,id", list(zip(resources, bad_ids, strict=False)))
async def test_get_item_by_id_bad(client, resource_type, id):
    """Test all per-ID endpoints for IDs that do not exist"""
    response = client.get(f"/v1/rise/{resource_type}/{id}")
    _skip_if_rise_unavailable(response)
    assert response.status_code == 404
    rise_direct_response = await make_get_req_to_rise(f"{EXT_RISE_BASE_URL}/{resource_type}/{id}")
    assert json.loads(response.text)["detail"] == rise_direct_response["detail"]


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("resource_type", resources)
async def test_get_collection(client, resource_type):
    """Test every resource collection endpoint - all default parameters"""
    # TODO - remove skip once the RISE api/result endpoint is no longer timing out
    if resource_type == "result":
        pytest.skip(f"Skipping {resource_type} endpoint test until RISE API endpoint stops timing out.")
    response = client.get(f"/v1/rise/{resource_type}")
    _skip_if_rise_unavailable(response)
    assert response.status_code == 200
    rise_direct_response = await make_get_req_to_rise(f"{EXT_RISE_BASE_URL}/{resource_type}")
    assert json.loads(response.text)["data"] == rise_direct_response["detail"]["data"]


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize("resource_type", resources)
async def test_get_collection_set_of_ids(client, resource_type):
    """Test every resource collection endpoint with a set of three IDs"""
    # TODO - remove skip once the RISE api/result endpoint is no longer timing out
    if resource_type == "result":
        pytest.skip(f"Skipping {resource_type} endpoint test until RISE API endpoint stops timing out.")
    response = client.get(f"/v1/rise/{resource_type}?id=3672,4462,10835")
    _skip_if_rise_unavailable(response)
    assert response.status_code == 200
    rise_direct_response = await make_get_req_to_rise(
        f"{EXT_RISE_BASE_URL}/{resource_type}?id=3672,4462,10835"
    )
    assert json.loads(response.text)["data"] == rise_direct_response["detail"]["data"]
