"""A file to hold ras cross-section tools"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
from botocore.exceptions import ClientError
from pyiceberg.catalog import Catalog
from pyiceberg.expressions import EqualTo

from icefabric.helpers.geopackage import to_geopandas
from icefabric.schemas.ras_xs import XsType


def subset_xs(
    catalog: Catalog, identifier: str, output_file: Path | None = None, xstype: XsType = XsType.MIP, **kwarg
) -> dict[str, pd.DataFrame | gpd.GeoDataFrame] | None:
    """Returns a geopackage subset from the xs iceberg catalog.

    This function delivers a subset of the cross-sections data by tracing from a
    given HUC identifier & collecting all relevant cross-section information based on
    additional identifiers provided.

    Parameters
    ----------
    catalog : Catalog
        The xs iceberg catalog comprised of the ras cross-sections data tables.
    identifier : str
        The HUC identifier.
    xstype : Type of cross-section data to subset.
        The type of cross-section data to read (e.g. mip, ble).
    output_file : Path, optional
        The output file path where the geopackage will be saved.

    Returns
    -------
    GeoDataFrame
        Subset of the mip cross-sections data based on identifiers.

    """
    ds_reach_id = kwarg.get("ds_reach_id", None)

    try:
        xs_table = catalog.load_table(f"{xstype.value}_xs.{identifier}")

    except ClientError as e:
        msg = "AWS Test account credentials expired. Can't access remote S3 endpoint"
        print(msg)
        raise e

    # By default, mip xs tables are filtered by huc
    df = xs_table.scan().to_pandas()

    if ds_reach_id:
        filter_cond = EqualTo("ds_reach_id", ds_reach_id)
        df = xs_table.scan(row_filter=filter_cond).to_pandas()
    data_gdf = to_geopandas(df)

    # Save data.
    if output_file:
        if len(data_gdf) > 0:
            gpd.GeoDataFrame(data_gdf).to_file(output_file, layer="ras_xs", driver="GPKG")
        else:
            print("Warning: Dataframe is empty")
        return data_gdf
