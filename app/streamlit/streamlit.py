import os
import pathlib
import sys
import tempfile

import streamlit as st

from icefabric.helpers.creds import load_creds

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

modules = {
    "": [st.Page("home.py", title="Home")],
    "Modules": [
        st.Page("hydrofabric_dash.py", title="NGWPC Hydrofabric", icon=":material/water_drop:"),
        st.Page("ras_xs_dash.py", title="RAS XS", icon=":material/arrow_range:"),
    ],
}
# Favicon image: "Iceberg" designed by Freepik
# source: https://www.flaticon.com/free-icon/iceberg_2466034 - Free for use with attribution.
st.logo("app/streamlit/resources/iceberg_favicon.png", size="large", link=None, icon_image=None)
st.set_page_config(
    page_title="icefabric", layout="wide", page_icon="app/streamlit/resources/iceberg_favicon.png"
)

# Cleanup temp files on app start
if "initialized" not in st.session_state or not st.session_state.initialized:
    if "NHF_SUBSET_OUTPUT_DIR" not in st.session_state:
        st.session_state["NHF_SUBSET_OUTPUT_DIR"] = (
            pathlib.Path(tempfile.gettempdir()) / "icefabric_streamlit_subsets"
        )
    for item in st.session_state.NHF_SUBSET_OUTPUT_DIR.iterdir():
        if item.is_dir():
            item.rmdir(missing_ok=True)
        else:
            item.unlink(missing_ok=True)
    st.session_state.initialized = True

pg = st.navigation(modules)
pg.run()
