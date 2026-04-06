import logging
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import geopandas as gpd
import polars as pl
import pyogrio
import rustworkx as rx
from botocore.exceptions import ClientError
from pyiceberg.catalog import Catalog
from pyiceberg.exceptions import NoSuchTableError

from icefabric.cli.streamflow import NoResultsFoundError
from icefabric.schemas.hydrofabric import HydrofabricNamespace

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()

# =============================================================================
# Graph Building
# =============================================================================


def _build_upstream_dict_from_nexus(
    flowpaths_pl: pl.DataFrame, edge_id: str = "fp_id", node_id: str = "nex_id"
) -> dict[int, list[int]]:
    """Build upstream connectivity dictionary from flowpath nexus connections."""
    fp_pl = flowpaths_pl.with_columns(
        [
            pl.col(edge_id).cast(pl.Int32),
            pl.col(f"up_{node_id}").cast(pl.Int32),
            pl.col(f"dn_{node_id}").cast(pl.Int32),
        ]
    )
    nexus_to_downstream = fp_pl.select(
        [pl.col(f"up_{node_id}").alias(node_id), pl.col(edge_id).alias(f"dn_{edge_id}")]
    ).filter(pl.col(node_id).is_not_null())

    nexus_to_upstream = fp_pl.select(
        [pl.col(f"dn_{node_id}").alias(node_id), pl.col(edge_id).alias(f"up_{edge_id}")]
    ).filter(pl.col(node_id).is_not_null())

    connections = nexus_to_upstream.join(nexus_to_downstream, on=node_id, how="inner").select(
        [pl.col(f"dn_{edge_id}"), pl.col(f"up_{edge_id}")]
    )

    upstream_dict_df = connections.group_by(f"dn_{edge_id}").agg(
        pl.col(f"up_{edge_id}").sort().alias("upstream_list")
    )

    return dict(
        zip(
            upstream_dict_df[f"dn_{edge_id}"].to_list(),
            upstream_dict_df["upstream_list"].to_list(),
            strict=False,
        )
    )


def _build_rustworkx_object(
    upstream_network: dict[int, list[int]],
) -> tuple[rx.PyDiGraph, dict[int, int]]:
    """Build a RustWorkX directed graph from upstream network dictionary."""
    graph = rx.PyDiGraph(check_cycle=True)
    node_indices: dict[Any, int] = {}

    for to_edge in sorted(upstream_network.keys()):
        from_edges = upstream_network[to_edge]
        if to_edge not in node_indices:
            node_indices[to_edge] = graph.add_node(to_edge)
        for from_edge in from_edges:
            if from_edge not in node_indices:
                node_indices[from_edge] = graph.add_node(from_edge)

    for to_edge, from_edges in upstream_network.items():
        for from_edge in from_edges:
            graph.add_edge(node_indices[from_edge], node_indices[to_edge], None)

    return graph, node_indices


# =============================================================================
# Data Source Abstraction
# =============================================================================


class HydrofabricSource:
    """Unified interface for reading hydrofabric data from Parquet or Iceberg."""

    def __init__(
        self,
        parquet_dir: Path | None = None,
        catalog: Catalog | None = None,
        namespace: HydrofabricNamespace = HydrofabricNamespace.NHF,
    ):
        self.parquet_dir = parquet_dir
        self.catalog = catalog
        self.namespace = namespace

        if parquet_dir is None and catalog is None:
            raise ValueError("Must provide either parquet_dir or catalog")

    def _get_lazy_frame(self, layer: str) -> pl.LazyFrame | None:
        """Get a LazyFrame for a given layer, or None if the layer doesn't exist."""
        if self.catalog is not None:
            table_id = f"{self.namespace.value}.{layer}"
            try:
                if not self.catalog.table_exists(table_id):
                    return None
                return self.catalog.load_table(table_id).to_polars()
            except (NoSuchTableError, ClientError):
                logger.warning(f"Could not access table {table_id}, treating as missing")
                return None
        else:
            path = self.parquet_dir / f"{layer}.parquet"
            if not path.exists():
                return None
            return pl.scan_parquet(path)

    @staticmethod
    def _empty_for_layer(layer: str) -> pl.DataFrame:
        """Return an empty DataFrame with the correct schema for a missing layer."""
        from icefabric.schemas.iceberg_tables import nhf_layers

        if layer in nhf_layers:
            return pl.from_arrow(nhf_layers[layer].arrow_schema().empty_table())
        return pl.DataFrame()

    def load_filtered(self, layer: str, col: str, ids: set[int]) -> pl.DataFrame:
        """Load a layer filtered by a set of IDs."""
        lf = self._get_lazy_frame(layer)
        if lf is None:
            return self._empty_for_layer(layer)
        return lf.filter(pl.col(col).is_in(ids)).collect()

    def load_filtered_eq(self, layer: str, col: str, value: str) -> pl.DataFrame:
        """Load a layer filtered by string equality."""
        lf = self._get_lazy_frame(layer)
        if lf is None:
            return self._empty_for_layer(layer)
        return lf.filter(pl.col(col) == value).collect()

    def load_columns(self, layer: str, columns: list[str]) -> pl.DataFrame:
        """Load specific columns from a layer."""
        lf = self._get_lazy_frame(layer)
        if lf is None:
            return self._empty_for_layer(layer)
        return lf.select(columns).collect()


