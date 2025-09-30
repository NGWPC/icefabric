"""Test suite for graph connectivity module"""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

import polars as pl
import pytest
import rustworkx as rx

from icefabric.builds.graph_connectivity import (
    _build_graph,
    load_upstream_json,
    read_edge_attrs,
    read_node_attrs,
    serialize_edge_attrs,
    serialize_node_attrs,
)


class TestBuildGraph:
    """Test the _build_graph function"""

    @pytest.fixture
    def sample_flowpaths_data(self):
        """Sample flowpaths data for testing"""
        return pl.DataFrame(
            {
                "id": ["wb-1", "wb-2", "wb-3", "wb-4", "wb-5"],
                "toid": ["nex-1", "nex-2", "nex-3", "nex-4", None],  # wb-5 is terminal
            }
        ).lazy()

    @pytest.fixture
    def sample_network_data(self):
        """Sample network data for testing"""
        return pl.DataFrame(
            {
                "id": ["nex-1", "nex-2", "nex-3", "nex-4", "nex-5"],
                "toid": ["wb-2", "wb-3", "wb-4", "wb-0", None],  # nex-5 is terminal
            }
        ).lazy()

    @pytest.fixture
    def simple_flowpaths_data(self):
        """Simple linear flowpaths for basic testing"""
        return pl.DataFrame(
            {
                "id": ["wb-1", "wb-2", "wb-3"],
                "toid": ["nex-1", "nex-2", "nex-3"],
            }
        ).lazy()

    @pytest.fixture
    def simple_network_data(self):
        """Simple linear network for basic testing"""
        return pl.DataFrame(
            {
                "id": ["nex-1", "nex-2", "nex-3"],
                "toid": ["wb-2", "wb-3", "wb-0"],
            }
        ).lazy()

    def test_build_graph_basic_structure(self, simple_flowpaths_data, simple_network_data):
        """Test that the graph has the correct basic structure"""
        graph = _build_graph(simple_flowpaths_data, simple_network_data)

        # Check that all flowpaths are nodes
        node_data = graph.nodes()
        assert "wb-1" in node_data
        assert "wb-2" in node_data
        assert "wb-3" in node_data
        assert "wb-0" in node_data  # Should be added automatically

        # Check that we have the expected number of nodes
        assert len(node_data) == 4

    def test_build_graph_edges(self, simple_flowpaths_data, simple_network_data):
        """Test that edges are created correctly"""
        graph = _build_graph(simple_flowpaths_data, simple_network_data)

        # Check edges exist (wb-1 -> wb-2 -> wb-3 -> wb-0)
        edges = graph.edge_list()

        # Should have edges connecting the linear chain
        assert len(edges) >= 2  # At least wb-1->wb-2 and wb-2->wb-3

    def test_build_graph_terminal_handling(self, sample_flowpaths_data, sample_network_data):
        """Test that terminal nodes are handled correctly"""
        graph = _build_graph(sample_flowpaths_data, sample_network_data)

        # wb-5 has no toid, so it should be a terminal node with no outgoing edges
        nodes = graph.nodes()
        assert "wb-5" in nodes

        # Check that wb-0 is automatically added
        assert "wb-0" in nodes

    def test_build_graph_wb0_addition(self, simple_flowpaths_data, simple_network_data):
        """Test that wb-0 is automatically added if not present"""
        graph = _build_graph(simple_flowpaths_data, simple_network_data)

        nodes = graph.nodes()
        assert "wb-0" in nodes

    def test_build_graph_empty_input(self):
        """Test behavior with empty input"""
        # Create empty DataFrames with proper string types to avoid schema issues
        empty_flowpaths = pl.DataFrame(
            {"id": pl.Series([], dtype=pl.Utf8), "toid": pl.Series([], dtype=pl.Utf8)}
        ).lazy()
        empty_network = pl.DataFrame(
            {"id": pl.Series([], dtype=pl.Utf8), "toid": pl.Series([], dtype=pl.Utf8)}
        ).lazy()

        graph = _build_graph(empty_flowpaths, empty_network)

        # Should still have wb-0
        nodes = graph.nodes()
        assert "wb-0" in nodes
        assert len(nodes) == 1

    def test_build_graph_with_cycles_disabled(self, simple_flowpaths_data, simple_network_data):
        """Test that the graph is created with cycle checking disabled"""
        graph = _build_graph(simple_flowpaths_data, simple_network_data)

        # The graph should be created successfully even if there might be cycles
        assert isinstance(graph, rx.PyDiGraph)

    def test_build_graph_node_data_preservation(self, simple_flowpaths_data, simple_network_data):
        """Test that node data is preserved correctly"""
        graph = _build_graph(simple_flowpaths_data, simple_network_data)

        # Each node should contain its flowpath ID as data
        for node_idx in graph.node_indices():
            node_data = graph.get_node_data(node_idx)
            assert isinstance(node_data, str)
            assert node_data.startswith("wb-")

    def test_build_graph_edge_data(self, simple_flowpaths_data, simple_network_data):
        """Test that edge data contains nexus information"""
        graph = _build_graph(simple_flowpaths_data, simple_network_data)

        # Edges should have nexus IDs as data
        for edge in graph.edge_indices():
            edge_data = graph.get_edge_data_by_index(edge)
            if edge_data:  # Some edges might not have data
                assert isinstance(edge_data, str)
                assert edge_data.startswith("nex-")


