# Panduan & Penjelasan Mendetail Notebook Training (ser-augmemted.ipynb)

### Penjelasan Komprehensif Preprocessing, Arsitektur WavLM, Tuning & Audio Signal Physics

Dokumen ini dirancang sebagai panduan komprehensif bagi developer yang ingin memahami aspek teknis pemrosesan sinyal audio, arsitektur deep learning WavLM, hyperparameter tuning, dan strategi penanganan noise pada notebook **`pipeline/ser-augmemted.ipynb` (WavLM v7)**.

---

## 1. Fisika Sinyal Suara & Preprocessing Audio

### 1.1 Mengapa Memilih `16,000 Hz` (16 kHz Sample Rate)?

- **Teorema Sampling Nyquist-Shannon**: Teorema ini menyatakan bahwa untuk mereplikasi sinyal analog ke digital tanpa kehilangan informasi (*aliasing*), frekuensi sampling minimal harus **2x lipat dari frekuensi tertinggi** yang ingin ditangkap:
  $$
  f_{\text{sample}} \ge 2 \times f_{\text{max}}
  $$
- **Spektrum Ucapan Manusia**: Suara manusia berada pada rentang frekuensi fundamental 85 Hz - 255 Hz (nada dasar suara laki-laki/perempuan). Namun, informasi emosi seperti formant, bisikan, dan intonasi tinggi berada pada kisaran 4,000 Hz - 8,000 Hz.
- **Hasil**: Dengan sample rate **16,000 Hz**, kita dapat menangkap sinyal audio hingga frekuensi **8,000 Hz** ($16,000 / 2$). Rentang ini mencakup **100% informasi spektral ucapan manusia** tanpa membuang memori untuk frekuensi musik tinggi (seperti 44.1 kHz yang tidak dibutuhkan untuk speech).
- **Spesifikasi Model WavLM**: Model *pre-trained* `microsoft/wavlm-base-plus` secara spesifik dilatih oleh Microsoft menggunakan input audio 16 kHz. Memasukkan sample rate lain akan merusak perhitungan langkah waktu (*time-step resolution*) model.

---

### 1.2 Mengapa `Mono` (1 Channel)?

- Informasi emosi manusia tersimpan dalam kontur intonasi, ritme, dan frekuensi ucapan, bukan pada arah spasial kiri/kanan (stereo). Merata-ratakan kanal stereo menjadi mono (`audio.mean(dim=0)`) menghemat 50% penggunaan memori GPU tanpa mengurangi akurasi inferensi.

---

### 1.3 Mengapa Durasi Dipotong ke `4.0 Detik` (`64,000` Sampel)?

- Pada audio ucapan manusia, ledakan emosi (*emotional burst*) paling pekat berada di **2 hingga 4 detik pertama**.
- Audio yang terlalu panjang (misal 6-10 detik) umumnya mengandung banyak hening (*silence*) di bagian akhir yang mengencerkan kelimpahan fitur emosi saat proses *pooling*.
- $4.0 \text{ detik} \times 16,000 \text{ sampel/detik} = 64,000 \text{ sampel}$ (panjang larik input tetap yang efisien untuk memori GPU T4/P100).

---

### 1.4 Silence Trimming (`top_db=30`) & Peak Normalization (`y / peak`)

- **Silence Trimming (`librosa.effects.trim(top_db=30)`)**: Memotong bagian diam di awal dan akhir audio yang berada 30 dB di bawah amplitudo puncak. Ini memastikan 4 detik yang diolah benar-benar berisi ucapan aktif.
- **Peak Normalization (`y = y / max(|y|)`)**: Mengubah amplitudo sinyal agar titik terkerasnya selalu berada pada skala `1.0` (rentang `[-1.0, 1.0]`). Tanpa normalisasi ini, ucapan lembut/tone rendah (`sedih` atau `marah` berbisik) memiliki amplitudo sangat kecil (misal 0.05) yang dibaca oleh WavLM sebagai ketidakpastian tinggi (*high uncertainty* / `takut`).

---

## 2. Arsitektur Model WavLMSER v7

### 2.1 WavLM Backbone (`microsoft/wavlm-base-plus`)
Berbeda dengan CNN yang memproses citra 2D, WavLM adalah arsitektur **Self-Supervised Transformer** 1D untuk sinyal audio:
1. **Convolutional Feature Encoder**: Mengubah sinyal mentah 64,000 sampel menjadi sekuens vektor fitur (200 frame per detik).
2. **Transformer Encoder**: 12/18 layer *Self-Attention* yang mempelajari hubungan kontekstual antarkata dan intonasi suara sepanjang waktu. WavLM dilatih dengan metode *Masked Speech Denoising* (mendengarkan jutaan jam audio berisik dan menebak bagian yang hilang), membuatnya sangat kebal terhadap bising latar belakang (*noise-robust*).

---

### 2.2 Attentive Stats Pooling

WavLM menghasilkan 800 frame vektor untuk audio 4 detik. Kita membutuhkan mekanisme untuk merangkum 800 frame tersebut menjadi 1 vektor emosi ringkas:

