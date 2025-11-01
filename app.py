import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import feedparser  # Library baru untuk membaca RSS feed
import requests    # Library baru untuk mengambil data
from datetime import datetime
import time

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="AI Trading Dashboard",
    page_icon="📊",
    layout="wide" # Mengubah layout menjadi 'wide' agar lebih muat
)

# --- Judul di Halaman Aplikasi ---
st.title("AI Trading Dashboard 📊")

# --- Penanganan API Key (Sama seperti sebelumnya) ---
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

# --- Konfigurasi Model AI (Sama seperti sebelumnya) ---
try:
    model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
except Exception as e:
    st.error(f"Gagal memuat model Gemini. Error: {e}")
    st.stop()


# --- FUNGSI BARU UNTUK MENGAMBIL BERITA ---
# Menggunakan cache Streamlit agar tidak mengambil data berulang-ulang
@st.cache_data(ttl=600) # Cache selama 10 menit (600 detik)
def fetch_news(feed_url):
    """Mengambil dan mem-parsing RSS feed."""
    try:
        # Menambahkan User-Agent agar tidak diblokir
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(feed_url, headers=headers, timeout=10)
        response.raise_for_status() # Cek jika ada error HTTP
        
        # Parsing data feed
        feed = feedparser.parse(response.content)
        return feed.entries
    except Exception as e:
        st.error(f"Gagal mengambil berita dari {feed_url}. Error: {e}")
        return None

# --- Daftar RSS Feed ---
# Kita tambahkan beberapa sumber berita
NEWS_FEEDS = {
    "Detik Finance (Umum)": "https://rss.detik.com/index.php/finance",
    "Kontan (Saham)": "https://rss.kontan.co.id/news/saham",
    "Kontan (Investasi)": "https://rss.kontan.co.id/news/investasi",
    "Investing.com (Berita Dunia)": "https://www.investing.com/rss/news.rss",
    "Cointelegraph (Crypto)": "https://cointelegraph.com/rss"
}


# === PEMBUATAN TAB ===
tab1, tab2 = st.tabs(["Analisis Chart", "Berita Finansial"])


# --- TAB 1: ANALISIS CHART ---
with tab1:
    st.header("Analisis Chart dengan AI")
    
    # --- Sistem Prompt (Sama seperti sebelumnya) ---
    system_prompt_chart = """Anda adalah seorang analis teknikal trading AI yang ahli. 
    Tugas utama Anda adalah menganalisis gambar screenshot chart trading...
    ... (Seluruh sisa system prompt Anda yang lama masuk di sini) ...
    ...
    Selalu akhiri dengan peringatan bahwa ini bukan nasihat keuangan (DYOR).
    Jawab dalam Bahasa Indonesia.
    """

    # --- UI (Sama seperti sebelumnya) ---
    uploaded_file = st.file_uploader("Pilih Gambar Screenshot", type=["jpg", "jpeg", "png"], key="chart_uploader")

    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file)
            st.image(image, caption="Gambar yang Diunggah", use_column_width=True)
        except Exception as e:
            st.error(f"Gagal memuat gambar: {e}")
            st.stop()
        
        timeframe = st.selectbox(
            "Pilih Timeframe Chart",
            ("1 Menit", "5 Menit", "15 Menit", "30 Menit", "1 Jam", "4 Jam", "1 Hari", "1 Minggu", "Lainnya / Tidak Tahu"),
            index=4
        )

        if st.button("Analisis Chart Sekarang"):
            with st.spinner("AI sedang menganalisis gambar Anda..."):
                try:
                    user_task = f"Lakukan analisis prediktif (bullish/bearish) pada gambar chart ini. Konteks timeframe adalah: {timeframe}."
                    full_prompt = f"{system_prompt_chart}\n\nPERINTAH SPESIFIK:\nGambar terlampir.\n{user_task}"
                    
                    contents = [
                        {
                            "role": "user",
                            "parts": [
                                {"text": full_prompt}, 
                                {"inline_data": {
                                    "mime_type": uploaded_file.type,
                                    "data": uploaded_file.getvalue()
                                }}
                            ]
                        }
                    ]
                    
                    response = model.generate_content(contents)
                    
                    st.subheader("Hasil Analisis AI:")
                    st.markdown(response.text)
                    st.warning(
                        "**Peringatan Penting:** Analisis AI ini sangat spekulatif dan bukan nasihat keuangan. Selalu lakukan riset Anda sendiri (DYOR)."
                    )

                except Exception as e:
                    st.error(f"Terjadi kesalahan saat menghubungi API Gemini: {e}")
    else:
        st.info("Silakan unggah gambar untuk memulai analisis chart.")


# --- TAB 2: BERITA FINANSIAL (FITUR BARU) ---
with tab2:
    st.header("Berita Finansial Terbaru")
    
    # Buat pilihan sumber berita
    selected_feed_name = st.selectbox("Pilih Sumber Berita:", NEWS_FEEDS.keys())
    
    if st.button("Dapatkan Berita Terbaru"):
        feed_url = NEWS_FEEDS[selected_feed_name]
        
        with st.spinner(f"Mengambil berita dari {selected_feed_name}..."):
            entries = fetch_news(feed_url) # Panggil fungsi baru kita
            
            if entries:
                st.subheader(f"Berita Terbaru dari {selected_feed_name}")
                
                # Tampilkan 10 berita teratas
                for entry in entries[:10]:
                    # Coba parsing tanggal
                    try:
                        pub_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z').strftime('%d %B %Y, %H:%M WIB')
                    except Exception:
                        pub_date = entry.get('published', 'Tanggal tidak tersedia')

                    st.markdown(f"#### [{entry.title}]({entry.link})")
                    st.caption(f"Dipublikasikan pada: {pub_date}")
                    
                    # Gunakan expander untuk ringkasan agar rapi
                    with st.expander("Baca Ringkasan"):
                        # Membersihkan HTML dari ringkasan (jika ada)
                        summary = entry.get('summary', 'Ringkasan tidak tersedia.')
                        st.markdown(summary, unsafe_allow_html=True)
                    
                    st.divider() # Garis pemisah
            
            else:
                st.error("Tidak ada berita yang dapat ditampilkan dari sumber ini.")

