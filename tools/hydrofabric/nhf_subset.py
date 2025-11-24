import argparse
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import polars as pl
import rustworkx as rx

logger = logging.getLogger(__name__)


def _build_upstream_dict_from_nexus(
    flowpaths_pl: pl.DataFrame, edge_id: str = "fp_id", node_id: str = "nex_id"
) -> dict[int, list[int]]:
    """Build upstream connectivity dictionary from flowpath nexus connections.

    Uses nexus IDs as the connection points between flowpaths.

    Parameters
    ----------
    flowpaths_pl : pl.DataFrame
        Flowpaths with fp_id, up_nex_id, dn_nex_id columns

    Returns
    -------
    dict[int, list[int]]
        Dictionary mapping downstream fp_id (int) -> list of upstream fp_ids (int)
    """
    fp_pl = flowpaths_pl.with_columns(
        [
            pl.col(edge_id).cast(pl.Int32),
            pl.col(f"up_{node_id}").cast(pl.Int32),
            pl.col(f"dn_{node_id}").cast(pl.Int32),
        ]
    )
    # Create mapping: nex_id -> downstream fp_id (where this nexus is the upstream nexus)
    nexus_to_downstream = fp_pl.select(
        [
            pl.col(f"up_{node_id}").alias(node_id),
            pl.col(edge_id).alias(f"dn_{edge_id}"),
        ]
    ).filter(pl.col(node_id).is_not_null())

    # Create mapping: nex_id -> upstream fp_id (where this nexus is the downstream nexus)
    nexus_to_upstream = fp_pl.select(
        [
            pl.col(f"dn_{node_id}").alias(node_id),
            pl.col(edge_id).alias(f"up_{edge_id}"),
        ]
    ).filter(pl.col(node_id).is_not_null())

    # Join to find connections: upstream fp -> nexus -> downstream fp
    connections = nexus_to_upstream.join(nexus_to_downstream, on=node_id, how="inner").select(
        [
            pl.col(f"dn_{edge_id}"),
            pl.col(f"up_{edge_id}"),
        ]
    )

    # Group by downstream to get list of upstreams
    upstream_dict_df = connections.group_by(f"dn_{edge_id}").agg(
        pl.col(f"up_{edge_id}").sort().alias("upstream_list")
    )

    # Convert to dictionary
    upstream_dict: dict[int, list[int]] = dict(
        zip(
            upstream_dict_df[f"dn_{edge_id}"].to_list(),
            upstream_dict_df["upstream_list"].to_list(),
            strict=False,
        )
    )

    return upstream_dict


def _build_rustworkx_object(
    upstream_network: dict[str, list[str]] | dict[int, list[int]],
) -> tuple[rx.PyDiGraph, dict[str, int] | dict[int, int]]:
    """Build a RustWorkX directed graph from upstream network dictionary.

    Parameters
    ----------
    upstream_network : dict[str, list[str]] | dict[int, list[int]]
        Dictionary mapping downstream flowpath IDs to lists of upstream flowpath IDs

    Returns
    -------
    tuple[rx.PyDiGraph, dict[str, int] | dict[int, int]]
        The flowpaths object in graph form and node indices for each object in the graph
    """
    graph = rx.PyDiGraph(check_cycle=True)
    node_indices: dict[Any, int] = {}
    for to_edge in sorted(upstream_network.keys()):
        from_edges = upstream_network[to_edge]  # type: ignore
        if to_edge not in node_indices:
            node_indices[to_edge] = graph.add_node(to_edge)
        for from_edge in from_edges:
            if from_edge not in node_indices:
                node_indices[from_edge] = graph.add_node(from_edge)
    for to_edge, from_edges in upstream_network.items():
        for from_edge in from_edges:
            graph.add_edge(node_indices[from_edge], node_indices[to_edge], None)
    return graph, node_indices


