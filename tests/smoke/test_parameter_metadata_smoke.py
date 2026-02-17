"""Smoke tests for the parameter_metadata endpoint against a deployed API."""

import os

import pytest
import requests

API_BASE_URL = os.environ.get("API_BASE_URL")

pytestmark = pytest.mark.skipif(not API_BASE_URL, reason="API_BASE_URL environment variable not set")

NUMERIC_FIELDS = ["initial_value", "min", "max"]

# All available modules from the endpoint
ALL_MODULES = [
    "CFE-S",
    "CFE-X",
    "LASAM",
    "LSTM",
    "Noah-OWP-Modular",
    "Sac-SMA",
    "SFT",
    "SMP",
    "Snow-17",
    "T-Route",
    "TopModel",
    "Topoflow-Glacier",
    "UEB",
]


def test_parameter_metadata_numeric_fields_not_null():
    """Verify numeric fields are not null in the parameter_metadata response for ALL modules."""
    modules_param = "&".join([f"modules={m}" for m in ALL_MODULES])
    url = f"{API_BASE_URL}/v1/modules/parameter_metadata/?{modules_param}"

    response = requests.get(url, timeout=30)
    assert response.status_code == 200, f"Request failed: {response.status_code}"

    data = response.json()
    assert "modules" in data

    violations = []
    for module in data["modules"]:
        module_name = module.get("module_name", "UNKNOWN")
        for param in module.get("calibratable_parameters", []):
            param_name = param.get("name", "UNKNOWN")
            for field in NUMERIC_FIELDS:
                if param.get(field) is None:
                    violations.append(f"Module '{module_name}', Parameter '{param_name}': '{field}' is null")

    assert len(violations) == 0, f"Found {len(violations)} null numeric field(s):\n" + "\n".join(violations)


def test_gage_specific_parameter_metadata_numeric_fields_not_null():
    """Verify numeric fields are not null when querying with domain and gage_id."""
    modules_param = "&".join([f"modules={m}" for m in ALL_MODULES])
    url = f"{API_BASE_URL}/v1/modules/parameter_metadata/?{modules_param}&domain=CONUS&gage_id=01123000"

    response = requests.get(url, timeout=30)
    assert response.status_code == 200, f"Request failed: {response.status_code}"

    data = response.json()
    assert "modules" in data

    violations = []
    for module in data["modules"]:
        module_name = module.get("module_name", "UNKNOWN")
        for param in module.get("calibratable_parameters", []):
            param_name = param.get("name", "UNKNOWN")
            for field in NUMERIC_FIELDS:
                if param.get(field) is None:
                    violations.append(f"Module '{module_name}', Parameter '{param_name}': '{field}' is null")

    assert len(violations) == 0, f"Found {len(violations)} null numeric field(s):\n" + "\n".join(violations)


def test_api_health():
    """Verify the API is reachable."""
    response = requests.head(f"{API_BASE_URL}/health", timeout=10)
    assert response.status_code == 200
