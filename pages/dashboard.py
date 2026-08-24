"""Halaman Dashboard — status sistem dan aktivitas analisis pada sesi berjalan."""

from __future__ import annotations

from collections import Counter

import pandas as pd
import streamlit as st
import torch

from config import EMOTION_ICONS, IS_CLOUD, MAX_CLOUD_PREDICTIONS
from services import check_model_ready
from components.ui import render_section_header


def main() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">Dashboard</div>
            <p class="hero-subtitle">Status sistem dan aktivitas analisis pada sesi ini.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    device_name = "cuda" if torch.cuda.is_available() else "cpu"
    model_ready, model_error = check_model_ready(device_name)
    device_label = "GPU (CUDA)" if device_name == "cuda" else "CPU"

    render_section_header("Status Sistem", "Kesiapan Layanan Saat Ini")

    cols = st.columns(3 if IS_CLOUD else 2)
    cols[0].metric("Status Model", "Siap" if model_ready else "Gagal")
    cols[1].metric("Perangkat", device_label)
    if IS_CLOUD:
        used = st.session_state.get("cloud_prediction_count", 0)
        cols[2].metric("Kuota Cloud Sesi Ini", f"{used}/{MAX_CLOUD_PREDICTIONS}")

    if not model_ready and model_error:
        st.error(model_error)

    render_section_header("Aktivitas Sesi Ini", "Riwayat Analisis pada Sesi Berjalan")

    history = st.session_state.get("prediction_history", [])
    if not history:
        st.info("Belum ada analisis yang dijalankan pada sesi ini.")
        st.page_link("pages/analisis.py", label="Mulai analisis pertama →", icon=":material/mic:")
    else:
        total_count = st.session_state.get("session_analysis_count", len(history))
        top_emotion, _ = Counter(entry["label"] for entry in history).most_common(1)[0]

        stat1, stat2 = st.columns(2)
        stat1.metric("Total Analisis Sesi Ini", total_count)
        stat2.metric(
            "Emosi Terbanyak",
            f"{EMOTION_ICONS.get(top_emotion, '')} {top_emotion.capitalize()}",
        )

        activity_df = pd.DataFrame(
            [
                {
                    "Waktu": entry["time"],
                    "File": entry["filename"],
                    "Emosi": f"{EMOTION_ICONS.get(entry['label'], '')} {entry['label'].capitalize()}",
                    "Confidence": f"{entry['confidence'] * 100:.1f}%",
                }
                for entry in history
            ]
        )
        st.dataframe(activity_df, use_container_width=True, hide_index=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    link1, link2 = st.columns(2)
    with link1:
        st.page_link("pages/model.py", label="Lihat detail Model →", icon=":material/psychology:")
    with link2:
        st.page_link("pages/dataset.py", label="Lihat detail Dataset →", icon=":material/dataset:")


main()