- **Attention Mechanism**: Memberikan bobot tinggi pada frame audio yang memiliki ledakan emosi (misal teriakan/isakan) dan bobot rendah pada frame netral.
- **Statistic Extraction**: Menghitung 2 nilai statistik terbobot:
  1. **Weighted Mean ($\mu$)**: Rerata kontur nada emosi.
  2. **Weighted Standard Deviation ($\sigma$)**: Variansi dinamika nada ucapan.
- Vektor hasil akhir digabungkan menjadi berukuran **1536** ($768 + 768$).

---

### 2.3 Classifier Head (`LayerNorm -> Linear -> GELU -> Linear`)

```
Input Feature Vector (1536)
       │
       ▼
nn.LayerNorm(1536)           <-- Menstabilkan variansi data
       │
       ▼
nn.Dropout(0.30)             <-- Mencegah overfitting
       │
       ▼
nn.Linear(1536, 256)         <-- Kompresi ke 256 fitur emosi abstrak
       │
       ▼
nn.GELU()                    <-- Non-linearitas halus (Gaussian Error Linear Unit)
       │
       ▼
nn.Dropout(0.225)            <-- Regularisasi tambahan (0.30 * 0.75)
       │
       ▼
nn.Linear(256, 6)            <-- Proyeksi ke 6 kelas emosi
```

- **Fungsi `GELU()` vs `ReLU()`**: `GELU()` melembutkan transisi pada nilai input negatif, mencegah neuron "mati" (*dead neuron problem*) yang sering terjadi pada `ReLU()`.

---

## 3. Tuning Hyperparameter & Strategi Training

### 3.1 Gradual Unfreezing (`UNFREEZE_LAST_N = 6`)

- Jika melatih seluruh 18 layer WavLM sekaligus dari awal (*full unfreeze*), pengetahuan dasar WavLM yang dilatih jutaan jam akan rusak (*catastrophic forgetting*).
- Notebook v7 membekukan 12 layer awal (pengetahuan akustik dasar) dan **hanya melatih 6 layer teratas** + classifier head.

---

### 3.2 Differential Learning Rates (`BACKBONE_LR = 1e-5`, `HEAD_LR = 3e-4`)

- **Backbone (`1e-5` / 0.00001)**: Diberi *learning rate* sangat kecil agar bobot pra-latih WavLM disempurnakan secara perlahan tanpa merusak representasi fitur dasar.
- **Classifier Head (`3e-4` / 0.0003)**: Diberi *learning rate* 30x lebih besar karena layer classifier baru diinisialisasi secara acak dan butuh penyesuaian cepat.

---

### 3.3 Mixup Augmentation (`MIXUP_ALPHA = 0.2`, `MIXUP_PROB = 0.25`)

- Mencampur 2 sampel audio pelatihan secara acak:

  $$
  \tilde{x} = \lambda x_i + (1 - \lambda) x_j
  $$

  $$
  \tilde{y} = \lambda y_i + (1 - \lambda) y_j
  $$
- Ini memaksa model mempelajari batas keputusan emosi yang halus dan mencegah model memprediksi probabilitas 100% secara berlebihan (*overconfidence*).

---

### 3.4 Label Smoothing (`LABEL_SMOOTHING = 0.10`)

- Mengubah target vektor kaku `[1, 0, 0, 0, 0, 0]` menjadi `[0.916, 0.016, 0.016, 0.016, 0.016, 0.016]`.
- Mencegah model menghafal label manusia yang mungkin salah atau subjektif.

---

### 3.5 2-Stage Training dengan Label Noise Detection

- **Stage 1 (22 Epoch)**: Melatih model pada seluruh dataset awal.
- **Noise Detection Task**: Menemukan sampel audio yang diprediksi salah oleh model dengan tingkat kepercayaan rendah (`confidence < 0.40`). Sampel ini ditandai sebagai *label noise* (label dari dataset asal yang salah ketik/subjektif).
- **Stage 2 Fine-Tuning (6 Epoch)**: Menurunkan bobot sampel yang dicurigai *noise* (`bobot * 0.3`), lalu melatih ulang model dengan *learning rate* kecil untuk menyempurnakan batas keputusan emosi akhir.

---

## 4. Peta Analogis untuk Web Developer

| Konsep Machine Learning Audio       | Analogi Web Development                                                  |
| :---------------------------------- | :----------------------------------------------------------------------- |
| **Sample Rate 16kHz**         | **Request Payload Rate / Data Resolution**                         |
| **Peak Normalization**        | **Input Payload Normalization (misal sanitasi string/trim)**       |
| **Attentive Stats Pooling**   | **Aggregation Processor (`GROUP BY` + Standard Deviation)**      |
| **GELU Activation**           | **Smooth Conditional Logic Filter**                                |
| **Gradual Unfreezing**        | **Incremental Migration (mengubah API tanpa merusak core system)** |
| **Label Noise Downweighting** | **Rate Limiting / Filtering Spam Requests**                        |
