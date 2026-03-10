import pathlib
import tempfile

import folium
import geopandas as gpd
import numpy as np
import streamlit as st
from botocore.exceptions import ClientError
from folium.plugins import Draw, MarkerCluster
from shapely import wkb
from shapely.geometry import box
from sklearn.cluster import DBSCAN
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
    three_dim_flowpath_legend,
    three_dim_flowpath_tooltip,
)
from icefabric.schemas import XsType


@st.cache_resource(show_spinner=False)
def generate_preview_xs_clusters():
    """Once per app-deployment, generate clustered preview points for all representative cross-sections to display on the map."""
    xs_geometries = (
        st.session_state.catalog.load_table("ras_xs.representative").to_polars().select("geometry").collect()
    )
    xs_centroids = [i[0].centroid for i in wkb.loads(xs_geometries)]
    gdf = gpd.GeoDataFrame(geometry=xs_centroids, crs="EPSG:5070").to_crs(epsg=4326)
    coords = np.array([[point.x, point.y] for point in gdf.geometry])
    db = DBSCAN(eps=0.075, min_samples=1).fit(coords)
    gdf["cluster"] = db.labels_
    clustered_points = gdf.dissolve(by="cluster", as_index=False).copy()
    clustered_points["geometry"] = clustered_points.to_crs(epsg=5070).geometry.centroid.to_crs(epsg=4326)
    return clustered_points.to_crs(epsg=4326)


temp_dir = pathlib.Path(tempfile.gettempdir())
tmp_path = temp_dir / "xs_subset.gpkg"

st.set_page_config(page_title="RAS XS", layout="wide")

catalog = st.session_state.catalog
xs_markers = generate_preview_xs_clusters()


@st.fragment
def get_ras_xs_user_input():
    """Get user input for subsetting RAS XS data."""
    xs_dom, xs_query, xs_id = None, None, None
    min_lat, min_lon, max_lat, max_lon = None, None, None, None
    box_area = None
    domain_options = [e.value for e in XsType]
    with st.container(border=True):
        st.markdown("### __Subset the data__")
        xs_dom = st.segmented_control(
            label="Cross-sectional Domain", options=domain_options, help=domain_tooltip
        )
        if xs_dom is not None:
            xs_dom = XsType(xs_dom)
            data_model_exp = st.expander("Domain Data Model", icon=":material/data_table:")
            data_model = create_table_from_schema(domain_class_map[xs_dom.value])
            data_model_exp.markdown(
                f"The selected domain (`{xs_dom.value}`) is stored/formatted as the data schema below:"
            )
            data_model_exp.dataframe(data=data_model, hide_index=True, row_height=65)
            xs_query = st.segmented_control(
                label="Query Type",
                options=["Flowpath", "Bounding Box (draw)", "Bounding Box (manual entry)"],
                help=query_type_tooltip,
            )
        if xs_query:
            if xs_query == "Flowpath":
                with st.expander("Examples", icon=":material/info:", expanded=False):
                    st.markdown("- 20059822\n- 17039777\n- 2539367")
                xs_id = st.text_input(
                    label="Flowpath ID", help=flowpath_id_tooltip, value=None, placeholder="e.g., 20059822"
                )
            elif xs_query == "Bounding Box (draw)":
                st.markdown("#### __Draw a Bounding Box__")
                st.markdown(bounding_box_tooltip)
                with st.container(border=True):
                    m = folium.Map(
                        location=[39.8283, -98.5795],
                        tiles=folium.TileLayer(tiles="Cartodb Positron", control=False),
                        zoom_start=4,
                        prefer_canvas=True,
                    )
                    # import pdb; pdb.set_trace()
                    marker_cluster = MarkerCluster().add_to(m)
                    for _, row in xs_markers[:5000].iterrows():
                        folium.Marker(location=[row.geometry.y, row.geometry.x]).add_to(marker_cluster)
                    Draw(
                        export=False,
                        show_geometry_on_click=True,
                        draw_options={
                            "rectangle": {"repeatMode": False},
                            "polyline": False,
                            "polygon": False,
                            "circle": False,
                            "marker": False,
                            "circlemarker": False,
                        },
                    ).add_to(m)
                    output = st_folium(m, use_container_width=True, height=500)
                    if output["last_active_drawing"]:
                        sw_corner = output["last_active_drawing"]["geometry"]["coordinates"][0][0]
                        ne_corner = output["last_active_drawing"]["geometry"]["coordinates"][0][2]
                        min_lat, min_lon = sw_corner[1], sw_corner[0]
                        max_lat, max_lon = ne_corner[1], ne_corner[0]
                        box_area = box(min_lon, min_lat, max_lon, max_lat).area
                        coord_disp = f"""\
                            ##### Selected Coordinates:
                            - **Min. Latitude:** {sw_corner[1]:.4f}°
                            - **Min. Longitude:** {sw_corner[0]:.4f}°
                            - **Max. Latitude:** {ne_corner[1]:.4f}°
                            - **Max. Longitude:** {ne_corner[0]:.4f}°
                        """
                        st.markdown(coord_disp)
                        if box_area >= 140:
                            st.warning(
                                "The selected bounding box is quite large and may take a long time to process. Please select a smaller area.",
                                icon=":material/warning:",
                            )
            elif xs_query == "Bounding Box (manual entry)":
                st.markdown("#### __Manually Enter Bounding Box Coordinates__")
                with st.container(border=True):
                    col1, col2 = st.columns(2, gap="medium")
                    with col1:
                        min_lat = st.number_input(
                            label="Min. Latitude (°)",
                            help="The minimum latitudinal coordinate that defines the bounding box.",
                            value=None,
                            format="%.6f",
                        )
                        max_lat = st.number_input(
                            label="Max. Latitude (°)",
                            help="The maximum latitudinal coordinate that defines the bounding box.",
                            value=None,
                            format="%.6f",
                        )
                    with col2:
                        min_lon = st.number_input(
                            label="Min. Longitude (°)",
                            help="The minimum longitudinal coordinate that defines the bounding box.",
                            value=None,
                            format="%.6f",
                        )
                        max_lon = st.number_input(
                            label="Max. Longitude (°)",
                            help="The maximum longitudinal coordinate that defines the bounding box.",
                            value=None,
                            format="%.6f",
                        )
                    if all(var is not None for var in [min_lat, min_lon, max_lat, max_lon]):
                        box_area = box(min_lon, min_lat, max_lon, max_lat).area
                        if box_area >= 140:
                            st.warning(
                                "The selected bounding box is quite large and may take a long time to process. Please select a smaller area.",
                                icon=":material/warning:",
                            )
        return xs_dom, xs_query, xs_id, box_area, min_lat, min_lon, max_lat, max_lon


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

