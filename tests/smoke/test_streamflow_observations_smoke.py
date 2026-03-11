"""Smoke tests for the streamflow_observations endpoint against a deployed API."""

import os

import pytest
import requests

API_BASE_URL = os.environ.get("API_BASE_URL")

pytestmark = pytest.mark.skipif(not API_BASE_URL, reason="API_BASE_URL environment variable not set")

VALID_STATION_ID = "01031500"


def test_available():
    """Verify the available endpoint returns a list of station IDs."""
    url = f"{API_BASE_URL}/v1/streamflow_observations/available?limit=10"

    response = requests.get(url, timeout=120)
    assert response.status_code == 200, f"Request failed: {response.status_code} - {response.text}"

    data = response.json()
    assert "identifiers" in data
    assert "total_identifiers" in data
    assert len(data["identifiers"]) > 0, "No identifiers returned"
    assert data["showing"] <= 10


def test_station_info():
    """Verify the info endpoint returns metadata for a known station."""
    url = f"{API_BASE_URL}/v1/streamflow_observations/{VALID_STATION_ID}/info"

    response = requests.get(url, timeout=120)
    assert response.status_code == 200, f"Request failed: {response.status_code} - {response.text}"

    data = response.json()
    assert data["identifier"] == VALID_STATION_ID
    assert data["total_records"] > 0
    assert "date_range" in data
    assert data["date_range"]["start"] is not None
    assert data["date_range"]["end"] is not None


def test_history():
    """Verify the history endpoint returns repo snapshots."""
    url = f"{API_BASE_URL}/v1/streamflow_observations/history"

    response = requests.get(url, timeout=120)
    assert response.status_code == 200, f"Request failed: {response.status_code} - {response.text}"

    data = response.json()
    assert "latest_snapshot" in data
    assert "snapshots" in data
    assert len(data["snapshots"]) > 0


def test_csv_download():
    """Verify CSV download works for a small time range."""
    url = (
        f"{API_BASE_URL}/v1/streamflow_observations/{VALID_STATION_ID}/csv"
        f"?start_date=2023-01-01&end_date=2023-01-02"
    )

    response = requests.get(url, timeout=120)
    assert response.status_code == 200, f"Request failed: {response.status_code} - {response.text}"
    assert len(response.content) > 0, "CSV response body is empty"


def test_invalid_station_returns_404():
    """Verify that a nonexistent station ID returns 404."""
    url = f"{API_BASE_URL}/v1/streamflow_observations/ZZZZZZZZZZ/info"

    response = requests.get(url, timeout=120)
    assert response.status_code == 404
