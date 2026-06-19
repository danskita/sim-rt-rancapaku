import streamlit as st
import datetime
from supabase import create_client, Client
from menu import tampilkan_menu

# ========================================================
# 1. KONFIGURASI HALAMAN WAJIB PALING ATAS (Hanya Satu Kali)
# ========================================================
st.set_page_config(
    page_title="Data Penduduk", 
    page_icon="👥", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

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


st.title("👥 Modul Data Penduduk (Master)")
st.markdown("Isi formulir di bawah ini untuk menambahkan data warga baru.")

# ==========================================
# LOGIKA ISOLASI DATA (KUNCI OTOMATIS RT/RW)
# ==========================================
role = st.session_state.get("role", "operator_rt")
rt_akses = st.session_state.get("rt_akses", "001")
rw_akses = st.session_state.get("rw_akses", "001")

pilihan_semua = [f"{i:03}" for i in range(1, 21)]

# Menentukan apakah dropdown RT/RW harus dikunci (disabled)
kunci_rt = True if role == "operator_rt" else False
kunci_rw = True if role in ["operator_rt", "admin_rw"] else False

# Menentukan daftar pilihan (jika dikunci, daftarnya hanya 1 angka)
list_rt = [rt_akses] if kunci_rt else pilihan_semua
list_rw = [rw_akses] if kunci_rw else pilihan_semua

with st.form("form_penduduk", clear_on_submit=True):
    st.subheader("1. Identitas Utama")
    col_id1, col_id2 = st.columns(2)
    with col_id1:
        no_kk = st.text_input("Nomor Kartu Keluarga (KK) *", max_chars=16, help="Wajib 16 digit angka")
    with col_id2:
        nik = st.text_input("Nomor Induk Kependudukan (NIK) *", max_chars=16, help="Wajib 16 digit angka")
        
    nama_lengkap_input = st.text_input("Nama Lengkap (Sesuai KTP) *")
    
    st.markdown("---")
    st.subheader("2. Kelahiran & Fisik")
    col_lahir1, col_lahir2 = st.columns(2)
    with col_lahir1:
        tempat_lahir_input = st.text_input("Tempat Lahir *")
        tanggal_lahir = st.date_input("Tanggal Lahir *", min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today(), format="DD/MM/YYYY")
    with col_lahir2:
        jenis_kelamin = st.selectbox("Jenis Kelamin *", ["Laki-laki", "Perempuan"])
        golongan_darah = st.selectbox("Golongan Darah", ["A", "B", "AB", "O", "Tidak Tahu"])
        
    st.markdown("---")
    st.subheader("3. Sosial & Legal")
    col_sos1, col_sos2 = st.columns(2)
    with col_sos1:
        agama = st.selectbox("Agama *", ["Islam", "Kristen", "Katolik", "Hindu", "Buddha", "Konghucu", "Kepercayaan Lainnya"])
        pendidikan = st.selectbox("Pendidikan Terakhir", ["Tidak/Belum Sekolah", "Belum Tamat SD/Sederajat", "Tamat SD/Sederajat", "SLTP/Sederajat", "SLTA/Sederajat", "Diploma I/II", "Akademi/Diploma III/S.Muda", "Diploma IV/Strata I", "Strata II", "Strata III"])
        # PERBAIKAN: Menambahkan tanda kutip dan opsi "Lainnya" untuk antisipasi
        pekerjaan = st.selectbox("Pekerjaan *", ["Belum/Tidak Bekerja", "Wiraswasta", "Petani", "Pedagang", "Mengurus Rumah Tangga", "Buruh Harian Lepas", "PNS", "Pelajar/Mahasiswa", "Pensiunan", "Lainnya"])
    with col_sos2:
        status_perkawinan = st.selectbox("Status Perkawinan *", ["Belum Kawin", "Kawin", "Cerai Hidup", "Cerai Mati"])
        shdk = st.selectbox("Status Hub. Dalam Keluarga (SHDK) *", ["Kepala Keluarga", "Suami", "Istri", "Anak", "Menantu", "Cucu", "Orang Tua", "Mertua", "Famili Lain", "Pembantu", "Lainnya"])
        kewarganegaraan = st.selectbox("Kewarganegaraan *", ["WNI", "WNA"])
        
    st.markdown("---")
    st.subheader("4. Detail Alamat")
    jalan_kampung_input = st.text_area("Jalan / Kampung / Perumahan *", help="Contoh: Jl. Merdeka Raya Blok A No. 12")
    
    col_alamat1, col_alamat2 = st.columns(2)
    with col_alamat1:
        rt = st.selectbox("RT *", list_rt, disabled=kunci_rt)
    with col_alamat2:
        rw = st.selectbox("RW *", list_rw, disabled=kunci_rw)

    st.markdown("*(Tanda * wajib diisi)*")
    submit_button = st.form_submit_button("Simpan Data Penduduk", type="primary", width="stretch")

    if submit_button:
        nama_lengkap = nama_lengkap_input.title().strip()
        tempat_lahir = tempat_lahir_input.title().strip()
        jalan_kampung = jalan_kampung_input.title().strip()
        # VARIABEL PEKERJAAN SUDAH DIAMBIL LANGSUNG DARI SELECTBOX DI ATAS

        if not no_kk.isdigit() or len(no_kk) != 16:
            st.error("❌ Gagal! Nomor KK harus berisi tepat 16 digit angka.")
        elif not nik.isdigit() or len(nik) != 16:
            st.error("❌ Gagal! NIK harus berisi tepat 16 digit angka.")
        elif not nama_lengkap or not tempat_lahir or not jalan_kampung:
            st.error("❌ Gagal! Pastikan Nama, Tempat Lahir, dan Alamat sudah diisi.")
        else:
            data_warga = {
                "nik": nik,
                "no_kk": no_kk,
                "nama_lengkap": nama_lengkap,
                "tempat_lahir": tempat_lahir,
                "tanggal_lahir": str(tanggal_lahir),
                "jenis_kelamin": jenis_kelamin,
                "golongan_darah": golongan_darah,
                "agama": agama,
                "pendidikan": pendidikan,
                "pekerjaan": pekerjaan, # Menggunakan nilai langsung dari Dropdown
                "status_perkawinan": status_perkawinan,
                "shdk": shdk,
                "kewarganegaraan": kewarganegaraan,
                "jalan_kampung": jalan_kampung,
                "rt": rt,
                "rw": rw
            }
            
            try:
                response = supabase.table("data_penduduk").insert(data_warga).execute()
                st.success(f"✅ Mantap! Data warga atas nama {nama_lengkap} berhasil disimpan ke database Cloud.")
            except Exception as e:
                if "duplicate key" in str(e).lower() or "23505" in str(e):
                    st.error(f"⚠️ NIK {nik} sudah terdaftar di sistem! Tidak boleh ada data ganda.")
                else:
                    st.error(f"⚠️ Terjadi kesalahan saat menyimpan ke database: {e}")