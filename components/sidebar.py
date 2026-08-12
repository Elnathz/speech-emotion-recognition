"""Komponen UI Sidebar."""

import streamlit as st
from config import SER_BACKBONE, MODEL_DISPLAY_PATH, EMOTION_COLORS, EMOTION_ICONS
from utils import ID2LABEL
from services import check_model_ready


def render_sidebar(device_name: str) -> None:
    model_ready, model_error = check_model_ready(device_name)
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

    sidebar_html = (
        f'<div class="sidebar-header">'
        f'<div class="sidebar-header-icon">🎙️</div>'
        f'<p class="sidebar-header-title">SER Assistant</p>'
        f'<p class="sidebar-header-sub">Deteksi emosi suara berbasis deep learning</p>'
        f"</div>"
        f'<div class="sidebar-stat-grid">'
        f'<div class="sidebar-stat-card"><div class="sidebar-stat-icon">🧠</div>'
        f'<div class="sidebar-stat-label">Backbone</div>'
        f'<div class="sidebar-stat-value">WavLM Base Plus</div></div>'
        f'<div class="sidebar-stat-card"><div class="sidebar-stat-icon">🎭</div>'
        f'<div class="sidebar-stat-label">Kelas</div>'
        f'<div class="sidebar-stat-value">6 Emosi</div></div>'
        f'<div class="sidebar-stat-card"><div class="sidebar-stat-icon">{device_icon}</div>'
        f'<div class="sidebar-stat-label">Perangkat</div>'
        f'<div class="sidebar-stat-value">{device_label}</div></div>'
        f'<div class="sidebar-stat-card"><div class="sidebar-stat-icon">📁</div>'
        f'<div class="sidebar-stat-label">Format</div>'
        f'<div class="sidebar-stat-value">.wav / .mp3</div></div>'
        f"</div>"
        f'<div class="sidebar-status-card {status_class}">'
        f'<div class="sidebar-status-dot {dot_class}"></div>'
        f"<div><div class=\"sidebar-status-text\">{status_text}</div>"
        f'<div class="sidebar-status-sub">{status_sub}</div></div>'
        f"</div>"
        f'<div class="sidebar-section-label">Peta Emosi</div>'
        f'<div class="sidebar-emotion-grid">{emotion_items}</div>'
    )

    with st.sidebar:
        st.markdown(sidebar_html, unsafe_allow_html=True)

        if not model_ready and model_error:
            st.error(model_error)

        history = st.session_state.get("prediction_history", [])
        if history:
            items = "".join(
                f'<div class="sidebar-history-item">'
                f'<span class="sidebar-history-emoji">{EMOTION_ICONS.get(entry["label"], "🎭")}</span>'
                f'<div class="sidebar-history-body">'
                f'<div class="sidebar-history-label">{entry["label"]} · {entry["confidence"] * 100:.0f}%</div>'
                f'<div class="sidebar-history-meta">{entry["time"]} · {entry["filename"]}</div>'
                f"</div></div>"
                for entry in history
            )
            st.markdown(
                f'<div class="sidebar-section-label">Riwayat Sesi</div>'
                f'<div class="sidebar-history-list">{items}</div>',
                unsafe_allow_html=True,
            )

        with st.expander("⚙️ Detail Teknis"):
            st.caption(f"Backbone: {SER_BACKBONE}")
            st.caption("Mode: inferensi saja (bukan training)")
            st.code(MODEL_DISPLAY_PATH, language=None)
