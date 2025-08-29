import os
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl
import pyarrow as pa
import pytest
import rustworkx as rx
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from pyiceberg.catalog import Catalog, load_catalog
from pyiceberg.expressions import EqualTo, In
from pyprojroot import here

from app.main import app
from icefabric.builds import load_upstream_json
from icefabric.builds.graph_connectivity import read_edge_attrs, read_node_attrs
from icefabric.schemas import NGWPCTestLocations

"""
Unified Mock PyIceberg Catalog Test Suite for Hydrofabric v2.2 Data using RustworkX Graph
"""

# Load the sample graph from the actual graph file
SAMPLE_GRAPH: rx.PyDiGraph = rx.from_node_link_json_file(
    str(here() / "data/hi_hf_graph_network.json"),
    edge_attrs=read_edge_attrs,
    node_attrs=read_node_attrs,
)  # type: ignore


class MockSnapshot:
    """Mock Pyiceberg snapshot"""

    def __init__(self):
        self.snapshot_id = "0"


class MockTable:
    """Mock PyIceberg Table with realistic Hawaii hydrofabric data"""

    def __init__(self, table_name: str, data: pd.DataFrame):
        self.table_name = table_name
        self.data = data
        self.current_snapshot = MockSnapshot
        self._polars_data = pl.from_pandas(data).lazy()

    def scan(self, row_filter=None):
        """Mock scan method that applies filters"""
        return MockScan(self._polars_data, row_filter)

    def to_polars(self) -> pl.LazyFrame:
        """Returns data as Polars DataFrame"""
        return self._polars_data


class MockScan:
    """Mock scan result that can be filtered and converted"""

    def __init__(self, data: pl.LazyFrame, row_filter=None):
        self.data = data
        self.row_filter = row_filter

    def _apply_filters(self) -> pl.DataFrame:
        """Apply filters to the data and return filtered Polars DataFrame"""
        if self.row_filter is None:
            return self.data.collect()

        # Handle different filter types
        if isinstance(self.row_filter, EqualTo):
            column_name = self.row_filter.term.name
            value = self.row_filter.literal.value
            return self.data.filter(pl.col(column_name) == value).collect()
        elif isinstance(self.row_filter, In):
            column_name = self.row_filter.term.name
            values = [lit.value for lit in self.row_filter.literals]
            return self.data.filter(pl.col(column_name).is_in(values)).collect()

        return self.data.collect()

    def to_polars(self) -> pl.DataFrame:
        """Apply filters and returns a Polars DataFrame"""
        return self._apply_filters()

    def to_pandas(self) -> pd.DataFrame:
        """Apply filters and returns a Pandas DataFrame"""
        return self._apply_filters().to_pandas()

    def to_arrow(self) -> pa.Table:
        """Returns data as arrow table"""
        return pa.Table.from_pandas()


