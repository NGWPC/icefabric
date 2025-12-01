import argparse
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
from pyiceberg.catalog import Catalog, load_catalog
from pyiceberg.expressions import EqualTo, In

from icefabric.cli.streamflow import NoResultsFoundError
from icefabric.helpers.creds import load_creds

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()


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


def pl_to_gdf(pl_df: pl.DataFrame, crs: str = "EPSG:5070") -> gpd.GeoDataFrame:
    """Convert Polars DataFrame with WKB geometry to GeoDataFrame."""
    df = pl_df.to_pandas()
    df["geometry"] = gpd.GeoSeries.from_wkb(df["geometry"])
    return gpd.GeoDataFrame(df, crs=crs)


def load_parquet_filtered(parquet_dir: Path, layer: str, col: str, ids: set[int]) -> pl.DataFrame:
    """Load parquet with predicate pushdown filtering (for int IDs)."""
    path = parquet_dir / f"{layer}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")
    return pl.scan_parquet(path).filter(pl.col(col).is_in(ids)).collect()


def load_parquet_filtered_str(parquet_dir: Path, layer: str, col: str, value: str) -> pl.DataFrame:
    """Load parquet with predicate pushdown filtering (for string equality)."""
    path = parquet_dir / f"{layer}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")
    return pl.scan_parquet(path).filter(pl.col(col) == value).collect()


def resolve_gage_to_flowpath(
    gage_id: str,
    parquet_dir: Path | None = None,
    catalog: Catalog | None = None,
) -> int:
    """Resolve a gage ID to its associated flowpath ID."""
    if catalog is not None:
        gage_df = catalog.load_table("nhf.gages").scan(row_filter=EqualTo("site_no", gage_id)).to_polars()
    else:
        gages_path = parquet_dir / "gages.parquet"
        if not gages_path.exists():
            raise FileNotFoundError(f"Gages parquet not found: {gages_path}")
        gage_df = pl.scan_parquet(gages_path).filter(pl.col("site_no") == gage_id).collect()

    if len(gage_df) == 0:
        raise NoResultsFoundError(f"Gage ID '{gage_id}' not found.")

    fp_id = gage_df["fp_id"][0]
    logger.debug(f"Gage '{gage_id}' maps to flowpath {fp_id}")
    return int(fp_id)


def resolve_vpu_to_flowpath_ids(
    vpu_id: str,
    parquet_dir: Path | None = None,
    catalog: Catalog | None = None,
) -> set[int]:
    """Resolve a VPU ID to all flowpath IDs within that VPU."""
    if catalog is not None:
        fp_df = (
            catalog.load_table("nhf.flowpaths")
            .scan(row_filter=EqualTo("vpu_id", vpu_id), selected_fields=("fp_id",))
            .to_polars()
        )
    else:
        fp_path = parquet_dir / "flowpaths.parquet"
        if not fp_path.exists():
            raise FileNotFoundError(f"Flowpaths parquet not found: {fp_path}")
        fp_df = pl.scan_parquet(fp_path).filter(pl.col("vpu_id") == vpu_id).select("fp_id").collect()

    if len(fp_df) == 0:
        raise NoResultsFoundError(f"VPU ID '{vpu_id}' not found or has no flowpaths.")

    fp_ids = set(fp_df["fp_id"].to_list())
    logger.debug(f"VPU '{vpu_id}' contains {len(fp_ids)} flowpaths")
    return fp_ids