# =============================================================================
# Conversion Utilities
# =============================================================================


def pl_to_gdf(pl_df: pl.DataFrame, crs: str = "EPSG:5070") -> gpd.GeoDataFrame:
    """Convert Polars DataFrame with WKB geometry to GeoDataFrame."""
    df = pl_df.to_pandas()
    df["geometry"] = gpd.GeoSeries.from_wkb(df["geometry"])
    return gpd.GeoDataFrame(df, crs=crs)


# =============================================================================
# ID Resolution
# =============================================================================


def resolve_gage_to_flowpath(source: HydrofabricSource, gage_id: str) -> int:
    """Resolve a gage ID to its associated flowpath ID."""
    gage_df = source.load_filtered_eq("gages", "site_no", gage_id)

    if len(gage_df) == 0:
        raise NoResultsFoundError(f"Gage ID '{gage_id}' not found.")

    fp_id = gage_df["fp_id"][0]
    logger.debug(f"Gage '{gage_id}' maps to flowpath {fp_id}")
    return int(fp_id)


def resolve_vpu_to_flowpath_ids(source: HydrofabricSource, vpu_id: str) -> set[int]:
    """Resolve a VPU ID to all flowpath IDs within that VPU."""
    fp_df = source.load_filtered_eq("flowpaths", "vpu_id", vpu_id)

    if len(fp_df) == 0:
        raise NoResultsFoundError(f"VPU ID '{vpu_id}' not found or has no flowpaths.")

    fp_ids = set(fp_df["fp_id"].to_list())
    logger.debug(f"VPU '{vpu_id}' contains {len(fp_ids)} flowpaths")
    return fp_ids


# =============================================================================
# Subsetting Logic
# =============================================================================