class MockCatalog:
    """Mock PyIceberg Catalog with sample Hawaii hydrofabric data based on RustworkX graph"""

    def __init__(self, catalog_type: str = "glue"):
        self.catalog_type = catalog_type
        self.connectivity_graph = SAMPLE_GRAPH
        self.name = "mock_hf"
        self.tables = self._create_sample_tables()

    def load_table(self, table_name: str) -> MockTable:
        """Load a mock table by name"""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} not found")
        return self.tables[table_name]

    def get_connectivity_graph(self, namespace: str = "mock_hf") -> rx.PyDiGraph:
        """Get the pre-built connectivity graph for the given namespace"""
        return self.connectivity_graph

    def _extract_graph_relationships(self) -> dict[str, Any]:
        """Extract connectivity relationships from the RustworkX graph"""
        nodes = self.connectivity_graph.nodes()

        # Build node relationships from the graph
        node_to_downstream = {}

        for edge_idx in self.connectivity_graph.edge_indices():
            source_idx, target_idx = self.connectivity_graph.get_edge_endpoints_by_index(edge_idx)
            source_node = self.connectivity_graph.get_node_data(source_idx)
            target_node = self.connectivity_graph.get_node_data(target_idx)
            nexus_id = self.connectivity_graph.get_edge_data_by_index(edge_idx)

            node_to_downstream[source_node] = {"target": target_node, "nexus": nexus_id}

        return {"nodes": nodes, "relationships": node_to_downstream}

    def _create_sample_tables(self) -> dict[str, MockTable]:
        """Create sample hydrofabric tables based on the RustworkX graph"""
        tables = {}

        # Extract relationships from the graph
        graph_info = self._extract_graph_relationships()

        # Network table - core connectivity data
        network_data = self._create_network_data_from_graph(graph_info)
        tables["mock_hf.network"] = MockTable("mock_hf.network", network_data)

        # Flowpaths table - stream geometry
        flowpaths_data = self._create_flowpaths_data(network_data)
        tables["mock_hf.flowpaths"] = MockTable("mock_hf.flowpaths", flowpaths_data)

        # Nexus table - connection points
        nexus_data = self._create_nexus_data(network_data)
        tables["mock_hf.nexus"] = MockTable("mock_hf.nexus", nexus_data)

        # Divides table - watershed boundaries
        divides_data = self._create_divides_data(network_data)
        tables["mock_hf.divides"] = MockTable("mock_hf.divides", divides_data)

        # Lakes table
        lakes_data = self._create_lakes_data()
        tables["mock_hf.lakes"] = MockTable("mock_hf.lakes", lakes_data)

        # Attribute tables
        tables["mock_hf.divide-attributes"] = MockTable(
            "mock_hf.divide-attributes", self._create_divide_attributes(divides_data)
        )
        tables["mock_hf.flowpath-attributes"] = MockTable(
            "mock_hf.flowpath-attributes", self._create_flowpath_attributes(flowpaths_data)
        )
        tables["mock_hf.flowpath-attributes-ml"] = MockTable(
            "mock_hf.flowpath-attributes-ml", self._create_flowpath_attributes_ml()
        )
        tables["mock_hf.pois"] = MockTable("mock_hf.pois", self._create_pois_data(network_data))
        tables["mock_hf.hydrolocations"] = MockTable(
            "mock_hf.hydrolocations", self._create_hydrolocations_data()
        )

        tables["divide_parameters.sac-sma_conus"] = MockTable(
            "divide_parameters.sac-sma_conus", self._create_sac_sma_divide_parameters(network_data)
        )
        tables["divide_parameters.snow-17_conus"] = MockTable(
            "divide_parameters.snow-17_conus", self._create_snow17_divide_parameters(network_data)
        )

        return tables

    def _create_network_data_from_graph(self, graph_info: dict[str, Any]) -> pd.DataFrame:
        """Create network data based on the actual RustworkX graph structure"""
        network_data = []
        poi_counter = 0
        hydroseq_counter = 1

        nodes = graph_info["nodes"]
        relationships = graph_info["relationships"]

        # Create flowpath records for each node in the graph
        for node_id in nodes:
            if not node_id.startswith("wb-"):
                continue

            wb_num = int(node_id.split("-")[1])

            # Get downstream connection from graph
            downstream_info = relationships.get(node_id, {})
            toid = downstream_info.get("nexus")  # The nexus this wb flows to

            # Some records have POIs
            has_poi = poi_counter % 10 == 0  # Every 10th watershed has a POI
            poi_id = float(poi_counter) if has_poi else None
            poi_counter += 1

            # Create the flowpath record
            record = {
                "id": node_id,
                "toid": toid,
                "divide_id": f"cat-{wb_num}",
                "ds_id": None,
                "mainstem": None,
                "poi_id": poi_id,
                "hydroseq": float(hydroseq_counter),
                "hf_source": "NHDPlusHR",
                "hf_id": str(wb_num),
                "lengthkm": round(0.5 + (wb_num % 100) / 10.0, 2),
                "areasqkm": round(1.0 + (wb_num % 500) / 10.0, 2),
                "tot_drainage_areasqkm": round(10.0 + (wb_num % 5000) / 10.0, 2),
                "type": "waterbody",
                "vpuid": "hi",
                "topo": "fl-nex",
                "hl_uri": f"gages-{wb_num:06d}" if has_poi else None,
            }

            network_data.append(record)
            hydroseq_counter += 1

        # Create nexus records based on the edges in the graph
        for source_node, info in relationships.items():
            if not source_node.startswith("wb-"):
                continue

            nexus_id = info.get("nexus")
            target_node = info.get("target")

            if nexus_id and target_node:
                source_num = int(source_node.split("-")[1])

                # Determine nexus type based on target
                if target_node == "wb-0":
                    nexus_type = "terminal"
                elif target_node.startswith("cnx-"):
                    nexus_type = "coastal"
                else:
                    nexus_type = "network"

                nexus_record = {
                    "id": nexus_id,
                    "toid": target_node,
                    "divide_id": f"cat-{source_num}",
                    "ds_id": None,
                    "mainstem": None,
                    "poi_id": None,
                    "hydroseq": float(hydroseq_counter),
                    "hf_source": "NHDPlusHR",
                    "hf_id": str(source_num),
                    "lengthkm": 0.01 if nexus_type != "terminal" else 0.001,
                    "areasqkm": 0.001 if nexus_type != "terminal" else 0.0001,
                    "tot_drainage_areasqkm": 0.01 if nexus_type != "terminal" else 0.001,
                    "type": nexus_type,
                    "vpuid": "hi",
                    "topo": "fl-nex",
                    "hl_uri": None,
                }

                network_data.append(nexus_record)
                hydroseq_counter += 1

        # Add wb-0 if not present (the ultimate outlet)
        wb_ids = [record["id"] for record in network_data if record["id"] and record["id"].startswith("wb-")]
        if "wb-0" not in wb_ids:
            wb0_record = {
                "id": "wb-0",
                "toid": None,
                "divide_id": "cat-0",
                "ds_id": None,
                "mainstem": None,
                "poi_id": None,
                "hydroseq": float(hydroseq_counter),
                "hf_source": "NHDPlusHR",
                "hf_id": "0",
                "lengthkm": 0.0,
                "areasqkm": 0.0,
                "tot_drainage_areasqkm": 0.0,
                "type": "outlet",
                "vpuid": "hi",
                "topo": "fl-nex",
                "hl_uri": None,
            }
            network_data.append(wb0_record)

        return pd.DataFrame(network_data)

    def _create_flowpaths_data(self, network_df: pd.DataFrame) -> pd.DataFrame:
        """Create sample flowpath geometry data"""
        flowpaths = []

        # Filter to only wb-* records (flowpaths)
        wb_records = network_df[network_df["id"].str.startswith("wb-", na=False)]

        for _, row in wb_records.iterrows():
            # Create a simple LineString geometry as binary (matching real schema)
            geometry_binary = b"\x01\x01\x00\x00\x00fl#\xd5g\xaf\x13\xc1\x96!\x8e\xa5\xfe\x14.A"

            flowpaths.append(
                {
                    "id": row["id"],
                    "toid": row["toid"],
                    "mainstem": None,  # DoubleType
                    "order": float(hash(row["id"]) % 7 + 1),  # DoubleType, stream order 1-7
                    "hydroseq": int(row["hydroseq"]) if row["hydroseq"] else None,  # IntegerType
                    "lengthkm": row["lengthkm"],  # DoubleType
                    "areasqkm": row["areasqkm"],  # DoubleType
                    "tot_drainage_areasqkm": row["tot_drainage_areasqkm"],  # DoubleType
                    "has_divide": True,  # BooleanType
                    "divide_id": row["divide_id"],  # StringType
                    "poi_id": str(int(row["poi_id"])) if pd.notna(row["poi_id"]) else None,  # StringType
                    "vpuid": "hi",  # StringType
                    "geometry": geometry_binary,  # BinaryType
                }
            )

        return pd.DataFrame(flowpaths)

    def _create_nexus_data(self, network_df: pd.DataFrame) -> pd.DataFrame:
        """Create sample nexus point data matching Hawaii schema"""
        nexus_points = []

        # Create nexus points for toids
        unique_toids = network_df["toid"].dropna().unique()

        counter = 1
        for toid in unique_toids:
            if toid and not toid.endswith("_downstream"):
                # Create mock binary geometry for Point (copying from a HY Nexus)
                geometry_binary = b"\x01\x01\x00\x00\x00fl#\xd5g\xaf\x13\xc1\x96!\x8e\xa5\xfe\x14.A"

                # Determine type and poi_id
                if toid.startswith("cnx-"):
                    nexus_type = "coastal"
                    poi_id = None
                elif toid.startswith("nex-"):
                    nexus_type = "network"
                    poi_id = str(counter) if counter % 3 == 0 else None
                elif toid.startswith("tnx-"):
                    nexus_type = "terminal"
                    poi_id = None
                else:
                    nexus_type = "network"
                    poi_id = None

                nexus_points.append(
                    {
                        "id": toid,
                        "toid": "wb-0" if nexus_type == "coastal" else None,
                        "poi_id": poi_id,  # StringType
                        "type": nexus_type,  # StringType
                        "vpuid": "hi",  # StringType
                        "geometry": geometry_binary,  # BinaryType
                    }
                )
                counter += 1

        return pd.DataFrame(nexus_points)

    def _create_divides_data(self, network_df: pd.DataFrame) -> pd.DataFrame:
        """Create sample watershed divide geometry data matching Hawaii schema"""
        divides = []

        # Filter to only wb-* records (flowpaths have divides)
        wb_records = network_df[network_df["id"].str.startswith("wb-", na=False)]

        for _, row in wb_records.iterrows():
            # Create a simple polygon for the watershed boundary as binary
            geometry_binary = b"\x01\x01\x00\x00\x00fl#\xd5g\xaf\x13\xc1\x96!\x8e\xa5\xfe\x14.A"

            # Determine toid and type based on actual network structure
            if pd.isna(row["toid"]) or row["toid"] == "wb-0":
                divide_type = "terminal"
                toid = f"tnx-{hash(row['id']) % 1000000}"  # Terminal nexus
            elif row["toid"] and row["toid"].startswith("cnx-"):
                divide_type = "coastal"
                toid = row["toid"]
            else:
                divide_type = "network"
                toid = row["toid"]

            divides.append(
                {
                    "divide_id": row["divide_id"],
                    "toid": toid,
                    "type": divide_type,  # StringType
                    "ds_id": None,  # DoubleType
                    "areasqkm": row["areasqkm"],  # DoubleType
                    "id": row["id"],  # StringType
                    "lengthkm": row["lengthkm"],  # DoubleType
                    "tot_drainage_areasqkm": row["tot_drainage_areasqkm"],  # DoubleType
                    "has_flowline": True,  # BooleanType
                    "vpuid": "hi",  # StringType
                    "geometry": geometry_binary,  # BinaryType
                }
            )

        return pd.DataFrame(divides)

    # ... (rest of the helper methods remain the same)
    def _create_lakes_data(self) -> pd.DataFrame:
        """Create sample lakes data matching Hawaii schema"""
        lakes = []

        # Create a few lakes with realistic Hawaii schema
        for i in range(5, 10):  # Create 5 lakes
            x = -100.0 + i * 0.02
            y = 40.0 + i * 0.02

            # Create mock binary geometry for Point (lake centroid)
            geometry_binary = b"\x01\x01\x00\x00\x00fl#\xd5g\xaf\x13\xc1\x96!\x8e\xa5\xfe\x14.A"

            lakes.append(
                {
                    "lake_id": float(800020000 + i),  # DoubleType
                    "LkArea": round(0.1 + i * 0.3, 2),  # DoubleType
                    "LkMxE": round(90.0 + i * 50, 2),  # DoubleType
                    "WeirC": 2.6,  # DoubleType
                    "WeirL": 10.0,  # DoubleType
                    "OrificeC": 0.6,  # DoubleType
                    "OrificeA": 1.0,  # DoubleType
                    "OrificeE": 10.0,  # DoubleType
                    "WeirE": 15.0,  # DoubleType
                    "ifd": 0.9,  # DoubleType
                    "Dam_Length": 100.0,  # DoubleType
                    "domain": "hi",  # StringType
                    "poi_id": i + 1000,  # IntegerType
                    "hf_id": float(8000010000000 + i),  # DoubleType
                    "reservoir_index_AnA": None,  # DoubleType
                    "reservoir_index_Extended_AnA": None,  # DoubleType
                    "reservoir_index_GDL_AK": None,  # DoubleType
                    "reservoir_index_Medium_Range": None,  # DoubleType
                    "reservoir_index_Short_Range": None,  # DoubleType
                    "res_id": f"res-{800020000 + i}",  # StringType
                    "vpuid": "hi",  # StringType
                    "lake_x": x,  # DoubleType
                    "lake_y": y,  # DoubleType
                    "geometry": geometry_binary,  # BinaryType
                }
            )
        return pd.DataFrame(lakes)

    def _create_divide_attributes(self, divides_df: pd.DataFrame) -> pd.DataFrame:
        """Create sample divide attributes data matching Hawaii schema"""
        attributes = []
        for _, row in divides_df.iterrows():
            # Create realistic soil and vegetation parameters
            attributes.append(
                {
                    "divide_id": row["divide_id"],  # StringType
                    "mode.bexp_soil_layers_stag.1": 7.457384,  # DoubleType
                    "mode.bexp_soil_layers_stag.2": 7.457384,  # DoubleType
                    "mode.bexp_soil_layers_stag.3": 7.457384,  # DoubleType
                    "mode.bexp_soil_layers_stag.4": 7.457384,  # DoubleType
                    "mode.ISLTYP": 1.0,  # DoubleType
                    "mode.IVGTYP": 7.0,  # DoubleType
                    "geom_mean.dksat_soil_layers_stag.1": 0.000012,  # DoubleType
                    "geom_mean.dksat_soil_layers_stag.2": 0.000012,  # DoubleType
                    "geom_mean.dksat_soil_layers_stag.3": 0.000012,  # DoubleType
                    "geom_mean.dksat_soil_layers_stag.4": 0.000012,  # DoubleType
                    "geom_mean.psisat_soil_layers_stag.1": -0.355872,  # DoubleType
                    "geom_mean.psisat_soil_layers_stag.2": -0.355872,  # DoubleType
                    "geom_mean.psisat_soil_layers_stag.3": -0.355872,  # DoubleType
                    "geom_mean.psisat_soil_layers_stag.4": -0.355872,  # DoubleType
                    "mean.cwpvt": 0.5,  # DoubleType
                    "mean.mfsno": 2.5,  # DoubleType
                    "mean.mp": 0.0,  # DoubleType
                    "mean.refkdt": 3.0,  # DoubleType
                    "mean.slope_1km": 0.1 + (hash(row["divide_id"]) % 50) / 500.0,  # DoubleType
                    "mean.smcmax_soil_layers_stag.1": 0.476,  # DoubleType
                    "mean.smcmax_soil_layers_stag.2": 0.476,  # DoubleType
                    "mean.smcmax_soil_layers_stag.3": 0.476,  # DoubleType
                    "mean.smcmax_soil_layers_stag.4": 0.476,  # DoubleType
                    "mean.smcwlt_soil_layers_stag.1": 0.135,  # DoubleType
                    "mean.smcwlt_soil_layers_stag.2": 0.135,  # DoubleType
                    "mean.smcwlt_soil_layers_stag.3": 0.135,  # DoubleType
                    "mean.smcwlt_soil_layers_stag.4": 0.135,  # DoubleType
                    "mean.vcmx25": 45.0,  # DoubleType
                    "mean.Coeff": 0.5,  # DoubleType
                    "mean.Zmax": 1.0,  # DoubleType
                    "mode.Expon": 3.0,  # DoubleType
                    "X": -100.0 + (hash(row["divide_id"]) % 1000) / 1000.0,  # DoubleType
                    "Y": 40.0 + (hash(row["divide_id"]) % 500) / 500.0,  # DoubleType
                    "mean.impervious": 0.1,  # DoubleType
                    "mean.elevation": 500.0 + hash(row["divide_id"]) % 1000,  # DoubleType
                    "mean.slope": 0.05 + (hash(row["divide_id"]) % 100) / 1000.0,  # DoubleType
                    "circ_mean.aspect": 180.0,  # DoubleType
                    "dist_4.twi": '[{"v":0.6137,"frequency":0.2501},{"v":2.558,"frequency":0.2499}]',  # StringType
                    "vpuid": "hi",  # StringType
                }
            )

        return pd.DataFrame(attributes)

    def _create_sac_sma_divide_parameters(self, network_df: pd.DataFrame) -> pd.DataFrame:
        """Create sample SAC-SMA divide parameters data matching CONUS schema"""
        attributes = []
        wb_records = network_df[network_df["id"].str.startswith("wb-", na=False)]

        for _, row in wb_records.iterrows():
            # Create realistic SAC-SMA parameters using hash for reproducible variation
            divide_hash = hash(row["divide_id"])
            attributes.append(
                {
                    "divide_id": row["divide_id"],  # StringType
                    "lzfpm": 80.0 + (divide_hash % 500) / 10.0,  # DoubleType
                    "lzfsm": 5.0 + (divide_hash % 200) / 20.0,  # DoubleType
                    "lzpk": 0.01 + (divide_hash % 50) / 2000.0,  # DoubleType
                    "lzsk": 0.10 + (divide_hash % 100) / 1000.0,  # DoubleType
                    "lztwm": 100.0 + (divide_hash % 600) / 10.0,  # DoubleType
                    "pfree": 0.05 + (divide_hash % 200) / 1000.0,  # DoubleType
                    "rexp": 1.0 + (divide_hash % 150) / 100.0,  # DoubleType
                    "uzfwm": 20.0 + (divide_hash % 200) / 10.0,  # DoubleType
                    "uzk": 0.30 + (divide_hash % 200) / 1000.0,  # DoubleType
                    "uztwm": 30.0 + (divide_hash % 300) / 10.0,  # DoubleType
                    "zperc": 40.0 + (divide_hash % 800) / 10.0,  # DoubleType
                }
            )

        return pd.DataFrame(attributes)

    def _create_snow17_divide_parameters(self, network_df: pd.DataFrame) -> pd.DataFrame:
        """Create sample Snow-17 divide parameters data matching CONUS schema"""
        attributes = []
        wb_records = network_df[network_df["id"].str.startswith("wb-", na=False)]

        for _, row in wb_records.iterrows():
            # Create realistic Snow-17 parameters using hash for reproducible variation
            divide_hash = hash(row["divide_id"])
            attributes.append(
                {
                    "divide_id": row["divide_id"],  # StringType
                    "mfmax": 1.5 + (divide_hash % 300) / 1000.0,  # DoubleType
                    "mfmin": 0.3 + (divide_hash % 100) / 1000.0,  # DoubleType
                    "uadj": 0.05 + (divide_hash % 50) / 1000.0,  # DoubleType
                }
            )

        return pd.DataFrame(attributes)

    def _create_flowpath_attributes(self, flowpath_df: pd.DataFrame) -> pd.DataFrame:
        """Create sample flowpath attributes data matching schema"""
        attributes = []
        for _, row in flowpath_df.iterrows():
            attributes.append(
                {
                    "link": row["id"],  # StringType
                    "to": row["toid"],  # StringType
                    "Length_m": (row["lengthkm"] * 1000) if row["lengthkm"] else None,  # DoubleType
                    "Y": round(0.5 + (hash(row["id"]) % 100) / 200.0, 6),  # DoubleType
                    "n": 0.035,  # DoubleType - Manning's n
                    "nCC": 0.035,  # DoubleType
                    "BtmWdth": 2.0,  # DoubleType
                    "TopWdth": 10.0,  # DoubleType
                    "TopWdthCC": 10.0,  # DoubleType
                    "ChSlp": 0.1,  # DoubleType
                    "alt": 1,  # IntegerType
                    "So": 0.01 + (hash(row["id"]) % 50) / 1000.0,  # DoubleType - slope
                    "MusX": 1800.0,  # DoubleType
                    "MusK": 0.2,  # DoubleType
                    "gage": None,  # StringType
                    "gage_nex_id": None,  # StringType
                    "WaterbodyID": None,  # StringType
                    "waterbody_nex_id": None,  # StringType
                    "id": row["id"],  # StringType
                    "toid": row["toid"],  # StringType
                    "vpuid": "hi",  # StringType
                }
            )

        return pd.DataFrame(attributes)

    def _create_flowpath_attributes_ml(self) -> pd.DataFrame:
        """Create sample ML flowpath attributes data"""
        # This table doesn't exist in the Hawaii schema based on the samples
        # Return empty DataFrame with expected structure
        return pd.DataFrame(columns=["id", "vpuid", "predicted_flow", "confidence"])

    def _create_pois_data(self, network_df: pd.DataFrame) -> pd.DataFrame:
        """Create sample points of interest data matching Hawaii schema"""
        pois = []

        # Create POIs for records that have poi_id
        poi_records = network_df[network_df["poi_id"].notna()]

        for _, row in poi_records.iterrows():
            # Create corresponding nexus ID
            if row["toid"] and row["toid"].startswith("nex-"):
                nex_id = row["toid"]
            else:
                nex_id = f"tnx-{hash(row['id']) % 1000000}"

            pois.append(
                {
                    "poi_id": int(row["poi_id"]),  # IntegerType
                    "id": row["id"],  # StringType
                    "nex_id": nex_id,  # StringType
                    "vpuid": "hi",  # StringType
                }
            )

        return pd.DataFrame(pois)

    def _create_hydrolocations_data(self) -> pd.DataFrame:
        """Create sample hydrolocations data matching Hawaii schema"""
        hydrolocations = []

        # Create some realistic hydrolocations based on graph nodes
        nodes = self.connectivity_graph.nodes()
        sample_nodes = [node for node in nodes if node.startswith("wb-")][:10]  # Take first 10

        for i, node_id in enumerate(sample_nodes):
            wb_num = int(node_id.split("-")[1])

            # Determine if this is a coastal or gage location
            is_coastal = i % 3 == 0

            if is_coastal:
                hl_data = {
                    "poi_id": i + 20,
                    "id": node_id,
                    "nex_id": f"tnx-{1000000000 + wb_num}",
                    "hl_link": f"HI{i + 1}",
                    "hl_reference": "coastal",
                    "hl_source": "NOAAOWP",
                    "hl_uri": f"coastal-HI{i + 1}",
                }
            else:
                hl_data = {
                    "poi_id": i + 20,
                    "id": node_id,
                    "nex_id": f"nex-{wb_num}",
                    "hl_link": f"167{wb_num:05d}",
                    "hl_reference": "gages",
                    "hl_source": "NWIS",
                    "hl_uri": f"gages-167{wb_num:05d}",
                }

            hydrolocations.append(
                {
                    **hl_data,
                    "hf_id": 8.000010e13,  # DoubleType
                    "vpuid": "hi",  # StringType
                }
            )

        return pd.DataFrame(hydrolocations)


