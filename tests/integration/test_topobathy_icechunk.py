import os
from pathlib import Path

import numpy as np
import pytest
import rasterio
from dotenv import load_dotenv

from icefabric.builds import IcechunkRepo
from icefabric.schemas import NGWPCTestLocations

load_dotenv()


@pytest.mark.slow
def test_topobathy(ic_raster: str) -> None:
    """This test is SLOW. It will temporarily download all topobathy layers, up to 9 GB individually.
    To run, call `pytest tests --run-slow`
    Corrupted rasters will load correctly in xarray but incorrectly in rasterio and cannot be exported.
    This test checks that when exported, a dataset has values that are non-no data.
    """
    data_dir = Path(__file__).parent / "data"
    os.makedirs(data_dir, exist_ok=True)

    temp_path = data_dir / "temp_raster.tif"

    local_creds_file = Path(__file__).parents[2] / ".env"
    if local_creds_file.exists is False:
        pytest.skip("Skipping as AWS creds are not available")

    try:
        # export icechunk zarr to geotiff raster
        repo = IcechunkRepo(location=NGWPCTestLocations[ic_raster].path)
        ds = repo.retrieve_dataset()
        raster = ds.elevation
        raster.rio.to_raster(temp_path, tiled=True, compress="LZW", bigtiff="YES")

        # open raster version
        with rasterio.open(temp_path, "r") as f:
            profile = f.profile
            ras = f.read(1)

        # assert all values are not nodata
        total_nd = np.where(ras == profile["nodata"], 1, 0).sum()
        assert total_nd != ras.size
        assert ras.min() != ras.max()

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pytest.mark.local
def test_local_topobathy(local_ic_raster: Path) -> None:
    """Tests local topobathy against local icechunk stores

    Parameters
    ----------
    local_ic_raster : str
        _description_
    """
    data_dir = Path(__file__).parent / "data"
    os.makedirs(data_dir, exist_ok=True)

    temp_path = data_dir / "temp_raster.tif"

    if local_ic_raster.exists() is False:
        pytest.skip("Local file for topobathy missing. Skipping test")

    try:
        # export icechunk zarr to geotiff raster
        repo = IcechunkRepo(local_ic_raster)
        ds = repo.retrieve_dataset()
        raster = ds.elevation
        raster.rio.to_raster(temp_path, tiled=True, compress="LZW", bigtiff="YES")

        # open raster version
        with rasterio.open(temp_path, "r") as f:
            profile = f.profile
            ras = f.read(1)

        # assert all values are not nodata
        total_nd = np.where(ras == profile["nodata"], 1, 0).sum()
        assert total_nd != ras.size
        assert ras.min() != ras.max()

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