def generate_subset_from_ids(
    source: HydrofabricSource,
    flowpath_ids: set[int],
    subset_file: Path | None = None,
) -> dict[str, gpd.GeoDataFrame]:
    """Subset hydrofabric to a given set of flowpath IDs."""
    logger.debug(f"Subsetting {len(flowpath_ids)} flowpaths")

    # Wave 1: fp_id/div_id filtered (parallel)
    with ThreadPoolExecutor(max_workers=6) as ex:
        f = {
            "fp": ex.submit(source.load_filtered, "flowpaths", "fp_id", flowpath_ids),
            "div": ex.submit(source.load_filtered, "divides", "div_id", flowpath_ids),
            "wb": ex.submit(source.load_filtered, "waterbodies", "fp_id", flowpath_ids),
            "gages": ex.submit(source.load_filtered, "gages", "fp_id", flowpath_ids),
            "ref_fp": ex.submit(source.load_filtered, "reference_flowpaths", "div_id", flowpath_ids),
            "lakes": ex.submit(source.load_filtered, "lakes", "fp_id", flowpath_ids),
        }
        subset_fp = f["fp"].result()
        subset_div = f["div"].result()
        subset_wb = f["wb"].result()
        subset_gages = f["gages"].result()
        subset_ref_fp = f["ref_fp"].result()
        subset_lakes = f["lakes"].result()

    # Derive dependent IDs
    all_nex_ids = set(
        subset_fp.filter(pl.col("up_nex_id").is_not_null())["up_nex_id"].cast(pl.Int64).to_list()
        + subset_fp.filter(pl.col("dn_nex_id").is_not_null())["dn_nex_id"].cast(pl.Int64).to_list()
    )
    all_v_fp_ids = set(subset_ref_fp["virtual_fp_id"].to_list())
    wb_hy_ids = subset_wb["hy_id"].to_list() if "hy_id" in subset_wb.columns else []
    gage_hy_ids = subset_gages["hy_id"].to_list() if "hy_id" in subset_gages.columns else []
    all_hy_ids = set(wb_hy_ids + gage_hy_ids)

    # Wave 2: nex_id/virtual_fp_id filtered (parallel)
    with ThreadPoolExecutor(max_workers=2) as ex:
        nex_f = ex.submit(source.load_filtered, "nexus", "nex_id", all_nex_ids)
        v_fp_f = ex.submit(source.load_filtered, "virtual_flowpaths", "virtual_fp_id", all_v_fp_ids)
        hy_id_f = ex.submit(source.load_filtered, "hydrolocations", "hy_id", all_hy_ids)
        subset_nex = nex_f.result()
        subset_v_fp = v_fp_f.result()
        subset_hydrolocations = hy_id_f.result()

    # Wave 3: virtual_nex_id filtered
    all_v_nex_ids = set(
        subset_v_fp.filter(pl.col("up_virtual_nex_id").is_not_null())["up_virtual_nex_id"]
        .cast(pl.Int64)
        .to_list()
        + subset_v_fp.filter(pl.col("dn_virtual_nex_id").is_not_null())["dn_virtual_nex_id"]
        .cast(pl.Int64)
        .to_list()
    )
    subset_v_nex = source.load_filtered("virtual_nexus", "virtual_nex_id", all_v_nex_ids)

    # ======================================================================
    # Post-processing: null out downstream pointers at outlets
    # ======================================================================
    logger.debug("Nulling outlet downstream pointers...")

    subset_nex = subset_nex.with_columns(
        pl.when(pl.col("dn_fp_id").is_in(flowpath_ids))
        .then(pl.col("dn_fp_id"))
        .otherwise(None)
        .alias("dn_fp_id")
    )

    subset_v_fp_ids = set(subset_v_fp["virtual_fp_id"].to_list())
    subset_v_nex = subset_v_nex.with_columns(
        pl.when(pl.col("dn_virtual_fp_id").is_in(subset_v_fp_ids))
        .then(pl.col("dn_virtual_fp_id"))
        .otherwise(None)
        .alias("dn_virtual_fp_id")
    )

    # ======================================================================
    # Write output
    # ======================================================================
    output = {
        "flowpaths": pl_to_gdf(subset_fp),
        "nexus": pl_to_gdf(subset_nex),
        "divides": pl_to_gdf(subset_div),
        "virtual_nexus": pl_to_gdf(subset_v_nex),
        "virtual_flowpaths": pl_to_gdf(subset_v_fp),
        "waterbodies": pl_to_gdf(subset_wb) if len(subset_wb) > 0 else subset_wb.to_pandas(),
        "gages": pl_to_gdf(subset_gages) if len(subset_gages) > 0 else subset_gages.to_pandas(),
        "lakes": pl_to_gdf(subset_lakes) if len(subset_lakes) > 0 else subset_lakes.to_pandas(),
        "reference_flowpaths": subset_ref_fp.to_pandas(),
        "hydrolocations": subset_hydrolocations.to_pandas(),
    }

    if subset_file is not None:
        logger.debug(f"Writing to {subset_file}...")
        subset_file.parent.mkdir(parents=True, exist_ok=True)

        spatial_layers = [
            "flowpaths",
            "nexus",
            "divides",
            "virtual_nexus",
            "virtual_flowpaths",
            "waterbodies",
            "gages",
            "lakes",
        ]
        for name in spatial_layers:
            df = output[name]
            logger.debug(f"  {name}: {len(df)} rows")
            if isinstance(df, gpd.GeoDataFrame) and len(df) > 0:
                pyogrio.write_dataframe(df, subset_file, layer=name)

        nonspatial_layers = ["reference_flowpaths", "hydrolocations"]
        conn = sqlite3.connect(subset_file)
        for name in nonspatial_layers:
            logger.debug(f"  {name}: {len(output[name])} rows")
            output[name].to_sql(name, conn, if_exists="replace", index=False)
        conn.close()

    return output


