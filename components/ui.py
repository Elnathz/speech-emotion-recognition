"""Komponen UI murni untuk merender elemen antarmuka."""

import json
from pathlib import Path

import streamlit as st
import pandas as pd
from config import EMOTION_ICONS, EMOTION_COLORS


def format_file_size(size_bytes: int | None) -> str:
    if not size_bytes:
        return "—"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def summarize_prediction(result: dict) -> dict:
    """Ringkas prediksi untuk tampilan ranking & margin (UI only)."""
    prob_df = result["probabilities_df"]
    top_pct = float(prob_df.iloc[0]["Persentase (%)"])

    second_label = None
    second_pct = 0.0
    if len(prob_df) > 1:
        second_label = str(prob_df.iloc[1]["Emosi"])
        second_pct = float(prob_df.iloc[1]["Persentase (%)"])

    margin_pp = top_pct - second_pct

    if margin_pp >= 20:
        separation = "Pemisahan kuat dari emosi lain"
    elif margin_pp >= 10:
        separation = "Pemisahan cukup jelas dari emosi lain"
    else:
        separation = "Pemisahan tipis — emosi lain masih dekat"

    return {
        "top_label": result["predicted_label"],
        "top_pct": top_pct,
        "second_label": second_label,
        "second_pct": second_pct,
        "margin_pp": margin_pp,
        "separation": separation,
        "num_classes": len(prob_df),
    }


def render_transcript_card(text: str) -> None:
    if text:
        body = f'<div class="transcript-text">"{text}"</div>'
    else:
        body = (
            '<div class="transcript-empty">Tidak ada ucapan yang terdeteksi '
            "(audio mungkin tanpa kata-kata yang jelas).</div>"
        )
    st.markdown(
        f"""
        <div class="transcript-card">
            <div class="transcript-head">📝 Transkrip Ucapan (Speech-to-Text)</div>
            {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _format_timestamp(seconds: float) -> str:
    total = int(round(seconds))
    return f"{total // 60:02d}:{total % 60:02d}"


def render_segment_timeline(segments: list[dict]) -> None:
    """Timeline emosi per-segmen transkrip (opt-in, hasil dari run_segment_predictions)."""
    st.markdown(
        '<div class="section-card">'
        '<div class="section-step">Per-Segmen</div>'
        '<div class="section-title">Emosi Sepanjang Transkrip</div>'
        "</div>",
        unsafe_allow_html=True,
    )
    for seg in segments:
        label = seg["result"]["predicted_label"]
        confidence = seg["result"]["confidence"] * 100
        icon = EMOTION_ICONS.get(label, "🎭")
        accent = EMOTION_COLORS.get(label, "#a3a3a3")
        time_range = f"{_format_timestamp(seg['start'])}–{_format_timestamp(seg['end'])}"
        text = seg["text"] or "(tanpa teks)"
        st.markdown(
            f"""
            <div class="segment-card" style="--emotion-color:{accent};">
                <div class="segment-time">{time_range}</div>
                <div class="segment-text">"{text}"</div>
                <div class="segment-emotion-row">
                    <span>{icon} <span style="text-transform:capitalize;">{label}</span></span>
                    <span>{confidence:.1f}%</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">Speech Emotion Recognition</div>
            <p class="hero-subtitle">
                Unggah atau rekam suara, dengarkan preview, lalu sistem akan memprediksi emosi
                dominan sekaligus menampilkan transkrip teks dari audio.
            </p>
            <span class="hero-badge">WavLM + Whisper STT</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">🎧</div>
            <div class="empty-title">Belum ada audio yang tersedia.</div>
            <div class="empty-desc">Unggah file .wav/.mp3 atau rekam langsung dari mikrofon.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metadata_card(
    filename: str,
    duration_sec: float,
    sample_rate: int,
    channels: int,
    file_size: str,
) -> None:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-step">Metadata Audio</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="meta-label">Nama File</div><div class="meta-value">{filename}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="meta-label">Durasi</div><div class="meta-value">{duration_sec} dtk</div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="meta-label">Sample Rate</div><div class="meta-value">{sample_rate} Hz</div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="meta-label">Channel</div><div class="meta-value">{channels}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="meta-label">Ukuran File</div><div class="meta-value">{file_size}</div>',
        unsafe_allow_html=True,
    )


