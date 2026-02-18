import pathlib
import tempfile

import streamlit as st
from botocore.exceptions import ClientError
from streamlit_folium import st_folium

from app.streamlit.helpers import (
    convert_for_download,
    create_table_from_schema,
    domain_class_map,
    format_xs_map,
    get_data,
)
from app.streamlit.tooltips import (
    bbox_examples,
    bounding_box_tooltip,
    domain_tooltip,
    flowpath_id_tooltip,
    query_type_tooltip,
    three_dim_flowpath_legend,
    three_dim_flowpath_tooltip,
)
from icefabric.schemas import XsType

temp_dir = pathlib.Path(tempfile.gettempdir())
tmp_path = temp_dir / "xs_subset.gpkg"

st.set_page_config(page_title="RAS XS", layout="wide")

catalog = st.session_state.catalog

with st.container():
    st.title("RAS XS")
    st.markdown(
        """
        This dashboard visualizes River Analysis System (RAS) Cross Sectional (XS) Data
        from the Iceberg catalog. The data can be subsetted through either:

        - filtering by flowpath ID
        - defining a geospatial bounding box
        """
    )

l_col, r_col = st.columns([1, 3], gap="large")

domain_options = [e.value for e in XsType]
xs_id = None
min_lat, min_lon, max_lat, max_lon = None, None, None, None

l_col.markdown("#### __Query__")
xs_dom = XsType(l_col.selectbox(label="Cross-sectional Domain", options=domain_options, help=domain_tooltip))
data_model_exp = l_col.expander("Domain Data Model", icon=":material/data_table:")
data_model = create_table_from_schema(domain_class_map[xs_dom.value])
data_model_exp.markdown(
    f"The selected domain (`{xs_dom.value}`) is stored/formatted as the data schema below:"
)
data_model_exp.dataframe(data=data_model, hide_index=True, row_height=65)
xs_query = l_col.selectbox(label="Query Type", options=["Flowpath", "Bounding Box"], help=query_type_tooltip)
if xs_query:
    if xs_query == "Flowpath":
        with l_col.expander("Examples", icon=":material/info:", expanded=False):
            st.markdown("- 20059822\n- 17039777\n- 2539367")
        xs_id = l_col.text_input(label="Flowpath ID", help=flowpath_id_tooltip, value="")
    elif xs_query == "Bounding Box":
        l_col.markdown("##### __Bounding Box Coordinates__", help=bounding_box_tooltip)
        with l_col.expander("Examples", icon=":material/info:", expanded=False):
            st.table(bbox_examples)
        min_lat = l_col.number_input("Min. Latitude (°)", format="%.4f")
        min_lon = l_col.number_input("Min. Longitude (°)", format="%.4f")
        max_lat = l_col.number_input("Max. Latitude (°)", format="%.4f")
        max_lon = l_col.number_input("Max. Longitude (°)", format="%.4f")

if l_col.button("Submit"):
    bbox_list = [min_lat, min_lon, max_lat, max_lon]

    # Get subset
    try:
        with st.spinner(text="Fetching data..."):
            if xs_id is not None:
                xs_gdf = get_data(catalog, xs_dom, xs_id)
            elif all(var is not None for var in bbox_list):
                xs_gdf = get_data(catalog, xs_dom, bbox_list)

        if xs_gdf.empty:
            l_col.error(
                f"ERROR - No results returned. Please try a different {xs_query}...", icon=":material/error:"
            )
        else:
            # Format and display map
            with st.spinner(text="Generating map..."):
                xs_map = format_xs_map(catalog, xs_gdf, xs_dom)
                r_col.markdown("#### Map")
                with r_col:
                    st_folium(fig=xs_map, width=725, returned_objects=[])
                    with st.container(border=True, width=725):
                        with st.expander("##### 3D Flowpaths Legend", icon=":material/info:"):
                            st.markdown(three_dim_flowpath_tooltip)
                        st.html(three_dim_flowpath_legend(upper_bound=25))

            # Format and display dataframe
            df = xs_gdf.drop(columns="geometry")
            df["geometry"] = xs_gdf["geometry"].apply(lambda geom: geom.wkt if geom else None)
            r_col.markdown("#### Dataframe")
            r_col.dataframe(df)

            convert_for_download(xs_gdf, tmp_path)
            with open(tmp_path, "rb") as file:
                r_col.download_button(
                    label="Download as Geopackage",
                    data=file,
                    file_name="xs_subset.gpkg",
                    on_click="ignore",
                    mime="application/geopackage+sqlite3",
                    icon=":material/download:",
                )
    except ClientError:
        l_col.error("ERROR - Authentication failed. Please update your credentials.", icon=":material/error:")
