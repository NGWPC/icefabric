"""Tests for the find_origin function using the RustworkX graph-based mock catalog"""

import polars as pl
import pytest

from icefabric.hydrofabric.origin import find_origin
from icefabric.schemas.hydrofabric import IdType


class TestFindOrigin:
    """Test the find_origin function with various identifier types"""

    def test_find_origin_success_with_hl_uri(self, mock_catalog):
        """Test successfully finding an origin by hl_uri"""
        catalog = mock_catalog("glue")
        network_table = catalog.load_table("mock_hf.network").to_polars()

        # Get valid hl_uri values from the network table
        hl_uri_records = network_table.filter(pl.col("hl_uri").is_not_null()).collect()

        if hl_uri_records.height > 0:
            # Test with the first valid hl_uri
            test_hl_uri = hl_uri_records["hl_uri"][0]
            result = find_origin(network_table, test_hl_uri, IdType.HL_URI)

            assert result.height == 1
            assert result["id"][0].startswith("wb-")

            expected_columns = ["id", "toid", "vpuid", "hydroseq"]
            assert all(col in result.columns for col in expected_columns)
        else:
            pytest.skip("No hl_uri values found in mock data")

    def test_find_origin_with_wb_id_type(self, mock_catalog):
        """Test finding origin by watershed ID (wb-*)"""
        catalog = mock_catalog("glue")
        network_table = catalog.load_table("mock_hf.network").to_polars()

        # Get a valid wb-* ID from the network table
        wb_records = network_table.filter(pl.col("id").str.starts_with("wb-")).collect()

        if wb_records.height > 0:
            test_wb_id = wb_records["id"][0]
            result = find_origin(network_table, test_wb_id, IdType.ID)

            assert result.height == 1
            assert result["id"][0] == test_wb_id
        else:
            pytest.skip("No wb-* IDs found in mock data")

    def test_find_origin_with_poi_id(self, mock_catalog):
        """Test finding origin by POI ID"""
        catalog = mock_catalog("glue")
        network_table = catalog.load_table("mock_hf.network").to_polars()

        # Get valid POI ID values from the network table
        poi_records = network_table.filter(pl.col("poi_id").is_not_null()).collect()

        if poi_records.height > 0:
            # Test with the first valid POI ID
            test_poi_id = float(poi_records["poi_id"][0])
            result = find_origin(network_table, test_poi_id, IdType.POI_ID)

            assert result.height == 1
            assert result["id"][0].startswith("wb-")

            # Verify the POI ID matches
            assert float(result["poi_id"][0]) == test_poi_id
        else:
            pytest.skip("No POI IDs found in mock data")

    @pytest.mark.parametrize("id_type", [IdType.ID, IdType.HL_URI, IdType.POI_ID])
    def test_find_origin_with_sample_graph_data(self, mock_catalog, id_type):
        """Test find_origin with various ID types from the RustworkX graph data"""
        catalog = mock_catalog("glue")
        network_table = catalog.load_table("mock_hf.network").to_polars()

        # Get appropriate test identifier based on type
        if id_type == IdType.ID:
            # Get first wb-* ID
            candidates = network_table.filter(pl.col("id").str.starts_with("wb-")).collect()
            if candidates.height == 0:
                pytest.skip(f"No valid {id_type.value} identifiers found")
            test_identifier = candidates["id"][0]

        elif id_type == IdType.HL_URI:
            # Get first non-null hl_uri
            candidates = network_table.filter(pl.col("hl_uri").is_not_null()).collect()
            if candidates.height == 0:
                pytest.skip(f"No valid {id_type.value} identifiers found")
            test_identifier = candidates["hl_uri"][0]

        elif id_type == IdType.POI_ID:
            # Get first non-null poi_id
            candidates = network_table.filter(pl.col("poi_id").is_not_null()).collect()
            if candidates.height == 0:
                pytest.skip(f"No valid {id_type.value} identifiers found")
            test_identifier = float(candidates["poi_id"][0])

        # Test the find_origin function
        result = find_origin(network_table, test_identifier, id_type)

        # Validate result
        assert result.height == 1
        assert result["id"][0].startswith("wb-")

        # Verify the identifier matches in the result
        if id_type == IdType.ID:
            assert result["id"][0] == test_identifier
        elif id_type == IdType.HL_URI:
            assert result["hl_uri"][0] == test_identifier
        elif id_type == IdType.POI_ID:
            assert float(result["poi_id"][0]) == test_identifier

    def test_find_origin_handles_null_values(self):
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
                    "hf_id": "1",
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
                    "poi_id": 123.0,
                    "divide_id": "cat-VALID001",
                    "ds_id": None,
                    "mainstem": None,
                    "hf_source": "NHDPlusHR",
                    "hf_id": "2",
                    "lengthkm": 1.0,
                    "areasqkm": 1.0,
                    "tot_drainage_areasqkm": 1.0,
                    "type": "waterbody",
                    "topo": "fl-nex",
                },
            ]
        ).lazy()

        # Should find the valid record by hl_uri
        result = find_origin(test_data, "ValidGage", IdType.HL_URI)
        assert result.height == 1
        assert result["id"][0] == "wb-VALID001"

        # Should find the valid record by POI ID
        result = find_origin(test_data, 123.0, IdType.POI_ID)
        assert result.height == 1
        assert result["id"][0] == "wb-VALID001"

    def test_find_origin_with_empty_dataframe(self):
        """Test behavior with empty network table"""
        empty_df = pl.DataFrame(
            {
                "id": pl.Series([], dtype=pl.Utf8),
                "toid": pl.Series([], dtype=pl.Utf8),
                "vpuid": pl.Series([], dtype=pl.Utf8),
                "hydroseq": pl.Series([], dtype=pl.Float64),
                "hl_uri": pl.Series([], dtype=pl.Utf8),
                "poi_id": pl.Series([], dtype=pl.Float64),
            }
        ).lazy()

        with pytest.raises(ValueError, match=r"No origin found"):
            find_origin(empty_df, "AnyIdentifier", IdType.HL_URI)

    def test_find_origin_nonexistent_identifier(self, mock_catalog):
        """Test behavior when identifier doesn't exist"""
        catalog = mock_catalog("glue")
        network_table = catalog.load_table("mock_hf.network").to_polars()

        with pytest.raises(ValueError, match=r"No origin found"):
            find_origin(network_table, "nonexistent-gage-999999", IdType.HL_URI)

        with pytest.raises(ValueError, match=r"No origin found"):
            find_origin(network_table, "wb-999999", IdType.ID)

        with pytest.raises(ValueError, match=r"No origin found"):
            find_origin(network_table, 999999.0, IdType.POI_ID)

    def test_find_origin_data_structure_validation(self, mock_catalog):
        """Test that the returned data has the expected structure"""
        catalog = mock_catalog("glue")
        network_table = catalog.load_table("mock_hf.network").to_polars()

        # Get a valid wb-* ID from the graph-based data
        wb_records = network_table.filter(pl.col("id").str.starts_with("wb-")).collect()

        if wb_records.height > 0:
            test_wb_id = wb_records["id"][0]
            result = find_origin(network_table, test_wb_id, IdType.ID)

            # Validate structure
            assert isinstance(result, pl.DataFrame)
            assert result.height == 1

            # Check required columns exist
            required_columns = ["id", "toid", "vpuid"]
            for col in required_columns:
                assert col in result.columns

            # Validate data types
            assert isinstance(result["id"][0], str)
            assert result["vpuid"][0] == "hi"  # Should be Hawaii

            # Check that toid is either a string or None
            toid_value = result["toid"][0]
            assert toid_value is None or isinstance(toid_value, str)
        else:
            pytest.skip("No wb-* IDs found in mock data")

    def test_find_origin_with_multiple_vpu_handling(self, mock_catalog):
        """Test that find_origin works correctly with VPU filtering"""
        catalog = mock_catalog("glue")
        network_table = catalog.load_table("mock_hf.network").to_polars()

        # All mock data should be Hawaii (vpuid = "hi")
        vpu_values = network_table.select(pl.col("vpuid").unique()).collect()["vpuid"].to_list()

        # Should only have Hawaii VPU in mock data
        assert "hi" in vpu_values

        # Test with a valid wb-* ID
        wb_records = network_table.filter(pl.col("id").str.starts_with("wb-")).collect()

        if wb_records.height > 0:
            test_wb_id = wb_records["id"][0]
            result = find_origin(network_table, test_wb_id, IdType.ID)

            assert result.height == 1
            assert result["vpuid"][0] == "hi"
        else:
            pytest.skip("No wb-* IDs found in mock data")

    @pytest.mark.parametrize("invalid_type", ["invalid_type", None, 123])
    def test_find_origin_invalid_id_type(self, mock_catalog, invalid_type):
        """Test that invalid ID types are handled appropriately"""
        catalog = mock_catalog("glue")
        network_table = catalog.load_table("mock_hf.network").to_polars()

        # This should raise an error due to invalid IdType
        with pytest.raises((ValueError, TypeError, AttributeError)):
            find_origin(network_table, "wb-test", invalid_type)

    def test_find_origin_graph_consistency(self, mock_catalog):
        """Test that find_origin works consistently with the RustworkX graph structure"""
        catalog = mock_catalog("glue")
        network_table = catalog.load_table("mock_hf.network").to_polars()
        graph = catalog.get_connectivity_graph("mock_hf")

        # Get a node from the graph
        graph_nodes = graph.nodes()
        wb_nodes = [node for node in graph_nodes if node.startswith("wb-")]

        if wb_nodes:
            test_node = wb_nodes[0]

            # This node should be findable in the network table
            result = find_origin(network_table, test_node, IdType.ID)

            assert result.height == 1
            assert result["id"][0] == test_node

            # The result should have data that's consistent with being part of a graph
            assert result["toid"][0] is None or isinstance(result["toid"][0], str)
        else:
            pytest.skip("No wb-* nodes found in graph")
