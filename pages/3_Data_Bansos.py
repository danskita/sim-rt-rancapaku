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
# GEMBOK KHUSUS: Hanya Operator RT yang boleh masuk untuk input/edit/hapus data
role = st.session_state.get("role", "")
if role in ["admin_rw", "super_admin"]:
    st.error("⛔ Akses Ditolak! Halaman ini adalah wewenang mutlak Pengurus RT. Anda (RW/Desa) hanya memiliki akses untuk melihat rekap data pada menu Cetak Laporan.")
    st.stop()

st.set_page_config(page_title="Data Bansos", page_icon="📦", layout="centered")

st.title("📦 Modul Data Bantuan Sosial (Bansos)")
st.markdown("Halaman ini digunakan untuk mencatat distribusi Bantuan Sosial warga RT.")

# Mengambil NIK dari memori session
nik_autofill = st.session_state.get('autofill_nik', '')

with st.form("form_bansos", clear_on_submit=True):
    st.info("Pastikan NIK penerima bansos sudah terdaftar di menu **Data Penduduk**.")
    # NIK terisi otomatis
    nik_penerima = st.text_input("NIK Penerima Bansos *", value=nik_autofill, max_chars=16, help="Wajib 16 digit angka sesuai Data Penduduk")
    
    col1, col2 = st.columns(2)
    with col1:
        jenis_bansos = st.selectbox("Jenis Bantuan *", [
            "BLT (Bantuan Langsung Tunai)",
            "PKH (Program Keluarga Harapan)",
            "BPNT (Bantuan Pangan Non Tunai)",
            "Bansos Beras / Sembako",
            "Bantuan Khusus RT",
            "Lainnya"
        ])
    with col2:
        tanggal_terima = st.date_input("Tanggal Penerimaan *", max_value=datetime.date.today())
        
    keterangan = st.text_area("Keterangan Tambahan", help="Contoh: Menerima beras 10kg dan minyak goreng")
    
    st.markdown("*(Tanda * wajib diisi)*")
    submit_bansos = st.form_submit_button("Simpan Data Bansos")
    
    # Validasi dan Insert
    if submit_bansos:
        if not nik_penerima.isdigit() or len(nik_penerima) != 16:
            st.error("❌ Gagal! NIK harus berisi tepat 16 digit angka.")
        else:
            data_bantuan = {
                "nik_penerima": nik_penerima,
                "jenis_bansos": jenis_bansos,
                "tanggal_terima": str(tanggal_terima),
                "keterangan": keterangan
            }
            
            try:
                response = supabase.table("data_bansos").insert(data_bantuan).execute()
                st.success(f"✅ Mantap! Data penerimaan {jenis_bansos} untuk NIK {nik_penerima} berhasil dicatat.")
                st.session_state['autofill_nik'] = ''
            except Exception as e:
                st.error(f"⚠️ Terjadi kesalahan: Pastikan NIK penerima sudah terdaftar di Data Penduduk. Detail: {e}")