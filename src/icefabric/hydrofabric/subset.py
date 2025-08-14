"""Functional hydrofabric subset implementation using pre-computed upstream lookup table with Polars"""

import geopandas as gpd
import pandas as pd
import polars as pl
import rustworkx as rx
from pyiceberg.catalog import Catalog
from pyiceberg.expressions import EqualTo, In

from icefabric.helpers.geopackage import to_geopandas
from icefabric.hydrofabric.origin import find_origin
from icefabric.schemas.hydrofabric import UPSTREAM_VPUS, IdType


def get_upstream_segments(origin: str, graph: rx.PyDiGraph) -> set[str]:
    """Subsets the hydrofabric to find all upstream watershed boundaries upstream of the origin fp

    Parameters
    ----------
    origin: str
        The starting point where we're tracing upstream
    graph: rx.PyDiGraph
        a dictionary which preprocesses all toid -> id relationships

    Returns
    -------
    set[str]
        The watershed boundary connections that make up the subset
    """
    indices = graph.node_indices()
    data_list = graph.nodes()
    node_to_index = dict(zip(data_list, indices, strict=False))

    start_idx = node_to_index.get(origin)

    if start_idx is None:
        return set()

    upstream_indices = rx.bfs_predecessors(graph, start_idx)
    flattened = set()
    for key, values in upstream_indices:
        flattened.add(key)
        flattened.update(values)

    return flattened


def subset_layers(
    catalog: Catalog,
    namespace: str,
    layers: list[str],
    upstream_ids: set[str],
    vpu_id: str,
) -> dict[str, pd.DataFrame | gpd.GeoDataFrame]:
    """Efficiently subset a layer using Polars and the upstream IDs

    Parameters
    ----------
    catalog : Catalog
        The pyiceberg catalog
    namespace : str
        the domain / namespace we're reading from in the catalog
    layers : list[str]
        The layers to read into a file
    upstream_ids : set[str]
        _description_
    vpu_id : str
        _description_

    Returns
    -------
    dict[str, pd.DataFrame | gpd.GeoDataFrame]
        _description_
    """
    # Ensuring there are always divides, flowpaths, network, and nexus layers
    if layers is None:
        layers = []
    layers.extend(["divides", "flowpaths", "network", "nexus"])
    layers = list(set(layers))

    upstream_ids_list = list(upstream_ids)

    # Create VPU filter
    if vpu_id in UPSTREAM_VPUS:
        # Use upstream VPUs mapping if available
        vpu_filter = In("vpuid", UPSTREAM_VPUS[vpu_id])
    else:
        # Use single VPU filter
        vpu_filter = EqualTo("vpuid", vpu_id)

    print("Subsetting network layer")
    network = catalog.load_table(f"{namespace}.network").scan(row_filter=vpu_filter).to_polars()
    filtered_network = network.filter(
        pl.col("id").is_in(upstream_ids_list) | pl.col("toid").is_in(upstream_ids_list)
    ).with_columns(
        pl.col("poi_id").map_elements(lambda x: str(int(x)) if x is not None else None, return_dtype=pl.Utf8)
    )
    valid_hf_id = (
        filtered_network.select(pl.col("hf_id").drop_nulls().unique().cast(pl.Float64)).to_series().to_list()
    )

    print("Subsetting flowpaths layer")
    flowpaths = catalog.load_table(f"{namespace}.flowpaths").scan(row_filter=vpu_filter).to_polars()
    filtered_flowpaths = flowpaths.filter(pl.col("id").is_in(upstream_ids_list))
    assert filtered_flowpaths.height > 0, "No flowpaths found"
    filtered_flowpaths_geo = to_geopandas(filtered_flowpaths.to_pandas())

    print("Subsetting nexus layer")
    valid_toids = filtered_flowpaths.filter(pl.col("toid").is_not_null()).get_column("toid").to_list()
    assert valid_toids, "No nexus points found"
    nexus = catalog.load_table(f"{namespace}.nexus").scan(row_filter=vpu_filter).to_polars()
    filtered_nexus_points = nexus.filter(pl.col("id").is_in(valid_toids)).with_columns(
        pl.col("poi_id").map_elements(lambda x: str(int(x)) if x is not None else None, return_dtype=pl.Utf8)
    )
    filtered_nexus_points_geo = to_geopandas(filtered_nexus_points.to_pandas())

    print("Subsetting divides layer")
    valid_divide_ids = (
        filtered_network.filter(pl.col("divide_id").is_not_null()).get_column("divide_id").unique().to_list()
    )
    assert valid_divide_ids, "No valid divide_ids found"
    divides = catalog.load_table(f"{namespace}.divides").scan(row_filter=vpu_filter).to_polars()
    filtered_divides = divides.filter(pl.col("divide_id").is_in(valid_divide_ids))
    filtered_divides_geo = to_geopandas(filtered_divides.to_pandas())

    output_layers = {
        "flowpaths": filtered_flowpaths_geo,
        "nexus": filtered_nexus_points_geo,
        "divides": filtered_divides_geo,
        "network": filtered_network.to_pandas(),  # Convert to pandas for final output
    }

    if "lakes" in layers:
        print("Subsetting lakes layer")
        lakes = catalog.load_table(f"{namespace}.lakes").scan(row_filter=vpu_filter).to_polars()
        filtered_lakes = lakes.filter(pl.col("hf_id").is_in(valid_hf_id))
        filtered_lakes_geo = to_geopandas(filtered_lakes.to_pandas())
        output_layers["lakes"] = filtered_lakes_geo

    if "divide-attributes" in layers:
        print("Subsetting divide-attributes layer")
        divides_attr = (
            catalog.load_table(f"{namespace}.divide-attributes").scan(row_filter=vpu_filter).to_polars()
        )
        filtered_divide_attr = divides_attr.filter(pl.col("divide_id").is_in(valid_divide_ids))
        output_layers["divide-attributes"] = filtered_divide_attr.to_pandas()

    if "flowpath-attributes" in layers:
        print("Subsetting flowpath-attributes layer")
        flowpath_attr = (
            catalog.load_table(f"{namespace}.flowpath-attributes").scan(row_filter=vpu_filter).to_polars()
        )
        filtered_flowpath_attr = flowpath_attr.filter(pl.col("id").is_in(upstream_ids_list))
        output_layers["flowpath-attributes"] = filtered_flowpath_attr.to_pandas()

    if "flowpath-attributes-ml" in layers:
        print("Subsetting flowpath-attributes-ml layer")
        flowpath_attr_ml = (
            catalog.load_table(f"{namespace}.flowpath-attributes-ml").scan(row_filter=vpu_filter).to_polars()
        )
        filtered_flowpath_attr_ml = flowpath_attr_ml.filter(pl.col("id").is_in(upstream_ids_list))
        output_layers["flowpath-attributes-ml"] = filtered_flowpath_attr_ml.to_pandas()

    if "pois" in layers:
        print("Subsetting pois layer")
        pois = catalog.load_table(f"{namespace}.pois").scan(row_filter=vpu_filter).to_polars()
        filtered_pois = pois.filter(pl.col("id").is_in(upstream_ids_list))
        output_layers["pois"] = filtered_pois.to_pandas()

    if "hydrolocations" in layers:
        print("Subsetting hydrolocations layer")
        hydrolocations = (
            catalog.load_table(f"{namespace}.hydrolocations").scan(row_filter=vpu_filter).to_polars()
        )
        filtered_hydrolocations = hydrolocations.filter(pl.col("id").is_in(upstream_ids_list))
        output_layers["hydrolocations"] = filtered_hydrolocations.to_pandas()

    return output_layers


