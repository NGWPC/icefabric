import pytest


@pytest.mark.slow
def test_subset_hl_uri_good(hydrofabric_client, gauge_hf_uri_good: str):
    """Test: /v1/hydrofabric/{gauge_hf_uri_good}/gpkg"""
    response = hydrofabric_client.get(
        f"/v1/hydrofabric/{gauge_hf_uri_good}/gpkg?id_type=hl_uri&domain=conus_hf&layers=divides&layers=flowpaths&layers=network&layers=nexus"
    )
    assert response.status_code == 200, f"Request failed with status {response.status_code}: {response.text}"


@pytest.mark.slow
def test_subset_hl_uri_bad(hydrofabric_client, gauge_hf_uri_bad: str):
    """Test: /v1/hydrofabric/{gauge_hf_uri_bad}/gpkg"""
    response = hydrofabric_client.get(
        f"/v1/hydrofabric/{gauge_hf_uri_bad}/gpkg?id_type=hl_uri&domain=conus_hf&layers=divides&layers=flowpaths&layers=network&layers=nexus"
    )
    assert response.status_code == 404, (
        f"Request did not fail as expected. Status: {response.status_code}: {response.text}"
    )


@pytest.mark.slow
def test_hl_history_good(hydrofabric_client):
    """Test: /v1/hydrofabric/history"""
    response = hydrofabric_client.get("/v1/hydrofabric/history?domain=conus_hf")
    assert response.status_code == 200, f"Request failed with status {response.status_code}: {response.text}"


@pytest.mark.slow
def test_hl_history_bad(hydrofabric_client):
    """Test: /v1/hydrofabric/history"""
    response = hydrofabric_client.get("/v1/hydrofabric/history?domain=prvi_hf")
    assert response.status_code == 404, (
        f"Request did not fail as expected. Status: {response.status_code}: {response.text}"
    )
