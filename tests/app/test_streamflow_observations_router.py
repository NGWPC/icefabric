from io import StringIO

import pandas as pd
import pytest


@pytest.mark.integration
def test_available_endpoint(mock_streamflow_api, client):
    """Test: GET /streamflow_observations/available"""
    response = client.get("/v1/streamflow_observations/available?limit=50")

    assert response.status_code == 200
    data = response.json()
    assert "repo" in data
    assert "description" in data
    assert "units" in data
    assert "total_identifiers" in data
    assert "identifiers" in data
    assert len(data["identifiers"]) <= 50
    mock_streamflow_api.assert_called_once()


@pytest.mark.integration
def test_history_endpoint(mock_streamflow_api, client):
    """Test: GET /streamflow_observations/history"""
    response = client.get("/v1/streamflow_observations/history")

    assert response.status_code == 200
    data = response.json()
    assert "repo" in data
    assert "description" in data
    assert "units" in data
    assert "latest_snapshot" in data
    assert "snapshots" in data
    assert len(data["snapshots"]) >= 1
    assert ["snapshot_id", "commit_message", "timestamp"] == list(data["snapshots"][0].keys())
    mock_streamflow_api.assert_called_once()


@pytest.mark.integration
def test_info_endpoint(mock_streamflow_api, client):
    """Test: GET /streamflow_observations/{identifier}/info"""
    response = client.get("/v1/streamflow_observations/01010000/info")

    assert response.status_code == 200
    data = response.json()
    assert data["repo"] == "hourly_streamflow_observations"
    assert "description" in data
    assert "units" in data
    assert data["identifier"] == "01010000"
    assert isinstance(data["total_records"], int)
    assert "date_range" in data
    assert "estimated_sizes" in data
    mock_streamflow_api.assert_called_once()


@pytest.mark.integration
def test_observation_endpoint(mock_streamflow_cli, local_usgs_streamflow_csv, client):
    """Test: GET /streamflow_observations/{identifier}/"""
    response = client.get(
        "/v1/streamflow_observations/01031500/csv",
        params={
            "start_date": "2021-12-31T14:00:00",
            "end_date": "2022-01-01T14:00:00",
            "include_headers": True,
        },
    )

    assert response.status_code == 200
    df = pd.read_csv(StringIO(response.text))
    assert local_usgs_streamflow_csv.equals(df)
    mock_streamflow_cli.assert_called_once()


# NOTE: To be updated in next test PR. Commentd out because failing due to endpoing update


# @pytest.mark.integration
# def test_csv_generation(remote_client, local_usgs_streamflow_csv):
#     """Test: GET /streamflow_observations/usgs/csv"""
#     response = remote_client.get(
#         "/v1/streamflow_observations/usgs/csv",
#         params={
#             "identifier": "01010000",
#             "start_date": "2021-12-31T14:00:00",
#             "end_date": "2022-01-01T14:00:00",
#         },
#     )

#     assert response.status_code in [200, 500]

#     if response.status_code == 200:
#         df = pd.read_csv(StringIO(response.text))
#         assert local_usgs_streamflow_csv.equals(df)


# @pytest.mark.integration
# def test_parquet_generation(remote_client, local_usgs_streamflow_parquet):
#     """Test: GET /streamflow_observations/usgs/parquet"""
#     response = remote_client.get(
#         "/v1/streamflow_observations/usgs/parquet",
#         params={
#             "identifier": "01010000",
#             "start_date": "2021-12-31T14:00:00",
#             "end_date": "2022-01-01T14:00:00",
#         },
#     )

#     assert response.status_code in [200, 500]

#     if response.status_code == 200:
#         df = pd.read_parquet(BytesIO(response.content))
#         assert local_usgs_streamflow_parquet.equals(df)
