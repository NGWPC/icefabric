import os

import altair as alt
import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
import streamlit as st
from matplotlib.dates import DateFormatter
from streamlit_folium import st_folium

from app.routers.streamflow_observations.router import get_data_and_repo_hist as get_all_sf_obsv
from app.routers.streamflow_observations.router import validate_identifier as get_sf_obsv
from app.streamlit.helpers import (
    STYLE_MAP,
)
from icefabric.hydrofabric.subset_nhf import (
    HydrofabricSource,
    resolve_gage_to_flowpath,
)


@st.fragment
def create_overall_sf_chart(df, gage_id_user_sel):
    """Creates/saves/displays overall discharge hydrograph for given gage ID selection."""
    sf_discharge_path = (
        st.session_state.TEMP_OUTPUT_DIR
        / "sf_obsv_discharge_hydrographs"
        / f"sf_discharge_{gage_id_user_sel}.jpeg"
    )
    sf_discharge_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.plot(df["time"], df["q_cms"], label="Discharge", color="blue")
    ax.set_title(f"Discharge Hydrograph of {gage_id_user_sel}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Discharge (cms)")
    ax.legend(loc="best", edgecolor="k")
    ax.xaxis.set_major_formatter(DateFormatter("%b %Y"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(os.getcwd(), sf_discharge_path))
    plt.close(fig)

    st.image(os.path.join(os.getcwd(), sf_discharge_path), caption="Discharge Hydrograph")


@st.fragment
def show_sf_data(df, gage_id_user_sel):
    """Creates and displays the streamflow observations dataframe and overall hydrograph for a given gage ID selection."""
    with st.expander(label="Full Results", expanded=True):
        l_col, r_col = st.columns([2, 3], gap="small")
        df = ds.sel(id=gage_id_user_sel).to_dataframe().reset_index()
        df.dropna(subset=["q_cms"], inplace=True)
        l_col.markdown(f"### Streamflow Observations for Gage ID `{gage_id_user_sel}`")
        df = df[df["q_cms"] >= 0]
        df.drop(columns=["id"], inplace=True)
        l_col.dataframe(df, hide_index=True, width=700)
        with r_col:
            create_overall_sf_chart(df, gage_id_user_sel)

    with st.expander(label="Interactive Subset", expanded=True):
        year_sel, month_sel, time_disp_string = None, None, None
        sf_years_available = np.unique(df["time"].dt.year).tolist()
        year_sel = st.pills(
            label="__Available Years__",
            options=sf_years_available,
            selection_mode="single",
            help="Select a year to view the streamflow hydrograph for that year.",
        )
        if year_sel:
            year_max = df[df["time"].dt.year == year_sel]["q_cms"].max()
            sf_months_available = np.unique(df[df["time"].dt.year == year_sel]["time"].dt.month).tolist()
            month_sel = st.pills(
                label="__Available Months__",
                options=sf_months_available,
                selection_mode="single",
                help="Select a month to view the streamflow hydrograph for that year & month.",
            )
            if month_sel:
                df_subset = df[(df["time"].dt.year == year_sel) & (df["time"].dt.month == month_sel)]
                start_of_month = f"{year_sel}-{str(month_sel).zfill(2)}"
                if month_sel == 12:
                    end_of_month = f"{year_sel + 1}-01-01 00:00:00"
                else:
                    end_of_month = f"{year_sel}-{str(month_sel + 1).zfill(2)}"
                all_hours = pd.date_range(start=start_of_month, end=end_of_month, freq="h")[:-1]
                time_disp_string = f"{year_sel}-{str(month_sel).zfill(2)}"
            else:
                df_subset = df[df["time"].dt.year == year_sel]
                all_hours = pd.date_range(start=str(year_sel), end=str(year_sel + 1), freq="h")[:-1]
                time_disp_string = f"{year_sel}"
            df_subset = df_subset.set_index("time").reindex(all_hours).reset_index(names="time")
            st.markdown(f"### Hourly Discharge Hydrograph (Gage `{gage_id_user_sel}` - {time_disp_string})")
            chart = (
                alt.Chart(df_subset)
                .mark_line(
                    point=True,
                )
                .encode(
                    x=alt.X("time:T", title="Time"),
                    y=alt.Y("q_cms:Q", title="Discharge (m³/s)", scale=alt.Scale(domain=[0, year_max * 1.1])),
                    tooltip=[
                        alt.Tooltip("time:T", title="Time", format="%Y-%m-%d %H:%M"),
                        alt.Tooltip("q_cms:Q", title="Discharge (m³/s)"),
                    ],
                )
                .properties(height=750, width=1500)
            ).interactive()
            st.altair_chart(chart)


@st.fragment
def show_sf_map(gage_id_user_sel):
    """Show flowpath map of gage location."""
    nhf_flowpath_id = resolve_gage_to_flowpath(nhf_source, gage_id_user_sel)

    fp_df = (
        catalog.load_table("nhf.flowpaths").to_polars().filter(pl.col("fp_id") == nhf_flowpath_id).collect()
    )
    fp_id, div_id = fp_df["fp_id"][0], fp_df["div_id"][0]
    dv_df = catalog.load_table("nhf.divides").to_polars().filter(pl.col("div_id") == div_id).collect()
    st.markdown(f"### Map of Gage `{gage_id_user_sel}` Location (maps to flowpath ID `{fp_id}`)")

    fp_gdf = gpd.GeoDataFrame(
        fp_df,
        columns=fp_df.columns,
        geometry=gpd.GeoSeries.from_wkb(fp_df["geometry"]),
        crs="EPSG:5070",
    ).to_crs(epsg=4326)
    dv_gdf = gpd.GeoDataFrame(
        dv_df,
        columns=dv_df.columns,
        geometry=gpd.GeoSeries.from_wkb(dv_df["geometry"]),
        crs="EPSG:5070",
    ).to_crs(epsg=4326)

    m = folium.Map(tiles=folium.TileLayer(tiles="Cartodb Positron", control=False))
    minx, miny, maxx, maxy = dv_gdf.bounds.values.tolist()[0]
    m.fit_bounds([[miny, minx], [maxy, maxx]])

    fp_df_fig = folium.FeatureGroup(name="Flowpath")
    dv_gdf_fig = folium.FeatureGroup(name="Divide")
    fp_poly = folium.GeoJson(
        data=fp_gdf,
        style_function=lambda x, style=STYLE_MAP["flowpaths"]["styling"]: style,
    )
    dv_poly = folium.GeoJson(
        data=dv_gdf,
        style_function=lambda x, style=STYLE_MAP["divides"]["styling"]: style,
    )
    m.add_child(dv_gdf_fig.add_child(dv_poly))
    m.add_child(fp_df_fig.add_child(fp_poly))

    folium.LayerControl(position="bottomright").add_to(m)
    folium.plugins.Fullscreen(
        position="topright",
        title="Expand me",
        title_cancel="Exit me",
        force_separate_button=True,
    ).add_to(m)

    st_folium(fig=m, width=770, returned_objects=[])


st.session_state.TEMP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Streamflow Observations", layout="wide")
st.title("Streamflow Observations")
st.write("Please select a gage ID to view the streamflow observations and corresponding hydrograph.")


catalog = st.session_state.catalog
nhf_source = HydrofabricSource(parquet_dir=None, catalog=catalog)
# Get list of gage IDs for dropdown selection
try:
    sf_obsv_ds, _ = get_all_sf_obsv()
    ids = np.unique(sf_obsv_ds.coords["id"]).tolist()
except PermissionError as e:
    st.error(f"{e}", icon=":material/error:")

with st.form("Select Gage", width=300):
    st.markdown("#### __Gage Selection__")
    ds = None
    gage_id_user_sel = st.selectbox(
        label="__ID__", options=ids, help="Select a gage ID to view its streamflow observations."
    )
    sel_submit = st.form_submit_button("Submit")
    if sel_submit:
        try:
            ds, _ = get_sf_obsv(gage_id_user_sel)
        except PermissionError as e:
            st.error(f"{e}", icon=":material/error:")
        df = ds.sel(id=gage_id_user_sel).to_dataframe().reset_index()
        df.dropna(subset=["q_cms"], inplace=True)

if sel_submit and ds:
    show_sf_data(df, gage_id_user_sel)

    with st.expander(label="Gage Map", expanded=True, width=800):
        show_sf_map(gage_id_user_sel)
