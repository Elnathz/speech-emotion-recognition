# Walkthrough

## [2026-08-13] Fix Waveform Chart Tidak Muncul + Verifikasi Visual dengan Playwright

### Konteks
User melaporkan grafik "Bentuk Gelombang" di sidebar Analisis tidak muncul, dan mengizinkan menambahkan browser headless ke environment kerja kalau memang dibutuhkan untuk verifikasi visual (redesign IA sebelumnya sempat menandai ini sebagai item yang tidak bisa diverifikasi karena tidak ada browser).

### Root Cause
Bukan bug logic Python maupun CSS proyek ini. Ditemukan lewat investigasi bertahap dengan Playwright (screenshot + inspeksi SVG langsung, dibandingkan di app bare tanpa CSS proyek sama sekali untuk isolasi):
- `utils.get_waveform_envelope()` sehat (data non-empty, rentang nilai wajar) — bukan di situ masalahnya.
- `st.line_chart(envelope_df, height=100, color=[...])` di `components/ui.py::render_waveform_chart` adalah akar masalahnya: pada Streamlit 1.61.1, memberi parameter `height` eksplisit yang kecil membuat area plot vertikal kolaps karena "chrome" (axis + legend) menghabiskan hampir seluruh tinggi yang dialokasikan. Dibuktikan dengan mengukur langsung koordinat Y pada SVG yang dirender: `height=100` -> rentang Y garis = 0px (benar-benar rata/tidak kelihatan), `height=140` (nilai SEBELUM redesign sesi ini) -> cuma ~11px dari 140px (nyaris tidak kelihatan juga), `height=220` -> ~36px rentang Y (jelas kelihatan), default (tanpa `height`) -> ~76px dari 350px.
- Bug ini sudah ada SEBELUM sesi redesign kemarin (height lama 140 sudah di ambang batas nyaris-tidak-kelihatan) — perubahan sesi kemarin (140 -> 100) mengubahnya dari "nyaris tidak kelihatan" jadi "benar-benar hilang".

### Perbaikan
- `components/ui.py::render_waveform_chart`: `height` dinaikkan dari `100` ke `220`, dengan komentar `ponytail:` menjelaskan kenapa nilai kecil tidak aman dan titik amannya di mana.

### Tooling Ditambahkan
- Playwright (`pip install playwright` + `playwright install chromium`) dipasang di `.venv` lokal, **bukan** di `requirements.txt` — murni alat verifikasi visual untuk sesi kerja, bukan dependency runtime aplikasi (lihat AGENTS.md 4.1, Inference Only Scope).
- Chromium butuh library sistem (`libnspr4.so` dkk.) yang tidak ada di Arch Linux secara default. `playwright install-deps` bawaan cuma support Debian/Ubuntu/Fedora (pakai `apt-get`, tidak ada di Arch). User menginstal manual lewat `pacman -S nss nspr at-spi2-core libcups libdrm mesa libxkbcommon libxcomposite libxdamage libxfixes libxrandr gtk3 pango cairo alsa-lib` di terminal asli mereka (sesi ini tidak punya TTY interaktif untuk prompt password `sudo`).