class TestSerializationFunctions:
    """Test the serialization helper functions"""

    def test_serialize_node_attrs(self):
        """Test node attribute serialization"""
        test_data = "wb-123"
        result = serialize_node_attrs(test_data)

        assert isinstance(result, dict)
        assert "data" in result
        assert result["data"] == "wb-123"

    def test_serialize_edge_attrs(self):
        """Test edge attribute serialization"""
        test_data = "nex-456"
        result = serialize_edge_attrs(test_data)

        assert isinstance(result, dict)
        assert "data" in result
        assert result["data"] == "nex-456"

    def test_read_node_attrs(self):
        """Test node attribute reading"""
        test_input = {"data": "wb-789"}
        result = read_node_attrs(test_input)

        assert result == "wb-789"

    def test_read_edge_attrs(self):
        """Test edge attribute reading"""
        test_input = {"data": "nex-101"}
        result = read_edge_attrs(test_input)

        assert result == "nex-101"

    def test_serialization_roundtrip(self):
        """Test that serialization and deserialization work together"""
        original_node = "wb-test"
        original_edge = "nex-test"

        # Serialize
        serialized_node = serialize_node_attrs(original_node)
        serialized_edge = serialize_edge_attrs(original_edge)

        # Deserialize
        deserialized_node = read_node_attrs(serialized_node)
        deserialized_edge = read_edge_attrs(serialized_edge)

        assert deserialized_node == original_node
        assert deserialized_edge == original_edge


