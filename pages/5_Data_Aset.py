import streamlit as st
# Gembok Keamanan: Cek apakah user sudah login
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("⚠️ Akses Ditolak! Silakan login melalui halaman utama terlebih dahulu.")
    st.stop() # Menghentikan kode di bawahnya agar tidak dieksekusi
# GEMBOK KHUSUS: Hanya Operator RT yang boleh masuk untuk input/edit/hapus data
role = st.session_state.get("role", "")
if role in ["admin_rw", "super_admin"]:
    st.error("⛔ Akses Ditolak! Halaman ini adalah wewenang mutlak Pengurus RT. Anda (RW/Desa) hanya memiliki akses untuk melihat rekap data pada menu Cetak Laporan.")
    st.stop()
import datetime
from supabase import create_client, Client
from menu import tampilkan_menu

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)
tampilkan_menu()
# ---------------------------

st.set_page_config(page_title="Data Sarpras & Aset", page_icon="⛺", layout="centered")

st.title("⛺ Modul Data Sarpras dan Aset RT")
st.markdown("Halaman ini digunakan untuk menginventarisasi barang dan aset milik lingkungan RT.")

with st.form("form_aset", clear_on_submit=True):
    nama_aset = st.text_input("Nama Barang / Aset *", help="Contoh: Tenda RT, Kursi Lipat, Sound System")
    
    col1, col2 = st.columns(2)
    with col1:
        kategori = st.selectbox("Kategori Aset *", [
            "Perlengkapan Acara (Tenda, Kursi, dll)",
            "Elektronik & Sound System",
            "Peralatan Gotong Royong",
            "ATK & Administrasi",
            "Lainnya"
        ])
        jumlah = st.number_input("Jumlah Barang *", min_value=1, step=1)
    with col2:
        kondisi = st.selectbox("Kondisi Barang *", ["Baik", "Rusak Ringan", "Rusak Berat"])
        tanggal_perolehan = st.date_input("Tanggal Perolehan / Pembelian", max_value=datetime.date.today())
        
    lokasi_penyimpanan = st.text_input("Lokasi Penyimpanan *", help="Contoh: Gudang RT, Rumah Ketua RT, Balai Warga")
    keterangan = st.text_area("Keterangan Tambahan", help="Contoh: Dibeli dari iuran warga bulan Agustus")
    
    st.markdown("*(Tanda * wajib diisi)*")
    submit_aset = st.form_submit_button("Simpan Data Aset")
    
    # Validasi dan Insert ke Supabase
    if submit_aset:
        if not nama_aset.strip() or not lokasi_penyimpanan.strip():
            st.error("❌ Gagal! Pastikan semua field bertanda bintang (*) telah terisi.")
        else:
            data_inventaris = {
                "nama_aset": nama_aset,
                "kategori": kategori,
                "jumlah": jumlah,
                "kondisi": kondisi,
                "tanggal_perolehan": str(tanggal_perolehan),
                "lokasi_penyimpanan": lokasi_penyimpanan,
                "keterangan": keterangan
            }
            
            try:
                response = supabase.table("data_aset").insert(data_inventaris).execute()
                st.success(f"✅ Mantap! Data aset **{nama_aset}** (Jumlah: {jumlah}) berhasil dicatat di inventaris.")
            except Exception as e:
                st.error(f"⚠️ Terjadi kesalahan saat menyimpan ke database: {e}")