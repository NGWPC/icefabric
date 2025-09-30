import pytest


@pytest.mark.slow
def test_subset_hl_uri(client, gauge_ids: str):
    """Test: GET /streamflow_observations/usgs/csv"""
    response = client.get(
        f"/v1/hydrofabric/{gauge_ids}/gpkg",
    )
    # Only checking assert since there are already tests in the tools
    assert response.status_code == 200, "Incorrect response"