# Utility functions for test setup
def create_test_environment(tmp_path: Path) -> dict[str, Any]:
    """Create a complete test environment with mock catalogs and graph data"""

    # Create a test graph file path
    graph_file = tmp_path / "data" / "hydrofabric" / "hi_hf_graph_network.json"
    graph_file.parent.mkdir(parents=True, exist_ok=True)

    # Create a simple test graph if the file doesn't exist
    if not graph_file.exists():
        test_graph = rx.PyDiGraph()
        # Add some test nodes and edges
        node1 = test_graph.add_node("wb-1001")
        node2 = test_graph.add_node("wb-1002")
        node3 = test_graph.add_node("wb-0")
        test_graph.add_edge(node1, node2, "nex-1001")
        test_graph.add_edge(node2, node3, "nex-1002")

        # Add metadata
        test_graph.attrs = {
            "generated_at": "2024-01-01T00:00:00+00:00",
            "catalog_name": "test",
            "flowpath_snapshot_id": "test_snapshot_123",
            "network_snapshot_id": "test_snapshot_456",
        }

        # Save the test graph
        from icefabric.builds.graph_connectivity import serialize_edge_attrs, serialize_node_attrs

        rx.node_link_json(
            test_graph,
            path=str(graph_file),
            graph_attrs=lambda attrs: dict(attrs),
            edge_attrs=serialize_edge_attrs,
            node_attrs=serialize_node_attrs,
        )

    # Create mock catalogs
    glue_catalog = MockCatalog("glue")
    sql_catalog = MockCatalog("sql")

    return {
        "glue_catalog": glue_catalog,
        "sql_catalog": sql_catalog,
        "graph_file": graph_file,
        "tmp_path": tmp_path,
    }


