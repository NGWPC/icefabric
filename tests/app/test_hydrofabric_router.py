import pytest


@pytest.mark.slow
def test_subset_hl_uri(remote_client, gauge_hf_uri: str):
    """Test: GET /streamflow_observations/usgs/csv"""
    response = remote_client.get(
        f"/v1/hydrofabric/{gauge_hf_uri}/gpkg",
    )
    # Only checking assert since there are already tests in the tools
    assert response.status_code == 200, "Incorrect response"