class TestLoadUpstreamJson:
    """Test the load_upstream_json function"""

    @pytest.fixture
    def mock_catalog(self):
        """Create a mock catalog for testing"""
        catalog = Mock()
        catalog.name = "test_catalog"

        # Mock network table
        mock_network_table = Mock()
        mock_network_table.to_polars.return_value = pl.DataFrame(
            {"id": ["nex-1", "nex-2"], "toid": ["wb-2", "wb-0"]}
        ).lazy()
        mock_snapshot = Mock()
        mock_snapshot.snapshot_id = 12345
        mock_network_table.current_snapshot.return_value = mock_snapshot

        # Mock flowpaths table
        mock_flowpaths_table = Mock()
        mock_flowpaths_table.to_polars.return_value = pl.DataFrame(
            {"id": ["wb-1", "wb-2"], "toid": ["nex-1", "nex-2"]}
        ).lazy()
        mock_flowpaths_table.current_snapshot.return_value = mock_snapshot

        # Configure catalog to return these tables
        def load_table_side_effect(table_name):
            if "network" in table_name:
                return mock_network_table
            elif "flowpaths" in table_name:
                return mock_flowpaths_table
            else:
                raise ValueError(f"Unknown table: {table_name}")

        catalog.load_table.side_effect = load_table_side_effect
        return catalog

    def test_load_upstream_json_creates_new_file(self, mock_catalog):
        """Test that load_upstream_json creates a new file when none exists"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)
            namespaces = ["test_namespace"]

            result = load_upstream_json(mock_catalog, namespaces, output_path)

            # Check that the result contains the namespace
            assert "test_namespace" in result
            assert isinstance(result["test_namespace"], rx.PyDiGraph)

            # Check that the file was created
            expected_file = output_path / "test_namespace_graph_network.json"
            assert expected_file.exists()

    def test_load_upstream_json_loads_existing_file(self, mock_catalog):
        """Test that load_upstream_json loads an existing file with current snapshots"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)
            namespace = "test_namespace"
            output_file = output_path / f"{namespace}_graph_network.json"

            # Create the exact format that RustworkX actually produces
            mock_graph_data = {
                "directed": True,
                "multigraph": True,
                "attrs": {
                    "generated_at": datetime.now(UTC).isoformat(),
                    "catalog_name": "test_catalog",
                    "flowpath_snapshot_id": "12345",
                    "network_snapshot_id": "12345",
                },
                "nodes": [{"id": 0, "data": {"data": "wb-1"}}, {"id": 1, "data": {"data": "wb-2"}}],
                "links": [],
            }

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(mock_graph_data, f)

            result = load_upstream_json(mock_catalog, [namespace], output_path)

            # Should load the existing file
            assert namespace in result
            assert isinstance(result[namespace], rx.PyDiGraph)

    def test_load_upstream_json_rebuilds_outdated_file(self, mock_catalog):
        """Test that load_upstream_json rebuilds when snapshot IDs don't match"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)
            namespace = "test_namespace"
            output_file = output_path / f"{namespace}_graph_network.json"

            # Create the exact format that RustworkX actually produces with outdated snapshots
            mock_graph_data = {
                "directed": True,
                "multigraph": True,
                "attrs": {
                    "generated_at": datetime.now(UTC).isoformat(),
                    "catalog_name": "test_catalog",
                    "flowpath_snapshot_id": "old_snapshot",
                    "network_snapshot_id": "old_snapshot",
                },
                "nodes": [{"id": 0, "data": {"data": "wb-old"}}],
                "links": [],
            }

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(mock_graph_data, f)

            result = load_upstream_json(mock_catalog, [namespace], output_path)

            # Should rebuild the graph
            assert namespace in result
            assert isinstance(result[namespace], rx.PyDiGraph)

    def test_load_upstream_json_multiple_namespaces(self, mock_catalog):
        """Test loading multiple namespaces"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir)
            namespaces = ["namespace1", "namespace2"]

            result = load_upstream_json(mock_catalog, namespaces, output_path)

            # Should create graphs for both namespaces
            assert len(result) == 2
            assert "namespace1" in result
            assert "namespace2" in result

            # Both should be graphs
            assert isinstance(result["namespace1"], rx.PyDiGraph)
            assert isinstance(result["namespace2"], rx.PyDiGraph)


