import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="Analisis Trading AI",
    page_icon="🔍",
    layout="centered"
)

# --- Judul di Halaman Aplikasi ---
st.title("Analisis Indikator Trading AI 📈🔍")
st.markdown("Unggah screenshot chart Anda, dan AI (Gemini) akan menganalisisnya.")

# --- Penanganan API Key ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except (KeyError, FileNotFoundError):
    st.error("File `.streamlit/secrets.toml` tidak ditemukan atau tidak berisi `GOOGLE_API_KEY`.")
    st.info("Harap buat file `.streamlit/secrets.toml` di folder proyek Anda dan tambahkan `GOOGLE_API_KEY = \"API_KEY_ANDA\"`.")
    st.stop()
except Exception as e:
    st.error(f"Gagal mengkonfigurasi Google AI. Pastikan API Key Anda valid. Error: {e}")
    st.stop()

# --- Konfigurasi Model AI ---
try:
    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
except Exception as e:
    st.error(f"Gagal memuat model Gemini. Error: {e}")
    st.stop()

# --- Sistem Prompt (Instruksi Permanen untuk AI) ---
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

# --- Custom CSS untuk Styling ---
st.markdown("""
    <style>
    /* Mengatur warna latar belakang dan teks default */
    body {
        background-color: #f0f2f6; /* Warna abu-abu terang */
        color: #333333;
    }
    .stApp {
        background-color: #f0f2f6;
    }
    
    /* Styling untuk bagian header/top bar (jika ada) */
    .css-1d391kg, .css-1dp5vir { /* Elemen yang mungkin memegang top bar atau header */
        background-color: #ffffff; /* Putih untuk top bar */
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        padding: 10px 20px;
        position: sticky;
        top: 0;
        z-index: 1000;
    }

    /* Styling untuk title dan markdown */
    h1 {
        color: #1a1a1a;
        text-align: left;
        margin-bottom: 0.5em;
    }
    h2 {
        color: #1a1a1a;
        font-size: 1.5em;
        margin-top: 1.5em;
    }
    p {
        font-size: 1em;
        line-height: 1.6;
    }

    /* Styling untuk st.file_uploader */
    .stFileUploader > div > div {
        border: 2px dashed #007bff; /* Biru */
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        background-color: #e9f5ff; /* Biru sangat muda */
        color: #007bff;
        margin-bottom: 20px;
    }
    .stFileUploader span {
        font-weight: bold;
    }
    .stFileUploader p {
        color: #555555;
    }

    /* Styling untuk st.image */
    .stImage > img {
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Styling untuk st.selectbox */
    .stSelectbox > div > div > div {
        border-radius: 8px;
        border: 1px solid #ced4da;
        padding: 5px 10px;
        background-color: #ffffff;
    }
    .stSelectbox label {
        font-weight: bold;
        color: #333333;
    }

    /* Styling untuk st.button */
    .stButton > button {
        background-color: #007bff; /* Biru */
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 1.1em;
        font-weight: bold;
        border: none;
        transition: background-color 0.3s ease;
        width: 100%;
        margin-top: 20px;
    }
    .stButton > button:hover {
        background-color: #0056b3; /* Biru lebih gelap saat hover */
    }

    /* Styling untuk hasil analisis AI */
    .stMarkdown h3 { /* Subheader untuk "Hasil Analisis AI:" */
        color: #1a1a1a;
        font-size: 1.3em;
        margin-top: 1.5em;
        margin-bottom: 0.8em;
    }
    .stMarkdown p {
        background-color: #f8f9fa; /* Latar belakang abu-abu sangat terang */
        border-left: 5px solid #007bff;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
        line-height: 1.7;
    }

    /* Styling untuk peringatan penting */
    .st-emotion-cache-1fixmsd { /* Class untuk st.warning */
        background-color: #fff3cd; /* Kuning muda */
        border-left: 5px solid #ffc107; /* Kuning */
        color: #664d03;
        padding: 15px;
        border-radius: 5px;
        margin-top: 20px;
    }
    .st-emotion-cache-1fixmsd strong {
        color: #664d03;
    }

    /* Styling untuk info pesan awal */
    .st-emotion-cache-1g8o837 { /* Class untuk st.info */
        background-color: #d1ecf1; /* Biru muda */
        border-left: 5px solid #17a2b8; /* Biru terang */
        color: #0c5460;
        padding: 15px;
        border-radius: 5px;
        margin-top: 20px;
    }

    /* Bottom Navigation Bar (ini adalah placeholder dan memerlukan implementasi yang lebih kompleks) */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #ffffff;
        box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-around;
        padding: 10px 0;
        z-index: 1000;
    }
    .bottom-nav-item {
        text-align: center;
        color: #6c757d;
        font-size: 0.8em;
        text-decoration: none;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .bottom-nav-item .icon {
        font-size: 1.5em;
        margin-bottom: 3px;
    }
    .bottom-nav-item.active {
        color: #007bff;
    }
    </style>
    """, unsafe_allow_html=True)