def subset_hydrofabric(
    catalog: Catalog,
    identifier: str | float,
    id_type: IdType,
    layers: list[str],
    namespace: str,
    graph: rx.PyDiGraph,
) -> dict[str, pd.DataFrame | gpd.GeoDataFrame]:
    """
    Main subset function using pre-computed upstream lookup

    Parameters
    ----------
    catalog : Catalog
        PyIceberg catalog
    identifier : str | float
        The identifier to subset around
    id_type : str
        Type of identifier
    layers : List[str]
        List of layers to subset
    namespace : str
        Domain name / namespace
    upstream_dict : Dict[str, Set[str]]
        Pre-computed upstream lookup dictionary

    Returns
    -------
    Dict[str, pl.LazyFrame]
        Dictionary of layer names to their subsetted lazy frames
    """
    print(f"Starting subset for {identifier}")

    network_table = catalog.load_table(f"{namespace}.network").to_polars()
    origin_row = find_origin(network_table, identifier, id_type, return_all=True)
    origin_ids = origin_row.select(pl.col("id")).to_series()
    to_ids = origin_row.select(pl.col("toid")).to_series()
    vpu_id = origin_row.select(pl.col("vpuid")).to_series()[0]  # only need the first
    upstream_ids = set()
    for origin_id, to_id in zip(origin_ids, to_ids, strict=False):
        print(f"Found origin flowpath: {origin_id}")
        _upstream_ids = get_upstream_segments(origin_id, graph)
        upstream_ids |= _upstream_ids  # in-place union
        if len(upstream_ids) == 0:
            upstream_ids.add(origin_id)  # Ensuring the origin WB is captured
        else:
            upstream_ids.add(to_id)  # Adding the nexus point to ensure it's captured in the network table
        print(f"Tracking {len(upstream_ids)} total upstream segments")

    output_layers = subset_layers(
        catalog=catalog, namespace=namespace, layers=layers, upstream_ids=upstream_ids, vpu_id=vpu_id
    )

    return output_layers
