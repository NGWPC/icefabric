from pathlib import Path

import geopandas as gpd
import pytest
from pyiceberg.catalog import Catalog

from icefabric.hydrofabric import subset
from icefabric.schemas import HydrofabricDomains, IdType


@pytest.mark.slow
def test_subset_hl_uri(hydrofabric_catalog: Catalog, gauge_hf_uri: str, testing_dir: Path, tmp_path: Path):
    """Tests all subset gauges in the sample data using hl_uri"""
    subset(
        catalog=hydrofabric_catalog,
        domain=HydrofabricDomains.CONUS,
        identifier=gauge_hf_uri,
        id_type=IdType.HL_URI,
        output_file=tmp_path / "subset.gpkg",
    )
    output_gdf = gpd.read_file(tmp_path / "subset.gpkg", layer="network")
    correct_gdf = gpd.read_file(testing_dir / f"{gauge_hf_uri}.gpkg", layer="network")
    assert output_gdf.equals(correct_gdf)

    output_gdf = gpd.read_file(tmp_path / "subset.gpkg", layer="divides")
    correct_gdf = gpd.read_file(testing_dir / f"{gauge_hf_uri}.gpkg", layer="divides")
    assert output_gdf.equals(correct_gdf)

    output_gdf = gpd.read_file(tmp_path / "subset.gpkg", layer="flowpaths")
    correct_gdf = gpd.read_file(testing_dir / f"{gauge_hf_uri}.gpkg", layer="flowpaths")
    assert output_gdf.equals(correct_gdf)

    output_gdf = gpd.read_file(tmp_path / "subset.gpkg", layer="nexus")
    correct_gdf = gpd.read_file(testing_dir / f"{gauge_hf_uri}.gpkg", layer="nexus")
    assert output_gdf.equals(correct_gdf)
