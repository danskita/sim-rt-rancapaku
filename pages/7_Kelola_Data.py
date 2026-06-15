import streamlit as st
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

st.set_page_config(page_title="Kelola Data", page_icon="⚙️", layout="centered")

st.title("⚙️ Kelola Data Penduduk")
st.markdown("Halaman ini digunakan untuk mengubah (Edit), menghapus (Hapus), serta melakukan aksi cepat administrasi warga.")

# ==========================================
# LOGIKA ISOLASI DATA (KUNCI OTOMATIS RT/RW)
# ==========================================
role = st.session_state.get("role", "operator_rt")
rt_akses = st.session_state.get("rt_akses", "001")
rw_akses = st.session_state.get("rw_akses", "001")

pilihan_semua = [f"{i:03}" for i in range(1, 21)]

# Menentukan apakah dropdown RT/RW harus dikunci saat mengedit
kunci_rt = True if role == "operator_rt" else False
kunci_rw = True if role in ["operator_rt", "admin_rw"] else False

list_rt = [rt_akses] if kunci_rt else pilihan_semua
list_rw = [rw_akses] if kunci_rw else pilihan_semua

def get_index(nilai, daftar_pilihan):
    return daftar_pilihan.index(nilai) if nilai in daftar_pilihan else 0

# ==========================================
# MENGAMBIL DATA DENGAN FILTER HAK AKSES
# ==========================================
@st.cache_data(ttl=10)
def ambil_daftar_warga():
    try:
        # Menyiapkan perintah dasar untuk mengambil data
        query = supabase.table("data_penduduk").select("nik, nama_lengkap, rt, rw")
        
        # Menerapkan Filter Berdasarkan Siapa yang Login
        if role == "operator_rt":
            query = query.eq("rt", rt_akses).eq("rw", rw_akses) # Hanya RT-nya sendiri
        elif role == "admin_rw":
            query = query.eq("rw", rw_akses) # Semua RT di dalam RW-nya
        # Jika "super_admin", query tidak ditambah filter = ambil semua data se-Desa
            
        response = query.execute()
        return response.data
    except Exception as e:
        st.error(f"Gagal mengambil data dari database: {e}")
        return []

data_warga = ambil_daftar_warga()

if not data_warga:
    st.info("Belum ada data penduduk yang tersimpan di wilayah kewenangan Anda.")
else:
    # Menambahkan keterangan RT/RW di belakang nama agar Admin RW/Desa tidak bingung
    pilihan_warga = [f"{w['nik']} - {w['nama_lengkap']} (RT {w['rt']}/RW {w['rw']})" for w in data_warga]
    warga_terpilih = st.selectbox("Pilih Warga yang akan dikelola (Berdasarkan NIK):", pilihan_warga)
    
    nik_target = warga_terpilih.split(" - ")[0]

    # Mengambil detail lengkap warga yang dipilih
    detail_warga = supabase.table("data_penduduk").select("*").eq("nik", nik_target).execute().data[0]

    st.markdown("---")
    
    # ==========================================
    # FITUR JALAN PINTAS (AKSI CEPAT)
    # ==========================================
    st.subheader("🚀 Aksi Cepat Administrasi")
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("✉️ Buat Surat"):
            st.session_state['autofill_nik'] = nik_target
            st.switch_page("pages/4_Data_Surat.py")
    with col_btn2:
        if st.button("🔄 Lapor Lampid"):
            st.session_state['autofill_nik'] = nik_target
            st.switch_page("pages/2_Data_Lampid.py")
    with col_btn3:
        if st.button("📦 Beri Bansos"):
            st.session_state['autofill_nik'] = nik_target
            st.switch_page("pages/3_Data_Bansos.py")

    st.markdown("---")
    
    # ==========================================
    # FITUR EDIT (DENGAN KUNCI RT/RW)
    # ==========================================
    st.subheader("✏️ Edit Data Warga")
    
    with st.form("form_edit"):
        nama_baru = st.text_input("Nama Lengkap", value=detail_warga.get('nama_lengkap', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            pendidikan_baru = st.text_input("Pendidikan", value=detail_warga.get('pendidikan', ''))
            pekerjaan_baru = st.text_input("Pekerjaan", value=detail_warga.get('pekerjaan', ''))
        with col2:
            rt_lama = detail_warga.get('rt', rt_akses)
            rw_lama = detail_warga.get('rw', rw_akses)
            
            # Kolom Edit RT/RW akan dikunci abu-abu jika yang login adalah Operator RT
            rt_baru = st.selectbox("RT", list_rt, index=get_index(rt_lama, list_rt) if not kunci_rt else 0, disabled=kunci_rt)
            rw_baru = st.selectbox("RW", list_rw, index=get_index(rw_lama, list_rw) if not kunci_rw else 0, disabled=kunci_rw)
            
        jalan_baru = st.text_area("Jalan / Kampung", value=detail_warga.get('jalan_kampung', ''))

        submit_edit = st.form_submit_button("Simpan Perubahan", type="primary")

        if submit_edit:
            data_update = {
                "nama_lengkap": nama_baru.title().strip(),
                "pendidikan": pendidikan_baru.title().strip(),
                "pekerjaan": pekerjaan_baru.title().strip(),
                "rt": rt_baru,
                "rw": rw_baru,
                "jalan_kampung": jalan_baru.title().strip()
            }
            
            try:
                supabase.table("data_penduduk").update(data_update).eq("nik", nik_target).execute()
                st.success("✅ Data berhasil diperbarui! Silakan muat ulang (refresh) halaman.")
                st.cache_data.clear() 
            except Exception as e:
                st.error(f"⚠️ Gagal memperbarui data: {e}")

    st.markdown("---")
    
    st.subheader("🗑️ Hapus Data Warga")
    konfirmasi = st.checkbox(f"Saya yakin ingin menghapus data dengan NIK {nik_target}")
    if konfirmasi:
        if st.button("Hapus Data Secara Permanen"):
            try:
                supabase.table("data_penduduk").delete().eq("nik", nik_target).execute()
                st.success("✅ Data berhasil dihapus.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ Gagal menghapus data: {e}")