def generate_subset_from_ids(
    flowpath_ids: set[int],
    parquet_dir: Path | None = None,
    catalog: Catalog | None = None,
    subset_file: Path | None = None,
) -> dict[str, pl.DataFrame]:
    """Subset hydrofabric to a given set of flowpath IDs

    Parameters
    ----------
    flowpath_ids : set[int]
        a set of flowpath ids
    parquet_dir : Path | None, optional
        the directory where the local parquet files exist, by default None
    catalog : Catalog | None, optional
        the pyiceberg catalog, by default None
    subset_file : Path | None, optional
        the output subsetted file, by default None

    Returns
    -------
    dict[str, pl.DataFrame]
        all layers of the hydrofabric
    """
    logger.debug(f"Subsetting {len(flowpath_ids)} flowpaths")

    if catalog is not None:
        # ==================================================================
        # ICEBERG PATH
        # ==================================================================
        logger.debug("Loading from Iceberg catalog...")
        fp_list = list(flowpath_ids)

        with ThreadPoolExecutor(max_workers=5) as ex:
            f = {
                "fp": ex.submit(
                    lambda: catalog.load_table("nhf.flowpaths")
                    .scan(row_filter=In("fp_id", fp_list))
                    .to_polars()
                ),
                "div": ex.submit(
                    lambda: catalog.load_table("nhf.divides")
                    .scan(row_filter=In("div_id", fp_list))
                    .to_polars()
                ),
                "wb": ex.submit(
                    lambda: catalog.load_table("nhf.waterbodies")
                    .scan(row_filter=In("fp_id", fp_list))
                    .to_polars()
                ),
                "gages": ex.submit(
                    lambda: catalog.load_table("nhf.gages").scan(row_filter=In("fp_id", fp_list)).to_polars()
                ),
                "ref_fp": ex.submit(
                    lambda: catalog.load_table("nhf.reference_flowpaths")
                    .scan(row_filter=In("div_id", fp_list))
                    .to_polars()
                ),
            }
            subset_fp = f["fp"].result()
            subset_div = f["div"].result()
            subset_wb = f["wb"].result()
            subset_gages = f["gages"].result()
            subset_ref_fp = f["ref_fp"].result()

        all_nex_ids = set(
            subset_fp.filter(pl.col("up_nex_id").is_not_null())["up_nex_id"].cast(pl.Int64).to_list()
            + subset_fp.filter(pl.col("dn_nex_id").is_not_null())["dn_nex_id"].cast(pl.Int64).to_list()
        )
        all_v_fp_ids = set(subset_ref_fp["virtual_fp_id"].to_list())

        with ThreadPoolExecutor(max_workers=2) as ex:
            nex_f = ex.submit(
                lambda: catalog.load_table("nhf.nexus")
                .scan(row_filter=In("nex_id", list(all_nex_ids)))
                .to_polars()
            )
            v_fp_f = ex.submit(
                lambda: catalog.load_table("nhf.virtual_flowpaths")
                .scan(row_filter=In("virtual_fp_id", list(all_v_fp_ids)))
                .to_polars()
            )
            subset_nex = nex_f.result()
            subset_v_fp = v_fp_f.result()

        all_v_nex_ids = set(
            subset_v_fp.filter(pl.col("up_virtual_nex_id").is_not_null())["up_virtual_nex_id"]
            .cast(pl.Int64)
            .to_list()
            + subset_v_fp.filter(pl.col("dn_virtual_nex_id").is_not_null())["dn_virtual_nex_id"]
            .cast(pl.Int64)
            .to_list()
        )
        subset_v_nex = (
            catalog.load_table("nhf.virtual_nexus")
            .scan(row_filter=In("virtual_nex_id", list(all_v_nex_ids)))
            .to_polars()
        )

    else:
        # ==================================================================
        # PARQUET PATH (Polars with predicate pushdown)
        # ==================================================================
        logger.debug(f"Loading from Parquet: {parquet_dir}")

        # Wave 1: fp_id/div_id filtered
        with ThreadPoolExecutor(max_workers=5) as ex:
            f = {
                "fp": ex.submit(load_parquet_filtered, parquet_dir, "flowpaths", "fp_id", flowpath_ids),
                "div": ex.submit(load_parquet_filtered, parquet_dir, "divides", "div_id", flowpath_ids),
                "wb": ex.submit(load_parquet_filtered, parquet_dir, "waterbodies", "fp_id", flowpath_ids),
                "gages": ex.submit(load_parquet_filtered, parquet_dir, "gages", "fp_id", flowpath_ids),
                "ref_fp": ex.submit(
                    load_parquet_filtered, parquet_dir, "reference_flowpaths", "div_id", flowpath_ids
                ),
            }
            subset_fp = f["fp"].result()
            subset_div = f["div"].result()
            subset_wb = f["wb"].result()
            subset_gages = f["gages"].result()
            subset_ref_fp = f["ref_fp"].result()

        # Derive dependent IDs
        all_nex_ids = set(
            subset_fp.filter(pl.col("up_nex_id").is_not_null())["up_nex_id"].cast(pl.Int64).to_list()
            + subset_fp.filter(pl.col("dn_nex_id").is_not_null())["dn_nex_id"].cast(pl.Int64).to_list()
        )
        all_v_fp_ids = set(subset_ref_fp["virtual_fp_id"].to_list())

        # Wave 2: nex_id/virtual_fp_id filtered
        with ThreadPoolExecutor(max_workers=2) as ex:
            nex_f = ex.submit(load_parquet_filtered, parquet_dir, "nexus", "nex_id", all_nex_ids)
            v_fp_f = ex.submit(
                load_parquet_filtered, parquet_dir, "virtual_flowpaths", "virtual_fp_id", all_v_fp_ids
            )
            subset_nex = nex_f.result()
            subset_v_fp = v_fp_f.result()

        # Wave 3: virtual_nex_id filtered
        all_v_nex_ids = set(
            subset_v_fp.filter(pl.col("up_virtual_nex_id").is_not_null())["up_virtual_nex_id"]
            .cast(pl.Int64)
            .to_list()
            + subset_v_fp.filter(pl.col("dn_virtual_nex_id").is_not_null())["dn_virtual_nex_id"]
            .cast(pl.Int64)
            .to_list()
        )
        subset_v_nex = load_parquet_filtered(parquet_dir, "virtual_nexus", "virtual_nex_id", all_v_nex_ids)

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
    if subset_file is not None:
        logger.debug(f"Writing to {subset_file}...")
        subset_file.parent.mkdir(parents=True, exist_ok=True)

        for name, df in [
            ("flowpaths", subset_fp),
            ("nexus", subset_nex),
            ("divides", subset_div),
            ("virtual_nexus", subset_v_nex),
            ("virtual_flowpaths", subset_v_fp),
            ("waterbodies", subset_wb),
            ("gages", subset_gages),
        ]:
            logger.debug(f"  {name}: {len(df)} rows")
            pyogrio.write_dataframe(pl_to_gdf(df), subset_file, layer=name)

        logger.debug(f"  reference_flowpaths: {len(subset_ref_fp)} rows")
        conn = sqlite3.connect(subset_file)
        subset_ref_fp.to_pandas().to_sql("reference_flowpaths", conn, if_exists="replace", index=False)
        conn.close()

    return {
        "flowpaths": subset_fp,
        "nexus": subset_nex,
        "divides": subset_div,
        "virtual_nexus": subset_v_nex,
        "virtual_flowpaths": subset_v_fp,
        "waterbodies": subset_wb,
        "gages": subset_gages,
        "reference_flowpaths": subset_ref_fp,
    }


