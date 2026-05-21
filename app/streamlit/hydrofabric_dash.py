import folium
import geopandas as gpd
import streamlit as st
from botocore.exceptions import ClientError
from streamlit_folium import st_folium

from app.streamlit.helpers import (
    STYLE_MAP,
    depth_to_gradient,
    display_nhf_schemas,
    load_hf_gpkg,
    post_transient_success_msg,
    set_id_fields_as_strings,
    validate_nhf_subset_query,
)
from app.streamlit.tooltips import (
    hf_subset_options_explanation,
    three_dim_flowpath_legend,
    three_dim_flowpath_tooltip,
)
from icefabric.cli.streamflow import NoResultsFoundError
from icefabric.hydrofabric import subset_nhf

st.session_state.TEMP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

catalog = st.session_state.catalog

st.set_page_config(page_title="NGWPC Hydrofabric", layout="wide")
st.title("NGWPC Hydrofabric")
st.write("Information for the NextGen Water Prediction Capability Hydrofabric")

st.write(
    "You can explore the data model/schemas for the NGWPC Hydrofabric, or subset the data and view/download the results."
)

top_layer_control = st.segmented_control(
    label="__Select an option to explore:__",
    options=["Data Model/Schemas", "Subset Data"],
    selection_mode="single",
    key="hf_section_sel",
)

if top_layer_control == "Data Model/Schemas":
    with st.container(border=True, width=900):
        display_nhf_schemas()
