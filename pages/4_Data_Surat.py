import streamlit as st
import datetime
from supabase import create_client, Client
from menu import tampilkan_menu
st.set_page_config(
    page_title="Halaman Login", 
    page_icon="logo_rtrw.png", 
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


st.set_page_config(page_title="Layanan Surat", page_icon="✉️", layout="centered")

st.title("✉️ Modul Layanan Surat Menyurat")
st.markdown("Halaman ini digunakan untuk mencatat pengajuan surat pengantar warga RT.")

# Mengambil NIK dari memori session jika pengguna melompat dari halaman Kelola Data
nik_autofill = st.session_state.get('autofill_nik', '')

with st.form("form_surat", clear_on_submit=True):
    st.info("Pastikan NIK pemohon sudah terdaftar di menu **Data Penduduk**.")
    # NIK terisi otomatis menggunakan parameter value=
    nik_pemohon = st.text_input("NIK Pemohon *", value=nik_autofill, max_chars=16, help="Wajib 16 digit angka sesuai Data Penduduk")
    
    col1, col2 = st.columns(2)
    with col1:
        jenis_surat = st.selectbox("Jenis Surat *", [
            "Surat Pengantar Domisili",
            "Surat Pengantar Pembuatan KTP/KK",
            "Surat Keterangan Tidak Mampu (SKTM)",
            "Surat Keterangan Usaha (SKU)",
            "Surat Keterangan Kematian",
            "Surat Pengantar Nikah",
            "Lainnya"
        ])
    with col2:
        tanggal_pengajuan = st.date_input("Tanggal Pengajuan *", max_value=datetime.date.today())
        
    keperluan = st.text_area("Keperluan / Keterangan Detail *", help="Contoh: Untuk persyaratan beasiswa anak sekolah")
    
    st.markdown("*(Tanda * wajib diisi)*")
    submit_surat = st.form_submit_button("Simpan Data Pengajuan Surat")
    
    # Validasi dan Insert ke Supabase
    if submit_surat:
        if not nik_pemohon.isdigit() or len(nik_pemohon) != 16:
            st.error("❌ Gagal! NIK harus berisi tepat 16 digit angka.")
        elif not keperluan.strip():
            st.error("❌ Gagal! Harap isi kolom keperluan surat.")
        else:
            data_pengajuan = {
                "nik_pemohon": nik_pemohon,
                "jenis_surat": jenis_surat,
                "tanggal_pengajuan": str(tanggal_pengajuan),
                "keperluan": keperluan,
                "status_surat": "Menunggu Proses"
            }
            
            try:
                response = supabase.table("data_surat").insert(data_pengajuan).execute()
                st.success(f"✅ Mantap! Pengajuan {jenis_surat} untuk NIK {nik_pemohon} berhasil dicatat.")
                # Hapus memori autofill setelah berhasil simpan agar form kembali netral
                st.session_state['autofill_nik'] = '' 
            except Exception as e:
                st.error(f"⚠️ Terjadi kesalahan: Pastikan NIK pemohon sudah terdaftar di Data Penduduk. Detail: {e}")