### Verifikasi
- Alur penuh diuji lewat Playwright: upload file audio sungguhan (file WAV sintetis dengan amplitude bervariasi, bukan nada murni konstan yang ternyata kasus degenerate) ke `st.file_uploader` di sidebar (Playwright bisa simulasikan upload file browser sungguhan, beda dengan `AppTest` yang tidak bisa), klik "Analisis Emosi", tunggu hasil.
- Konfirmasi visual: waveform (garis Puncak putih + Lembah abu-abu) tampil jelas di sidebar setelah perbaikan; screenshot sebelum vs sesudah dibandingkan langsung.
- Konfirmasi hasil analisis lengkap tampil di konten utama: result card, transkrip, Top 3 Emosi, confidence bars, tombol export, expander Detail Teknis — menutup item verifikasi "alur upload sampai hasil belum diverifikasi end-to-end" dari redesign sebelumnya.
- Sekalian ditutup: navbar top (grup Beranda/Analisis/Insight, termasuk dropdown "Analisis" yang perlu diklik dulu untuk membuka) dan layout halaman Home terkonfirmasi tampil benar lewat screenshot — item yang sebelumnya juga ditandai belum diverifikasi.
- Sempat salah duga ada bug kedua ("hasil analisis tidak muncul, tetap menampilkan empty-state walau audio sudah di-upload") — ternyata false alarm dari metodologi tes sendiri: `render_empty_state()` dipanggil dari 2 tempat berbeda dengan pesan yang SAMA (belum ada audio sama sekali, vs audio ada tapi belum di-klik Analisis), dan skenario tes awal memang belum pernah klik tombol "Analisis Emosi". Dikonfirmasi lewat debug print sementara di server (dihapus lagi setelah terbukti) yang menunjukkan `audio_file` sudah terisi benar di run yang bersangkutan. Dicatat sebagai potensi perbaikan copy kecil di masa depan (bedakan pesan "belum ada audio" vs "audio siap, klik Analisis Emosi"), bukan bug.
- `python -m py_compile` dan `streamlit.testing.v1.AppTest` (kelima halaman) dijalankan ulang setelah semua perubahan -> bersih, tanpa exception.

### Yang Tidak Diubah
- Tidak ada perubahan pada logic inferensi/model.
- `requirements.txt` tidak disentuh (Playwright sengaja tidak jadi dependency project).

### Follow-up yang Disarankan
- Pertimbangkan pesan empty-state yang berbeda untuk "belum ada audio" vs "audio sudah dipilih, klik Analisis Emosi di sidebar" supaya tidak membingungkan (ditemukan saat verifikasi sesi ini, bukan diminta user).
- Kalau ke depan mau QA visual jadi bagian rutin (bukan cuma ad-hoc), pertimbangkan skrip Playwright permanen di repo (di luar scope sesi ini per instruksi user).

## [2026-08-13] Redesign UI Streamlit: Konsolidasi Token CSS & Komponen Section Header

### Konteks
Permintaan redesign tampilan Streamlit. Setelah eksplorasi kode, arsitektur komponen (`components/ui.py`, `css.py`, `sidebar.py`, `pages/*.py`) sudah cukup baik, tapi implementasi CSS-nya berantakan: warna/radius ditulis sebagai literal `rgba(...)` berulang di ~480 baris `components/css.py`, dan markup section header (step label + judul) diduplikasi manual di 4 halaman berbeda. Pengguna memutuskan lingkup redesign: fokus visual look & feel, tetap monokrom (dipoles bukan diganti skema warna), mencakup semua halaman.

### Keputusan Desain
- Tidak mengganti palet warna monokrom yang sudah ada, hanya menjadikannya konsisten lewat CSS custom properties (`:root`) di `components/css.py`, bukan membangun sistem token Python baru karena `EMOTION_COLORS`/`EMOTION_ICONS` di `config.py` memang harus tetap di Python (dipakai untuk inline style).
- Skala radius disederhanakan jadi 3 tingkat (`--radius-sm/md/lg`) menggantikan campuran 10-20px yang sebelumnya dipilih tidak konsisten antar komponen.
- Transisi hover ditambahkan pada card yang berperilaku seperti daftar (`section-card`, `top3-card`, `segment-card`, item sidebar), bukan pada `hero-card`/`result-card` yang statis.
- Inkonsistensi confusion matrix (PNG statis di `dashboard.py` vs Altair recompute di `model.py`) sengaja tidak disentuh karena itu masalah data/logic, bukan visual.
- Tidak membangun theming light/dark karena pengguna memilih tetap monokrom.

### File yang Diubah
- `components/css.py`: tambah blok `:root` token (surface, border, teks, radius, transisi), ganti literal berulang dengan `var(--token)`, tambah hover state.
- `components/ui.py`: tambah `render_section_header(step, title="", desc=None)`, escape teks dinamis (`transcript`, `segment text`) dengan `html.escape()` di `render_transcript_card()` dan `render_segment_timeline()`, pindahkan `summarize_prediction()` keluar (murni logic, bukan render).
- `utils.py`: terima `summarize_prediction()` dari `components/ui.py`.
- `pages/analisis.py`, `pages/dashboard.py`, `pages/model.py`: ganti markup `section-card` manual (masing-masing 2-3 lokasi) dengan pemanggilan `render_section_header()`.
- `pages/dataset.py`: hapus helper lokal `_section()`, pakai `render_section_header()` yang dibagi bersama.

