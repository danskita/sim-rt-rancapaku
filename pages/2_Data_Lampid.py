import streamlit as st
import datetime
from supabase import create_client, Client
from menu import tampilkan_menu

# ========================================================
# 1. KONFIGURASI HALAMAN WAJIB PALING ATAS (Hanya Satu Kali)
# ========================================================
st.set_page_config(
    page_title="Data Lampid", 
    page_icon="🔄", 
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


st.title("🔄 Modul Data Lampid")
st.markdown("Pilih tab di bawah ini untuk menginput data Lahir, Mati, Pindah, atau Datang.")

# Mengambil NIK dari memori session
nik_autofill = st.session_state.get('autofill_nik', '')

tab_lahir, tab_mati, tab_pindah, tab_datang = st.tabs(["👶 Lahir", "🪦 Mati", "📦 Pindah", "👋 Datang"])

# ==========================================
# TAB 1: KELAHIRAN
# ==========================================
with tab_lahir:
    st.subheader("Form Laporan Kelahiran")
    
    with st.form("form_lahir", clear_on_submit=True):
        nama_bayi = st.text_input("Nama Lengkap Bayi *")
        
        col1, col2 = st.columns(2)
        with col1:
            tanggal_lahir = st.date_input("Tanggal Lahir *", max_value=datetime.date.today())
            tempat_persalinan = st.text_input("Tempat Persalinan *", help="Contoh: RSIA / Bidan / Rumah")
            # NIK Ibu Autofill
            nik_ibu = st.text_input("NIK Ibu *", value=nik_autofill, max_chars=16, help="Wajib 16 digit angka sesuai Data Penduduk")
            anak_ke = st.number_input("Anak Ke- *", min_value=1, step=1)
        with col2:
            jenis_kelamin = st.selectbox("Jenis Kelamin *", ["Laki-laki", "Perempuan"])
            berat_bayi = st.text_input("Berat Bayi", help="Contoh: 3.2 kg")
            nik_ayah = st.text_input("NIK Ayah", max_chars=16, help="Opsional. 16 digit angka")
            
        st.markdown("*(Tanda * wajib diisi)*")
        submit_lahir = st.form_submit_button("Simpan Data Kelahiran", type="primary", width="stretch")
        
        if submit_lahir:
            if not nik_ibu.isdigit() or len(nik_ibu) != 16:
                st.error("❌ Gagal! NIK Ibu harus berisi tepat 16 digit angka.")
            elif not nama_bayi.strip() or not tempat_persalinan.strip():
                st.error("❌ Gagal! Pastikan semua field bertanda bintang (*) terisi.")
            else:
                data_kelahiran = {
                    "nama_bayi": nama_bayi,
                    "tanggal_lahir": str(tanggal_lahir),
                    "jenis_kelamin": jenis_kelamin,
                    "tempat_persalinan": tempat_persalinan,
                    "nik_ibu": nik_ibu,
                    "nik_ayah": nik_ayah if nik_ayah else None,
                    "anak_ke": anak_ke,
                    "berat_bayi": berat_bayi
                }
                
                try:
                    response = supabase.table("data_lahir").insert(data_kelahiran).execute()
                    st.success(f"✅ Mantap! Data kelahiran bayi {nama_bayi} berhasil dicatat.")
                    st.session_state['autofill_nik'] = ''
                except Exception as e:
                    st.error(f"⚠️ Terjadi kesalahan: Pastikan NIK Ibu sudah terdaftar di Data Penduduk. Detail: {e}")

# ==========================================
# TAB 2: KEMATIAN
# ==========================================
with tab_mati:
    st.subheader("Form Laporan Kematian Warga")
    
    with st.form("form_mati", clear_on_submit=True):
        # NIK Autofill
        nik_jenazah = st.text_input("NIK Warga yang Meninggal *", value=nik_autofill, max_chars=16, help="Wajib 16 digit angka sesuai Data Penduduk")
        
        col1, col2 = st.columns(2)
        with col1:
            tanggal_wafat = st.date_input("Tanggal Wafat *", max_value=datetime.date.today())
            tempat_wafat = st.text_input("Tempat Wafat *", help="Contoh: RSUD / Rumah Duka")
        with col2:
            penyebab = st.text_input("Penyebab/Keterangan", help="Contoh: Sakit / Usia Lanjut")
            nama_pelapor = st.text_input("Nama Pelapor *")
            
        st.markdown("*(Tanda * wajib diisi)*")
        submit_mati = st.form_submit_button("Simpan Data Kematian", type="primary", width="stretch")
        
        if submit_mati:
            if not nik_jenazah.isdigit() or len(nik_jenazah) != 16:
                st.error("❌ Gagal! NIK harus berisi tepat 16 digit angka.")
            elif not tempat_wafat.strip() or not nama_pelapor.strip():
                st.error("❌ Gagal! Pastikan semua field bertanda bintang (*) terisi.")
            else:
                data_kematian = {
                    "nik_jenazah": nik_jenazah,
                    "tanggal_wafat": str(tanggal_wafat),
                    "tempat_wafat": tempat_wafat,
                    "penyebab": penyebab,
                    "nama_pelapor": nama_pelapor
                }
                
                try:
                    response = supabase.table("data_mati").insert(data_kematian).execute()
                    st.success(f"✅ Mantap! Data kematian untuk NIK {nik_jenazah} berhasil dicatat.")
                    st.session_state['autofill_nik'] = ''
                except Exception as e:
                    st.error(f"⚠️ Terjadi kesalahan: Pastikan NIK Jenazah sudah terdaftar di Data Penduduk. Detail: {e}")

# ==========================================
# TAB 3: PINDAH (KELUAR)
# ==========================================
with tab_pindah:
    st.subheader("Form Laporan Warga Pindah")
    
    with st.form("form_pindah", clear_on_submit=True):
        # NIK Autofill
        nik_pindah = st.text_input("NIK Warga yang Pindah *", value=nik_autofill, max_chars=16, help="Wajib 16 digit angka sesuai Data Penduduk")
        
        col1, col2 = st.columns(2)
        with col1:
            tanggal_pindah = st.date_input("Tanggal Pindah *", max_value=datetime.date.today())
            alasan_pindah = st.text_input("Alasan Pindah *", help="Contoh: Pindah Tugas / Ikut Suami")
        with col2:
            alamat_tujuan = st.text_area("Alamat Tujuan Lengkap *", help="Masukkan alamat tempat tinggal baru")
            
        st.markdown("*(Tanda * wajib diisi)*")
        submit_pindah = st.form_submit_button("Simpan Data Pindah", type="primary", width="stretch")
        
        if submit_pindah:
            if not nik_pindah.isdigit() or len(nik_pindah) != 16:
                st.error("❌ Gagal! NIK harus berisi tepat 16 digit angka.")
            elif not alasan_pindah.strip() or not alamat_tujuan.strip():
                st.error("❌ Gagal! Pastikan semua field bertanda bintang (*) terisi.")
            else:
                data_kepindahan = {
                    "nik_pindah": nik_pindah,
                    "tanggal_pindah": str(tanggal_pindah),
                    "alamat_tujuan": alamat_tujuan,
                    "alasan_pindah": alasan_pindah
                }
                
                try:
                    response = supabase.table("data_pindah").insert(data_kepindahan).execute()
                    st.success(f"✅ Mantap! Data kepindahan untuk NIK {nik_pindah} berhasil dicatat.")
                    st.session_state['autofill_nik'] = ''
                except Exception as e:
                    st.error(f"⚠️ Terjadi kesalahan: Pastikan NIK sudah terdaftar di Data Penduduk. Detail: {e}")

# ==========================================
# TAB 4: DATANG (MASUK)
# ==========================================
with tab_datang:
    st.subheader("Form Laporan Warga Pendatang")
    
    with st.form("form_datang", clear_on_submit=True):
        st.info("Pastikan identitas warga pendatang sudah diinput di menu **Data Penduduk** terlebih dahulu.")
        # NIK Autofill
        nik_datang = st.text_input("NIK Warga Pendatang *", value=nik_autofill, max_chars=16, help="Wajib 16 digit angka sesuai Data Penduduk")
        
        col1, col2 = st.columns(2)
        with col1:
            tanggal_datang = st.date_input("Tanggal Kedatangan *", max_value=datetime.date.today())
            alasan_datang = st.text_input("Alasan Datang *", help="Contoh: Pindah Domisili / Bekerja / Ikut Keluarga")
        with col2:
            alamat_asal = st.text_area("Alamat Asal Lengkap *", help="Masukkan alamat tempat tinggal sebelumnya")
            
        st.markdown("*(Tanda * wajib diisi)*")
        submit_datang = st.form_submit_button("Simpan Data Kedatangan", type="primary", width="stretch")
        
        if submit_datang:
            if not nik_datang.isdigit() or len(nik_datang) != 16:
                st.error("❌ Gagal! NIK harus berisi tepat 16 digit angka.")
            elif not alasan_datang.strip() or not alamat_asal.strip():
                st.error("❌ Gagal! Pastikan semua field bertanda bintang (*) terisi.")
            else:
                data_kedatangan = {
                    "nik_datang": nik_datang,
                    "tanggal_datang": str(tanggal_datang),
                    "alamat_asal": alamat_asal,
                    "alasan_datang": alasan_datang
                }
                
                try:
                    response = supabase.table("data_datang").insert(data_kedatangan).execute()
                    st.success(f"✅ Mantap! Data kedatangan untuk NIK {nik_datang} berhasil dicatat.")
                    st.session_state['autofill_nik'] = ''
                except Exception as e:
                    st.error(f"⚠️ Terjadi kesalahan: Pastikan NIK pendatang sudah terdaftar di Data Penduduk terlebih dahulu. Detail: {e}")