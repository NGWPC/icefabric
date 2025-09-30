import os
from pathlib import Path

import pandas as pd
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from pyiceberg.catalog import Catalog, load_catalog

from app.main import app
from icefabric.schemas import NGWPCTestLocations

# Setting .env/.pyiceberg creds based on project root
env_path = Path.cwd() / ".env"
load_dotenv(dotenv_path=env_path)
pyiceberg_file = Path.cwd() / ".pyiceberg.yaml"
if pyiceberg_file.exists():
    os.environ["PYICEBERG_HOME"] = str(Path(__file__).parents[1])
else:
    raise FileNotFoundError(
        "Cannot find .pyiceberg.yaml. Please download this from NGWPC confluence or create "
    )


sample_gauges = [
    # "01010000",
    # "02450825",
    # "03173000",
    # "04100500",
    # "05473450",
    # "06823500",
    # "07060710",
    # "08070000",
    # "09253000",
    # "10316500",
    # "11456000",
    # "12411000",
    # "13337000",
    # "14020000",
    "06710385",
]

sample_hf_uri = [
    # "gages-01010000",
    # "gages-02450825",
    # "gages-03173000",
    # "gages-04100500",
    # "gages-05473450",
    # "gages-06823500",
    # "gages-07060710",
    # "gages-08070000",
    # "gages-09253000",
    # "gages-10316500",
    # "gages-11456000",
    # "gages-12411000",
    # "gages-13337000",
    # "gages-14020000",
    "gages-06710385"
]

test_ic_rasters = [f for f in NGWPCTestLocations._member_names_ if "TOPO" in f]
local_ic_rasters = [
    Path(__file__).parent / "data/topo_tifs/nws-nos-surveys/Albemarle_Sound_NOS_NCEI",
    Path(__file__).parent / "data/topo_tifs/nws-nos-surveys/Chesapeake_Bay_NOS_NCEI",
    Path(__file__).parent / "data/topo_tifs/nws-nos-surveys/Mobile_Bay_NOS_NCEI",
    Path(__file__).parent / "data/topo_tifs/nws-nos-surveys/Tangier_Sound_NOS_NCEI",
    Path(__file__).parent / "data/topo_tifs/tbdem_alaska_10m",
    Path(__file__).parent / "data/topo_tifs/tbdem_alaska_30m",
    Path(__file__).parent / "data/topo_tifs/tbdem_conus_atlantic_gulf_30m",
    Path(__file__).parent / "data/topo_tifs/tbdem_conus_pacific_30m",
    Path(__file__).parent / "data/topo_tifs/tbdem_great_lakes_30m",
    Path(__file__).parent / "data/topo_tifs/tbdem_hawaii_10m",
    Path(__file__).parent / "data/topo_tifs/tbdem_hawaii_30m",
    Path(__file__).parent / "data/topo_tifs/tbdem_pr_usvi_10m",
    Path(__file__).parent / "data/topo_tifs/tbdem_pr_usvi_30m",
]


@pytest.fixture(params=test_ic_rasters)
def ic_raster(request) -> str:
    """Returns AWS S3 icechunk stores/rasters for checking correctness"""
    return request.param


@pytest.fixture(params=local_ic_rasters)
def local_ic_raster(request) -> Path:
    """Returns local icechunk stores/rasters for checking correctness"""
    return request.param


@pytest.fixture(params=sample_gauges)
def gauge_ids(request) -> str:
    """Returns individual gauge identifiers for parameterized testing"""
    return request.param


@pytest.fixture(params=sample_hf_uri)
def gauge_hf_uri(request) -> str:
    """Returns individual gauge identifiers for parameterized testing"""
    return request.param


@pytest.fixture
def testing_dir() -> Path:
    """Returns the testing data dir"""
    return Path(__file__).parent / "data/"


@pytest.fixture(scope="session")
def client():
    """Create a test client for the FastAPI app."""
    app.state.catalog = load_catalog("glue")  # defaulting to GLUE
    return TestClient(app)


@pytest.fixture
def local_usgs_streamflow_csv():
    """Returns a locally downloaded CSV file from a specific gauge and time"""
    file_path = Path(__file__).parent / "data/usgs_01010000_data_from_20211231_1400_to_20220101_1400.csv"
    return pd.read_csv(file_path)


@pytest.fixture
def local_usgs_streamflow_parquet():
    """Returns a locally downloaded CSV file from a specific gauge and time"""
    file_path = Path(__file__).parent / "data/usgs_01010000_data_from_20211231_1400_to_20220101_1400.parquet"
    return pd.read_parquet(file_path)


@pytest.fixture
def hydrofabric_catalog() -> Catalog:
    """Returns an iceberg catalog object for the hydrofabric"""
    return load_catalog("glue")


def pytest_addoption(parser):
    """Adds addoption tags"""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests",
    )
    parser.addoption(
        "--run-local",
        action="store_true",
        default=False,
        help="Run slow tests",
    )


def pytest_collection_modifyitems(config, items):
    """Allows pytest to read the --run-slow tag"""
    if not config.getoption("--run-slow"):
        skipper = pytest.mark.skip(reason="Only run when --run-slow is given")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skipper)


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow tests")
    config.addinivalue_line("markers", "local: marks tests as local tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
