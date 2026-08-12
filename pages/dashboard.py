"""Halaman Dashboard — ringkasan dataset training & performa model."""

from __future__ import annotations

import altair as alt
import streamlit as st
import torch

from config import EMOTION_COLORS, MODEL_DISPLAY_PATH, SER_BACKBONE
from services import MODELS_DIR, load_dataset_metadata, load_model_metrics, load_ser_model


def _id_number(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def main() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">Dashboard</div>
            <p class="hero-subtitle">Ringkasan dataset training dan performa model WavLM SER.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = load_dataset_metadata()
    metrics = load_model_metrics() or {}

    if df is None:
        st.warning("File metadata dataset (models/metadata_split_v7.csv) tidak ditemukan.")
        return

    device_name = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        model, _ = load_ser_model(device_name)
        param_label = f"{sum(p.numel() for p in model.parameters()) / 1e6:.1f} Jt"
    except Exception:
        param_label = "—"

    test_acc = metrics.get("test_acc")
    val_acc = metrics.get("best_val_acc")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Dataset", _id_number(len(df)))
    c2.metric("Parameter Model", param_label)
    c3.metric("Akurasi Test", f"{test_acc * 100:.1f}%" if test_acc is not None else "—")
    c4.metric("Akurasi Validasi Terbaik", f"{val_acc * 100:.1f}%" if val_acc is not None else "—")

    st.markdown(
        """
        <div class="section-card">
            <div class="section-step">Dataset</div>
            <div class="section-title">Distribusi Sampel</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.caption("Per Kelas Emosi")
        emo_df = df["emosi"].value_counts().rename_axis("Emosi").reset_index(name="Jumlah")
        chart = (
            alt.Chart(emo_df)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
            .encode(
                x=alt.X("Emosi:N", sort="-y", title=None),
                y=alt.Y("Jumlah:Q", title="Jumlah Sampel"),
                color=alt.Color(
                    "Emosi:N",
                    scale=alt.Scale(domain=list(EMOTION_COLORS.keys()), range=list(EMOTION_COLORS.values())),
                    legend=None,
                ),
                tooltip=["Emosi", "Jumlah"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart, use_container_width=True)

    with col2:
        st.caption("Per Split (Train / Val / Test)")
        split_df = df["split"].value_counts().reindex(["train", "val", "test"]).rename("Jumlah")
        st.bar_chart(split_df, height=300)

    st.caption("Per Sumber Dataset")
    sumber_df = df["sumber"].value_counts().rename("Jumlah")
    st.bar_chart(sumber_df, height=280)

    st.markdown(
        """
        <div class="section-card">
            <div class="section-step">Model</div>
            <div class="section-title">Kurva Training & Confusion Matrix</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    curve_path = MODELS_DIR / "kurva_training_v7.png"
    cm_path = MODELS_DIR / "confusion_matrix_v7.png"
    if curve_path.exists():
        st.image(str(curve_path), caption="Kurva Training vs Validasi", use_container_width=True)
    if cm_path.exists():
        st.image(str(cm_path), caption="Confusion Matrix (Test Set)", use_container_width=True)

    with st.expander("Detail Konfigurasi Model"):
        st.caption(f"Backbone: {SER_BACKBONE}")
        st.caption(f"Epoch terbaik: {metrics.get('best_epoch', '—')}")
        st.code(MODEL_DISPLAY_PATH, language=None)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    link1, link2 = st.columns(2)
    with link1:
        st.page_link("pages/model.py", label="Lihat detail Model →", icon="🧠")
    with link2:
        st.page_link("pages/dataset.py", label="Lihat detail Dataset →", icon="📚")


main()
