import pytest


@pytest.mark.slow
def test_subset_hl_uri_good(client, watershed_bound_id_good: str):
    """Test: /v1/hydrofabric/{gauge_hf_uri_good}/gpkg"""
    response = client.get(
        f"/v1/hydrofabric/{watershed_bound_id_good}/gpkg?id_type=flowpath_id&domain=hi_hf&layers=divides&layers=flowpaths&layers=network&layers=nexus"
    )
    assert response.status_code == 200, f"Request failed with status {response.status_code}: {response.text}"


@pytest.mark.slow
def test_subset_hl_uri_bad(client, watershed_bound_id_bad: str):
    """Test: /v1/hydrofabric/{gauge_hf_uri_bad}/gpkg"""
    response = client.get(
        f"/v1/hydrofabric/{watershed_bound_id_bad}/gpkg?id_type=flowpath_id&domain=hi_hf&layers=divides&layers=flowpaths&layers=network&layers=nexus"
    )
    assert response.status_code == 404, (
        f"Request did not fail as expected. Status: {response.status_code}: {response.text}"
    )


@pytest.mark.slow
def test_hl_history_good(client):
    """Test: /v1/hydrofabric/history"""
    response = client.get("/v1/hydrofabric/history?domain=hi_hf")
    assert response.status_code == 200, f"Request failed with status {response.status_code}: {response.text}"


@pytest.mark.slow
def test_hl_history_bad(client):
    """Test: /v1/hydrofabric/history"""
    response = client.get("/v1/hydrofabric/history?domain=prvi_hf")
    assert response.status_code == 404, (
        f"Request did not fail as expected. Status: {response.status_code}: {response.text}"
    )
