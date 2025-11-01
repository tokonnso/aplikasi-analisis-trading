import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# --- Konfigurasi Halaman ---
# Mengatur judul tab browser dan ikon
st.set_page_config(
    page_title="Analisis Trading AI",
    page_icon="🔍",
    layout="centered"
)

# --- Judul di Halaman Aplikasi ---
st.title("Analisis Indikator Trading AI 📈🔍")
st.markdown("Unggah screenshot chart Anda, dan AI (Gemini) akan menganalisisnya.")

# --- Penanganan API Key ---
# Streamlit akan mencoba membaca key dari file rahasia .streamlit/secrets.toml
# yang telah Anda buat (untuk lokal) atau dari Secrets di dashboard Streamlit Cloud (untuk deployment).
try:
    # Mengambil API key dari Streamlit Secrets
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except (KeyError, FileNotFoundError):
    # Pesan error jika file secrets.toml atau key-nya tidak ditemukan
    st.error("File `.streamlit/secrets.toml` tidak ditemukan atau tidak berisi `GOOGLE_API_KEY`.")
    st.info("Harap buat file `.streamlit/secrets.toml` di folder proyek Anda dan tambahkan `GOOGLE_API_KEY = \"API_KEY_ANDA\"`.")
    st.stop() # Menghentikan eksekusi aplikasi
except Exception as e:
    # Menangani error lain terkait konfigurasi API
    st.error(f"Gagal mengkonfigurasi Google AI. Pastikan API Key Anda valid. Error: {e}")
    st.stop()

# --- Konfigurasi Model AI ---
# Kita menggunakan model gemini-2.5-flash-preview-09-2025 yang cepat dan mendukung input gambar
try:
    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
except Exception as e:
    st.error(f"Gagal memuat model Gemini. Error: {e}")
    st.stop()


# --- Sistem Prompt (Instruksi Permanen untuk AI) ---
# Ini adalah "otak" dari AI Anda, memberitahunya harus berperan sebagai apa.
system_prompt = """Anda adalah seorang analis teknikal trading AI yang ahli. 
Tugas utama Anda adalah menganalisis gambar screenshot chart trading yang diberikan dan secara proaktif mengidentifikasi pola indikator untuk memprediksi sinyal bullish atau bearish.
Pengguna akan memberikan konteks timeframe (misal: '1 Menit', '1 Jam', '1 Hari'). Gunakan informasi timeframe ini untuk menyempurnakan analisis Anda. Timeframe yang lebih pendek (scalping) memiliki implikasi yang berbeda dari timeframe harian (swing).

Fokus pada:
1.  **Analisis Indikator:** Cari sinyal di RSI (overbought, oversold, divergence), MACD (crossover, divergence), Moving Averages (golden cross, death cross), Bollinger Bands (squeeze, breakout).
2.  **Analisis Pola Candlestick:** Identifikasi pola reversal atau continuation (doji, hammer, engulfing).
3.  **Analisis Pola Chart:** Cari pola yang lebih besar (double top/bottom, head and shoulders, triangles, wedges).
4.  **Volume:** Analisis volume untuk mengkonfirmasi kekuatan sinyal.

**PENTING:** Jika ada pola chart yang jelas atau level support/resistance yang terlihat, coba identifikasi potensi target pergerakan harga atau level penting dalam analisis Anda. Namun, **TEGASKAN BAHWA INI SANGAT SPEKULATIF DAN HANYA BERDASARKAN VISUAL, BUKAN DATA REAL-TIME.** AI tidak memiliki akses ke data harga langsung atau fundamental pasar.

Setelah menganalisis semua ini, berikan kesimpulan prediksi: **BULLISH**, **BEARISH**, atau **NETRAL/SIDEWAYS**.
Jelaskan alasan Anda secara ringkas dan jelas berdasarkan apa yang Anda lihat di gambar.

Selalu akhiri dengan peringatan bahwa ini bukan nasihat keuangan (DYOR).
Jawab dalam Bahasa Indonesia.
"""

# --- UI (Tampilan) Aplikasi Streamlit ---

# 1. Input Gambar
uploaded_file = st.file_uploader("Pilih Gambar Screenshot", type=["jpg", "jpeg", "png"])

# Hanya tampilkan sisa UI jika gambar sudah diunggah
if uploaded_file is not None:
    # 2. Pratinjau Gambar
    try:
        image = Image.open(uploaded_file)
        # Menampilkan gambar yang diunggah
        st.image(image, caption="Gambar yang Diunggah", use_column_width=True)
    except Exception as e:
        st.error(f"Gagal memuat gambar: {e}")
        st.stop()
    
    # 3. Pilih Timeframe
    timeframe = st.selectbox(
        "Pilih Timeframe Chart",
        ("1 Menit", "5 Menit", "15 Menit", "30 Menit", "1 Jam", "4 Jam", "1 Hari", "1 Minggu", "Lainnya / Tidak Tahu"),
        index=4  # Default pilihan ke '1 Jam'
    )

    # 4. Tombol Analisis
    if st.button("Analisis Sekarang"):
        # Tampilkan loader saat AI bekerja
        with st.spinner("AI sedang menganalisis gambar Anda..."):
            try:
                # Buat prompt pengguna
                user_prompt = f"Lakukan analisis prediktif (bullish/bearish) pada gambar chart ini. Konteks timeframe adalah: {timeframe}."
                
                # Siapkan 'contents' untuk API
                contents = [
                    {
                        "role": "user",
                        "parts": [
                            {"text": user_prompt},
                            # Konversi gambar ke format yang dimengerti API
                            {"inline_data": {
                                "mime_type": uploaded_file.type,
                                "data": uploaded_file.getvalue()
                            }}
                        ]
                    }
                ]
                
                # Panggil API
                response = model.generate_content(
                    contents,
                    system_instruction=system_prompt
                )
                
                # 5. Tampilkan Hasil
                st.subheader("Hasil Analisis AI:")
                st.markdown(response.text)
                
                # Tampilkan Peringatan Penting
                st.warning(
                    "**Peringatan Penting:** Prediksi target harga atau pergerakan spesifik oleh AI hanya berdasarkan "
                    "analisis visual gambar statis dan sangat spekulatif. JANGAN gunakan ini sebagai dasar keputusan "
                    "trading Anda. AI TIDAK memiliki akses ke data harga real-time atau informasi pasar terkini.\n\n"
                    "*Ini adalah analisis AI dan bukan nasihat keuangan. Selalu lakukan riset Anda sendiri (DYOR).*"
                )

            except Exception as e:
                st.error(f"Terjadi kesalahan saat menghubungi API Gemini: {e}")
else:
    # Pesan jika belum ada gambar
    st.info("Silakan unggah gambar untuk memulai analisis.")

