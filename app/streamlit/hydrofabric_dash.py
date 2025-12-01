import pathlib
import tempfile

import streamlit as st
from botocore.exceptions import ClientError

from app.streamlit.helpers import (
    create_table_from_schema,
    load_hf_gpkg,
    post_transient_success_msg,
)
from app.streamlit.tooltips import hf_loading_info_box
from icefabric.cli.streamflow import NoResultsFoundError
from icefabric.schemas.iceberg_tables import nhf_layers
from tools.hydrofabric.nhf_subset import subset_hydrofabric

TMP_DIR = pathlib.Path(tempfile.gettempdir())
NHF_PARQUETS_DIR = pathlib.Path("data/nhf_parquets")


def subset_query(type):
    """Helper to track subset query submission/reset."""
    if type == "submit":
        st.session_state.subset_submitted = True
    if type == "reset":
        st.session_state.subset_submitted = False


# Initialize tracker for generated subset files
if "hf_subset_files" not in st.session_state:
    st.session_state["hf_subset_files"] = []

if "subset_submitted" not in st.session_state:
    st.session_state.subset_submitted = False

st.set_page_config(page_title="NGWPC Hydrofabric", layout="wide")
st.title("NGWPC Hydrofabric")
st.write("Information for the NextGen Water Prediction Capability Hydrofabric")

hf_options = list(nhf_layers.keys())
hf_options_display = [opt.replace("_", " ").title() for opt in hf_options]
l_col, r_col = st.columns(2, gap="large")

l_col.image(
    "app/streamlit/resources/hydrofabric_diagram.png",
    width=900,
    caption="Entity Relationship Diagram (ERD) for the Iceberg Hydrofabric Data Catalog.",
)
table_sel = l_col.pills(label="__Data Models__", options=hf_options_display, selection_mode="single")

if table_sel is not None:
    selected_schema = hf_options[hf_options_display.index(table_sel)]
    data_model_exp = l_col.expander("HF Table Data Model", icon=":material/data_table:")
    data_model = create_table_from_schema(nhf_layers[selected_schema])
    data_model_exp.markdown(
        f"The selected table (`{table_sel}`) is stored/formatted as the data schema below:"
    )
    data_model_exp.dataframe(data=data_model, hide_index=True, row_height=65)

r_col.markdown("#### Subset the data")
r_col.write(
    "Enter an origin node ID below to subset the hydrofabric. Upstream data will be returned, originating from that node."
)
origin_id = r_col.text_input(
    label="Origin ID", value="", on_change=subset_query, args=("reset",), placeholder="e.g., 01010000"
)
if origin_id != "" and origin_id is not None:
    if origin_id.isdigit():
        origin_id = int(origin_id.rstrip())
    else:
        origin_id = ""
        r_col.error("ERROR - Origin ID must be a numeric value.", icon=":material/error:")

r_col.button("Submit", on_click=subset_query, args=("submit",), disabled=(origin_id == ""))

if st.session_state.subset_submitted and origin_id != "":
    subset_gpkg_file = TMP_DIR / f"subset_origin_{origin_id}.gpkg"
    subset_successful = False

    # Subset, unless already done for this origin ID in this session
    if subset_gpkg_file not in st.session_state["hf_subset_files"]:
        try:
            subset_status = r_col.empty()
            hf_loading_markdown = hf_loading_info_box(origin_id)
            subset_status.info(hf_loading_markdown, icon=":material/hourglass_empty:")
            subset_hydrofabric(parquet_dir=NHF_PARQUETS_DIR, flowpath_id=origin_id, output=subset_gpkg_file)
            subset_status.empty()
            st.session_state["hf_subset_files"].append(subset_gpkg_file)
            post_transient_success_msg("Subsetting complete!")
            subset_successful = True
        except ClientError:
            r_col.error(
                "ERROR - Authentication failed. Please update/validate your credentials.",
                icon=":material/error:",
            )
        except NoResultsFoundError as nrf:
            r_col.error(f"ERROR - {nrf} - please try a different origin ID.", icon=":material/error:")
    else:
        subset_successful = True

    if subset_successful:
        # Vertical spacing
        r_col.space()

        # Load and display subset data
        subset_dfs = load_hf_gpkg(subset_gpkg_file)
        df_group = r_col.container(border=True)
        with df_group:
            st.markdown(f"#### __Subset Data Results ({origin_id})__")
            for name, df in subset_dfs.items():
                with st.expander(f"##### __{name}__", icon=":material/data_table:"):
                    st.dataframe(data=df, hide_index=False)

        with open(subset_gpkg_file, "rb") as file:
            r_col.download_button(
                label="Download as Geopackage",
                data=file,
                file_name=subset_gpkg_file.name,
                on_click="ignore",
                mime="application/geopackage+sqlite3",
                icon=":material/download:",
            )
