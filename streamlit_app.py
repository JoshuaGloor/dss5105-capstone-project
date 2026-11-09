"""Run with: sh scripts/run_app.sh (or uv run streamlit run streamlit_app.py)."""

import streamlit as st

from dss5105 import assistant_page, lab_page, memory_page, web_app, workshop_ui

st.set_page_config(page_title="StitchFlow", page_icon=":material/graphic_eq:", layout="wide")
pages = [
    st.Page(assistant_page.render, title="Assistant", icon=":material/graphic_eq:", default=True),
    st.Page(web_app.main, title="Desk", icon=":material/space_dashboard:", url_path="desk"),
    st.Page(workshop_ui.render_page, title="Workshops", icon=":material/factory:", url_path="workshops"),
    st.Page(lab_page.render, title="Objective lab", icon=":material/science:", url_path="lab"),
    st.Page(memory_page.render, title="Memory", icon=":material/neurology:", url_path="memory"),
]
st.navigation(pages, position="top").run()
