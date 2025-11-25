import pathlib

import streamlit as st

st.set_page_config(page_title="icefabric", layout="wide")
st.image("docs/img/icefabric.png", width=300)
st.markdown(pathlib.Path("README.md").read_text(), unsafe_allow_html=True)