def generate_subset_upstream(
    origin: int,
    graph: rx.PyDiGraph,
    node_indices: dict[int, int],
    parquet_dir: Path | None = None,
    catalog: Catalog | None = None,
    subset_file: Path | None = None,
) -> dict[str, pl.DataFrame]:
    """Subset hydrofabric to upstream nodes from a given origin."""
    start_idx = node_indices[origin]
    ancestor_indices = rx.ancestors(graph, start_idx)
    ancestor_ids = {graph[idx] for idx in ancestor_indices} | {origin}

    return generate_subset_from_ids(
        flowpath_ids=ancestor_ids,
        parquet_dir=parquet_dir,
        catalog=catalog,
        subset_file=subset_file,
    )


def subset_hydrofabric(
    flowpath_id: int | None = None,
    gage_id: str | None = None,
    vpu_id: str | None = None,
    catalog: bool = False,
    parquet_dir: Path | None = None,
    output: Path | None = None,
):
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
    """
    # Validate inputs - exactly one of the three must be provided
    provided = sum(x is not None for x in [flowpath_id, gage_id, vpu_id])
    if provided == 0:
        logger.error("Must provide one of --flowpath-id, --gage-id, or --vpu-id")
        sys.exit(1)
    if provided > 1:
        logger.error("Can only provide one of --flowpath-id, --gage-id, or --vpu-id")
        sys.exit(1)

    iceberg_catalog: Catalog | None = None

    if catalog:
        logger.debug("Using Iceberg catalog...")
        load_creds()
        iceberg_catalog = load_catalog("glue")
    else:
        if parquet_dir is None:
            logger.error("Must provide --parquet-dir when not using --catalog")
            sys.exit(1)
        if not parquet_dir.exists():
            raise FileNotFoundError(f"Parquet directory not found: {parquet_dir}")

    # ==================================================================
    # VPU PATH - no graph needed, just filter by vpu_id
    # ==================================================================
    if vpu_id is not None:
        output_file = output or Path(f"subset_vpu_{vpu_id}.gpkg")

        flowpath_ids = resolve_vpu_to_flowpath_ids(vpu_id, parquet_dir, iceberg_catalog)

        generate_subset_from_ids(
            flowpath_ids=flowpath_ids,
            parquet_dir=parquet_dir,
            catalog=iceberg_catalog,
            subset_file=output_file,
        )

        logger.info(f"\nDone! Output: {output_file}")
        return

    # ==================================================================
    # UPSTREAM PATH - requires graph traversal
    # ==================================================================

    # Resolve gage_id to flowpath_id if needed
    if gage_id is not None:
        flowpath_id = resolve_gage_to_flowpath(gage_id, parquet_dir, iceberg_catalog)
        output_file = output or Path(f"subset_gage_{gage_id}.gpkg")
    else:
        flowpath_id = int(flowpath_id)
        output_file = output or Path(f"subset_{flowpath_id}.gpkg")

    # Build graph for upstream traversal
    logger.debug("Building network graph...")
    if iceberg_catalog:
        fp_pl = (
            iceberg_catalog.load_table("nhf.flowpaths")
            .scan(selected_fields=("fp_id", "up_nex_id", "dn_nex_id"))
            .to_polars()
        )
    else:
        fp_path = parquet_dir / "flowpaths.parquet"
        if not fp_path.exists():
            raise FileNotFoundError(f"Flowpaths parquet not found: {fp_path}")
        fp_pl = pl.scan_parquet(fp_path).select(["fp_id", "up_nex_id", "dn_nex_id"]).collect()

    logger.debug(f"  {len(fp_pl)} flowpaths loaded")

    upstream_dict = _build_upstream_dict_from_nexus(fp_pl)
    graph, node_indices = _build_rustworkx_object(upstream_dict)
    logger.debug(f"  Graph: {graph.num_nodes()} nodes, {graph.num_edges()} edges")

    if flowpath_id not in node_indices:
        raise NoResultsFoundError(f"Flowpath {flowpath_id} not found in network.")

    generate_subset_upstream(
        origin=flowpath_id,
        graph=graph,
        node_indices=node_indices,
        parquet_dir=parquet_dir,
        catalog=iceberg_catalog,
        subset_file=output_file,
    )

    logger.info(f"\nDone! Output: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Subset hydrofabric by flowpath, gage, or VPU.")
    parser.add_argument("-c", "--catalog", action="store_true", help="Use Iceberg catalog")
    parser.add_argument("-p", "--parquet-dir", type=Path, help="Path to parquet directory")
    parser.add_argument("-f", "--flowpath-id", type=int, help="Origin flowpath ID (traces upstream)")
    parser.add_argument("-g", "--gage-id", type=str, help="Gage ID (traces upstream from gage's flowpath)")
    parser.add_argument("-v", "--vpu-id", type=str, help="VPU ID (extracts entire VPU)")
    parser.add_argument("-o", "--output", type=Path, help="Output GeoPackage path")

    args = parser.parse_args()
    subset_hydrofabric(
        flowpath_id=args.flowpath_id,
        gage_id=args.gage_id,
        vpu_id=args.vpu_id,
        catalog=args.catalog,
        parquet_dir=args.parquet_dir,
        output=args.output,
    )
