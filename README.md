# Speech Emotion Recognition (SER) & Whisper STT App

Aplikasi web berbasis Streamlit untuk mendeteksi emosi ucapan (Speech Emotion Recognition) menggunakan arsitektur WavLM (`microsoft/wavlm-base-plus`) versi v7 yang diintegrasikan dengan transkrip teks otomatis Whisper STT (`openai/whisper-small`).

---

## Fitur Utama

- Analisis Emosi Berbasis WavLM v7: Mendeteksi 6 kelas emosi (netral, senang, sedih, marah, takut, jijik) dengan model WavLM + Attentive Pooling yang dilatih pada multi-corpus dataset.
- Transkrip Teks Otomatis (Speech-to-Text): Mentranskripsi pembicaraan audio penuh menggunakan OpenAI Whisper via transformers (tanpa butuh instalasi binary FFmpeg).
- Visualisasi Probabilitas: Menampilkan tingkat kepercayaan (confidence score) dan grafik batang probabilitas emosi.
- Auto-Download Checkpoint: Otomatis mendownload checkpoint model `ser_wavlm_v7_best.pt` dari Google Drive jika belum ada di lokal.
- Mobile-First Responsive Interface: Antarmuka adaptif yang nyaman diakses dari smartphone maupun desktop.

---

## Spesifikasi Inferensi Model

| Parameter                  | Spesifikasi                                |
| :------------------------- | :----------------------------------------- |
| Model Backbone             | `microsoft/wavlm-base-plus`              |
| Model Checkpoint           | `models/ser_wavlm_v7_best.pt` (WavLM v7) |
| Sample Rate Input          | 16,000 Hz (Mono)                           |
| Durasi Maksimum SER        | 4.0 detik (pad / crop otomatis)            |
| Transkrip STT              | Audio Gelombang Penuh (Full Waveform)      |
| Fungsi Aktivasi Classifier | `nn.GELU()`                              |

### Class Index & Label Emosi:

| ID | Label Emosi | Visual Icon |
| :-: | :---------- | :---------: |
| 0 | `netral`  |     😐     |
| 1 | `senang`  |     😊     |
| 2 | `sedih`   |     😢     |
| 3 | `marah`   |     😡     |
| 4 | `takut`   |     😨     |
| 5 | `jijik`   |     🤢     |

---

## Panduan Instalasi (Step-by-Step)

Ikuti langkah-langkah di bawah ini secara berurutan untuk menghindari kesalahan konfigurasi lingkungan (environment):

### 1. Clone Repositori & Masuk Direktori

```bash
git clone https://github.com/Elnathz/speech-emotion-detection.git
cd speech-emotion-detection
```

### 2. Buat & Aktifkan Virtual Environment (.venv)

> **PENTING:** Selalu gunakan Virtual Environment agar paket tidak mengotori Python sistem global dan terhindar dari bentrok Environment PATH.

- **Windows (PowerShell)**:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **Linux / macOS (Bash/Zsh)**:
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  ```

### 3. Install Dependensi Python

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## Menjalankan Aplikasi

Jalankan Streamlit menggunakan Python Module Runner (`python -m streamlit`) di terminal yang sudah teraktifkan `.venv`:

```powershell
python -m streamlit run app.py
```

Aplikasi akan otomatis terbuka di browser pada alamat: `http://localhost:8501`.

---

## Troubleshooting & Kesalahan Umum (Gotchas)

Berikut adalah daftar masalah umum yang sering terjadi beserta solusinya:

### 1. `streamlit : The term 'streamlit' is not recognized...`

- **Penyebab**: Executable `streamlit.exe` berada di folder `Scripts` yang tidak terdaftar di Windows Environment Variable `PATH` sistem.
- **Solusi**:
  - Pastikan Virtual Environment `.venv` sudah diaktifkan (`.\.venv\Scripts\Activate.ps1`), ATAU
  - Jalankan Streamlit dengan perintah `python -m streamlit run app.py`.

### 2. Error Kompilasi C NumPy / Ninja / GCC (subcommand failed) saat `pip install`
- **Penyebab**: Menggunakan Python 3.13 dengan `requirements.txt` lama yang mematok `numpy<2.0` atau `numba==0.58.1`. PyPI tidak menyediakan pre-built `.whl` untuk NumPy 1.x pada Python 3.13 sehingga pip mencoba mengompilasi dari C source.
- **Solusi**: Gunakan file `requirements.txt` terbaru pada repo ini yang sudah melonggarkan batas versi (`numpy>=1.24.0`) agar pip secara otomatis mengunduh wheel binary pra-kompilasi.

### 3. `ImportError: cannot import name 'Wav2Vec2FeatureExtractor' from 'transformers'`
- **Penyebab**: Menjalankan aplikasi Streamlit ketika proses `pip install` di terminal lain belum selesai 100%, atau masalah lazy import pada versi `transformers` tertentu.
- **Solusi**: Tunggu hingga `pip install -r requirements.txt` selesai penuh. Kode di `app.py` sudah dilengkapi penanganan fallback ke `AutoFeatureExtractor`.

### 4. `NameError: name 'torch' is not defined`
- **Penyebab**: Modul `import torch` terhapus atau tertimpa pada baris atas `app.py`.
- **Solusi**: Pastikan baris `import torch` terpasang di bagian atas file `app.py` sebelum pemanggilan `torch.cuda.is_available()`.


---

## Struktur Proyek

```
speech-emotion-detection/
├── app.py                  # Entry point Streamlit — konfigurasi global & navigasi antar halaman
├── pages/
│   ├── analisis.py         # Halaman Analisis Emosi (upload/rekam audio, prediksi)
│   └── dashboard.py        # Halaman Dashboard — statistik dataset & performa model
├── model.py                # Arsitektur WavLMSERModel PyTorch & auto-download model
├── utils.py                # Preprocessing audio (16kHz mono, 4s crop, STT pipeline)
├── requirements.txt        # Daftar dependensi Python
├── AGENTS.md               # Sumber kebenaran operasional & konvensi commit
├── tdd_changes_tracker.md  # Pencatatan perubahan siklus TDD & audio spec
├── README.md               # Dokumentasi proyek
├── models/
│   └── ser_wavlm_v7_best.pt# Checkpoint model terlatih WavLM v7 (Auto-downloaded)
└── pipeline/
    └── ser-augmemted.ipynb # Notebook Jupyter sumber training & eksperimen model v7
```

---

## Standar Komitmen Kode (Conventional Commits)

Proyek ini menerapkan standar Conventional Commits (v1.0.0). Format pesan commit yang diizinkan:

```
<type>(<scope>): <subject>

[optional body]

Refs: tdd_changes_tracker.md / notebook v7
```

Tipe commit yang valid: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`.
Scope yang valid: `model`, `pipeline`, `ui`, `docs`, `chore`.
