"""Smoke tests for the hydrofabric endpoint against a deployed API."""

import os

import pytest
import requests

API_BASE_URL = os.environ.get("API_BASE_URL")

pytestmark = pytest.mark.skipif(not API_BASE_URL, reason="API_BASE_URL environment variable not set")


def test_gage_id_conus_nhf():
    """Verify gage_id request returns a gpkg for CONUS NHF."""
    url = f"{API_BASE_URL}/v1/hydrofabric/01010000/gpkg?id_type=gage_id&domain=CONUS&source=nhf"

    response = requests.get(url, timeout=120)
    assert response.status_code == 200, f"Request failed: {response.status_code} - {response.text}"
    assert len(response.content) > 0, "Response body is empty"


def test_gage_id_conus_hf():
    """Verify gage_id request returns a gpkg for CONUS HF v2.2."""
    url = f"{API_BASE_URL}/v1/hydrofabric/01010000/gpkg?id_type=gage_id&domain=CONUS&source=hf"

    response = requests.get(url, timeout=60)
    assert response.status_code == 200, f"Request failed: {response.status_code} - {response.text}"
    assert len(response.content) > 0, "Response body is empty"
