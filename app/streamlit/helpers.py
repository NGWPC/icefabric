import geopandas as gpd
import pandas as pd
import streamlit as st
from pyiceberg.catalog import load_catalog
from pyiceberg.expressions import In
from shapely.geometry import box

from icefabric.helpers import to_geopandas
from icefabric.ras_xs import subset_xs
from icefabric.schemas.iceberg_tables.ras_xs import ConflatedRasXS, RepresentativeRasXS

domain_class_map = {"representative": RepresentativeRasXS, "conflated": ConflatedRasXS}


@st.cache_data(show_spinner=False)
def get_data(xs_dom, subset):
    """Helper to call XS subsetting function. Caches the results."""
    catalog = load_catalog("glue")
    if type(subset) is str:
        xs_gdf = subset_xs(catalog=catalog, xstype=xs_dom, identifier=subset)
    elif type(subset) is list:
        bbox = box(*subset)
        xs_gdf = subset_xs(catalog=catalog, xstype=xs_dom, bbox=bbox)
    return xs_gdf


def convert_for_download(gdf, tmp_path):
    """Helper to create GeoPackage for download."""
    if "tmp_path" in locals() and tmp_path.exists():
        tmp_path.unlink(missing_ok=True)
    gpd.GeoDataFrame(gdf).to_file(tmp_path, driver="GPKG", mode="w")


def format_xs_map(xs_gdf):
    """Helper to create/format a folium map to display the cross-sectional data."""
    catalog = load_catalog("glue")
    # Pull and filter reference divides/flowpaths from the catalog
    reference_divides = to_geopandas(
        catalog.load_table("conus_reference.reference_divides")
        .scan(row_filter=In("flowpath_id", xs_gdf["flowpath_id"]))
        .to_pandas()
    )
    reference_flowpaths = to_geopandas(
        catalog.load_table("conus_reference.reference_flowpaths")
        .scan(row_filter=In("flowpath_id", xs_gdf["flowpath_id"]))
        .to_pandas()
    )

    # Convert all data to the EPSG:4326 coordinate reference system
    reference_divides = reference_divides.to_crs(epsg=4326)
    reference_flowpaths = reference_flowpaths.to_crs(epsg=4326)
    gdf = xs_gdf.to_crs(epsg=4326)

    ref_div_ex = reference_divides.explore(color="grey")
    ref_flo_ex = reference_flowpaths.explore(m=ref_div_ex, color="blue")

    # Final Map
    xs_map = gdf.explore(m=ref_flo_ex, color="black")
    return xs_map


def create_table_from_schema(iceberg_schema):
    """Takes an iceberg data model object and returns a dataframe defining the model"""
    names = [f.name for f in iceberg_schema.schema().fields]
    descs = [f.doc for f in iceberg_schema.schema().fields]
    types = [str(f.field_type).capitalize() for f in iceberg_schema.schema().fields]
    data_model = pd.DataFrame(
        {
            "Field Name": names,
            "Data Type": types,
            "Description": descs,
        }
    )
    return data_model