# Setting .env/.pyiceberg creds based on project root
env_path = Path.cwd() / ".env"
load_dotenv(dotenv_path=env_path)
pyiceberg_file = Path.cwd() / ".pyiceberg.yaml"
if pyiceberg_file.exists():
    os.environ["PYICEBERG_HOME"] = str(here())
else:
    raise FileNotFoundError(
        "Cannot find .pyiceberg.yaml. Please download this from NGWPC confluence or create "
    )

# Test data constants
sample_hf_uri = [
    "gages-01010000",
    "gages-02450825",
    "gages-03173000",
    "gages-04100500",
    "gages-05473450",
    "gages-06823500",
    "gages-07060710",
    "gages-08070000",
    "gages-09253000",
    "gages-10316500",
    "gages-11456000",
    "gages-12411000",
    "gages-13337000",
    "gages-14020000",
]

test_ic_rasters = [f for f in NGWPCTestLocations._member_names_ if "TOPO" in f]
local_ic_rasters = [
    here() / "tests/data/topo_tifs/nws-nos-surveys/Albemarle_Sound_NOS_NCEI",
    here() / "tests/data/topo_tifs/nws-nos-surveys/Chesapeake_Bay_NOS_NCEI",
    here() / "tests/data/topo_tifs/nws-nos-surveys/Mobile_Bay_NOS_NCEI",
    here() / "tests/data/topo_tifs/nws-nos-surveys/Tangier_Sound_NOS_NCEI",
    here() / "tests/data/topo_tifs/tbdem_alaska_10m",
    here() / "tests/data/topo_tifs/tbdem_alaska_30m",
    here() / "tests/data/topo_tifs/tbdem_conus_atlantic_gulf_30m",
    here() / "tests/data/topo_tifs/tbdem_conus_pacific_30m",
    here() / "tests/data/topo_tifs/tbdem_great_lakes_30m",
    here() / "tests/data/topo_tifs/tbdem_hawaii_10m",
    here() / "tests/data/topo_tifs/tbdem_hawaii_30m",
    here() / "tests/data/topo_tifs/tbdem_pr_usvi_10m",
    here() / "tests/data/topo_tifs/tbdem_pr_usvi_30m",
]


