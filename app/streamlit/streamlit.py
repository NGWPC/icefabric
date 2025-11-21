import os
import pathlib
import sys
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
    bounding_box_tooltip,
    domain_tooltip,
    flowpath_id_tooltip,
    query_type_tooltip,
)
from icefabric.helpers.creds import load_creds
from icefabric.schemas import XsType

# Deploy environment default is "test"
deploy_env = "test"
args_provided = sys.argv[1:]
if any("deploy-env=" in a for a in args_provided):
    try:
        deploy_env_pass = " ".join(args_provided).split("deploy-env=")[1].split()[0]
        if deploy_env_pass.lower() in ["t", "test", "p", "prod", "production"]:
            deploy_env = deploy_env_pass.lower()
    except IndexError:
        # No deploy env provided, use default
        pass

# Load creds/env details.
if str(os.environ.get("ICEFABRIC_DEPLOY_ENV")).lower() in ["t", "test", "p", "prod", "production"]:
    # Override the deploy env. Allows for specifying the env when running a docker container
    load_creds(os.environ["ICEFABRIC_DEPLOY_ENV"].lower())
else:
    load_creds(deploy_env)

temp_dir = pathlib.Path(tempfile.gettempdir())
tmp_path = temp_dir / "xs_subset.gpkg"

st.set_page_config(layout="wide")

with st.container():
    st.title("RAS XS Data")
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
        xs_id = l_col.text_input(label="Flowpath ID", help=flowpath_id_tooltip, value="")
    elif xs_query == "Bounding Box":
        l_col.markdown("##### __Bounding Box Coordinates__", help=bounding_box_tooltip)
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
                xs_gdf = get_data(xs_dom, xs_id)
            elif all(var is not None for var in bbox_list):
                xs_gdf = get_data(xs_dom, bbox_list)

        if xs_gdf.empty:
            l_col.error(
                f"ERROR - No results returned. Please try a different {xs_query}...", icon=":material/error:"
            )
        else:
            # Format and display map
            with st.spinner(text="Generating map..."):
                xs_map = format_xs_map(xs_gdf)
                r_col.markdown("#### Map")
                with r_col:
                    st_folium(fig=xs_map, width=725, returned_objects=[])

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