def get_upstream_nodes(origin: int, graph: rx.PyDiGraph) -> pd.DataFrame:
    """Get all upstream nodes and their attributes from a given origin node in the graph.

    Parameters
    ----------
    origin: int
        The starting point (node id) where we're tracing upstream
    graph: rx.PyDiGraph
        a dictionary which preprocesses all toid -> id relationships

    Returns
    -------
    pd.DataFrame
        DataFrame containing all upstream nodes and their attributes
    """
    nex = pd.DataFrame.from_records(graph.nodes(), index="nex_id")
    nex["idx"] = graph.node_indices()
    if origin not in nex.index:
        raise ValueError(f"Origin id {origin} not found in graph node ids")
    origin_idx = nex.loc[origin, "idx"]
    upstream_indices = rx.bfs_predecessors(graph, origin_idx)

    flattened: list[dict] = []
    # add origin node itself but with dn_fp_id = -1
    flattened.append({"nex_id": origin, "dn_fp_id": -1})
    # add upstream nodes
    for _, values in upstream_indices:
        flattened.extend(values)

    logger.info(f"Found {len(flattened) - 1} upstream nexus nodes from origin {origin}")

    return pd.DataFrame.from_records(flattened, index="nex_id")


def pl_to_gdf(pl_df: pl.DataFrame, crs: str = "EPSG:5070") -> gpd.GeoDataFrame:
    """Convert Polars DataFrame with WKB geometry to GeoDataFrame."""
    df = pl_df.to_pandas()
    df["geometry"] = gpd.GeoSeries.from_wkb(df["geometry"])
    return gpd.GeoDataFrame(df, crs=crs)


