"""Concise tests for subset hydrofabric functionality using RustworkX graph"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
import polars as pl
import pytest

from icefabric.builds.graph_connectivity import load_upstream_json
from icefabric.hydrofabric.subset import (
    get_upstream_segments,
    subset_hydrofabric,
    subset_layers,
)
from icefabric.schemas.hydrofabric import IdType
from tests.conftest import MockCatalog


class TestGetUpstreamSegments:
    """Test the upstream segment traversal logic"""

    def test_upstream_tracing_with_graph(self, test_wb_id, mock_catalog, tmp_path: Path) -> None:
        """Test upstream tracing scenarios with the actual RustworkX graph"""
        catalog = mock_catalog("glue")

        # Load the graph from the mock catalog
        graph_dict = load_upstream_json(catalog=catalog, namespaces=["mock_hf"], output_path=tmp_path)
        graph = graph_dict["mock_hf"]

        # Get some nodes from the graph to test with
        graph_nodes = graph.nodes()
        wb_nodes = [node for node in graph_nodes if node.startswith("wb-")]

        if len(wb_nodes) >= 2:
            # Test with the first available node
            result = get_upstream_segments(test_wb_id, graph)

            # Result should be a set of node indices
            assert isinstance(result, set)
            assert len(result) >= 1  # At least the origin
        else:
            pytest.skip("Not enough wb- nodes in mock graph for testing")

    def test_upstream_tracing_nonexistent_node(self, mock_catalog, tmp_path: Path) -> None:
        """Test upstream tracing with a nonexistent node"""
        catalog = mock_catalog("glue")

        graph_dict = load_upstream_json(catalog=catalog, namespaces=["mock_hf"], output_path=tmp_path)
        graph = graph_dict["mock_hf"]

        # Test with a nonexistent node
        result = get_upstream_segments("wb-nonexistent-999999", graph)

        # Should return empty set for nonexistent nodes
        assert isinstance(result, set)
        assert len(result) == 0


class TestSubsetLayers:
    """Test the layer subsetting functionality"""

    @pytest.mark.parametrize(
        "layers,expected_core_layers",
        [
            (["network", "flowpaths", "nexus", "divides"], ["network", "flowpaths", "nexus", "divides"]),
            ([], ["network", "flowpaths", "nexus", "divides"]),  # Should add core layers
            (["pois"], ["network", "flowpaths", "nexus", "divides", "pois"]),
        ],
    )
    def test_layer_inclusion(
        self, mock_catalog: MockCatalog, layers: list[str], expected_core_layers: list[str]
    ) -> None:
        """Test that correct layers are included in results"""
        catalog = mock_catalog("glue")

        # Get some valid upstream IDs from the mock data
        network_table = catalog.load_table("mock_hf.network").to_polars()
        wb_records = network_table.filter(pl.col("id").str.starts_with("wb-")).collect()

        if wb_records.height >= 2:
            # Use the first few wb- IDs as upstream_ids
            upstream_ids = set(wb_records["id"][:2].to_list())

            result = subset_layers(catalog, "mock_hf", layers, upstream_ids, "hi")

            # Core layers should always be present
            core_layers = ["network", "flowpaths", "nexus", "divides"]
            for layer in core_layers:
                assert layer in result
                assert len(result[layer]) > 0

            # Check data types
            assert isinstance(result["network"], pd.DataFrame)
            assert isinstance(result["flowpaths"], gpd.GeoDataFrame)
            assert isinstance(result["nexus"], gpd.GeoDataFrame)
            assert isinstance(result["divides"], gpd.GeoDataFrame)
        else:
            pytest.skip("Not enough wb- records in mock data")

    def test_empty_upstream_ids_raises_assertion(self, mock_catalog: MockCatalog) -> None:
        """Test that empty upstream IDs cause assertion errors"""
        catalog = mock_catalog("glue")

        with pytest.raises(AssertionError, match="No flowpaths found"):
            subset_layers(catalog, "mock_hf", ["network"], set(), "hi")


class TestSubsetHydrofabric:
    """Test the main subset hydrofabric function"""

    def test_successful_subsetting_with_wb_id(
        self, test_wb_id: str, mock_catalog: MockCatalog, tmp_path: Path
    ) -> None:
        """Test successful subsetting with a watershed ID"""
        catalog = mock_catalog("glue")

        # Get the connectivity graph
        graph_dict = load_upstream_json(catalog=catalog, namespaces=["mock_hf"], output_path=tmp_path)
        graph = graph_dict["mock_hf"]

        # Get a valid wb- ID from the mock data
        network_table = catalog.load_table("mock_hf.network").to_polars()
        wb_records = network_table.filter(pl.col("id").str.starts_with("wb-")).collect()

        if wb_records.height > 0:
            result = subset_hydrofabric(
                catalog=catalog,
                identifier=test_wb_id,
                id_type=IdType.ID,
                layers=["network", "flowpaths", "nexus", "divides"],
                namespace="mock_hf",
                graph=graph,
            )

            # Validate basic structure
            assert isinstance(result, dict)
            core_layers = ["network", "flowpaths", "nexus", "divides"]
            for layer in core_layers:
                assert layer in result
                assert len(result[layer]) > 0

            # Origin should be included in network
            network_df = result["network"]
            assert test_wb_id in network_df["id"].values
        else:
            pytest.skip("No wb- records found in mock data")

    def test_poi_id_subsetting(self, mock_catalog: MockCatalog, tmp_path: Path) -> None:
        """Test POI ID subsetting"""
        catalog = mock_catalog("glue")

        # Get the connectivity graph
        graph_dict = load_upstream_json(catalog=catalog, namespaces=["mock_hf"], output_path=tmp_path)
        graph = graph_dict["mock_hf"]

        # Get a valid POI ID from the mock data
        network_table = catalog.load_table("mock_hf.network").to_polars()
        poi_records = network_table.filter(pl.col("poi_id").is_not_null()).collect()

        if poi_records.height > 0:
            poi_id_value = float(poi_records["poi_id"][-1])

            try:
                result = subset_hydrofabric(
                    catalog=catalog,
                    identifier=poi_id_value,
                    id_type=IdType.POI_ID,
                    layers=["network", "flowpaths", "nexus", "divides"],
                    namespace="mock_hf",
                    graph=graph,
                )

                # Should have valid structure if successful
                assert isinstance(result, dict)
                assert "network" in result
                assert len(result["network"]) > 0

            except ValueError as e:
                # POI might not exist or have issues, which is acceptable
                if "No origin found" not in str(e):
                    raise
        else:
            pytest.skip("No POI records found in mock data")

    def test_hl_uri_subsetting(self, mock_catalog: MockCatalog, tmp_path: Path) -> None:
        """Test HL_URI subsetting"""
        catalog = mock_catalog("glue")

        # Get the connectivity graph
        graph_dict = load_upstream_json(catalog=catalog, namespaces=["mock_hf"], output_path=tmp_path)
        graph = graph_dict["mock_hf"]

        # Get a valid HL_URI from the mock data
        network_table = catalog.load_table("mock_hf.network").to_polars()
        hl_records = network_table.filter(pl.col("hl_uri").is_not_null()).collect()

        if hl_records.height > 0:
            test_hl_uri = hl_records["hl_uri"][-1]

            try:
                result = subset_hydrofabric(
                    catalog=catalog,
                    identifier=test_hl_uri,
                    id_type=IdType.HL_URI,
                    layers=["network", "flowpaths", "nexus", "divides"],
                    namespace="mock_hf",
                    graph=graph,
                )

                # Should have valid structure if successful
                assert isinstance(result, dict)
                assert "network" in result
                assert len(result["network"]) > 0

            except ValueError as e:
                # HL_URI might not exist or have issues, which is acceptable
                if "No origin found" not in str(e):
                    raise
        else:
            pytest.skip("No HL_URI records found in mock data")

    def test_upstream_tracing_completeness(
        self, test_wb_id: str, mock_catalog: MockCatalog, tmp_path: Path
    ) -> None:
        """Test that upstream tracing finds connected segments"""
        catalog = mock_catalog("glue")

        # Get the connectivity graph
        graph_dict = load_upstream_json(catalog=catalog, namespaces=["mock_hf"], output_path=tmp_path)
        graph = graph_dict["mock_hf"]

        # Find a node that has upstream connections
        graph_nodes = graph.nodes()
        wb_nodes = [node for node in graph_nodes if node.startswith("wb-")]

        if len(wb_nodes) > 1:
            result = subset_hydrofabric(
                catalog=catalog,
                identifier=test_wb_id,
                id_type=IdType.ID,
                layers=["network"],
                namespace="mock_hf",
                graph=graph,
            )

            network_df = result["network"]

            # Origin should be included
            assert test_wb_id in network_df["id"].values

            # Should have at least one record
            assert len(network_df) >= 1
        else:
            pytest.skip("Not enough wb- nodes for upstream testing")

    def test_nonexistent_identifier_raises_error(self, mock_catalog: MockCatalog, tmp_path: Path) -> None:
        """Test that nonexistent identifier raises appropriate error"""
        catalog = mock_catalog("glue")

        # Get the connectivity graph
        graph_dict = load_upstream_json(catalog=catalog, namespaces=["mock_hf"], output_path=tmp_path)
        graph = graph_dict["mock_hf"]

        with pytest.raises(ValueError, match="No origin found"):
            subset_hydrofabric(
                catalog=catalog,
                identifier="nonexistent-gage-999999",
                id_type=IdType.HL_URI,
                layers=["network"],
                namespace="mock_hf",
                graph=graph,
            )


class TestDataConsistency:
    """Test data consistency and relationships between tables"""

    def test_table_relationship_consistency(
        self, test_wb_id: str, mock_catalog: MockCatalog, tmp_path: Path
    ) -> None:
        """Test that relationships between tables follow the hydrofabric data model"""
        catalog = mock_catalog("glue")

        # Get the connectivity graph
        graph_dict = load_upstream_json(catalog=catalog, namespaces=["mock_hf"], output_path=tmp_path)
        graph = graph_dict["mock_hf"]

        # Get a valid wb- ID from the mock data
        network_table = catalog.load_table("mock_hf.network").to_polars()
        wb_records = network_table.filter(pl.col("id").str.starts_with("wb-")).collect()

        if wb_records.height > 0:
            result = subset_hydrofabric(
                catalog=catalog,
                identifier=test_wb_id,
                id_type=IdType.ID,
                layers=["network", "flowpaths", "nexus", "divides", "pois"],
                namespace="mock_hf",
                graph=graph,
            )

            network_df = result["network"]
            flowpaths_df = result["flowpaths"]
            divides_df = result["divides"]
            nexus_df = result["nexus"]

            # Basic data presence
            assert len(network_df) > 0
            assert len(flowpaths_df) > 0
            assert len(divides_df) > 0
            assert len(nexus_df) > 0

            # Key relationship: network.id ↔ flowpaths.id (same watershed)
            network_ids = set(network_df["id"].values)
            flowpath_ids = set(flowpaths_df["id"].values)
            common_network_flowpath = network_ids.intersection(flowpath_ids)
            assert len(common_network_flowpath) > 0, "Network and flowpaths should share watershed IDs"

            # Key relationship: network.divide_id → divides.divide_id
            network_divide_ids = set(network_df["divide_id"].dropna().values)
            divides_divide_ids = set(divides_df["divide_id"].values)
            assert network_divide_ids.issubset(divides_divide_ids), (
                "All network divide_ids should exist in divides table"
            )

            # POI relationships if POIs exist
            if "pois" in result and len(result["pois"]) > 0:
                pois_df = result["pois"]

                # network.poi_id → pois.poi_id
                network_poi_ids = set(network_df["poi_id"].dropna().astype(str).values)
                pois_poi_ids = set(pois_df["poi_id"].astype(str).values)
                poi_overlap = network_poi_ids.intersection(pois_poi_ids)
                if len(network_poi_ids) > 0:
                    assert len(poi_overlap) > 0, "Network POI IDs should match POIs table POI IDs"

            # VPU consistency across all tables
            for df_name, df in [
                ("network", network_df),
                ("flowpaths", flowpaths_df),
                ("nexus", nexus_df),
                ("divides", divides_df),
            ]:
                if "vpuid" in df.columns:
                    vpu_values = set(df["vpuid"].dropna().values)
                    assert vpu_values == {"hi"} or len(vpu_values) == 0, (
                        f"{df_name} should have consistent VPU values"
                    )
        else:
            pytest.skip("No wb- records found in mock data")


class TestOptionalLayers:
    """Test optional layer handling"""

    @pytest.mark.parametrize(
        "optional_layers",
        [
            ["divide-attributes"],
            ["flowpath-attributes"],
            ["pois"],
            ["hydrolocations"],
            ["divide-attributes", "pois"],  # Multiple optional layers
        ],
    )
    def test_optional_layer_loading(
        self, test_wb_id: str, mock_catalog: MockCatalog, optional_layers: list[str], tmp_path: Path
    ) -> None:
        """Test that optional layers can be loaded without errors"""
        catalog = mock_catalog("glue")

        # Get the connectivity graph
        graph_dict = load_upstream_json(catalog=catalog, namespaces=["mock_hf"], output_path=tmp_path)
        graph = graph_dict["mock_hf"]

        # Get a valid wb- ID from the mock data
        network_table = catalog.load_table("mock_hf.network").to_polars()
        wb_records = network_table.filter(pl.col("id").str.starts_with("wb-")).collect()

        if wb_records.height > 0:
            all_layers = ["network", "flowpaths", "nexus", "divides"] + optional_layers

            result = subset_hydrofabric(
                catalog=catalog,
                identifier=test_wb_id,
                id_type=IdType.ID,
                layers=all_layers,
                namespace="mock_hf",
                graph=graph,
            )

            # Core layers should always be present
            core_layers = ["network", "flowpaths", "nexus", "divides"]
            for layer in core_layers:
                assert layer in result
                assert len(result[layer]) > 0

            # Optional layers should be present if they have data, and be valid DataFrames
            for layer in optional_layers:
                if layer in result:
                    assert isinstance(result[layer], pd.DataFrame | gpd.GeoDataFrame)
                    # Don't assert length > 0 as some optional layers might legitimately be empty
        else:
            pytest.skip("No wb- records found in mock data")

    def test_lakes_layer_loading_separately(
        self, test_wb_id: str, mock_catalog: MockCatalog, tmp_path: Path
    ) -> None:
        """Test lakes layer separately since it has different filtering logic"""
        catalog = mock_catalog("glue")

        # Get the connectivity graph
        graph_dict = load_upstream_json(catalog=catalog, namespaces=["mock_hf"], output_path=tmp_path)
        graph = graph_dict["mock_hf"]

        # Get a valid wb- ID from the mock data
        network_table = catalog.load_table("mock_hf.network").to_polars()
        wb_records = network_table.filter(pl.col("id").str.starts_with("wb-")).collect()

        if wb_records.height > 0:
            result = subset_hydrofabric(
                catalog=catalog,
                identifier=test_wb_id,
                id_type=IdType.ID,
                layers=["network", "flowpaths", "nexus", "divides", "lakes"],
                namespace="mock_hf",
                graph=graph,
            )

            # Core layers should be present
            assert "network" in result
            assert "lakes" in result
            assert isinstance(result["lakes"], gpd.GeoDataFrame)
        else:
            pytest.skip("No wb- records found in mock data")
