import statistics
import time

import folium
import geopandas as gpd
import matplotlib as mpl
import numpy as np
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

STYLE_MAP = {
    "divides": {
        "styling": {
            "color": "grey",
            "weight": 2,
            "opacity": 0.5,
            "fillOpacity": 0.33,
            "dashArray": [5, 5],
        },
        "highlight_styling": {
            "weight": 4,
            "opacity": 0.75,
            "fillOpacity": 0.5,
        },
    },
    "flowpaths": {
        "styling": {
            "color": "darkblue",
            "weight": 3,
            "opacity": 1,
        },
        "highlight_styling": {
            "weight": 6,
        },
    },
    "nexus": {"marker_styling": folium.Marker(icon=folium.Icon(color="orange", icon="filter"))},
    "waterbodies": {"marker_styling": folium.Marker(icon=folium.Icon(color="blue", icon="tint"))},
    "gages": {"marker_styling": folium.Marker(icon=folium.Icon(color="darkred", icon="record"))},
    "virtual_flowpaths": {
        "styling": {
            "color": "white",
            "weight": 2,
            "opacity": 1,
        },
        "highlight_styling": {
            "weight": 4,
        },
    },
    "virtual_nexus": {"marker_styling": folium.Marker(icon=folium.Icon(color="green", icon="filter"))},
    "lakes": {
        "marker_styling": folium.Marker(icon=folium.Icon(color="darkblue", prefix="fa", icon="sailboat"))
    },
    "ras_xs": {
        "styling": {
            "color": "black",
            "weight": 2,
            "opacity": 1,
        },
        "highlight_styling": {
            "weight": 4,
        },
    },
}


def depth_to_gradient(val, domain="NHF", min_val=0, max_val=6.5, start_color="#7073FF", end_color="#0B0B1B"):
    """Given a flowpath depth value, return a hex color code representing its position on a gradient"""
    if val is None:
        return "#FFFFFF"  # White for null values
    if domain == "XS":
        max_val = 25
    if val > max_val:
        val = max_val

    # Normalize value between 0 and 1
    norm = (val - min_val) / (max_val - min_val)
    c1 = mpl.colors.to_rgb(start_color)
    c2 = mpl.colors.to_rgb(end_color)
    # Linear interpolation
    rgb = [(1 - norm) * c1[i] + norm * c2[i] for i in range(3)]
    return mpl.colors.to_hex(rgb)


def normalize_width(val, domain="NHF", min=0, max=384, nmin=2, nmax=50):
    """Given a flowpath width value, normalize it to a new range (for styling)"""
    if val is None:
        return 1  # Width for null values
    if domain == "XS":
        max = 1224
    if val > max:
        return nmax
    else:
        return round(nmin + (((val - min) * (nmax - nmin)) / (max - min)))


def set_id_fields_as_strings(gdf):
    """Helper to ensure id fields are of type string."""
    id_field_names = [c for c in gdf.columns.tolist() if c.endswith("_id") and c != "vpu_id"]
    for fn in id_field_names:
        if gdf[fn].dtype == "int64" or gdf[fn].dtype == "float64":
            # Convert floats/ints to string, handling NaNs
            gdf[fn] = gdf[fn].apply(lambda x: f"{int(x)}" if pd.notna(x) else np.nan)
    return gdf


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


