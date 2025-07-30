"""Tests for the find_origin function using the mock catalog"""

import polars as pl
import pytest

from icefabric.hydrofabric.origin import find_origin
from icefabric.schemas.hydrofabric import IdType


def test_find_origin_success_with_hl_uri(mock_catalog):
    """Test successfully finding an origin by hl_uri"""
    catalog = mock_catalog("glue")
    network_table = catalog.load_table("mock_hf.network").to_polars()
    identifiers = network_table.select(pl.col("hl_uri")).collect().to_pandas().values.squeeze()
    for identifier in identifiers:
        if identifier is not None:
            result = find_origin(network_table, identifier, IdType.HL_URI)

            assert result.height == 1
            assert "wb" in result["id"][0]

            expected_columns = ["id", "toid", "vpuid", "hydroseq"]
            assert all(col in result.columns for col in expected_columns)


def test_find_origin_with_poi_id_type(mock_catalog):
    """Test finding origin by POI ID"""
    catalog = mock_catalog("glue")
    network_table = catalog.load_table("mock_hf.network").to_polars()
    poi_records = network_table.filter(pl.col("poi_id").is_not_null()).collect()

    if poi_records.height > 0:
        test_poi_id = float(poi_records.get_column("poi_id")[0])
        expected_wb_id = poi_records.get_column("id")[0]

        result = find_origin(network_table, test_poi_id, IdType.POI_ID)

        assert result.height == 1
        assert result["id"][0] == expected_wb_id

        expected_columns = ["id", "toid", "vpuid", "hydroseq"]
        assert all(col in result.columns for col in expected_columns)


def test_find_origin_with_wb_id_type(mock_catalog):
    """Test finding origin by watershed ID (wb-*)"""
    # Use an existing watershed ID from our mock data
    test_wb_id = "wb-2813"
    catalog = mock_catalog("glue")
    network_table = catalog.load_table("mock_hf.network").to_polars()
    result = find_origin(network_table, test_wb_id, IdType.ID)

    assert result.height == 1
    assert result["id"][0] == test_wb_id


def test_find_origin_handles_null_values():
    """Test that function handles null values properly"""
    # Create test data with null hl_uri values
    test_data = pl.DataFrame(
        [
            {
                "id": "wb-NULL001",
                "toid": "nex-NULL001",
                "vpuid": "hi",
                "hydroseq": 1000.0,
                "hl_uri": None,
                "poi_id": None,
                "divide_id": "cat-NULL001",
                "ds_id": None,
                "mainstem": None,
                "hf_source": "NHDPlusHR",
                "hf_id": 1.0,
                "lengthkm": 1.0,
                "areasqkm": 1.0,
                "tot_drainage_areasqkm": 1.0,
                "type": "waterbody",
                "topo": "fl-nex",
            },
            {
                "id": "wb-VALID001",
                "toid": "nex-VALID001",
                "vpuid": "hi",
                "hydroseq": 2000.0,
                "hl_uri": "ValidGage",
                "poi_id": None,
                "divide_id": "cat-VALID001",
                "ds_id": None,
                "mainstem": None,
                "hf_source": "NHDPlusHR",
                "hf_id": 2.0,
                "lengthkm": 1.0,
                "areasqkm": 1.0,
                "tot_drainage_areasqkm": 1.0,
                "type": "waterbody",
                "topo": "fl-nex",
            },
        ]
    ).lazy()

    # Should find the valid record
    result = find_origin(test_data, "ValidGage", IdType.HL_URI)
    assert result.height == 1
    assert result["id"][0] == "wb-VALID001"


def test_find_origin_with_empty_dataframe():
    """Test behavior with empty network table"""
    empty_df = pl.DataFrame({"id": [], "toid": [], "vpuid": [], "hydroseq": [], "hl_uri": []}).lazy()

    with pytest.raises(ValueError, match=r"No origin found"):
        find_origin(empty_df, "AnyIdentifier", IdType.HL_URI)
