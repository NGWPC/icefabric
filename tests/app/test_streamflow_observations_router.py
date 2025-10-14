from io import BytesIO, StringIO

import pandas as pd
import pytest


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
def test_observation_csv(mock_streamflow_cli, local_usgs_streamflow_csv, client):
    """Test: GET /streamflow_observations/{identifier}/{type}"""
    response = client.get(
        "/v1/streamflow_observations/01010000/csv?start_date=2021-12-31%2014%3A00%3A00&end_date=2022-01-01%2014%3A00%3A00&include_headers=true",
    )

    assert response.status_code == 200
    df = pd.read_csv(StringIO(response.text))
    assert local_usgs_streamflow_csv.equals(df)
    mock_streamflow_cli.assert_called_once()


@pytest.mark.integration
def test_observation_csv__no_headers(mock_streamflow_cli, local_usgs_streamflow_csv__no_headers, client):
    """Test: GET /streamflow_observations/{identifier}/{type}"""
    response = client.get(
        "/v1/streamflow_observations/01010000/csv?start_date=2021-12-31%2014%3A00%3A00&end_date=2022-01-01%2014%3A00%3A00&include_headers=false",
    )

    assert response.status_code == 200
    df = pd.read_csv(StringIO(response.text))
    assert local_usgs_streamflow_csv__no_headers.equals(df)
    mock_streamflow_cli.assert_called_once()


@pytest.mark.integration
def test_observation_parquet(mock_streamflow_cli, local_usgs_streamflow_parquet, client):
    """Test: GET /streamflow_observations/{identifier}/{type}"""
    response = client.get(
        "/v1/streamflow_observations/01010000/parquet?start_date=2021-12-31%2014%3A00%3A00&end_date=2022-01-01%2014%3A00%3A00",
    )

    assert response.status_code == 200
    df = pd.read_parquet(BytesIO(response.content))
    assert local_usgs_streamflow_parquet.equals(df)
    mock_streamflow_cli.assert_called_once()


@pytest.mark.integration
def test_observation__404(mock_streamflow_cli, client):
    """Test: GET /streamflow_observations/{identifier}/{type} 404 missing data
    Demo data is 2021-12-31 -> 2022-01-01"""
    response = client.get(
        "/v1/streamflow_observations/01010000/parquet?start_date=2020-12-31%2014%3A00%3A00&end_date=2021-01-01%2014%3A00%3A00",
    )

    assert response.status_code == 404
    mock_streamflow_cli.assert_called_once()


@pytest.mark.integration
def test_observation__422(mock_streamflow_cli, client):
    """Test: GET /streamflow_observations/{identifier}/{type} 422 invalid response"""
    response = client.get(
        "/v1/streamflow_observations/0101000/fake?start_date=2021-12-31%2014%3A00%3A00&end_date=2022-01-01%2014%3A00%3A00",
    )

    assert response.status_code == 422
    mock_streamflow_cli.assert_not_called()