def format_xs_map(_catalog, xs_gdf, domain):
    """Helper to create/format a folium map to display the cross-sectional data."""
    # Create base map
    m = folium.Map(tiles=folium.TileLayer(tiles="Cartodb Positron", control=False), prefer_canvas=True)

    # Format cross-sectional data
    ras_xs = xs_gdf.to_crs(epsg=4326)

    # Pull and format reference layers
    reference_divides = to_geopandas(
        _catalog.load_table("conus_reference.reference_divides")
        .scan(row_filter=In("flowpath_id", xs_gdf["flowpath_id"]))
        .to_pandas()
    ).to_crs(epsg=4326)
    reference_flowpaths = to_geopandas(
        _catalog.load_table("conus_reference.reference_flowpaths")
        .scan(row_filter=In("flowpath_id", xs_gdf["flowpath_id"]))
        .to_pandas()
    ).to_crs(epsg=4326)

    # Ensure ID fields are strings for proper display in popups
    ras_xs = set_id_fields_as_strings(ras_xs)
    reference_divides = set_id_fields_as_strings(reference_divides)
    reference_flowpaths = set_id_fields_as_strings(reference_flowpaths)

    # Sort dataframes by flowpath_id for consistent ordering
    ras_xs = ras_xs.sort_values(by="flowpath_id", ascending=True)
    reference_flowpaths = reference_flowpaths.sort_values(by="flowpath_id", ascending=True)
    reference_divides = reference_divides.sort_values(by="flowpath_id", ascending=True)

    # Sometimes even representative XS data can have multiple entries per flowpath_id
    unique_flowpaths = ras_xs["flowpath_id"].unique().tolist()

    # Add width and depth to reference flowpaths
    avg_widths, avg_depths = [], []
    for fp in unique_flowpaths:
        avg_widths.append(statistics.mean(ras_xs[ras_xs["flowpath_id"] == fp].TW.tolist()))
        if domain == "representative":
            avg_depths.append(statistics.mean(ras_xs[ras_xs["flowpath_id"] == fp].Y.tolist()))
        elif domain == "conflated":
            avg_depths.append(statistics.mean(ras_xs[ras_xs["flowpath_id"] == fp].Ym.tolist()))
    reference_flowpaths["width"] = avg_widths
    reference_flowpaths["depth"] = avg_depths

    # Fit map to data bounds
    min_points = [(row.miny, row.minx) for row in reference_flowpaths.geometry.bounds.itertuples()]
    max_points = [(row.maxy, row.maxx) for row in reference_flowpaths.geometry.bounds.itertuples()]
    lat_lon_coll = min_points + max_points
    m.fit_bounds(lat_lon_coll)

    # Reference divides GeoJSON layer
    div_popup_fields = [col for col in reference_divides.columns if col != "geometry"]
    div_style = STYLE_MAP["divides"].get("styling", {})
    div_hl_style = STYLE_MAP["divides"].get("highlight_styling", {})
    ref_div_poly = folium.GeoJson(
        data=reference_divides,
        popup=folium.GeoJsonPopup(fields=list(div_popup_fields[:25])),
        tooltip=folium.GeoJsonTooltip(
            fields=[div_popup_fields[0]],
            aliases=["Divide ID:"],
        ),
        style_function=lambda x: div_style,
        highlight_function=lambda x: div_hl_style,
    )

    # Reference/Channel Geometry GeoJSON layers
    fp_popup_fields = [col for col in reference_flowpaths.columns if col != "geometry"]
    fp_style = STYLE_MAP["flowpaths"].get("styling", {})
    fp_hl_style = STYLE_MAP["flowpaths"].get("highlight_styling", {})
    ref_fp_poly = folium.GeoJson(
        data=reference_flowpaths,
        popup=folium.GeoJsonPopup(fields=list(fp_popup_fields[:25])),
        tooltip=folium.GeoJsonTooltip(
            fields=[fp_popup_fields[0]],
            aliases=["Flowpath ID:"],
        ),
        style_function=lambda x: fp_style,
        highlight_function=lambda x: fp_hl_style,
    )

    # Project flowpath line geometry to a metric CRS for buffering (to visualize width as a buffer around the line)
    three_dim_fp_data = reference_flowpaths.to_crs(epsg=5070)
    # Scale factor for better visualization; may need to adjust as needed
    three_dim_fp_data["topwdth_half"] = (three_dim_fp_data["width"] / 2) / 3
    three_dim_fp_data["geometry"] = three_dim_fp_data.geometry.buffer(three_dim_fp_data["topwdth_half"])
    three_dim_fp_poly = folium.GeoJson(
        data=three_dim_fp_data,
        popup=folium.GeoJsonPopup(fields=list(fp_popup_fields[:25])),
        tooltip=folium.GeoJsonTooltip(
            fields=[fp_popup_fields[0], "width", "depth"],
            aliases=["Flowpath ID:", "Width (m):", "Depth (m):"],
            localize=True,
        ),
        style_function=lambda x: fp_style
        | {
            "stroke": False,
            "fillColor": depth_to_gradient(x["properties"]["depth"], domain="XS"),
            "fillOpacity": 1,
            "dashArray": [5, 5] if not x["properties"]["width"] else {},
        },
        highlight_function=lambda x: fp_hl_style
        | {
            "stroke": True,
            "color": "black",
            "weight": 2,
        },
        popup_keep_highlighted=True,
    )

    # Cross-sectional data GeoJSON layer
    ras_xs_popup_fields = [col for col in ras_xs.columns if col != "geometry"]
    ras_xs_style = STYLE_MAP["ras_xs"].get("styling", {})
    ras_xs_hl_style = STYLE_MAP["ras_xs"].get("highlight_styling", {})
    ras_xs_poly = folium.GeoJson(
        data=ras_xs,
        popup=folium.GeoJsonPopup(fields=list(ras_xs_popup_fields[:25])),
        tooltip=folium.GeoJsonTooltip(
            fields=[ras_xs_popup_fields[0]],
            aliases=["XS Flowpath ID:"],
        ),
        style_function=lambda x: ras_xs_style,
        highlight_function=lambda x: ras_xs_hl_style,
    )

    # Add layers to map with layer control
    m.add_child(folium.FeatureGroup(name="Reference Divides").add_child(ref_div_poly))
    m.add_child(folium.FeatureGroup(name="Reference Flowpaths").add_child(ref_fp_poly))
    m.add_child(folium.FeatureGroup(name="RAS XS").add_child(ras_xs_poly))
    m.add_child(folium.FeatureGroup(name="Channel Geometry", show=False).add_child(three_dim_fp_poly))

    # Move layer control to bottom right and add fullscreen button
    folium.LayerControl(position="bottomright").add_to(m)
    folium.plugins.Fullscreen(
        position="topright",
        title="Expand me",
        title_cancel="Exit me",
        force_separate_button=True,
    ).add_to(m)

    return m


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
    layers = gpd.list_layers(path)
    for _index, row in layers.iterrows():
        layer_name, has_geom = row["name"], row["geometry_type"] is not None
        if layer_name in nhf_layers.keys():
            if has_geom:
                hf_dict[layer_name] = pl.from_pandas(gpd.read_file(path, layer=layer_name).to_wkt())
            else:
                hf_dict[layer_name] = pl.from_pandas(gpd.read_file(path, layer=layer_name))
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
            "app/streamlit/resources/nhf_schema.png",
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
