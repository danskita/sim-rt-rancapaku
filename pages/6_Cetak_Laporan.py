import streamlit as st
import pandas as pd
import plotly.express as px
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

# --- VARIABEL HAK AKSES ---
role = st.session_state.get("role", "operator_rt")
rt_akses = st.session_state.get("rt_akses", "001")
rw_akses = st.session_state.get("rw_akses", "001")
nama_wilayah = st.session_state.get("nama_wilayah", "Wilayah Tidak Diketahui")

st.set_page_config(page_title="Dashboard & Laporan", page_icon="📊", layout="wide")

st.title("📊 Dashboard & Cetak Laporan")
st.markdown(f"Pusat pemantauan dan unduh data untuk **{nama_wilayah}**")

# ==========================================
# LOGIKA ISOLASI FILTER RT/RW
# ==========================================
pilihan_semua = ["Semua"] + [f"{i:03}" for i in range(1, 21)]

# Mengunci dropdown sesuai peran
kunci_rt = True if role == "operator_rt" else False
kunci_rw = True if role in ["operator_rt", "admin_rw"] else False

list_rt = [rt_akses] if kunci_rt else pilihan_semua
list_rw = [rw_akses] if kunci_rw else pilihan_semua

st.markdown("### 🔍 Filter Wilayah")
col_f1, col_f2 = st.columns(2)
with col_f1:
    filter_rw = st.selectbox("Pilih RW", list_rw, disabled=kunci_rw)
with col_f2:
    filter_rt = st.selectbox("Pilih RT", list_rt, disabled=kunci_rt)

# ==========================================
# FUNGSI TARIK DATA DENGAN KEAMANAN GANDA
# ==========================================
@st.cache_data(ttl=10)
def get_data(nama_tabel):
    query = supabase.table(nama_tabel).select("*")
    
    # KUNCI PERBAIKAN: Pastikan filter RT/RW hanya aktif untuk tabel "data_penduduk"
    if nama_tabel == "data_penduduk":
        if filter_rw != "Semua":
            query = query.eq("rw", filter_rw)
            
        if filter_rt != "Semua":
            query = query.eq("rt", filter_rt)
            
    res = query.execute()
    df = pd.DataFrame(res.data) if res.data else pd.DataFrame()
    
    # PENYELESAIAN PERMANEN: Menormalkan nama kolom jadi huruf kecil agar kebal error
    if not df.empty:
        df.columns = df.columns.str.lower()
        
    return df

with st.spinner("Menyiapkan laporan khusus wilayah Anda..."):
    df_penduduk = get_data("data_penduduk")
    df_lahir = get_data("data_lahir")
    df_mati = get_data("data_mati")
    df_pindah = get_data("data_pindah")
    df_datang = get_data("data_datang")
    df_bansos = get_data("data_bansos")
    df_surat = get_data("data_surat")

st.markdown("---")

if df_penduduk.empty:
    st.info("Belum ada data warga di wilayah ini.")
else:
    # ==========================================
    # METRIK & GRAFIK (Hanya Data yang Difilter)
    # ==========================================
    st.subheader("📈 Ringkasan Penduduk")
    
    total_warga = len(df_penduduk)

    # Cek dulu apakah tabelnya ada isinya dan kolomnya tersedia
    if not df_penduduk.empty and 'jenis_kelamin' in df_penduduk.columns:
        total_l = len(df_penduduk[df_penduduk['jenis_kelamin'] == 'Laki-laki'])
        total_p = len(df_penduduk[df_penduduk['jenis_kelamin'] == 'Perempuan'])
    else:
        total_l = 0
        total_p = 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Warga", total_warga)
    col2.metric("Laki-laki", total_l)
    col3.metric("Perempuan", total_p)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        # Pengecekan sebelum membuat diagram Pie
        if 'jenis_kelamin' in df_penduduk.columns and not df_penduduk['jenis_kelamin'].isna().all():
            fig_gender = px.pie(df_penduduk, names='jenis_kelamin', title='Proporsi Jenis Kelamin', hole=0.4)
            st.plotly_chart(fig_gender, width="stretch")
        else:
            st.info("Data jenis kelamin belum tersedia untuk membuat grafik.")
            
    with col_chart2:
        # Pengecekan sebelum membuat diagram Bar Agama
        if 'agama' in df_penduduk.columns and not df_penduduk['agama'].isna().all():
            agama_count = df_penduduk['agama'].value_counts().reset_index()
            agama_count.columns = ['Agama', 'Jumlah']
            fig_agama = px.bar(agama_count, x='Agama', y='Jumlah', title='Distribusi Agama')
            st.plotly_chart(fig_agama, width="stretch")
        else:
            st.info("Data agama belum tersedia untuk membuat grafik.")

    st.markdown("---")
    
    # ==========================================
    # UNDUH LAPORAN (TABS)
    # ==========================================
    st.subheader("🗂️ Ekspor Laporan Wilayah (.CSV)")
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Data Penduduk", "🔄 Laporan LAMPID", "📦 Bansos & Surat", "🏢 Aset RT"])
    
    with tab1:
        st.dataframe(df_penduduk, width="stretch")
        csv_penduduk = df_penduduk.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Unduh CSV Penduduk", data=csv_penduduk, file_name=f"Data_Penduduk_{filter_rw}_{filter_rt}.csv", mime="text/csv")
        
    with tab2:
        st.markdown("**Bayi Lahir**")
        st.dataframe(df_lahir, width="stretch")
        st.markdown("**Warga Meninggal**")
        st.dataframe(df_mati, width="stretch")
        
    with tab3:
        st.markdown("**Riwayat Penerima Bansos**")
        st.dataframe(df_bansos, width="stretch")
        st.markdown("**Riwayat Permohonan Surat**")
        st.dataframe(df_surat, width="stretch")
        
    with tab4:
        df_aset = get_data("data_aset")
        st.dataframe(df_aset, width="stretch")