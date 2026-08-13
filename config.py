"""File konfigurasi untuk aplikasi Streamlit SER."""

import os

# ---------------------------------------------------------------------------
# Konfigurasi STT (Speech-to-Text) — Whisper via transformers
# ---------------------------------------------------------------------------
SER_BACKBONE = "microsoft/wavlm-base-plus"
MODEL_DISPLAY_PATH = "models/ser_wavlm_v7_best.pt"
IS_CLOUD = os.environ.get("STREAMLIT_SERVER_HEADLESS") == "true"
ENABLE_STT = not IS_CLOUD  # STT hanya di lokal; cloud gratis RAM tidak cukup untuk 2 model
WHISPER_MODEL = "openai/whisper-small" if not IS_CLOUD else "openai/whisper-tiny"
WHISPER_LANGUAGE = "indonesian"

# Cloud gratis ~1 GB RAM — aman untuk 1 prediksi per sesi, refresh (F5) untuk file baru
MAX_CLOUD_PREDICTIONS = 1

# Aturan UX rekam mikrofon langsung (bukan bagian kontrak preprocessing model —
# lihat utils.MIN_DURATION_SECONDS/MAX_DURATION_SECONDS untuk itu)
MIN_RECORD_DURATION_SECONDS = 0.4

EMOTION_ICONS = {
    "netral": "😐",
    "senang": "😊",
    "sedih": "😢",
    "marah": "😠",
    "takut": "😨",
    "jijik": "🤢",
}

EMOTION_COLORS = {
    "netral": "#94a3b8",
    "senang": "#fbbf24",
    "sedih": "#60a5fa",
    "marah": "#f87171",
    "takut": "#38bdf8",
    "jijik": "#06b6d4",
}
