"""A file to hold all replace and route (RnR) geospatial scripts"""

import geopandas as gpd
import numpy as np
import pandas as pd
import polars as pl
from pyiceberg.catalog import Catalog
from pyiceberg.expressions import And, EqualTo, In, LessThanOrEqual

from icefabric.helpers.geopackage import table_to_geopandas, to_geopandas
from icefabric.schemas.hydrofabric import UPSTREAM_VPUS


def get_rnr_segment(
    catalog: Catalog, reach_id: str, domain="conus_hf"
) -> dict[str, pd.DataFrame | gpd.GeoDataFrame]:
    """Returns a geopackage subset from the hydrofabric based on RnR rules

    Parameters
    ----------
    catalog : Catalog
        The iceberg catalog of the hydrofabric
    reach_id : str
        The reach_id, or hf_id, from the NWPS API

    Returns
    -------
    dict[str, pd.DataFrame | gpd.GeoDataFrame]
        a dictionary of dataframes and geodataframes containing HF layers
    """
    network = catalog.load_table(f"{domain}.network")
    origin_row = network.scan(row_filter=f"hf_id = {reach_id}").to_pandas()

    vpu_id = origin_row["vpuid"].iloc[0]
    if vpu_id in UPSTREAM_VPUS:
        vpu_filter = In("vpuid", UPSTREAM_VPUS[vpu_id])
    else:
        vpu_filter = EqualTo("vpuid", vpu_id)

    flowpaths = catalog.load_table(f"{domain}.flowpaths").scan(row_filter=vpu_filter).to_polars()
    lakes = catalog.load_table(f"{domain}.lakes").scan(row_filter=vpu_filter).to_polars()

    pois = catalog.load_table(f"{domain}.pois")
    hydrolocations = catalog.load_table(f"{domain}.hydrolocations")
    divides = catalog.load_table(f"{domain}.divides")
    nexus = catalog.load_table(f"{domain}.nexus")
    flowpath_attr = catalog.load_table(f"{domain}.flowpath-attributes")
    divides_attr = catalog.load_table(f"{domain}.divide-attributes")

    mainstem_expression = EqualTo("hf_mainstem", origin_row["hf_mainstem"].iloc[0])
    hydroseq_expression = LessThanOrEqual("hydroseq", origin_row["hydroseq"].iloc[0])

    combined_filter = And(And(mainstem_expression, hydroseq_expression), vpu_filter)

    # Find all streams with the same stream order
    mainstem_features = network.scan(row_filter=combined_filter).to_polars()
    segment_flowpaths = flowpaths.filter(
        pl.col("divide_id").is_in(mainstem_features["divide_id"].unique().implode())
    )
    joined_df = mainstem_features.join(segment_flowpaths, on="divide_id", how="full")
    stream_order = joined_df.filter(pl.col("hf_id") == int(reach_id))["order"].item()
    filtered_flowpaths = segment_flowpaths.filter(pl.col("order") == stream_order)

    # Find any lakes contained in the RnR segment
    poi_ids = filtered_flowpaths["poi_id"].filter(filtered_flowpaths["poi_id"].is_not_null()).cast(pl.Int64)
    filtered_lakes = lakes.filter(pl.col("poi_id").is_in(poi_ids.implode()))

    if filtered_lakes.shape[0] > 0:
        # Ensuring we break connectivity at lakes
        lake_ids = filtered_lakes["hf_id"].filter(filtered_lakes["hf_id"].is_not_null())
        network_rows = mainstem_features.filter(pl.col("hf_id").is_in(lake_ids.implode()))
        upstream_lake = network_rows[
            "hf_hydroseq"
        ].max()  # since hydroseq decreases as you go downstream, we want the upstream most value
        mainstem_features = mainstem_features.filter(pl.col("hf_hydroseq").ge(upstream_lake))
        segment_flowpaths = flowpaths.filter(
            pl.col("divide_id").is_in(mainstem_features["divide_id"].unique().implode())
        )
        joined_df = mainstem_features.join(segment_flowpaths, on="divide_id", how="full")
        stream_order = joined_df.filter(pl.col("hf_id") == int(reach_id))["order"].item()
        filtered_flowpaths = segment_flowpaths.filter(pl.col("order") == stream_order)

        poi_ids = (
            filtered_flowpaths["poi_id"].filter(filtered_flowpaths["poi_id"].is_not_null()).cast(pl.Int64)
        )
        filtered_lakes = lakes.filter(pl.col("poi_id").is_in(poi_ids.implode()))

    # Convert output to geopandas
    filtered_nexus_points = table_to_geopandas(
        table=nexus, row_filter=In("id", filtered_flowpaths["toid"].to_numpy().tolist())
    )
    filtered_divides = table_to_geopandas(
        table=divides, row_filter=In("divide_id", filtered_flowpaths["divide_id"].to_numpy().tolist())
    )
    filtered_divide_attr = divides_attr.scan(
        row_filter=In("divide_id", filtered_flowpaths["divide_id"].to_numpy().tolist())
    ).to_pandas()
    filtered_flowpath_attr = flowpath_attr.scan(
        row_filter=In("id", filtered_flowpaths["id"].to_numpy().tolist())
    ).to_pandas()
    filtered_pois = pois.scan(row_filter=In("poi_id", poi_ids.to_numpy().tolist())).to_pandas()
    filtered_hydrolocations = hydrolocations.scan(
        row_filter=In("poi_id", poi_ids.to_numpy().tolist())
    ).to_pandas()
    filtered_flowpaths = to_geopandas(filtered_flowpaths.to_pandas())
    filtered_network = network.scan(
        row_filter=In(
            "id", np.concatenate([filtered_flowpaths["toid"].to_numpy(), filtered_flowpaths["id"].to_numpy()])
        )
    ).to_pandas()
    filtered_lakes = to_geopandas(filtered_lakes.to_pandas())

    layers = {
        "flowpaths": filtered_flowpaths,
        "nexus": filtered_nexus_points,
        "divides": filtered_divides,
        "divide-attributes": filtered_divide_attr,
        "network": filtered_network,
        "pois": filtered_pois,
        "flowpath-attributes": filtered_flowpath_attr,
        "hydrolocations": filtered_hydrolocations,
    }
    if len(filtered_lakes) > 0:
        layers["lakes"] = filtered_lakes
    return layers
