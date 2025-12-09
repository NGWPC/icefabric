import time

import geopandas as gpd
import pandas as pd
import polars as pl
import streamlit as st
from pyiceberg.expressions import In
from shapely.geometry import box

from icefabric.helpers import to_geopandas
from icefabric.ras_xs import subset_xs
from icefabric.schemas.iceberg_tables import nhf_layers
from icefabric.schemas.iceberg_tables.ras_xs import ConflatedRasXS, RepresentativeRasXS

domain_class_map = {"representative": RepresentativeRasXS, "conflated": ConflatedRasXS}


@st.cache_data(show_spinner=False)
def get_data(_catalog, xs_dom, subset):
    """Helper to call XS subsetting function. Caches the results."""
    if type(subset) is str:
        xs_gdf = subset_xs(catalog=_catalog, xstype=xs_dom, identifier=subset)
    elif type(subset) is list:
        bbox = box(*subset)
        xs_gdf = subset_xs(catalog=_catalog, xstype=xs_dom, bbox=bbox)
    return xs_gdf


def convert_for_download(gdf, tmp_path):
    """Helper to create GeoPackage for download."""
    if "tmp_path" in locals() and tmp_path.exists():
        tmp_path.unlink(missing_ok=True)
    gpd.GeoDataFrame(gdf).to_file(tmp_path, driver="GPKG", mode="w")


def format_xs_map(_catalog, xs_gdf):
    """Helper to create/format a folium map to display the cross-sectional data."""
    # Pull and filter reference divides/flowpaths from the catalog
    reference_divides = to_geopandas(
        _catalog.load_table("conus_reference.reference_divides")
        .scan(row_filter=In("flowpath_id", xs_gdf["flowpath_id"]))
        .to_pandas()
    )
    reference_flowpaths = to_geopandas(
        _catalog.load_table("conus_reference.reference_flowpaths")
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


def post_transient_success_msg(msg, length_s=1.5):
    """Helper to post a transient success message in Streamlit."""
    success_placeholder = st.empty()
    success_placeholder.success(msg, icon=":material/check_circle:")
    # Wait 2 seconds
    time.sleep(length_s)
    success_placeholder.empty()


def load_hf_gpkg(path):
    """Helper to load the subsetted GPKG and return a dictionary of GeoDataFrames for each layer."""
    hf_dict = {}
    for t in list(nhf_layers.keys()):
        if t == "reference_flowpaths" or t == "hydrolocations":
            hf_dict[t] = pl.from_pandas(gpd.read_file(path, layer=t))
        else:
            hf_dict[t] = pl.from_pandas(gpd.read_file(path, layer=t).to_wkt())
    return hf_dict


@st.fragment
def display_nhf_schemas():
    """Helper to display the NHF data schemas"""
    hf_options = list(nhf_layers.keys())
    hf_options_display = [opt.replace("_", " ").title() for opt in hf_options]
    image_expander = st.expander(
        "NGWPC Hydrofabric Data Catalog Overview", expanded=True, icon=":material/schema:"
    )
    with image_expander:
        st.image(
            "app/streamlit/resources/hydrofabric_diagram.png",
            width="content",
            caption="Entity Relationship Diagram (ERD) for the Iceberg NGWPC Hydrofabric Data Catalog.",
        )
    schema_display_sel = st.pills(
        label="__Data Models__", options=hf_options_display, selection_mode="single"
    )

    if schema_display_sel is not None:
        selected_schema = hf_options[hf_options_display.index(schema_display_sel)]
        data_model_exp = st.expander("HF Table Data Model", expanded=True, icon=":material/data_table:")
        data_model = create_table_from_schema(nhf_layers[selected_schema])
        data_model_exp.markdown(
            f"The selected table (`{schema_display_sel}`) is stored/formatted as the data schema below:"
        )
        data_model_exp.dataframe(data=data_model, hide_index=True, row_height=65)


def validate_nhf_subset_query(subset_type, subset_user_sel):
    """Helper to validate the subset query inputs."""
    submit_valid = False
    if None in [subset_type, subset_user_sel]:
        st.error("Please select a subset method and provide an ID.", icon=":material/error:")
    elif subset_user_sel.rstrip() == "":
        st.error("Please provide a non-empty ID.", icon=":material/error:")
    else:
        if subset_type == "Flowpath ID":
            if not subset_user_sel.isdigit():
                st.error(
                    "Flowpath IDs must be numeric. Please provide a valid Flowpath ID.",
                    icon=":material/error:",
                )
            else:
                submit_valid = True
                subset_user_sel = int(subset_user_sel.rstrip())
        else:
            submit_valid = True
            subset_user_sel = subset_user_sel.rstrip()
    return submit_valid
