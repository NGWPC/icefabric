"""A file to hold all replace and route (RnR) geospatial scripts"""

import geopandas as gpd
import numpy as np
import pandas as pd
from pyiceberg.catalog import Catalog
from pyiceberg.expressions import And, EqualTo, In, LessThanOrEqual

from icefabric.helpers.geopackage import table_to_geopandas, to_geopandas


def get_rnr_segment(catalog: Catalog, reach_id: str, output_file: str) -> gpd.GeoDataFrame | None:
    """Returns a geopackage subset from the hydrofabric based on RnR rules

    Parameters
    ----------
    catalog : Catalog
        The iceberg catalog of the hydrofabric
    reach_id : str
        The reach_id, or hf_id, from the NWPS API
    output_file : str
        The output file where we want to save the geopackage

    Returns
    -------
    gpd.GeoDataFrame
        _description_
    """
    network = catalog.load_table("hydrofabric.network")
    divides = catalog.load_table("hydrofabric.divides")
    flowpaths = catalog.load_table("hydrofabric.flowpaths")
    divides_attr = catalog.load_table("hydrofabric.divide-attributes")
    flowpaths = catalog.load_table("hydrofabric.flowpaths")
    flowpath_attr = catalog.load_table("hydrofabric.flowpath-attributes")
    flowpath_attr_ml = catalog.load_table("hydrofabric.flowpath-attributes-ml")
    nexus = catalog.load_table("hydrofabric.nexus")
    pois = catalog.load_table("hydrofabric.pois")
    hydrolocations = catalog.load_table("hydrofabric.hydrolocations")

    origin_row = network.scan(row_filter=f"hf_id = {reach_id}").to_pandas()
    mainstem_expression = EqualTo("hf_mainstem", origin_row["hf_mainstem"].values[0])
    hydroseq_expression = LessThanOrEqual("hydroseq", origin_row["hydroseq"].values[0])
    combined_filter = And(mainstem_expression, hydroseq_expression)

    # Find all streams with the same stream order
    # TODO Determine lakes to break segments
    mainstem_features = network.scan(row_filter=combined_filter).to_pandas()
    segment_flowpaths = flowpaths.scan(
        row_filter=In("divide_id", mainstem_features["divide_id"].drop_duplicates().values)
    ).to_pandas()
    joined_df = pd.merge(mainstem_features, segment_flowpaths, on="divide_id", how="outer")
    stream_order = joined_df[joined_df["hf_id"] == reach_id]["order"].values[0]
    filtered_flowpaths = segment_flowpaths[segment_flowpaths["order"] == stream_order]
    filtered_poi_list = [
        int(_id)
        for _id in segment_flowpaths[segment_flowpaths["order"] == stream_order]["poi_id"].values
        if _id is not None
    ]

    # Get full river network
    filtered_nexus_points = table_to_geopandas(table=nexus, row_filter=In("id", filtered_flowpaths["toid"]))
    filtered_divides = table_to_geopandas(
        table=divides, row_filter=In("divide_id", filtered_flowpaths["divide_id"])
    )
    filtered_divide_attr = divides_attr.scan(
        row_filter=In("divide_id", filtered_flowpaths["divide_id"])
    ).to_pandas()
    filtered_flowpath_attr = flowpath_attr.scan(row_filter=In("id", filtered_flowpaths["id"])).to_pandas()
    filtered_flowpath_attr_ml = flowpath_attr_ml.scan(
        row_filter=In("id", filtered_flowpaths["id"])
    ).to_pandas()
    filtered_pois = pois.scan(row_filter=In("poi_id", filtered_poi_list)).to_pandas()
    filtered_hydrolocations = hydrolocations.scan(row_filter=In("poi_id", filtered_poi_list)).to_pandas()
    filtered_flowpaths = to_geopandas(filtered_flowpaths)
    filtered_network = network.scan(
        row_filter=In(
            "id", np.concatenate([filtered_flowpaths["toid"].values, filtered_flowpaths["id"].values])
        )
    ).to_pandas()

    layers = {
        "flowpaths": filtered_flowpaths,
        "nexus": filtered_nexus_points,
        "divides": filtered_divides,
        "divide-attributes": filtered_divide_attr,
        "network": filtered_network,
        "pois": filtered_pois,
        "flowpath-attributes-ml": filtered_flowpath_attr_ml,
        "flowpath-attributes": filtered_flowpath_attr,
        # "lakes": filtered_water_bodies,
        "hydrolocations": filtered_hydrolocations,
    }
    for table, layer in layers.items():
        gpd.GeoDataFrame(layer).to_file(output_file, layer=table, driver="GPKG")