### Yang Tidak Diubah
- Skema warna monokrom, `EMOTION_COLORS`/`EMOTION_ICONS` di `config.py`.
- Layout kolom (`st.columns`) di setiap halaman, jadi responsivitas mobile-first yang sudah ada tidak berubah; hover state hanya berlaku desktop dan tidak memengaruhi perangkat sentuh.
- Confusion matrix ganda (PNG di dashboard vs Altair di halaman model), logic inferensi, arsitektur model, pipeline audio.

### Verifikasi
- `python -m py_compile` untuk seluruh file yang diubah plus `app.py`, `config.py`, `model.py`, `services.py` -> tanpa error sintaks.
- `streamlit.testing.v1.AppTest` dijalankan lewat entry point `app.py` (mensimulasikan `st.navigation` asli, bukan impor file halaman langsung) untuk keempat halaman (Analisis, Dashboard, Model, Dataset) -> tanpa exception, markup `render_section_header()` ter-render dengan benar termasuk escaping karakter HTML.
- Server Streamlit dijalankan lokal (`.venv/bin/streamlit run app.py`) untuk memastikan proses start tanpa error sebelum verifikasi lewat AppTest.
- Ditemukan (tapi tidak diperbaiki, di luar lingkup redesign visual): `AppTest.from_file("pages/dashboard.py")` yang dipanggil langsung (tanpa lewat `app.py`) gagal dengan `ImportError` karena tabrakan nama modul antara `model.py` di root dan `pages/model.py`. Dikonfirmasi lewat `git stash` bahwa masalah ini sudah ada sebelum redesign ini dan tidak muncul saat navigasi lewat `app.py` yang sebenarnya.

### Follow-up yang Disarankan (Belum Dikerjakan)
- Uji visual manual di browser (screenshot sebelum/sesudah tiap halaman) karena environment kerja ini tidak punya headless browser/Playwright untuk verifikasi otomatis.
- Pertimbangkan menyatukan tabrakan nama `model.py`/`pages/model.py` yang ditemukan di atas, di luar lingkup task ini.

## [2026-08-12] Fitur Rekam Mikrofon Langsung (Live Record)

### Konteks
Branch `dev-eln`. Sebelumnya aplikasi hanya menerima audio melalui `st.file_uploader` (.wav/.mp3). Ditambahkan opsi rekam langsung dari mikrofon browser, lalu pengguna tetap menekan tombol "Analisis Emosi" secara manual (bukan inferensi otomatis saat rekaman selesai).

### Keputusan Desain
- Menggunakan `st.audio_input` native Streamlit, bukan dependency pihak ketiga (`streamlit-webrtc` dsb). Hasilnya adalah `UploadedFile` (subclass `BytesIO`) berformat WAV yang langsung kompatibel dengan `load_audio()` di `utils.py` tanpa modifikasi decoder.
- Tidak mengimplementasikan inferensi real-time/streaming. Kebutuhan yang diminta adalah pola "rekam, berhenti, preview, analisis", sesuai opsi 1 dari dua kemungkinan makna "live record" yang didiskusikan.
- Cache key prediksi diubah dari `(nama_file, ukuran_file)` menjadi `(sumber, sha256(bytes_audio))` karena dua rekaman mikrofon dapat memiliki nama dan ukuran identik, sehingga cache lama berisiko tidak ter-invalidasi dengan benar.

### File yang Diubah
- `app.py`: pemilih sumber (`st.radio`), integrasi `st.audio_input`, unifikasi variabel `uploaded_file` -> `audio_file`, fungsi `_audio_key()` menggantikan `_upload_key()`.
- `components/ui.py`: copy `render_hero()` dan `render_empty_state()` diperbarui agar netral terhadap sumber audio (unggah atau rekam).
- `requirements.txt`: `streamlit>=1.28.0` dinaikkan ke `streamlit>=1.41.0` karena `st.audio_input` baru general availability di v1.40.0 dengan perbaikan bug penting di v1.41.0.
- `tdd_changes_tracker.md`: dicatat sesuai kebijakan proyek untuk perubahan yang menyentuh alur input inferensi.