def generate_subset_upstream(
    source: HydrofabricSource,
    origin: int,
    graph: rx.PyDiGraph,
    node_indices: dict[int, int],
    subset_file: Path | None = None,
) -> dict[str, gpd.GeoDataFrame]:
    """Subset hydrofabric to upstream nodes from a given origin."""
    start_idx = node_indices[origin]
    ancestor_indices = rx.ancestors(graph, start_idx)
    ancestor_ids = {graph[idx] for idx in ancestor_indices} | {origin}

    return generate_subset_from_ids(
        source=source,
        flowpath_ids=ancestor_ids,
        subset_file=subset_file,
    )


# =============================================================================
# Main Entry Point
# =============================================================================


def subset_nhf(
    flowpath_id: int | None = None,
    gage_id: str | None = None,
    vpu_id: str | None = None,
    catalog: Catalog | None = None,
    parquet_dir: Path | None = None,
    output: Path | None = None,
    namespace: HydrofabricNamespace = HydrofabricNamespace.NHF,
) -> dict[str, gpd.GeoDataFrame]:
    """Subset hydrofabric by flowpath ID, gage ID, or VPU ID.

    Parameters
    ----------
    flowpath_id : int | None
        Origin flowpath ID to trace upstream from
    gage_id : str | None
        Gage ID to resolve to a flowpath ID (traces upstream)
    vpu_id : str | None
        VPU ID to extract all flowpaths within
    catalog : bool
        Use Iceberg catalog instead of parquet files
    parquet_dir : Path | None
        Path to parquet directory
    output : Path | None
        Output GeoPackage path

    Returns
    -------
    dict[str, gpd.GeoDataFrame]
        the output layers
    """
    # Validate inputs - exactly one of the three must be provided
    provided = sum(x is not None for x in [flowpath_id, gage_id, vpu_id])
    if provided == 0:
        logger.error("Must provide one of --flowpath-id, --gage-id, or --vpu-id")
        sys.exit(1)
    if provided > 1:
        logger.error("Can only provide one of --flowpath-id, --gage-id, or --vpu-id")
        sys.exit(1)

    # Initialize data source
    if catalog is None:
        if parquet_dir is None:
            logger.error("Must provide --parquet-dir when not using --catalog")
            sys.exit(1)
        if not parquet_dir.exists():
            raise FileNotFoundError(f"Parquet directory not found: {parquet_dir}")

    source = HydrofabricSource(parquet_dir=parquet_dir, catalog=catalog, namespace=namespace)

    # ==================================================================
    # VPU PATH - no graph needed, just filter by vpu_id
    # ==================================================================
    if vpu_id is not None:
        flowpath_ids = resolve_vpu_to_flowpath_ids(source, vpu_id)

        output_layers = generate_subset_from_ids(
            source=source,
            flowpath_ids=flowpath_ids,
            subset_file=output,
        )

        logger.info(f"\nDone! Output: {output}")
        return output_layers

    # ==================================================================
    # UPSTREAM PATH - requires graph traversal
    # ==================================================================

    # Resolve gage_id to flowpath_id if needed
    if gage_id is not None:
        flowpath_id = resolve_gage_to_flowpath(source, gage_id)
    else:
        flowpath_id = int(flowpath_id)

    # Build graph for upstream traversal
    logger.debug("Building network graph...")
    fp_pl = source.load_columns("flowpaths", ["fp_id", "up_nex_id", "dn_nex_id"])
    logger.debug(f"  {len(fp_pl)} flowpaths loaded")

    upstream_dict = _build_upstream_dict_from_nexus(fp_pl)
    graph, node_indices = _build_rustworkx_object(upstream_dict)
    logger.debug(f"  Graph: {graph.num_nodes()} nodes, {graph.num_edges()} edges")

    if flowpath_id not in node_indices:
        raise NoResultsFoundError(f"Flowpath {flowpath_id} not found in network.")

    output_layers = generate_subset_upstream(
        source=source,
        origin=flowpath_id,
        graph=graph,
        node_indices=node_indices,
        subset_file=output,
    )

    logger.info(f"\nDone! Output: {output}")

    return output_layers
