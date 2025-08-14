"""Finds the origin of the Hydrofabric id"""

import polars as pl
from polars import LazyFrame

from icefabric.schemas.hydrofabric import IdType


def find_origin(
    network_table: LazyFrame,
    identifier: str | float,
    id_type: IdType = IdType.HL_URI,
    return_all: bool = False,
) -> pl.DataFrame:
    """Find an origin point in the hydrofabric network.

    This function handles the case where multiple records match the identifier.
    It follows the R implementation to select a single origin point based on
    the minimum hydroseq value.

    Parameters
    ----------
    network_table : LazyFrame
        The HF network table from the hydrofabric catalog
    identifier : str | float
        The unique identifier you want to find the origin of
    id_type : IdType, optional
        The network table column you can query from, by default "hl_uri"
    return_all: bool, False
        Returns all origin points (for subsetting)

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
    # Get all matching records
    origin_candidates = (
        network_table.filter(pl.col(id_type.value).is_not_null() & (pl.col(id_type.value) == identifier))
        .select(["id", "toid", "vpuid", "hydroseq", "poi_id", "hl_uri"])
        .collect()
    )

    if origin_candidates.height == 0:
        raise ValueError(f"No origin found for {id_type}='{identifier}'")

    origin = origin_candidates.unique()

    if not return_all:
        # Find the record with minimum hydroseq if column exists
        if "hydroseq" in origin.columns:
            # Check if there are multiple unique hydroseq values
            unique_hydroseq = origin.select(pl.col("hydroseq").unique())
            if unique_hydroseq.height > 1:
                # Sort by hydroseq and take the first row (minimum)
                origin = origin.sort("hydroseq").slice(0, 1)

        # Check for multiple origins after processing
        if origin.height > 1:
            origin_ids = origin.get_column("id").to_list()
            raise ValueError(f"Multiple origins found: {origin_ids}")

    return origin