### Yang Tidak Diubah
- `model.py`, arsitektur `WavLMSERModel`, dan `services.py` (loading model/feature extractor).
- `utils.py`, termasuk `MAX_DURATION_SECONDS = 4.0`, target sample rate `16000 Hz`, dan pipeline STT Whisper.
- Label emosi Bahasa Indonesia (`netral`, `senang`, `sedih`, `marah`, `takut`, `jijik`).

### Verifikasi
- `python -m py_compile app.py components\ui.py components\sidebar.py components\css.py services.py config.py utils.py model.py` -> berhasil tanpa error sintaks.
- Verifikasi runtime penuh (`import streamlit`, `import utils`) tidak dapat dijalankan di environment kerja ini karena dependency (`streamlit`, `soundfile`, dll.) belum terpasang dan tidak ada virtualenv lokal (`.venv`) yang tersedia. Perlu dijalankan manual sebelum deployment:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  python -m streamlit run app.py
  ```

### Implikasi Operasional
- Mikrofon browser memerlukan konteks aman (`localhost` atau HTTPS). Pada deployment cloud tanpa HTTPS, tombol rekam akan gagal meminta izin mikrofon.
- Jika pengguna menolak izin mikrofon, mode "Unggah File" tetap tersedia sebagai fallback karena kedua mode independen melalui `st.radio`.

### Follow-up yang Disarankan (Belum Dikerjakan)
- Uji manual end-to-end dengan Streamlit terpasang: rekam audio, verifikasi metadata, jalankan prediksi, dan transkrip Whisper.
- Review responsivitas mobile untuk `st.radio` dan `st.audio_input` pada layar kecil, karena keduanya belum diverifikasi visual pada breakpoint mobile-first proyek ini.

## [2026-08-12] Perbaikan Bug Kritis: Crash Inferensi & Penyimpangan Arsitektur Pooling dari Checkpoint v7

### Konteks
Setelah fitur live record ditambahkan, pengguna melaporkan error "File audio tidak dapat diproses" saat menekan tombol Analisis Emosi. Investigasi lanjutan (bukan asumsi langsung) mengonfirmasi via tanya-jawab bahwa: (1) metadata dan pratinjau audio tampil normal sebelum error, artinya decode audio berhasil; (2) mode unggah file juga gagal dengan pesan sama. Kedua fakta ini mengeliminasi fitur live record sebagai penyebab, mengarah ke bug pre-existing di pipeline inferensi bersama.

### Root Cause yang Ditemukan
Tiga bug ditemukan lewat pembacaan kode dan perbandingan langsung dengan `pipeline/ser-augmemted.ipynb` (sumber kebenaran v7 per AGENTS.md):

1. **Crash `AttributeError`** di `utils.py` fungsi `predict_emotion()`. Pemanggilan `processor(...)` tanpa `return_tensors="pt"` mengembalikan list numpy, bukan tensor, sehingga `.to(device)` gagal. `except Exception` generik di `app.py` membungkam error asli menjadi pesan menyesatkan.

2. **Silent correctness bug** di `model.py` `AttentionPooling`. Implementasi lama mengembalikan `[attn_pooled, plain_mean]`, sedangkan checkpoint `ser_wavlm_v7_best.pt` dilatih dengan `[weighted_mean, weighted_std]` (attentive stats pooling). Karena nama atribut kebetulan sama, `load_state_dict(strict=True)` tidak pernah mendeteksi ketidakcocokan ini. Model tetap berjalan dan mengeluarkan angka, tapi separuh fitur classifier menerima distribusi input yang salah secara matematis.

3. **Preprocessing menyimpang dari kontrak v7** di `utils.py` `preprocess_audio()`. Tidak ada silence trim, peak normalization, atau zero-padding untuk audio pendek. Audio di bawah 4 detik (kasus umum untuk rekaman mikrofon) sebelumnya diloloskan dengan panjang tensor variabel, tidak pernah tepat 64000 sampel seperti kondisi training.

### Perbaikan yang Dilakukan
- `model.py`: `AttentionPooling.forward()` ditulis ulang menjadi attentive statistics pooling (weighted mean + weighted std), `WavLMSERModel.forward()` disesuaikan agar tidak lagi concat mean tambahan. `masked_fill` diganti dari `-inf` ke `-1e4` untuk mencegah NaN. `DEFAULT_DROPOUT` diselaraskan dari `0.35` ke `0.30`.
- `utils.py`: `predict_emotion()` dilengkapi argumen `padding`, `truncation`, `max_length`, `return_attention_mask`, `return_tensors="pt"` persis sesuai notebook. `preprocess_audio()` ditambah fungsi `_trim_silence()`, `_peak_normalize()`, `_fix_length_eval()` yang mereplikasi urutan wajib: sanitasi NaN -> trim 30dB (dengan guard panjang minimum) -> peak normalization -> center crop / right zero-pad ke tepat 64000 sampel.
- `app.py`: pesan error kini menyertakan `type(exc).__name__` dan pesan asli, ditambah expander traceback lengkap untuk debugging.

### Verifikasi yang Dilakukan
Karena `streamlit`, `torch`, dll. tidak terpasang di environment kerja utama, dibuat virtual environment sementara (`.venv_test`) khusus untuk pengujian, dihapus setelah selesai (tidak tercatat di git, tidak mengubah `requirements.txt` project):

1. Unit test murni numpy untuk `_trim_silence`, `_peak_normalize`, `_fix_length_eval`, dan sanitasi NaN, mencakup kasus audio pendek, audio panjang, audio hening total. Semua PASS, output selalu tepat 64000 sampel tanpa NaN.
2. Unit test `AttentionPooling` dan `WavLMSERModel.forward()` dengan backbone `microsoft/wavlm-base-plus` asli (bukan mock). Shape pooled `(1, 1536)`, shape logits `(1, 6)`, tanpa NaN, termasuk edge case partial attention mask.
3. Test `predict_emotion()` dengan `AutoFeatureExtractor` asli: berhasil tanpa `AttributeError`, softmax probabilitas menjumlah ke `1.0`.
4. Test pipeline penuh `preprocess_audio() -> predict_emotion()` untuk dua skenario: simulasi rekaman mikrofon pendek (1.5 detik, sample rate 48kHz, khas browser) dan simulasi unggah file panjang (6 detik, 16kHz). Keduanya PASS tanpa exception.

`python -m py_compile` juga dijalankan ulang untuk seluruh file yang diubah, berhasil tanpa error sintaks.

### Yang Belum Diverifikasi
- Akurasi aktual terhadap `models/evaluasi_test_v7.csv` untuk mengonfirmasi angka `test_acc 0.7746` di `models/config_v7.json` tercapai kembali setelah perbaikan pooling. Test yang dilakukan memakai waveform acak (random noise), bukan audio nyata dengan label ground truth, sehingga hanya membuktikan tidak ada crash dan shape/NaN benar, bukan membuktikan akurasi.
- Uji manual UI langsung (Streamlit berjalan) dengan rekaman mikrofon dan file unggah nyata.

### Dampak yang Perlu Diketahui
Hasil prediksi akan berbeda dibanding sebelum perbaikan ini, untuk audio yang sama persis. Ini disengaja karena perilaku lama salah secara matematis terhadap checkpoint yang dimuat. Jika ada laporan atau demo yang sudah terlanjur memakai output dari kode lama, angkanya tidak akan lagi cocok.

### Follow-up yang Disarankan
- Jalankan skrip evaluasi batch terhadap `models/evaluasi_test_v7.csv` atau subset test set asli untuk mengonfirmasi akurasi kembali ke kisaran `0.77`.
- Verifikasi manual di UI Streamlit dengan audio suara manusia nyata (bukan random noise), untuk kedua mode: unggah dan rekam mikrofon.