l_col, r_col = st.columns([2, 3], gap="medium")

xs_dom, xs_query, xs_id, box_area, min_lat, min_lon, max_lat, max_lon = (
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    None,
)
with l_col.container():
    xs_dom, xs_query, xs_id, box_area, min_lat, min_lon, max_lat, max_lon = get_ras_xs_user_input()

if l_col.button("Submit"):
    bbox_list = [min_lat, min_lon, max_lat, max_lon]
    xs_gdf = None

    # Get subset
    try:
        if xs_dom is None:
            l_col.error("ERROR - Please select a domain to query.", icon=":material/error:")
        elif xs_query is None:
            l_col.error(
                "ERROR - Please select a query type and submit to retrieve data.", icon=":material/error:"
            )
        elif xs_query == "Flowpath" and xs_id is None:
            l_col.error(
                "ERROR - Please enter a flowpath ID to submit a flowpath query.", icon=":material/error:"
            )
        elif xs_query.startswith("Bounding Box") and not all(var is not None for var in bbox_list):
            l_col.error(
                "ERROR - Please draw a bounding box on the map to submit a bounding box query.",
                icon=":material/error:",
            )
        elif xs_query.startswith("Bounding Box") and box_area is not None and box_area >= 140:
            l_col.error(
                "ERROR - The selected bounding box is too large to process. Please select a smaller area.",
                icon=":material/error:",
            )
        else:
            with l_col:
                with st.spinner(text="Fetching data..."):
                    if xs_id is not None:
                        xs_gdf = get_data(catalog, xs_dom, xs_id)
                    elif all(var is not None for var in bbox_list):
                        xs_gdf = get_data(catalog, xs_dom, bbox_list)
            if xs_gdf is None or xs_gdf.empty:
                l_col.error(
                    "ERROR - No results returned. Please try a different query...", icon=":material/error:"
                )
            else:
                # Format and display map
                with l_col:
                    with st.spinner(text="Generating map...", show_time=True):
                        xs_map = format_xs_map(catalog, xs_gdf, xs_dom)
                r_col.markdown("#### Map")
                with r_col:
                    st_folium(fig=xs_map, width=725, returned_objects=[])

                with r_col.container(border=True, width=725):
                    with st.expander("##### Channel Geometry Legend", icon=":material/info:"):
                        st.markdown(three_dim_flowpath_tooltip(d_type="Y", w_type="TW"))
                    st.html(three_dim_flowpath_legend(upper_bound=25))
                    st.markdown(
                        "##### __Width (m)__\nRange: 0 &rarr; ~52450 meters. Mouseover reveals width value."
                    )

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