# --- UI (Tampilan) Aplikasi Streamlit ---

# 1. Input Gambar
st.write("---") # Garis pemisah untuk desain
st.subheader("Unggah Gambar Chart Anda")
uploaded_file = st.file_uploader("Pilih Gambar Screenshot", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

# Hanya tampilkan sisa UI jika gambar sudah diunggah
if uploaded_file is not None:
    # 2. Pratinjau Gambar
    try:
        image = Image.open(uploaded_file)
        st.subheader("Gambar yang Diunggah:")
        st.image(image, caption="Gambar Anda", use_column_width=True)
    except Exception as e:
        st.error(f"Gagal memuat gambar: {e}")
        st.stop()
    
    # 3. Pilih Timeframe
    st.subheader("Pilih Timeframe Analisis")
    timeframe = st.selectbox(
        "Pilih Timeframe Chart",
        ("1 Menit", "5 Menit", "15 Menit", "30 Menit", "1 Jam", "4 Jam", "1 Hari", "1 Minggu", "Lainnya / Tidak Tahu"),
        index=4,  # Default pilihan ke '1 Jam'
        label_visibility="collapsed"
    )

    # 4. Tombol Analisis
    if st.button("Analisis Sekarang"):
        with st.spinner("AI sedang menganalisis gambar Anda..."):
            try:
                user_prompt = f"Lakukan analisis prediktif (bullish/bearish) pada gambar chart ini. Konteks timeframe adalah: {timeframe}."
                
                contents = [
                    {
                        "role": "user",
                        "parts": [
                            {"text": user_prompt},
                            {"inline_data": {
                                "mime_type": uploaded_file.type,
                                "data": uploaded_file.getvalue()
                            }}
                        ]
                    }
                ]
                
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
    st.info("Silakan unggah gambar untuk memulai analisis.")

# --- Bottom Navigation Bar (Placeholder) ---
# Implementasi navigation bar yang interaktif di Streamlit agak kompleks
# karena membutuhkan interaksi antar halaman atau perubahan state.
# Untuk demo ini, saya akan menampilkannya sebagai elemen HTML statis.
st.markdown("""
    <div class="bottom-nav">
        <a href="#" class="bottom-nav-item active">
            <span class="icon">🧠</span>
            <span>Analisis AI</span>
        </a>
        <a href="#" class="bottom-nav-item">
            <span class="icon">🕒</span>
            <span>History</span>
        </a>
        <a href="#" class="bottom-nav-item">
            <span class="icon">📈</span>
            <span>Pasar aset</span>
        </a>
        <a href="#" class="bottom-nav-item">
            <span class="icon">📰</span>
            <span>Berita</span>
        </a>
        <a href="#" class="bottom-nav-item">
            <span class="icon">👑</span>
            <span>Premium</span>
        </a>
        <a href="#" class="bottom-nav-item">
            <span class="icon">👤</span>
            <span>Profile</span>
        </a>
    </div>
    """, unsafe_allow_html=True)
