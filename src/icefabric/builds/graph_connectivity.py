"""Creates a rustworkx graph containing network table information"""

from datetime import UTC, datetime
from pathlib import Path

import polars as pl
import rustworkx as rx
from pyiceberg.catalog import Catalog
from tqdm import tqdm


def _build_graph(flowpaths: pl.LazyFrame, network: pl.LazyFrame) -> rx.PyDiGraph:
    """A function to build a rustworkx graph for getting upstream river segments

    Parameters
    ----------
    flowpaths: pl.LazyFrame
        The flowpaths table in LazyFrame mode
    network: pl.LazyFrame
        The network table in LazyFrame mode

    Return
    ------
    rx.PyDiGraph
        The rustworkx graph object
    """
    fp = flowpaths.select([pl.col("id"), pl.col("toid")]).collect()

    if "wb-0" not in fp["id"].to_list():
        wb0_df = pl.DataFrame({"id": ["wb-0"], "toid": [None]})
        fp = pl.concat([fp, wb0_df], how="vertical")

    fp = fp.lazy()

    network_table = network.select([pl.col("id"), pl.col("toid")]).collect()
    network_table = network_table.filter(pl.col("id").str.starts_with("wb-").not_())

    fp = fp.with_row_index(name="idx").collect()
    network_table = network_table.unique(subset=["id"])

    _values = zip(fp["idx"], fp["toid"], strict=False)
    fp = dict(zip(fp["id"], _values, strict=True))

    # define network as a dictionary of nexus ids to downstream flowpath ids
    network_dict = dict(zip(network_table["id"], network_table["toid"], strict=True))

    graph = rx.PyDiGraph(check_cycle=False, node_count_hint=len(fp), edge_count_hint=len(fp))
    gidx = graph.add_nodes_from(fp.keys())
    for idx in tqdm(gidx, desc="Building network graph"):
        id = graph.get_node_data(idx)
        nex = fp[id][1]  # the downstream nexus id
        terminal = False
        ds_wb = network_dict.get(nex)
        if ds_wb is None:
            # we found a terminal nexus
            terminal = True
        if not terminal:
            graph.add_edge(idx, fp[ds_wb][0], nex)

    return graph


def serialize_node_attrs(node_data):
    """Convert node data to string key-value pairs"""
    return {"data": str(node_data)}


def serialize_edge_attrs(edge_data):
    """Convert edge data to string key-value pairs"""
    return {"data": str(edge_data)}


def read_node_attrs(node_data):
    """Convert node data to an output list"""
    return node_data["data"]


def read_edge_attrs(edge_data):
    """Convert edge data to an output list"""
    return edge_data["data"]


def load_upstream_json(catalog: Catalog, namespaces: list[str], output_path: Path) -> dict[str, rx.PyDiGraph]:
    """Builds an upstream lookup graph and save to JSON file

    Parameters
    ----------
    catalog : str
        The pyiceberg catalog
    namespaces : str
        the hydrofabric namespaces to read from
    output_file : Path
        Where the json file should be saved
    """
    graph_dict = {}
    for namespace in namespaces:
        output_file = output_path / f"{namespace}_graph_network.json"
        network_table = catalog.load_table(f"{namespace}.network")
        flowpaths_table = catalog.load_table(f"{namespace}.flowpaths")
        if not output_file.exists():
            graph = _build_graph(flowpaths=flowpaths_table.to_polars(), network=network_table.to_polars())
            graph.attrs = {
                "generated_at": datetime.now(UTC).isoformat(),
                "catalog_name": catalog.name,
                "flowpath_snapshot_id": str(flowpaths_table.current_snapshot().snapshot_id),
                "network_snapshot_id": str(network_table.current_snapshot().snapshot_id),
            }
            output_path.parent.mkdir(parents=True, exist_ok=True)
            rx.node_link_json(
                graph,
                path=str(output_file),
                graph_attrs=lambda attrs: dict(attrs),
                edge_attrs=serialize_edge_attrs,
                node_attrs=serialize_node_attrs,
            )
        else:
            print(f"Loading existing network graph from disk for: {namespace}")
            graph: rx.PyDiGraph = rx.from_node_link_json_file(
                str(output_file),
                edge_attrs=read_edge_attrs,
                node_attrs=read_node_attrs,
            )  # type: ignore
            uses_updated_network_table = graph.attrs["network_snapshot_id"] == str(
                network_table.current_snapshot().snapshot_id
            )
            uses_updated_flowpaths_table = graph.attrs["flowpath_snapshot_id"] == str(
                flowpaths_table.current_snapshot().snapshot_id
            )
            if not uses_updated_network_table or not uses_updated_flowpaths_table:
                graph = _build_graph(
                    flowpaths=flowpaths_table.to_polars(),
                    network=network_table.to_polars(),
                )
                graph.attrs = {
                    "generated_at": datetime.now(UTC).isoformat(),
                    "catalog_name": catalog.name,
                    "flowpath_snapshot_id": str(flowpaths_table.current_snapshot().snapshot_id),
                    "network_snapshot_id": str(network_table.current_snapshot().snapshot_id),
                }
                rx.node_link_json(
                    graph,
                    path=str(output_file),
                    graph_attrs=lambda attrs: attrs,  # using the graph's own attributes
                    edge_attrs=serialize_edge_attrs,
                    node_attrs=serialize_node_attrs,
                )
        graph_dict[namespace] = graph
    return graph_dict
