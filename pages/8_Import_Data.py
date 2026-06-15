import streamlit as st
import pandas as pd
import math
import io
from supabase import create_client, Client
from menu import tampilkan_menu

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)
tampilkan_menu()
# ---------------------------

# Gembok Keamanan
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("⚠️ Akses Ditolak! Silakan login melalui halaman utama terlebih dahulu.")
    st.stop()
# GEMBOK KHUSUS: Hanya Operator RT yang boleh masuk untuk input/edit/hapus data
role = st.session_state.get("role", "")
if role in ["admin_rw", "super_admin"]:
    st.error("⛔ Akses Ditolak! Halaman ini adalah wewenang mutlak Pengurus RT. Anda (RW/Desa) hanya memiliki akses untuk melihat rekap data pada menu Cetak Laporan.")
    st.stop()

st.set_page_config(page_title="Import Data", page_icon="📥", layout="centered")

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
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

st.markdown("---")

# 2. FITUR UPLOAD FILE EXCEL
st.subheader("2. Upload Data Excel")
uploaded_file = st.file_uploader("Pilih file Excel (.xlsx) yang sudah diisi", type=['xlsx'])

if uploaded_file is not None:
    try:
        # Membaca file Excel
        df = pd.read_excel(uploaded_file)
        
        # Pastikan data NIK dan No KK dibaca sebagai teks utuh tanpa angka nol di belakang (.0)
        if 'nik' in df.columns:
            df['nik'] = df['nik'].astype(str).str.replace(r'\.0', '', regex=True)
        if 'no_kk' in df.columns:
            df['no_kk'] = df['no_kk'].astype(str).str.replace(r'\.0', '', regex=True)

        # --- PERBAIKAN FORMAT TANGGAL OTOMATIS ---
        if 'tanggal_lahir' in df.columns:
            # Pandas akan secara pintar menerjemahkan tanggal dari Excel (DD-MM-YYYY) menjadi standar Database (YYYY-MM-DD)
            df['tanggal_lahir'] = pd.to_datetime(df['tanggal_lahir'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
        # ----------------------------------------

        st.write("Preview Data yang akan diimpor:")
        st.dataframe(df.head(), width='stretch')
        
        if st.button("Mulai Import ke Database", type="primary"):
            with st.spinner("Sedang mengimpor data..."):
                # Membersihkan data (mengubah NaN/Data Kosong menjadi format None yang diterima database)
                df = df.where(pd.notnull(df), None)
                data_records = df.to_dict(orient='records')
                
                # Kirim ke Supabase
                response = supabase.table("data_penduduk").insert(data_records).execute()
                st.success(f"✅ Berhasil mengimpor {len(data_records)} data penduduk dari file Excel.")
                
    except Exception as e:
        st.error(f"⚠️ Terjadi kesalahan: {e}")