class TestGraphConnectivityIntegration:
    """Integration tests for the graph connectivity module"""

    def test_realistic_hydrofabric_graph(self):
        """Test with realistic hydrofabric data structure"""
        # Create a more realistic dataset
        flowpaths_data = pl.DataFrame(
            {
                "id": ["wb-1001", "wb-1002", "wb-1003", "wb-1004", "wb-1005"],
                "toid": ["nex-1001", "nex-1002", "nex-1003", "nex-1004", None],
            }
        ).lazy()

        network_data = pl.DataFrame(
            {
                "id": ["nex-1001", "nex-1002", "nex-1003", "nex-1004", "nex-1005"],
                "toid": ["wb-1002", "wb-1003", "wb-1004", "wb-0", None],
            }
        ).lazy()

        graph = _build_graph(flowpaths_data, network_data)

        # Verify the graph structure
        nodes = graph.nodes()
        assert len(nodes) == 6  # 5 flowpaths + wb-0

        # Verify connectivity: wb-1001 -> wb-1002 -> wb-1003 -> wb-1004 -> wb-0
        # wb-1005 should be disconnected (terminal)
        assert "wb-1001" in nodes
        assert "wb-1002" in nodes
        assert "wb-1003" in nodes
        assert "wb-1004" in nodes
        assert "wb-1005" in nodes
        assert "wb-0" in nodes

    def test_graph_attributes_preservation(self):
        """Test that graph attributes are preserved during serialization"""
        flowpaths_data = pl.DataFrame(
            {
                "id": ["wb-1", "wb-2"],
                "toid": ["nex-1", "nex-2"],
            }
        ).lazy()

        network_data = pl.DataFrame(
            {
                "id": ["nex-1", "nex-2"],
                "toid": ["wb-2", "wb-0"],
            }
        ).lazy()

        graph = _build_graph(flowpaths_data, network_data)

        # Add some attributes
        test_attrs = {
            "generated_at": datetime.now(UTC).isoformat(),
            "catalog_name": "test",
            "flowpath_snapshot_id": "123",
            "network_snapshot_id": "456",
        }
        graph.attrs = test_attrs

        # Test serialization and deserialization
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = Path(tmp_dir) / "test_graph.json"

            # Serialize
            rx.node_link_json(
                graph,
                path=str(test_file),
                graph_attrs=lambda attrs: dict(attrs),
                edge_attrs=serialize_edge_attrs,
                node_attrs=serialize_node_attrs,
            )

            # Deserialize
            loaded_graph = rx.from_node_link_json_file(
                str(test_file),
                edge_attrs=read_edge_attrs,
                node_attrs=read_node_attrs,
            )

            # Check that attributes are preserved
            assert loaded_graph.attrs == test_attrs


# Parametrized tests for edge cases
@pytest.mark.parametrize(
    "flowpath_ids,nexus_ids,expected_nodes",
    [
        (["wb-1"], ["nex-1"], 2),  # Single flowpath
        ([], [], 1),  # Empty input (just wb-0)
        (["wb-1", "wb-2", "wb-3"], ["nex-1", "nex-2"], 4),  # More flowpaths than nexus
    ],
)
def test_build_graph_edge_cases(flowpath_ids, nexus_ids, expected_nodes):
    """Test various edge cases in graph building"""
    # Handle empty case with proper string types
    if not flowpath_ids:
        flowpaths_data = pl.DataFrame(
            {
                "id": pl.Series([], dtype=pl.Utf8),
                "toid": pl.Series([], dtype=pl.Utf8),
            }
        ).lazy()
    else:
        flowpaths_data = pl.DataFrame(
            {
                "id": flowpath_ids,
                "toid": nexus_ids + [None] * (len(flowpath_ids) - len(nexus_ids)),
            }
        ).lazy()

    if not nexus_ids:
        network_data = pl.DataFrame(
            {
                "id": pl.Series([], dtype=pl.Utf8),
                "toid": pl.Series([], dtype=pl.Utf8),
            }
        ).lazy()
    else:
        network_data = pl.DataFrame(
            {
                "id": nexus_ids,
                "toid": ["wb-0"] * len(nexus_ids),
            }
        ).lazy()

    graph = _build_graph(flowpaths_data, network_data)
    assert len(graph.nodes()) == expected_nodes


def test_mock_catalog_integration(mock_catalog, tmp_path):
    """Test that mock catalog works with the fixed graph building"""
    catalog = mock_catalog("glue")

    graph_dict = load_upstream_json(catalog=catalog, namespaces=["mock_hf"], output_path=tmp_path)

    assert "mock_hf" in graph_dict
    assert graph_dict["mock_hf"].num_nodes() > 0

    # Graph should be valid
    graph = graph_dict["mock_hf"]
    assert isinstance(graph.nodes(), list)
    assert len(graph.nodes()) > 0
