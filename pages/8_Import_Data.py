import streamlit as st
import pandas as pd
import numpy as np # WAJIB DITAMBAHKAN UNTUK PEMBERSIH NaN
import math
import io
from supabase import create_client, Client
from menu import tampilkan_menu

# ========================================================
# 1. KONFIGURASI HALAMAN WAJIB PALING ATAS (Hanya Satu Kali)
# ========================================================
st.set_page_config(
    page_title="Import Data", 
    page_icon="📥", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

tampilkan_menu()
# ---------------------------

# Gembok Keamanan Umum
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("⚠️ Akses Ditolak! Silakan login melalui halaman utama terlebih dahulu.")
    st.stop()

# --- PERBAIKAN 1: BUKA GEMBOK UNTUK ADMIN DESA ---
# Kini Operator RT dan Kepala Desa (super_admin) diizinkan melakukan Import masal. 
# Hanya Admin RW yang kita blokir (atau hapus blok ini jika RW juga diizinkan).
role = st.session_state.get("role", "")
if role == "admin_rw":
    st.error("⛔ Akses Ditolak! Halaman Import Data adalah wewenang Pengurus RT dan Admin Desa.")
    st.stop()


st.title("📥 Import Data Penduduk Masal (Excel)")

# 1. FITUR UNDUH TEMPLATE EXCEL
st.subheader("1. Unduh Template Excel")
st.markdown("Unduh template berformat **Excel (.xlsx)** di bawah ini. Anda bisa membukanya di Microsoft Excel, mengisinya secara manual, lalu menyimpannya kembali.")

# Kolom standar SIAK
cols = [
    'nik', 'no_kk', 'nama_lengkap', 'tempat_lahir', 'tanggal_lahir', 
    'jenis_kelamin', 'golongan_darah', 'agama', 'pendidikan', 'pekerjaan', 
    'status_perkawinan', 'shdk', 'kewarganegaraan', 'jalan_kampung', 'rt', 'rw'
]
df_template = pd.DataFrame(columns=cols)

# Konversi DataFrame ke format Excel di dalam memori
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    df_template.to_excel(writer, index=False, sheet_name='Template_Warga')
excel_data = buffer.getvalue()

st.download_button(
    label="📥 Unduh Template Excel (.xlsx)",
    data=excel_data,
    file_name='Template_Data_Penduduk.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    use_container_width=True
)

st.markdown("---")

# 2. FITUR UPLOAD FILE EXCEL
st.subheader("2. Upload Data Excel")
uploaded_file = st.file_uploader("Pilih file Excel (.xlsx) yang sudah diisi", type=['xlsx'])

if uploaded_file is not None:
    try:
        # Membaca file Excel
        df = pd.read_excel(uploaded_file)
        
        # >>> SOLUSI PAMUNGKAS 1: PAKSA SEMUA JUDUL KOLOM JADI HURUF KECIL & HAPUS SPASI <<<
        df.columns = df.columns.str.strip().str.lower()
        
        # >>> SOLUSI PAMUNGKAS 2: KAMUS PENERJEMAH KOLOM (EXCEL -> DATABASE) <<<
        # Menyamakan judul kolom Excel yang ada spasinya ke standar Supabase
        kamus_kolom = {
            'no. kk': 'no_kk',
            'nama lengkap': 'nama_lengkap',
            'tempat lahir': 'tempat_lahir',
            'tanggal lahir (yyyy-mm-dd)': 'tanggal_lahir',
            'jenis kelamin': 'jenis_kelamin',
            'golongan darah': 'golongan_darah',
            'pendidikan terakhir': 'pendidikan',
            'status perkawinan': 'status_perkawinan',
            'jalan / kampung / perumahan': 'jalan_kampung'
        }
        df = df.rename(columns=kamus_kolom)
        
        # 1. PEMBERSIH NIK & KK: Pastikan dibaca sebagai teks utuh tanpa koma nol (.0)
        if 'nik' in df.columns:
            df['nik'] = df['nik'].astype(str).str.replace(r'\.0$', '', regex=True)
        if 'no_kk' in df.columns:
            df['no_kk'] = df['no_kk'].astype(str).str.replace(r'\.0$', '', regex=True)
            
        # 2. PENERJEMAH RT & RW: Paksa menjadi 3 digit otomatis (contoh: "1" menjadi "001")
        if 'rt' in df.columns:
            df['rt'] = df['rt'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(3)
        if 'rw' in df.columns:
            df['rw'] = df['rw'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(3)

        # 3. PENERJEMAH TANGGAL: Menggunakan format='mixed' agar Pandas tidak protes saat melihat variasi format
        if 'tanggal_lahir' in df.columns:
            df['tanggal_lahir'] = pd.to_datetime(df['tanggal_lahir'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
        # >>> SOLUSI PAMUNGKAS 3: SAPU BERSIH DATA KOSONG <<<
        # Menggunakan metode yang lebih aman dari Numpy untuk mencegah error JSON
        df = df.where(pd.notnull(df), None)

        # Tampilkan preview data yang sudah dirapikan kepada pengguna
        st.write("Preview Data yang siap diimpor:")
        st.dataframe(df)

        # Tombol untuk mengeksekusi import ke database Supabase
        if st.button("🚀 Mulai Import ke Database", use_container_width=True, type="primary"):
            with st.spinner("Sedang menyimpan data ke cloud..."):
                # Konversi dataframe Pandas menjadi format dictionary untuk Supabase
                data_import = df.to_dict(orient="records")
                
                # Masukkan data secara masal ke tabel data_penduduk
                response = supabase.table("data_penduduk").insert(data_import).execute()
                
                st.success(f"✅ Mantap! {len(df)} data warga berhasil diimpor ke database.")
                
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan saat membaca atau menyimpan file: {e}")
        st.info("Pastikan Anda menggunakan Template Excel yang diunduh dari aplikasi ini dan tidak ada NIK yang ganda.")