"""A file to hold all hydrofabric geospatial tools"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
from botocore.exceptions import ClientError
from pyiceberg.catalog import Catalog
from pyiceberg.expressions import And, EqualTo, In
from pyiceberg.table import Table

from icefabric.helpers.geopackage import table_to_geopandas, to_geopandas
from icefabric.hydrofabric.origin import find_origin
from icefabric.schemas.hydrofabric import UPSTREAM_VPUS, HydrofabricDomains, IdType


def get_sorted_network(network_df: pd.DataFrame, outlets: list[str] | str) -> pd.DataFrame:
    """Python implementation similar to R's nhdplusTools::get_sorted().

    This function traces upstream from outlet points through a network topology
    to find all connected upstream segments and their relationships.

    Parameters
    ----------
    network_df : pd.DataFrame
        Network data with 'id' and 'toid' columns representing the topology.
        Each row represents a network segment with its downstream connection.
    outlets : list of str or str
        Outlet IDs to start tracing from. If a single string is provided,
        it will be converted to a list.

    Returns
    -------
    pd.DataFrame
        Sorted network topology with 'id' and 'toid' columns representing
        the upstream connections found during the trace. Each row shows
        a segment and what it flows into.

    Notes
    -----
    The function performs a recursive upstream trace from the specified outlets,
    building a network of all connected upstream segments. It also handles
    special cases like nexus points and ensures all relevant connections
    are captured.
    """
    if isinstance(outlets, str):
        outlets = [outlets]

    # Create a mapping of toid -> list of ids that flow into it
    downstream_map: dict[str, list[str]] = {}
    all_segments: set = set()

    # Build the network mapping
    for _, row in network_df.iterrows():
        segment_id = row["id"]
        toid = row["toid"]
        all_segments.add(segment_id)
        if pd.notna(toid):
            if toid not in downstream_map:
                downstream_map[toid] = []
            downstream_map[toid].append(segment_id)

    visited: set = set()
    sorted_pairs: list[dict[str, str]] = []
    upstream_segments: set = set()

    def trace_upstream_recursive(current_id: str) -> None:
        """Recursively trace upstream from current_id.

        Parameters
        ----------
        current_id : str
            The current segment ID to trace upstream from
        """
        if current_id in visited:
            return
        visited.add(current_id)
        upstream_segments.add(current_id)

        # Find all segments that flow into current_id
        if current_id in downstream_map:
            for upstream_id in downstream_map[current_id]:
                if upstream_id not in visited:
                    sorted_pairs.append({"id": upstream_id, "toid": current_id})
                    trace_upstream_recursive(upstream_id)

    # Start tracing from each outlet
    for outlet in outlets:
        if outlet in all_segments or outlet in downstream_map:
            trace_upstream_recursive(outlet)

    # Additional pass: find any headwater segments that might have been missed
    # These are segments that don't appear as 'toid' for any other segment
    # but are connected to our upstream network
    connected_segments: set = set(upstream_segments)

    # Look for segments that flow into our connected network but weren't found
    for _, row in network_df.iterrows():
        segment_id = row["id"]
        toid = row["toid"]

        # If this segment flows into something we've already found,
        # but we haven't included this segment yet, add it
        if (
            pd.notna(toid)
            and toid in connected_segments
            and segment_id not in connected_segments
            and segment_id not in visited
        ):
            sorted_pairs.append({"id": segment_id, "toid": toid})
            connected_segments.add(segment_id)

    # Specific fix for nexus points: Include nexus points that are targets of our upstream segments
    # but weren't included in the original trace
    all_toids_in_pairs = {pair["toid"] for pair in sorted_pairs}
    for _, row in network_df.iterrows():
        segment_id = row["id"]
        toid = row["toid"]

        # If this segment flows to a nexus point that should be included
        if (
            segment_id in connected_segments
            and pd.notna(toid)
            and toid.startswith("nex-")
            and toid not in all_toids_in_pairs
            and toid not in connected_segments
        ):
            # Add the nexus point as a target
            sorted_pairs.append({"id": segment_id, "toid": toid})
            connected_segments.add(toid)
            print(f"Added missing nexus point: {toid}")

    return pd.DataFrame(sorted_pairs)


def get_all_upstream_ids(network: Table, origin_data: pd.DataFrame) -> list[str]:
    """Get all upstream segment IDs using topology sorting approach.

    This function identifies all upstream segments from a given origin point
    by filtering the network data and performing topology sorting to trace
    upstream connections.

    Parameters
    ----------
    network : pyiceberg.table.Table
        The network table from iceberg catalog containing network topology data
    origin_data : pd.DataFrame
        Single row DataFrame representing the origin point with columns including
        'vpuid', 'toid', and 'id'

    Returns
    -------
    list of str
        All upstream segment IDs found by tracing upstream from the origin point.
        Includes the origin ID itself if not already present.

    Raises
    ------
    AssertionError
        If no upstream topology is found for the given ID

    Notes
    -----
    The function applies VPU (Vector Processing Unit) filtering when available
    to reduce data size. It supports special upstream VPU mappings defined
    in UPSTREAM_VPUS for catchments that may extend across multiple VPUs.
    """
    # Filter network by VPU if available to reduce data size
    network_filters = []

    if "vpuid" in origin_data.columns and pd.notna(origin_data["vpuid"].iloc[0]):
        if origin_data["vpuid"].iloc[0] in UPSTREAM_VPUS.keys():
            vpuid_filter = In("vpuid", UPSTREAM_VPUS[origin_data["vpuid"].iloc[0]])
        else:
            vpuid_filter = EqualTo("vpuid", origin_data["vpuid"].iloc[0])
        network_filters.append(vpuid_filter)

    # Apply filters to get network subset
    if network_filters:
        combined_filter = network_filters[0]
        for filter_expr in network_filters[1:]:
            combined_filter = And(combined_filter, filter_expr)
        network_data = network.scan(row_filter=combined_filter).to_pandas()
    else:
        # Get all network data - might be large, consider adding other filters
        network_data = network.scan().to_pandas()

    # Select only needed columns for topology sorting
    network_subset = network_data[["id", "toid"]].dropna(subset=["id"]).drop_duplicates()

    # Get the outlet (toid of the origin)
    outlets = origin_data["toid"].dropna().tolist()
    if not outlets:
        print("Warning: No outlets found for origin")
        return []

    print(f"Tracing upstream from outlet(s): {list(set(outlets))}")
    # Use topology sorting to find all upstream segments
    topology = get_sorted_network(network_subset, outlets)

    assert len(topology) != 0, "No upstream topology found for ID"

    print(f"Found {len(topology)} topology connections")

    # Don't remove the last row initially - include more segments like R version
    topology = topology.drop_duplicates()

    # Get all unique IDs from topology (include both directions)
    all_ids = pd.concat([topology["id"], topology["toid"]]).dropna().unique().tolist()

    # Also include the origin ID itself
    origin_id = origin_data["id"].iloc[0]
    if origin_id not in all_ids:
        all_ids.append(origin_id)
    return all_ids


def subset(
    catalog: Catalog,
    identifier: str,
    id_type: IdType,
    layers: list[str] | None = None,
    output_file: Path | None = None,
    domain: HydrofabricDomains = HydrofabricDomains.CONUS,
) -> dict[str, pd.DataFrame | gpd.GeoDataFrame] | None:
    """Returns a geopackage subset from the hydrofabric.

    Based on logic from HfsubsetR, this function creates a subset of the
    hydrofabric data by tracing upstream from a given identifier and collecting
    all related geospatial layers.

    Parameters
    ----------
    catalog : Catalog
        The iceberg catalog of the hydrofabric containing all data tables
    identifier : str
        The identifier to start tracing from (e.g., catchment ID, POI ID)
    id_type : IdType
        The type of identifier being used (HL_URI, HF_ID, ID, or POI_ID)
    layers : list of str, optional
        List of layer names to include in the subset. Default layers are
        ["divides", "flowpaths", "network", "nexus"]. Optional layers include
        "divide-attributes", "flowpath-attributes", "flowpath-attributes-ml",
        "pois", and "hydrolocations"
    output_file : Path, optional
        The output file path where the geopackage will be saved. If None,
        returns the data as a dictionary instead of saving to file
    domain : HydrofabricDomains, optional
        The domain to read the HF from

    Returns
    -------
    dict of str to DataFrame/GeoDataFrame, optional
        Dictionary containing the filtered layers with layer names as keys
        and the corresponding data as values. Only returned if output_file
        is None.

    Raises
    ------
    AssertionError
        If no valid divide_ids, flowpaths, or divide IDs are found during
        the subsetting process

    Notes
    -----
    The function performs the following steps:
    1. Finds the origin point using the provided identifier
    2. Traces upstream to find all connected segments
    3. Filters each requested layer to include only relevant features
    4. Converts POI IDs to string format for consistency
    5. Either saves to geopackage or returns the filtered data

    The function handles special data type conversions for poi_id fields
    and filters out None/NaN values appropriately for each layer type.
    """
    # Ensuring there are always divides, flowpaths, network, and nexus layers
    if layers is None:
        layers = []
    layers.extend(["divides", "flowpaths", "network", "nexus"])
    layers = list(set(layers))
    try:
        network = catalog.load_table(f"{domain.value}.network")
        divides = catalog.load_table(f"{domain.value}.divides")
        flowpaths = catalog.load_table(f"{domain.value}.flowpaths")
        nexus = catalog.load_table(f"{domain.value}.nexus")
    except ClientError as e:
        msg = "AWS Test account credentials expired. Can't access remote S3 endpoint"
        print(msg)
        raise e
    # Find the origin point
    origin_row = find_origin(network_table=network, identifier=identifier, id_type=id_type.value)
    origin_filter = EqualTo("id", origin_row["id"].iloc[0])
    origin_data = network.scan(row_filter=origin_filter).to_pandas()

    # Get all upstream segment IDs using topology sorting approach (like R version)
    all_upstream_ids = get_all_upstream_ids(network, origin_data)

    if len(all_upstream_ids) == 0:
        print("No upstream segments found")
        return None

    print(f"Found {len(all_upstream_ids)} upstream segments")

    id_filter = In("id", all_upstream_ids)
    filtered_network = network.scan(row_filter=id_filter).to_pandas()
    filtered_network["poi_id"] = filtered_network["poi_id"].apply(
        lambda x: str(int(x)) if pd.notna(x) else None
    )

    # Get flowpaths for all upstream segments (filter out None values)
    valid_divide_ids = filtered_network["divide_id"].dropna().drop_duplicates().values.tolist()
    assert valid_divide_ids is not None, "No valid divide_ids found"
    filtered_flowpaths = flowpaths.scan(row_filter=In("divide_id", valid_divide_ids)).to_pandas()

    assert len(filtered_flowpaths) > 0, "No flowpaths found"
    valid_toids = filtered_flowpaths["toid"].dropna().values.tolist()  # Filter to remove None values
    assert valid_toids, "No flowpaths found"
    filtered_nexus_points = table_to_geopandas(table=nexus, row_filter=In("id", valid_toids))
    filtered_flowpaths = to_geopandas(filtered_flowpaths)
    filtered_nexus_points["poi_id"] = filtered_nexus_points["poi_id"].apply(
        lambda x: str(int(x)) if pd.notna(x) else None
    )

    valid_divide_ids_for_divides = filtered_flowpaths["divide_id"].dropna().values.tolist()
    assert valid_divide_ids_for_divides is not None, "No divide IDS found"
    filtered_divides = table_to_geopandas(
        table=divides, row_filter=In("divide_id", valid_divide_ids_for_divides)
    )

    output_layers = {
        "flowpaths": filtered_flowpaths,
        "nexus": filtered_nexus_points,
        "divides": filtered_divides,
        "network": filtered_network,
    }

    # Getting any optional fields:
    if "divide-attributes" in layers:
        divides_attr = catalog.load_table(f"{domain.value}.divide-attributes")
        filtered_divide_attr = divides_attr.scan(
            row_filter=In("divide_id", valid_divide_ids_for_divides)
        ).to_pandas()
        output_layers["divide-attributes"] = filtered_divide_attr

    if "flowpath-attributes" in layers:
        flowpath_attr = catalog.load_table(f"{domain.value}.flowpath-attributes")
        valid_flowpath_ids = filtered_flowpaths["id"].dropna().values.tolist()
        filtered_flowpath_attr = flowpath_attr.scan(row_filter=In("id", valid_flowpath_ids)).to_pandas()
        output_layers["flowpath-attributes"] = filtered_flowpath_attr

    if "flowpath-attributes-ml" in layers:
        flowpath_attr_ml = catalog.load_table(f"{domain.value}.flowpath-attributes-ml")
        valid_flowpath_ids = filtered_flowpaths["id"].dropna().values.tolist()
        filtered_flowpath_attr_ml = flowpath_attr_ml.scan(row_filter=In("id", valid_flowpath_ids)).to_pandas()
        output_layers["flowpath-attributes-ml"] = filtered_flowpath_attr_ml

    if "pois" in layers:
        pois = catalog.load_table(f"{domain.value}.pois")
        poi_values = filtered_flowpaths["poi_id"].dropna().values
        filtered_poi_list = list({int(x) for x in poi_values if pd.notna(x)})
        filtered_pois = pois.scan(row_filter=In("poi_id", filtered_poi_list)).to_pandas()
        output_layers["pois"] = filtered_pois

    if "hydrolocations" in layers:
        hydrolocations = catalog.load_table(f"{domain.value}.hydrolocations")
        poi_values = filtered_flowpaths["poi_id"].dropna().values
        filtered_poi_list = list({int(x) for x in poi_values if pd.notna(x)})
        filtered_hydrolocations = hydrolocations.scan(row_filter=In("poi_id", filtered_poi_list)).to_pandas()
        output_layers["hydrolocations"] = filtered_hydrolocations

    if output_file:
        for table_name, _layer in output_layers.items():
            if len(_layer) > 0:  # Only save non-empty layers
                gpd.GeoDataFrame(_layer).to_file(output_file, layer=table_name, driver="GPKG")
            else:
                print(f"Warning: {table_name} layer is empty")
        return None
    else:
        return output_layers