# Pytest fixtures
@pytest.fixture
def mock_catalog():
    """Fixture providing a mock Glue catalog with RustworkX graph"""
    return MockCatalog


@pytest.fixture
def sample_graph() -> rx.PyDiGraph:
    """Fixture providing the sample RustworkX graph"""
    return SAMPLE_GRAPH


@pytest.fixture
def temp_graph_file(tmp_path):
    """Fixture creating a temporary graph file for testing"""
    graph_file = tmp_path / "hi_hf_graph_network.json"
    graph_file.parent.mkdir(parents=True, exist_ok=True)

    # Create a simple test graph
    test_graph = rx.PyDiGraph()
    node1 = test_graph.add_node("wb-1001")
    node2 = test_graph.add_node("wb-1002")
    node3 = test_graph.add_node("wb-0")
    test_graph.add_edge(node1, node2, "nex-1001")
    test_graph.add_edge(node2, node3, "nex-1002")

    test_graph.attrs = {
        "generated_at": "2024-01-01T00:00:00+00:00",
        "catalog_name": "test",
        "flowpath_snapshot_id": "test_snapshot_123",
        "network_snapshot_id": "test_snapshot_456",
    }

    # Save using the same serialization functions
    from icefabric.builds.graph_connectivity import serialize_edge_attrs, serialize_node_attrs

    rx.node_link_json(
        test_graph,
        path=str(graph_file),
        graph_attrs=lambda attrs: dict(attrs),
        edge_attrs=serialize_edge_attrs,
        node_attrs=serialize_node_attrs,
    )

    return graph_file