def render_waveform_chart(envelope_df: pd.DataFrame) -> None:
    if envelope_df.empty:
        return
    st.markdown('<div class="meta-label" style="margin-top:0.75rem;">Bentuk Gelombang</div>', unsafe_allow_html=True)
    st.line_chart(envelope_df, height=140, color=["#fafafa", "#737373"])


def render_top3_cards(prob_df: pd.DataFrame) -> None:
    top3 = prob_df.head(3).reset_index(drop=True)
    cols = st.columns(3)
    for i, col in enumerate(cols):
        if i >= len(top3):
            break
        row = top3.iloc[i]
        emotion = row["Emosi"]
        pct = row["Persentase (%)"]
        col.markdown(
            f"""
            <div class="top3-card">
                <div class="top3-rank">#{i + 1}</div>
                <div class="top3-emoji">{EMOTION_ICONS.get(emotion, "🎭")}</div>
                <div class="top3-label">{emotion}</div>
                <div class="top3-conf-label">Confidence</div>
                <div class="top3-pct">{pct:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_probability_bars(prob_df: pd.DataFrame, highlight: str | None = None) -> None:
    for _, row in prob_df.iterrows():
        emotion = row["Emosi"]
        pct = float(row["Persentase (%)"])
        color = EMOTION_COLORS.get(emotion, "#a3a3a3")
        weight = "700" if emotion == highlight else "500"
        st.markdown(
            f"""
            <div class="prob-row-label">
                <span style="font-weight:{weight}; text-transform:capitalize;">
                    {EMOTION_ICONS.get(emotion, "")} {emotion}
                </span>
                <span style="font-weight:650; color:#fafafa;">{pct:.1f}%</span>
            </div>
            <div class="prob-bar-wrap">
                <div class="prob-bar-fill" style="width:{pct:.1f}%; background:{color};"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_export_buttons(result: dict, transcript: str | None, filename: str) -> None:
    """Tombol unduh hasil prediksi sebagai CSV atau JSON."""
    prob_df = result["probabilities_df"][["Emosi", "Persentase (%)"]]
    payload = {
        "filename": filename,
        "predicted_label": result["predicted_label"],
        "confidence": result["confidence"],
        "probabilities": {
            row["Emosi"]: round(float(row["Persentase (%)"]), 2) for _, row in prob_df.iterrows()
        },
        "transcript": transcript,
    }

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Unduh CSV",
            data=prob_df.to_csv(index=False).encode("utf-8"),
            file_name=f"ser_hasil_{Path(filename).stem}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "Unduh JSON",
            data=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=f"ser_hasil_{Path(filename).stem}.json",
            mime="application/json",
            use_container_width=True,
        )


def render_result_card(summary: dict) -> None:
    label = summary["top_label"]
    confidence = summary["top_pct"] / 100
    icon = EMOTION_ICONS.get(label, "🎭")
    accent = EMOTION_COLORS.get(label, "#a3a3a3")

    margin_html = ""
    if summary["second_label"]:
        margin_html = (
            f'<div class="result-margin">+{summary["margin_pp"]:.1f} p.p. dari '
            f'{summary["second_label"]} (#2 · {summary["second_pct"]:.1f}%)</div>'
        )

    st.markdown(
        f"""
        <div class="result-card" style="border-color: {accent}44;">
            <div class="result-inner">
                <div class="result-dominance">Emosi Dominan · Tertinggi dari {summary["num_classes"]} kelas</div>
                <div class="result-emoji">{icon}</div>
                <p class="result-label">{label}</p>
                <div class="result-conf-label">Skor Tertinggi</div>
                <div class="result-confidence">{summary["top_pct"]:.1f}%</div>
                <p class="result-rank-note">{summary["separation"]}</p>
                {margin_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
