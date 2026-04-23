"""Smoke tests for the parameter_metadata endpoint against a deployed API."""

import os

import pytest
import requests

API_BASE_URL = os.environ.get("API_BASE_URL")

pytestmark = pytest.mark.skipif(not API_BASE_URL, reason="API_BASE_URL environment variable not set")

# All available modules from the endpoint
ALL_MODULES = [
    "CFE-S",
    "CFE-X",
    "LASAM",
    "LSTM",
    "Noah-OWP-Modular",
    "PET",
    "Sac-SMA",
    "SFT",
    "SMP",
    "Snow-17",
    "T-Route",
    "TopModel",
    "Topoflow-Glacier",
    "UEB",
]


def _assert_all_modules_no_error(url):
    """Helper to verify all modules in a response return without error."""
    response = requests.get(url, timeout=120)
    assert response.status_code == 200, f"Request failed: {response.status_code}"

    data = response.json()
    assert "modules" in data

    errors = []
    for module in data["modules"]:
        module_name = module.get("module_name", "UNKNOWN")
        if "error" in module:
            errors.append(f"Module '{module_name}': {module['error']}")

    assert len(errors) == 0, f"Found {len(errors)} module error(s):\n" + "\n".join(errors)


def test_all_valid_modules_return_no_error():
    """Verify that all valid modules return without an error message."""
    modules_param = "&".join([f"modules={m}" for m in ALL_MODULES])
    url = f"{API_BASE_URL}/v1/modules/parameter_metadata/?{modules_param}"
    _assert_all_modules_no_error(url)


def test_all_valid_modules_conus_nhf():
    """Verify all modules return without error for CONUS NHF."""
    modules_param = "&".join([f"modules={m}" for m in ALL_MODULES])
    url = f"{API_BASE_URL}/v1/modules/parameter_metadata/?{modules_param}&gage_id=01010000&domain=CONUS&source=nhf"
    _assert_all_modules_no_error(url)


def test_all_valid_modules_conus_hf():
    """Verify all modules return without error for CONUS HF v2.2."""
    modules_param = "&".join([f"modules={m}" for m in ALL_MODULES])
    url = f"{API_BASE_URL}/v1/modules/parameter_metadata/?{modules_param}&gage_id=01010000&domain=CONUS&source=hf"
    _assert_all_modules_no_error(url)


def test_invalid_module_returns_error():
    """Verify that a bogus module name returns an error message."""
    url = f"{API_BASE_URL}/v1/modules/parameter_metadata/?modules=bogus_module"

    response = requests.get(url, timeout=30)
    assert response.status_code == 200, f"Request failed: {response.status_code}"

    data = response.json()
    assert "modules" in data
    assert len(data["modules"]) == 1

    module = data["modules"][0]
    assert "error" in module, "Expected an error for invalid module name"
    assert module["module_name"] == "bogus_module"


def test_api_health():
    """Verify the API is reachable."""
    response = requests.head(f"{API_BASE_URL}/health", timeout=10)
    assert response.status_code == 200