elif top_layer_control == "Subset Data":
    with st.form("Subset", width=900):
        # ==============================
        # Form to subset the hydrofabric
        # ==============================
        st.markdown("#### Subset the data")
        st.write(
            "View/download a subset of the NGWPC Hydrofabric. The NGWPC Hydrofabric can be subsetted in a few ways:"
        )
        st.markdown(hf_subset_options_explanation)
        st.write("Select a subset method and provide the necessary information:")
        subset_types_display = ["Flowpath ID", "Gage ID", "VPU ID"]
        subset_type = st.pills(
            label="__Subset Method__", options=subset_types_display, selection_mode="single"
        )
        subset_user_sel = st.text_input(label="__ID__", value=None)
        subset_submit = st.form_submit_button("Submit")
        if subset_submit:
            submit_valid = validate_nhf_subset_query(subset_type, subset_user_sel)

    if subset_submit and submit_valid:
        l_col, r_col = st.columns([2, 3], gap="medium")
        subset_gpkg_file = (
            st.session_state.TEMP_OUTPUT_DIR
            / "nhf_subset_gpkg_files"
            / f"nhf_subset_by_{subset_type.replace(' ', '_').lower()}_{subset_user_sel}.gpkg"
        )
        subset_successful = False

        # Subset, unless already done for this ID in this session
        if not subset_gpkg_file.exists():
            try:
                with st.spinner(
                    f"**Subsetting hydrofabric ({subset_type} {subset_user_sel})...**", show_time=True
                ):
                    if subset_type == "Flowpath ID":
                        subset_nhf(catalog=catalog, flowpath_id=subset_user_sel, output=subset_gpkg_file)
                    elif subset_type == "Gage ID":
                        subset_nhf(catalog=catalog, gage_id=subset_user_sel, output=subset_gpkg_file)
                    elif subset_type == "VPU ID":
                        subset_nhf(catalog=catalog, vpu_id=subset_user_sel, output=subset_gpkg_file)

                post_transient_success_msg("Subsetting complete!")
                subset_successful = True
            except ClientError:
                st.error(
                    "ERROR - Authentication failed. Please update/validate your credentials.",
                    icon=":material/error:",
                )
            except NoResultsFoundError as nrf:
                st.error(
                    f"ERROR - {nrf} - please try a different origin point or VPU ID.", icon=":material/error:"
                )
        else:
            post_transient_success_msg("Subset data already cached!")
            subset_successful = True

        if subset_successful:
            # Vertical spacing
            st.space()

            subset_dfs = load_hf_gpkg(subset_gpkg_file)

            # Display/download subset data
            df_group = l_col.container(border=True)
            with df_group:
                st.markdown(f"#### __Subset Data Results ({subset_type}: `{subset_user_sel}`)__")
                for name, df in subset_dfs.items():
                    with st.expander(f"##### __{name}__", icon=":material/data_table:"):
                        st.dataframe(data=df, hide_index=False)
                # Download button
                with open(subset_gpkg_file, "rb") as file:
                    st.download_button(
                        label=f"__Download as Geopackage__ (*{subset_gpkg_file.name}*)",
                        data=file,
                        file_name=subset_gpkg_file.name,
                        on_click="ignore",
                        mime="application/geopackage+sqlite3",
                        icon=":material/download:",
                    )

            # Display map
            if subset_type != "VPU ID":
                with r_col.expander("Map View", icon=":material/map:", expanded=True):
                    st.markdown(f"#### __Map Results ({subset_type}: `{subset_user_sel}`)__")

                    # Create a folium map centered on the subset data
                    m = folium.Map(tiles=folium.TileLayer(tiles="Cartodb Positron", control=False))
                    lat_lon_coll = [
                        (row.lat, row.lon) for row in subset_dfs["divides"].to_pandas().itertuples()
                    ]
                    m.fit_bounds(lat_lon_coll)
                    fp_data = None
                    for layer_name, df in subset_dfs.items():
                        if "geometry" in df.columns and not df.is_empty():
                            df = df.to_pandas()
                            gdf = gpd.GeoDataFrame(
                                df,
                                geometry=gpd.GeoSeries.from_wkt(df["geometry"]),
                                crs="EPSG:5070",
                            ).to_crs(epsg=4326)

                            # Ensure ID fields are strings for proper display in popups
                            gdf = set_id_fields_as_strings(gdf)

                            if layer_name == "flowpaths":
                                fp_data = gdf.copy()
                            style = STYLE_MAP[layer_name].get("styling", {})
                            hl_style = STYLE_MAP[layer_name].get("highlight_styling", {})
                            marker_style = STYLE_MAP[layer_name].get("marker_styling", None)
                            popup_fields = [c for c in gdf.columns if c != "geometry"]
                            gdf_poly = folium.GeoJson(
                                data=gdf,
                                popup=folium.GeoJsonPopup(fields=popup_fields[:25]),
                                tooltip=folium.GeoJsonTooltip(
                                    fields=[popup_fields[0]],
                                    aliases=[f"{layer_name.title().replace('_', ' ')} ID:"],
                                ),
                                style_function=lambda x, style=style: style,
                                highlight_function=lambda x, hl_style=hl_style: hl_style,
                                marker=marker_style,
                            )
                            if layer_name == "divides" or layer_name == "flowpaths":
                                gdf_fig = folium.FeatureGroup(name=layer_name.title().replace("_", " "))
                            else:
                                gdf_fig = folium.FeatureGroup(
                                    name=layer_name.title().replace("_", " "), show=False
                                )
                            gdf_fig.add_child(gdf_poly)
                            m.add_child(gdf_fig)

                    fp_popup_fields = [c for c in fp_data.columns if c != "geometry"]
                    fp_styling = STYLE_MAP["flowpaths"].get("styling", {})
                    three_dim_fp_hl = STYLE_MAP["channel_geometries"].get("highlight_styling", {})

                    # Project flowpath line geometry to a metric CRS for buffering (to visualize width as a buffer around the line)
                    fp_data = fp_data.to_crs(epsg=5070)
                    # Scale factor for better visualization; may need to adjust as needed
                    fp_data["topwdth_half"] = (fp_data["topwdth"] / 2) * 20
                    fp_data["geometry"] = fp_data.geometry.buffer(fp_data["topwdth_half"])

                    three_dim_fp_poly = folium.GeoJson(
                        data=fp_data,
                        popup=folium.GeoJsonPopup(
                            fields=list(fp_popup_fields[:25]),
                        ),
                        tooltip=folium.GeoJsonTooltip(
                            fields=[fp_popup_fields[0], "topwdth", "y_ml"],
                            aliases=["Flowpath ID:", "Width (m):", "Depth (m):"],
                            localize=True,
                        ),
                        style_function=lambda x: fp_styling
                        | {
                            "stroke": False if x["properties"]["topwdth"] else True,
                            "color": "black" if x["properties"]["topwdth"] else {},
                            "fillColor": depth_to_gradient(x["properties"]["y_ml"]),
                            "fillOpacity": 1,
                            "dashArray": [5, 5] if not x["properties"]["topwdth"] else {},
                        },
                        highlight_function=lambda x: three_dim_fp_hl,
                        popup_keep_highlighted=True,
                    )
                    m.add_child(
                        folium.FeatureGroup(name="Channel Geometry", show=False).add_child(three_dim_fp_poly)
                    )

                    folium.LayerControl(position="bottomright").add_to(m)
                    folium.plugins.Fullscreen(
                        position="topright",
                        title="Expand me",
                        title_cancel="Exit me",
                        force_separate_button=True,
                    ).add_to(m)
                    st_folium(fig=m, width=725, returned_objects=[])

                    with st.container(border=True, width=725):
                        with st.expander(
                            "##### Channel Geometry Visualization Legend", icon=":material/info:"
                        ):
                            st.markdown(three_dim_flowpath_tooltip())
                        st.html(three_dim_flowpath_legend())
                        st.markdown(
                            "##### __Width (m)__\nRange: 0 &rarr; ~384 meters. Mouseover reveals width value."
                        )
