import os
import pathlib
import sys
import tempfile

import streamlit as st
from pyiceberg.catalog import load_catalog

from icefabric.helpers.creds import load_creds

# Deploy environment default is "test"
deploy_env = "test"
args_provided = sys.argv[1:]

# Parse deploy-env argument
if any("deploy-env=" in a for a in args_provided):
    try:
        deploy_env_pass = " ".join(args_provided).split("deploy-env=")[1].split()[0]
        if deploy_env_pass.lower() in ["t", "test", "p", "prod", "production", "l", "local"]:
            deploy_env = deploy_env_pass.lower()
    except IndexError:
        pass

# Check environment variable override
deploy_env = os.environ.get("ICEFABRIC_DEPLOY_ENV") or os.environ.get("ENVIRONMENT") or deploy_env

# Set catalog type based on deploy environment
catalog_type = "sql" if deploy_env in ["l", "local"] else "glue"

# Load credentials
load_creds(deploy_env)

# Load catalog and store in session state
if "catalog" not in st.session_state:
    st.session_state.catalog = load_catalog(catalog_type)
if "catalog_type" not in st.session_state:
    st.session_state.catalog_type = catalog_type
if "deploy_env" not in st.session_state:
    st.session_state.deploy_env = deploy_env

modules = {
    "": [st.Page("home.py", title="Home")],
    "Modules": [
        st.Page("hydrofabric_dash.py", title="NGWPC Hydrofabric", icon=":material/water_drop:"),
        st.Page("ras_xs_dash.py", title="RAS XS", icon=":material/arrow_range:"),
        st.Page("sf_obsv_dash.py", title="Streamflow Observations", icon=":material/waves:"),
    ],
}

st.logo("app/streamlit/resources/iceberg_favicon.png", size="large", link=None, icon_image=None)
st.set_page_config(
    page_title="icefabric", layout="wide", page_icon="app/streamlit/resources/iceberg_favicon.png"
)

# Cleanup temp files on app start
if "initialized" not in st.session_state or not st.session_state.initialized:
    if "TEMP_OUTPUT_DIR" not in st.session_state:
        st.session_state["TEMP_OUTPUT_DIR"] = (
            pathlib.Path(tempfile.gettempdir()) / "icefabric_streamlit_tmp_files"
        )
    st.session_state.TEMP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for dir in st.session_state.TEMP_OUTPUT_DIR.iterdir():
        for item in dir.iterdir():
            if item.is_dir():
                pass
            else:
                item.unlink(missing_ok=True)
    st.session_state.initialized = True

pg = st.navigation(modules)
pg.run()
