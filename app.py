"""Entry point aplikasi Streamlit — konfigurasi global & navigasi antar halaman."""

from __future__ import annotations

import streamlit as st

from components.css import inject_custom_css

st.set_page_config(
    page_title="Speech Emotion Recognition",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()

pages = [
    st.Page("pages/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("pages/analisis.py", title="Analisis Emosi", icon=":material/mic:"),
    st.Page("pages/dashboard.py", title="Dashboard", icon=":material/dashboard:"),
    st.Page("pages/model.py", title="Model", icon=":material/psychology:"),
    st.Page("pages/dataset.py", title="Dataset", icon=":material/dataset:"),
]
pg = st.navigation(pages, position="top")
pg.run()