def subset_hydrofabric(
    origin: int,
    graph: rx.PyDiGraph,
    node_indices: dict[str, int] | dict[int, int],
    nhf: Path,
    subset_file: Path | None = None,
):
    """Subset hydrofabric to upstream nodes from a given origin.

    Parameters
    ----------
    origin: int
        Origin fp ID to trace upstream from
    graph: rx.PyDiGraph
        Graph representing the hydrofabric network
    node_indices: dict[str, int] | dict[int, int]
        Mapping of fp_id to graph node indices
    nhf: Path
        Path to the hydrofabric GeoPackage file
    subset_file: Path | None
        Optional path to write subset hydrofabric

    Returns
    -------
    dict[str, pl.DataFrame]
        Dictionary containing all subset layers as Polars DataFrames
    """
    # Get all upstream flowpath IDs
    start_idx = node_indices[origin]
    ancestor_indices = rx.ancestors(graph, start_idx)
    ancestor_ids = [graph[idx] for idx in ancestor_indices] + [origin]
    # Load all layers
    fp = pl.from_pandas(gpd.read_file(nhf, layer="flowpaths").to_wkb())
    nex = pl.from_pandas(gpd.read_file(nhf, layer="nexus").to_wkb())
    div = pl.from_pandas(gpd.read_file(nhf, layer="divides").to_wkb())
    ref_fp = pl.from_pandas(gpd.read_file(nhf, layer="reference_flowpaths"))
    v_nex = pl.from_pandas(gpd.read_file(nhf, layer="virtual_nexus").to_wkb())
    v_fp = pl.from_pandas(gpd.read_file(nhf, layer="virtual_flowpaths").to_wkb())
    wb = pl.from_pandas(gpd.read_file(nhf, layer="waterbodies").to_wkb())
    gages = pl.from_pandas(gpd.read_file(nhf, layer="gages").to_wkb())

    # Subsetting layers
    subset_fp = fp.filter(pl.col("fp_id").is_in(ancestor_ids))
    up_nex_ids = (
        subset_fp.select("up_nex_id")
        .filter(pl.col("up_nex_id").is_not_null())["up_nex_id"]
        .cast(pl.Int64)
        .to_list()
    )
    dn_nex_ids = (
        subset_fp.select("dn_nex_id")
        .filter(pl.col("dn_nex_id").is_not_null())["dn_nex_id"]
        .cast(pl.Int64)
        .to_list()
    )
    all_nex_ids = list(set(up_nex_ids + dn_nex_ids))

    subset_nex = nex.filter(pl.col("nex_id").is_in(all_nex_ids))
    subset_div = div.filter(pl.col("div_id").is_in(ancestor_ids))
    subset_ref_fp = ref_fp.filter(pl.col("div_id").is_in(ancestor_ids))
    all_v_fps = subset_ref_fp.select("virtual_fp_id")["virtual_fp_id"].to_list()
    subset_v_fp = v_fp.filter(pl.col("virtual_fp_id").is_in(all_v_fps))

    v_up_nex_ids = (
        subset_v_fp.select("up_virtual_nex_id")
        .filter(pl.col("up_virtual_nex_id").is_not_null())["up_virtual_nex_id"]
        .cast(pl.Int64)
        .to_list()
    )
    v_dn_nex_ids = (
        subset_v_fp.select("dn_virtual_nex_id")
        .filter(pl.col("dn_virtual_nex_id").is_not_null())["dn_virtual_nex_id"]
        .cast(pl.Int64)
        .to_list()
    )
    all_v_nex_ids = list(set(v_up_nex_ids + v_dn_nex_ids))

    subset_v_nex = v_nex.filter(pl.col("virtual_nex_id").is_in(all_v_nex_ids))
    subset_wb = wb.filter(pl.col("fp_id").is_in(ancestor_ids))
    subset_gages = gages.filter(pl.col("fp_id").is_in(ancestor_ids))

    if subset_file is not None:
        subset_file.parent.mkdir(parents=True, exist_ok=True)
        pl_to_gdf(subset_fp).to_file(subset_file, layer="flowpaths", driver="GPKG")
        pl_to_gdf(subset_nex).to_file(subset_file, layer="nexus", driver="GPKG")
        pl_to_gdf(subset_div).to_file(subset_file, layer="divides", driver="GPKG")
        pl_to_gdf(subset_v_nex).to_file(subset_file, layer="virtual_nexus", driver="GPKG")
        pl_to_gdf(subset_v_fp).to_file(subset_file, layer="virtual_flowpaths", driver="GPKG")
        pl_to_gdf(subset_wb).to_file(subset_file, layer="waterbodies", driver="GPKG")
        pl_to_gdf(subset_gages).to_file(subset_file, layer="gages", driver="GPKG")
        conn = sqlite3.connect(subset_file)
        subset_ref_fp.to_pandas().to_sql("reference_flowpaths", conn, if_exists="replace", index=False)
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Subset a hydrofabric GeoPackage to upstream nodes from a given origin nexus ID.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "nhf",
        type=Path,
        help="Path to the nhf GeoPackage file",
    )
    parser.add_argument(
        "flowpath_id",
        type=int,
        help="Origin nexus ID to trace upstream from",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path for subset GeoPackage (default: subset_origin_<ID>_<input_name>.gpkg)",
    )

    args = parser.parse_args()

    # Validate input file exists
    if not args.nhf.exists():
        logger.error(f"Hydrofabric file {args.nhf} does not exist.")
        sys.exit(1)

    if args.output is None:
        output_file = args.nhf.with_name(f"subset_origin_{args.flowpath_id}_{args.nhf.stem}.gpkg")
    else:
        output_file = args.output

    # Read graph
    print("Reading hydrofabric graph...")
    fp = gpd.read_file(args.nhf, layer="flowpaths")
    fp_pl = pl.from_pandas(fp.drop(columns=["geometry"]))
    upstream_dict = _build_upstream_dict_from_nexus(fp_pl)
    graph, node_indices = _build_rustworkx_object(upstream_dict)

    print("subsetting hydrofabric graph...")
    subset_hydrofabric(
        origin=args.flowpath_id,
        subset_file=output_file,
        graph=graph,
        nhf=args.nhf,
        node_indices=node_indices,
    )

    print(f"subsetting complete! saved to {output_file}")