@pytest.fixture(params=test_ic_rasters)
def ic_raster(request) -> str:
    """Returns AWS S3 icechunk stores/rasters for checking correctness"""
    return request.param


@pytest.fixture(params=local_ic_rasters)
def local_ic_raster(request) -> Path:
    """Returns local icechunk stores/rasters for checking correctness"""
    return request.param


@pytest.fixture(params=sample_hf_uri)
def gauge_hf_uri(request) -> str:
    """Returns individual gauge identifiers for parameterized testing"""
    return request.param


@pytest.fixture
def testing_dir() -> Path:
    """Returns the testing data dir"""
    return here() / "tests/data/"


@pytest.fixture(scope="session")
def remote_client():
    """Create a test client for the FastAPI app with real Glue catalog."""
    catalog = load_catalog("glue")
    hydrofabric_namespaces = ["conus_hf", "ak_hf", "gl_hf", "hi_hf", "prvi_hf"]
    app.state.catalog = catalog
    app.state.network_graphs = load_upstream_json(
        catalog=catalog,
        namespaces=hydrofabric_namespaces,
        output_path=here() / "data",
    )
    return TestClient(app)


@pytest.fixture(scope="session")
def client():
    """Create a test client for the FastAPI app with mock catalog."""
    app.state.catalog = MockCatalog()  # defaulting to use the mock catalog
    return TestClient(app)


