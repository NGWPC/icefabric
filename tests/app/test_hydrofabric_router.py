import pytest


@pytest.mark.slow
def test_subset_hl_uri(remote_client, gauge_hf_uri: str):
    """Test: /v1/hydrofabric/{gauge_hf_uri}/gpkg"""
    response = remote_client.get(
        f"/v1/hydrofabric/{gauge_hf_uri}/gpkg?id_type=hl_uri&domain=conus_hf&layers=divides&layers=flowpaths&layers=network&layers=nexus"
    )

    assert response.status_code == 200, f"Request failed with status {response.status_code}: {response.text}"
