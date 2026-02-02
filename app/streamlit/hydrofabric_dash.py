import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st
from botocore.exceptions import ClientError
from streamlit_folium import st_folium

from app.streamlit.helpers import (
    LAYER_FOLIUM_STYLING_MAP,
    display_nhf_schemas,
    load_hf_gpkg,
    post_transient_success_msg,
    validate_nhf_subset_query,
)
from app.streamlit.tooltips import hf_subset_options_explanation
from icefabric.cli.streamflow import NoResultsFoundError
from icefabric.hydrofabric import subset_nhf

st.session_state.NHF_SUBSET_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

catalog = st.session_state.catalog

st.set_page_config(page_title="NGWPC Hydrofabric", layout="wide")
st.title("NGWPC Hydrofabric")
st.write("Information for the NextGen Water Prediction Capability Hydrofabric")

l_col, r_col = st.columns([2, 3], gap="large")

with l_col:
    display_nhf_schemas()

with r_col.form("Subset"):
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
    subset_type = st.pills(label="__Subset Method__", options=subset_types_display, selection_mode="single")
    subset_user_sel = st.text_input(label="__ID__", value=None)
    subset_submit = st.form_submit_button("Submit")
    if subset_submit:
        submit_valid = validate_nhf_subset_query(subset_type, subset_user_sel)

if subset_submit and submit_valid:
    subset_gpkg_file = (
        st.session_state.NHF_SUBSET_OUTPUT_DIR
        / f"nhf_subset_by_{subset_type.replace(' ', '_').lower()}_{subset_user_sel}.gpkg"
    )
    subset_successful = False

    # Subset, unless already done for this ID in this session
    if not subset_gpkg_file.exists():
        try:
            with r_col:
                with st.spinner(
                    f"**Subsetting hydrofabric ({subset_type} {subset_user_sel})...**", show_time=True
                ):
                    if subset_type == "Flowpath ID":
                        subset_nhf(catalog=catalog, flowpath_id=subset_user_sel, output=subset_gpkg_file)
                    elif subset_type == "Gage ID":
                        subset_nhf(catalog=catalog, gage_id=subset_user_sel, output=subset_gpkg_file)
                    elif subset_type == "VPU ID":
                        subset_nhf(catalog=catalog, vpu_id=subset_user_sel, output=subset_gpkg_file)
            with r_col:
                post_transient_success_msg("Subsetting complete!")
            subset_successful = True
        except ClientError:
            r_col.error(
                "ERROR - Authentication failed. Please update/validate your credentials.",
                icon=":material/error:",
            )
        except NoResultsFoundError as nrf:
            r_col.error(
                f"ERROR - {nrf} - please try a different origin point or VPU ID.", icon=":material/error:"
            )
    else:
        with r_col:
            post_transient_success_msg("Subset data already cached!")
        subset_successful = True

    if subset_successful:
        # Vertical spacing
        r_col.space()

        subset_dfs = load_hf_gpkg(subset_gpkg_file)

        # Display subset data
        df_group = r_col.container(border=True)
        with df_group:
            st.markdown(f"#### __Subset Data Results ({subset_type}: {subset_user_sel})__")
            for name, df in subset_dfs.items():
                with st.expander(f"##### __{name}__", icon=":material/data_table:"):
                    st.dataframe(data=df, hide_index=False)

        # Display map
        if subset_type != "VPU ID":
            with r_col.expander("Map View", icon=":material/map:", expanded=True):
                st.markdown(f"#### __Map Results ({subset_type}: {subset_user_sel})__")

                # Create a folium map centered on the subset data
                m = folium.Map(tiles=folium.TileLayer(tiles="Cartodb Positron", control=False))
                lat_lon_coll = [(row.lat, row.lon) for row in subset_dfs["divides"].to_pandas().itertuples()]
                m.fit_bounds(lat_lon_coll)
                for layer_name, df in subset_dfs.items():
                    if "geometry" in df.columns and not df.is_empty():
                        df = df.to_pandas()
                        gdf = gpd.GeoDataFrame(
                            df,
                            geometry=gpd.GeoSeries.from_wkt(df["geometry"]),
                            crs="EPSG:5070",
                        ).to_crs(epsg=4326)

                        # Ensure ID fields are strings for proper display in popups
                        id_field_names = [
                            c for c in gdf.columns.tolist() if c.endswith("_id") and c != "vpu_id"
                        ]
                        for fn in id_field_names:
                            if gdf[fn].dtype == "int64" or gdf[fn].dtype == "float64":
                                # Convert floats/ints to string, handling NaNs
                                gdf[fn] = df[fn].apply(lambda x: f"{int(x)}" if pd.notna(x) else np.nan)

                        styling = LAYER_FOLIUM_STYLING_MAP[layer_name].get("styling", {})
                        highlight_styling = LAYER_FOLIUM_STYLING_MAP[layer_name].get("highlight_styling", {})
                        marker_styling = LAYER_FOLIUM_STYLING_MAP[layer_name].get("marker_styling", None)
                        popup_fields = list(gdf.columns)
                        popup_fields.remove("geometry")
                        gdf_poly = folium.GeoJson(
                            data=gdf,
                            popup=folium.GeoJsonPopup(fields=popup_fields[:15]),
                            tooltip=folium.GeoJsonTooltip(
                                fields=[popup_fields[0]],
                                aliases=[f"{layer_name.title().replace('_', ' ')} ID:"],
                            ),
                            style_function=lambda x, styling=styling: styling,
                            highlight_function=lambda x,
                            highlight_styling=highlight_styling: highlight_styling,
                            marker=marker_styling,
                        )
                        if layer_name == "divides" or layer_name == "flowpaths":
                            gdf_fig = folium.FeatureGroup(name=layer_name)
                        else:
                            gdf_fig = folium.FeatureGroup(name=layer_name, show=False)
                        gdf_fig.add_child(gdf_poly)
                        m.add_child(gdf_fig)

                folium.LayerControl(position="bottomright").add_to(m)
                folium.plugins.Fullscreen(
                    position="topright",
                    title="Expand me",
                    title_cancel="Exit me",
                    force_separate_button=True,
                ).add_to(m)
                m.save("map.html")
                st_folium(fig=m, width=725, returned_objects=[])

        # Download button
        with open(subset_gpkg_file, "rb") as file:
            r_col.download_button(
                label=f"__Download as Geopackage__ (*{subset_gpkg_file.name}*)",
                data=file,
                file_name=subset_gpkg_file.name,
                on_click="ignore",
                mime="application/geopackage+sqlite3",
                icon=":material/download:",
            )