@pytest.fixture
def local_usgs_streamflow_csv():
    """Returns a locally downloaded CSV file from a specific gauge and time"""
    file_path = here() / "tests/data/usgs_01010000_data_from_20211231_1400_to_20220101_1400.csv"
    return pd.read_csv(file_path)


@pytest.fixture
def local_usgs_streamflow_parquet():
    """Returns a locally downloaded Parquet file from a specific gauge and time"""
    file_path = here() / "tests/data/usgs_01010000_data_from_20211231_1400_to_20220101_1400.parquet"
    return pd.read_parquet(file_path)


@pytest.fixture
def hydrofabric_catalog() -> Catalog:
    """Returns an iceberg catalog object for the hydrofabric"""
    return load_catalog("glue")


@pytest.fixture(params=["wb-1435", "wb-1440", "wb-1686", "wb-1961"])
def test_wb_id(request):
    """Fixture providing test watershed IDs for parameterized tests"""
    return request.param


# Pytest configuration functions
def pytest_addoption(parser):
    """Adds custom command line options for pytest"""
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
        help="Run local tests",
    )


def pytest_collection_modifyitems(config, items):
    """Modifies test collection based on command line options"""
    if not config.getoption("--run-slow"):
        skipper = pytest.mark.skip(reason="Only run when --run-slow is given")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skipper)

    if not config.getoption("--run-local"):
        skipper = pytest.mark.skip(reason="Only run when --run-local is given")
        for item in items:
            if "local" in item.keywords:
                item.add_marker(skipper)


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow tests")
    config.addinivalue_line("markers", "local: marks tests as local tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
