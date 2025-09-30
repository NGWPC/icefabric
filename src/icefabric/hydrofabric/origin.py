"""Finds the origin of the Hydrofabric id"""

import pandas as pd
from pyiceberg.table import Table


def find_origin(network_table: Table, identifier: str, id_type: str = "hl_uri") -> pd.DataFrame:
    """Find an origin point in the hydrofabric network.

    This function handles the case where multiple records match the identifier.
    It follows the R implementation to select a single origin point based on
    the minimum hydroseq value.

    Parameters
    ----------
    network_table : Table
        The HF network table from the hydrofabric catalog
    identifier : str
        The unique identifier you want to find the origin of
    id_type : str, optional
        The network table column you can query from, by default "hl_uri"

    Returns
    -------
    pd.DataFrame
        The origin row from the network table

    Raises
    ------
    ValueError
        The provided identifier is not supported
    ValueError
        No origin for the point is found
    ValueError
        Multiple origins for the point are found
    """
    # Filter network table by the identifier
    if id_type == "hl_uri":
        row_filter = f"{id_type} == '{identifier}'"
    elif id_type == "comid":
        row_filter = f"hf_id == {identifier}"
    elif id_type == "id":
        row_filter = f"id == '{identifier}'"
    elif id_type == "poi_id":
        row_filter = f"poi_id == '{identifier}'"
    else:
        raise ValueError(f"Identifier {id_type} not supported")

    # Get all matching records
    origin_candidates = network_table.scan(row_filter=row_filter).to_pandas()

    if len(origin_candidates) == 0:
        raise ValueError(f"No origin found for {id_type}='{identifier}'")

    # Select relevant columns for the origin
    origin_cols = ["id", "toid", "vpuid", "topo", "hydroseq"]
    available_cols = [col for col in origin_cols if col in origin_candidates.columns]

    # Select only the relevant columns and drop duplicates
    origin = origin_candidates[available_cols].drop_duplicates()

    # Find the record with minimum hydroseq
    if "hydroseq" in origin.columns:
        # For consistency with R, check if there are unique hydroseq values
        if len(origin["hydroseq"].unique()) > 1:
            # Sort by hydroseq and take the minimum
            origin = origin.sort_values("hydroseq").iloc[0:1]

    # Throwing an error for multiple origin points
    if len(origin) > 1:
        raise ValueError(f"Multiple origins found: {origin['id'].tolist()}")

    return origin
