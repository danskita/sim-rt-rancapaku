import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client
from menu import tampilkan_menu

# ========================================================
# 1. KONFIGURASI HALAMAN WAJIB PALING ATAS (Hanya Satu Kali)
# ========================================================
st.set_page_config(
    page_title="Arsip Digital", 
    page_icon="🗂️", 
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

# Ambil data profil
role = st.session_state.get("role", "")
rt_akses = st.session_state.get("rt_akses", "-")
rw_akses = st.session_state.get("rw_akses", "-")

tampilkan_menu()
# ---------------------------

st.title("🗂️ Arsip Digital (Surat & Dokumen)")
st.markdown("Fasilitas penyimpanan dokumen administratif seperti Surat Masuk, Laporan Kegiatan, dan Undangan resmi.")
st.markdown("---")

# Menentukan Tingkat Wilayah berdasarkan Role
if role == "super_admin":
    tingkat_aktif = "Desa"
    filter_rt = "-"
    filter_rw = "-"
elif role == "admin_rw":
    tingkat_aktif = "RW"
    filter_rt = "-"
    filter_rw = rw_akses
else:
    tingkat_aktif = "RT"
    filter_rt = rt_akses
    filter_rw = rw_akses

# ==========================================
# FUNGSI MENARIK DATA ARSIP
# ==========================================
@st.cache_data(ttl=10)
def load_data_arsip(role_aktif, rt_aktif, rw_aktif):
    try:
        query = supabase.table("data_arsip").select("*")
        if role_aktif == "operator_rt":
            query = query.eq("tingkat", "RT").eq("rt", rt_aktif).eq("rw", rw_aktif)
        elif role_aktif == "admin_rw":
            query = query.eq("tingkat", "RW").eq("rw", rw_aktif)
        
        response = query.order("tanggal", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

df_arsip = load_data_arsip(role, filter_rt, filter_rw)

# Membuat 3 Tab Utama
tab_tabel, tab_tambah, tab_hapus = st.tabs(["📂 Tabel Daftar Arsip", "➕ Unggah Arsip Baru", "🗑️ Kelola & Hapus"])

# ==========================================
# TAB 1: TABEL DAFTAR ARSIP (DENGAN FILTER)
# ==========================================
with tab_tabel:
    st.subheader(f"Tabel Data Arsip Tingkat {tingkat_aktif}")
    
    if not df_arsip.empty:
        # Fitur Filter Interaktif
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            daftar_jenis = ["Tampilkan Semua"] + list(df_arsip['jenis'].unique())
            filter_jenis = st.selectbox("🔍 Filter Berdasarkan Jenis:", daftar_jenis)
        with col_filter2:
            cari_judul = st.text_input("🔍 Cari Judul Arsip:")

        # Terapkan Filter
        df_tampil = df_arsip.copy()
        if filter_jenis != "Tampilkan Semua":
            df_tampil = df_tampil[df_tampil['jenis'] == filter_jenis]
        if cari_judul:
            df_tampil = df_tampil[df_tampil['judul'].str.contains(cari_judul, case=False, na=False)]

        st.caption(f"Menampilkan {len(df_tampil)} dokumen arsip.")

        if not df_tampil.empty:
            # Merapikan dan mengurutkan kolom untuk tabel
            df_tabel = df_tampil[['id', 'tanggal', 'jenis', 'judul', 'keterangan', 'tingkat', 'url_file']]
            
            # Menampilkan tabel interaktif Streamlit
            st.dataframe(
                df_tabel, 
                use_container_width=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", format="%d", width="small"),
                    "tanggal": st.column_config.DateColumn("Tanggal", format="DD/MM/YYYY"),
                    "jenis": "Jenis Dokumen",
                    "judul": "Judul Arsip",
                    "keterangan": "Keterangan",
                    "tingkat": "Tingkat",
                    "url_file": st.column_config.LinkColumn("Buka File", display_text="Unduh / Lihat PDF")
                },
                hide_index=True
            )
        else:
            st.info("Pencarian tidak menemukan hasil yang sesuai.")
    else:
        st.info("📭 Belum ada arsip yang tersimpan di wilayah Anda.")
        
    if st.button("🔄 Segarkan Tabel", use_container_width=True):
        st.cache_data.clear()

# ==========================================
# TAB 2: TAMBAH ARSIP MANUAL
# ==========================================
with tab_tambah:
    st.subheader("Unggah Dokumen Baru")
    st.write("Gunakan fitur ini untuk menyimpan Surat Masuk atau laporan fisik yang sudah di-scan.")
    
    with st.form("form_tambah_arsip", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            input_tanggal = st.date_input("Tanggal Surat/Kegiatan", datetime.date.today())
            input_jenis = st.selectbox("Jenis Arsip", ["Surat Masuk", "Surat Keluar", "Laporan Kegiatan", "Undangan", "SK / Peraturan", "Dokumen Lainnya"])
        with col2:
            input_judul = st.text_input("Judul Dokumen (Misal: Undangan Rapat Desa)")
            input_ket = st.text_area("Keterangan Singkat", height=68)
            
        file_arsip = st.file_uploader("Pilih File (PDF, JPG, PNG)", type=["pdf", "jpg", "jpeg", "png"])
        
        submit_arsip = st.form_submit_button("💾 Unggah & Simpan Arsip", use_container_width=True, type="primary")
        
        if submit_arsip:
            if not input_judul:
                st.error("❌ Judul dokumen wajib diisi!")
            elif file_arsip is None:
                st.error("❌ Anda belum memilih file untuk diunggah!")
            else:
                with st.spinner("Sedang mengunggah file ke brankas digital..."):
                    try:
                        # 1. Buat nama file unik
                        ekstensi = file_arsip.name.split('.')[-1]
                        waktu_sekarang = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                        nama_file_unik = f"Manual_{tingkat_aktif}_{waktu_sekarang}.{ekstensi}"
                        
                        # 2. Upload ke Supabase Storage
                        file_bytes = file_arsip.getvalue()
                        supabase.storage.from_("arsip_digital").upload(
                            path=nama_file_unik,
                            file=file_bytes,
                            file_options={"content-type": file_arsip.type}
                        )
                        
                        # 3. Dapatkan Link Publik
                        url_publik = supabase.storage.from_("arsip_digital").get_public_url(nama_file_unik)
                        
                        # 4. Simpan data ke tabel data_arsip
                        data_insert = {
                            "tanggal": input_tanggal.strftime("%Y-%m-%d"),
                            "jenis": input_jenis,
                            "judul": input_judul,
                            "keterangan": input_ket,
                            "url_file": url_publik,
                            "tingkat": tingkat_aktif,
                            "rt": filter_rt,
                            "rw": filter_rw
                        }
                        supabase.table("data_arsip").insert(data_insert).execute()
                        
                        st.success("✅ Arsip berhasil disimpan dan diunggah!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"⚠️ Gagal menyimpan arsip: {e}")

# ==========================================
# TAB 3: KELOLA / HAPUS ARSIP
# ==========================================
with tab_hapus:
    st.subheader("Kelola & Hapus Arsip")
    st.write("Gunakan fitur ini jika ada dokumen yang salah unggah atau ingin dibersihkan.")
    
    if df_arsip.empty:
        st.info("Belum ada data arsip yang bisa dihapus.")
    else:
        pilihan_hapus = []
        for _, row in df_arsip.iterrows():
            tgl_format = pd.to_datetime(row['tanggal']).strftime('%d/%m/%Y')
            pilihan_hapus.append(f"ID: {row['id']} | {tgl_format} - {row['jenis']} - {row['judul']}")
            
        target_hapus = st.selectbox("Pilih arsip yang ingin DHAPUS PERMANEN:", pilihan_hapus)
        id_hapus = int(target_hapus.split(" | ")[0].replace("ID: ", ""))
        
        st.warning("⚠️ Perhatian: File yang dihapus dari tabel tidak akan bisa dikembalikan.")
        
        if st.button("🗑️ Hapus Arsip Terpilih", type="primary", use_container_width=True):
            with st.spinner("Sedang menghapus arsip..."):
                try:
                    # Hapus dari tabel data_arsip
                    supabase.table("data_arsip").delete().eq("id", id_hapus).execute()
                    
                    st.success("✅ Arsip berhasil dihapus dari sistem!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"⚠️ Gagal menghapus arsip: {e}")