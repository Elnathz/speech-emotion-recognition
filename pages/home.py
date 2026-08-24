"""Halaman Home — landing page pengenalan project Speech Emotion Recognition."""

from __future__ import annotations

import torch
import streamlit as st

from config import EMOTION_COLORS, EMOTION_ICONS
from services import check_model_ready
from utils import ID2LABEL
from components.ui import render_hero


def main() -> None:
    render_hero()

    device_name = "cuda" if torch.cuda.is_available() else "cpu"
    model_ready, _ = check_model_ready(device_name)
    device_icon = "🚀" if device_name == "cuda" else "💻"
    device_label = "GPU (CUDA)" if device_name == "cuda" else "CPU"

    status_class = "sidebar-status-ok" if model_ready else "sidebar-status-fail"
    dot_class = "ok" if model_ready else "fail"
    status_text = "Model Siap" if model_ready else "Model Gagal"
    status_sub = "Checkpoint berhasil dimuat" if model_ready else "Periksa file model"

    emotion_items = "".join(
        f'<div class="sidebar-emotion-item" style="--emotion-color:{EMOTION_COLORS[label]};">'
        f'<span class="sidebar-emotion-emoji">{EMOTION_ICONS[label]}</span>'
        f"<span>{label}</span>"
        f'<span class="sidebar-emotion-id">{idx}</span></div>'
        for idx in sorted(ID2LABEL)
        for label in [ID2LABEL[idx]]
    )

    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown(
            f"""
            <div class="sidebar-stat-grid">
                <div class="sidebar-stat-card"><div class="sidebar-stat-icon">🧠</div>
                <div class="sidebar-stat-label">Backbone</div>
                <div class="sidebar-stat-value">WavLM Base Plus</div></div>
                <div class="sidebar-stat-card"><div class="sidebar-stat-icon">🎭</div>
                <div class="sidebar-stat-label">Kelas</div>
                <div class="sidebar-stat-value">6 Emosi</div></div>
                <div class="sidebar-stat-card"><div class="sidebar-stat-icon">{device_icon}</div>
                <div class="sidebar-stat-label">Perangkat</div>
                <div class="sidebar-stat-value">{device_label}</div></div>
                <div class="sidebar-stat-card"><div class="sidebar-stat-icon">📁</div>
                <div class="sidebar-stat-label">Format</div>
                <div class="sidebar-stat-value">.wav / .mp3</div></div>
            </div>
            <div class="sidebar-status-card {status_class}">
                <div class="sidebar-status-dot {dot_class}"></div>
                <div><div class="sidebar-status-text">{status_text}</div>
                <div class="sidebar-status-sub">{status_sub}</div></div>
            </div>
            <div class="sidebar-section-label">Peta Emosi</div>
            <div class="sidebar-emotion-grid">{emotion_items}</div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
        st.page_link("pages/analisis.py", label="Mulai Analisis →", icon="🎙️")
        st.page_link("pages/model.py", label="Lihat detail Model →", icon="🧠")


main()  