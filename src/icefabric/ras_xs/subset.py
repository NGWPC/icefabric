"""A file to hold ras cross-section tools"""

from pathlib import Path

import geopandas as gpd
import pandas as pd
from botocore.exceptions import ClientError
from pyiceberg.catalog import Catalog
from pyiceberg.expressions import And, EqualTo, GreaterThanOrEqual, LessThanOrEqual
from pyiceberg.expressions.literals import literal
from shapely.geometry import Polygon

from icefabric.helpers.geopackage import to_geopandas
from icefabric.schemas.ras_xs import XsType


def subset_xs(
    catalog: Catalog,
    xstype: XsType = XsType.CONFLATED,
    identifier: str | None = None,
    bbox: Polygon | None = None,
    output_file: Path | None = None,
) -> dict[str, pd.DataFrame | gpd.GeoDataFrame] | None:
    """Returns a geopackage subset from the RAS XS iceberg catalog.

    This function delivers a subset of the cross-sectional data by filtering the data with either a
    given flowpath identifier or bounding box. Collects all relevant cross-sectional information in a
    geopackage.

    Parameters
    ----------
    catalog : Catalog
        The iceberg catalog containing the RAS XS data
    xstype : XsType, optional
        The schema of cross-sectional data to subset (conflated or representative).
    identifier : str, optional
        The flowpath ID. Used when subsetting on flowpath ID.
    bbox : Polygon, optional
        A lat/lon bounding box for subsetting based on geospatial location.
    output_file : Path, optional
        The output file path where the geopackage will be saved.

    Returns
    -------
    GeoDataFrame
        Subset of the cross-sectional data based on identifiers.
    """
    try:
        xs_table = catalog.load_table(f"ras_xs.{xstype.value}")
    except ClientError as e:
        msg = "AWS Test account credentials expired. Can't access remote S3 Table"
        print(msg)
        raise e

    # Filter prior to pandas conversion, to save time/memory
    if identifier:
        filter_cond = EqualTo("flowpath_id", literal(identifier))
    elif bbox:
        min_lat, min_lon, max_lat, max_lon = bbox.bounds
        filter_cond = And(
            GreaterThanOrEqual("min_y", min_lat),
            GreaterThanOrEqual("min_x", min_lon),
            LessThanOrEqual("max_y", max_lat),
            LessThanOrEqual("max_x", max_lon),
        )
    else:
        raise ValueError("Please either supply an identifier or bounding box to subset the dataset.")
    xs_scan = xs_table.scan(row_filter=filter_cond)
    df = xs_scan.to_pandas()

    data_gdf = to_geopandas(df)

    # Save data.
    if output_file:
        if len(data_gdf) > 0:
            gpd.GeoDataFrame(data_gdf).to_file(output_file, layer="ras_xs", driver="GPKG")
        else:
            print("Warning: Dataframe is empty")
        return data_gdf
