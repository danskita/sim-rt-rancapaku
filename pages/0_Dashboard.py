import streamlit as st
import pandas as pd
from supabase import create_client, Client
from menu import tampilkan_menu

# ========================================================
# 1. KONFIGURASI HALAMAN WAJIB PALING ATAS (Hanya Satu Kali)
# ========================================================
st.set_page_config(
    page_title="Dashboard Utama", 
    page_icon="📊", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# Gembok Keamanan
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("⚠️ Akses Ditolak! Silakan login melalui halaman utama terlebih dahulu.")
    st.stop()

# Ambil data profil pengguna
role = st.session_state.get("role", "")
rt_akses = st.session_state.get("rt_akses", "-")
rw_akses = st.session_state.get("rw_akses", "-")
nama_wilayah = st.session_state.get("nama_wilayah", "Pengurus")

tampilkan_menu()
# ---------------------------

st.title(f"📊 Dashboard Statistik {nama_wilayah}")
st.markdown("Ringkasan data kependudukan secara *real-time*.")
st.markdown("---")

# FUNGSI MENARIK DATA (DENGAN FILTER OTOMATIS)
@st.cache_data(ttl=300) # Data di-refresh otomatis setiap 5 menit
def load_data_dashboard(role_aktif, rt_aktif, rw_aktif):
    # Hanya mengambil kolom yang dibutuhkan agar loading sangat cepat
    query = supabase.table("data_penduduk").select("nik, no_kk, jenis_kelamin, agama, pendidikan, pekerjaan")
    
    # Filter sesuai hak akses
    if role_aktif == "operator_rt":
        query = query.eq("rt", rt_aktif).eq("rw", rw_aktif)
    elif role_aktif == "admin_rw":
        query = query.eq("rw", rw_aktif)
    
    res = query.execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

# Eksekusi penarikan data
df = load_data_dashboard(role, rt_akses, rw_akses)

# JIKA DATA MASIH KOSONG
if df.empty:
    st.info("📭 Belum ada data penduduk yang tersimpan di wilayah Anda.")
    st.stop()

# ==========================================
# 1. KARTU METRIK UTAMA (ANGKA)
# ==========================================
# Menghitung metrik
total_warga = len(df)
total_kk = df['no_kk'].nunique() if 'no_kk' in df.columns else 0
laki = len(df[df['jenis_kelamin'] == 'Laki-laki']) if 'jenis_kelamin' in df.columns else 0
perempuan = len(df[df['jenis_kelamin'] == 'Perempuan']) if 'jenis_kelamin' in df.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("👥 Total Warga", f"{total_warga} Jiwa")
col2.metric("📋 Kepala Keluarga", f"{total_kk} KK")
col3.metric("👨 Laki-laki", f"{laki} Jiwa")
col4.metric("👩 Perempuan", f"{perempuan} Jiwa")

st.markdown("---")

# ==========================================
# 2. GRAFIK VISUALISASI DATA
# ==========================================
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Distribusi Agama")
    if 'agama' in df.columns and not df['agama'].isnull().all():
        data_agama = df['agama'].value_counts()
        st.bar_chart(data_agama, color="#2E86C1", height=300)
    else:
        st.caption("Data agama belum diisi.")

with col_chart2:
    st.subheader("Distribusi Pendidikan")
    if 'pendidikan' in df.columns and not df['pendidikan'].isnull().all():
        data_pendidikan = df['pendidikan'].value_counts()
        st.bar_chart(data_pendidikan, color="#28B463", height=300)
    else:
        st.caption("Data pendidikan belum diisi.")