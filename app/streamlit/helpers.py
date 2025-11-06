import geopandas as gpd
import streamlit as st
from dotenv import load_dotenv
from pyiceberg.catalog import load_catalog
from pyiceberg.expressions import In
from shapely.geometry import box

from icefabric.helpers import to_geopandas
from icefabric.ras_xs import subset_xs


@st.cache_data(show_spinner=False)
def get_data(xs_dom, subset):
    """Helper to call XS subsetting function. Caches the results."""
    load_dotenv()
    catalog = load_catalog("glue")
    if type(subset) is str:
        xs_gdf = subset_xs(catalog=catalog, xstype=xs_dom, identifier=subset)
    elif type(subset) is list:
        bbox = box(*subset)
        xs_gdf = subset_xs(catalog=catalog, xstype=xs_dom, bbox=bbox)
    return xs_gdf


def convert_for_download(gdf):
    """Helper to create GeoPackage for download."""
    gpd.GeoDataFrame(gdf).to_file("xs_subset.gpkg", layer="ras_xs", driver="GPKG", overwrite=True)


def format_xs_map(xs_gdf):
    """Helper to create/format a folium map to display the cross-sectional data."""
    load_dotenv()
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
