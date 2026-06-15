import streamlit as st
import pandas as pd
from supabase import create_client, Client
from menu import tampilkan_menu

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)
tampilkan_menu()
# ---------------------------

# Gembok Keamanan Umum
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("⚠️ Akses Ditolak! Silakan login melalui halaman utama terlebih dahulu.")
    st.stop()

# GEMBOK KHUSUS: Hanya Super Admin & Admin RW yang boleh masuk
role = st.session_state.get("role", "operator_rt")
if role == "operator_rt":
    st.error("⛔ Akses Ditolak! Halaman ini hanya diperuntukkan bagi Kepala Desa dan Ketua RW.")
    st.stop()

st.set_page_config(page_title="Manajemen Akun", page_icon="🔐", layout="wide")

st.title("🔐 Manajemen Akun Pengurus")
st.markdown("Kelola hak akses (Username & Password) untuk pengurus di wilayah Anda.")

tab_daftar, tab_tambah = st.tabs(["📋 Daftar Akun Aktif", "➕ Tambah Akun Baru"])

# ==========================================
# TAB 1: DAFTAR AKUN AKTIF & HAPUS AKUN
# ==========================================
with tab_daftar:
    st.subheader("Daftar Pengurus Terdaftar")
    
    try:
        if role == "super_admin":
            res = supabase.table("data_admin").select("*").execute()
        elif role == "admin_rw":
            rw_akses = st.session_state.get("rw_akses", "001")
            res = supabase.table("data_admin").select("*").eq("rw_akses", rw_akses).neq("role", "super_admin").execute()
            
        df_admin = pd.DataFrame(res.data)
        
        if not df_admin.empty:
            df_tampil = df_admin[['nama_wilayah', 'username', 'role', 'rt_akses', 'rw_akses']]
            # Perbaikan peringatan width
            st.dataframe(df_tampil, width='stretch')
            
            st.markdown("---")
            st.markdown("### 🗑️ Hapus Akun")
            with st.form("form_hapus_akun"):
                akun_dihapus = st.selectbox("Pilih Username yang akan dihapus:", df_admin['username'].tolist())
                submit_hapus = st.form_submit_button("Hapus Akun Permanen")
                
                if submit_hapus:
                    if akun_dihapus == st.session_state['username']:
                        st.error("❌ Anda tidak bisa menghapus akun Anda sendiri yang sedang digunakan!")
                    else:
                        supabase.table("data_admin").delete().eq("username", akun_dihapus).execute()
                        st.success(f"✅ Akun dengan username '{akun_dihapus}' berhasil dihapus.")
                        st.rerun()
        else:
            st.info("Belum ada akun pengurus yang terdaftar.")
            
    except Exception as e:
        st.error(f"Gagal memuat data akun: {e}")

# ==========================================
# TAB 2: TAMBAH AKUN BARU
# ==========================================
with tab_tambah:
    st.subheader("Buat Akses Pengurus Baru")
    
    with st.form("form_tambah_akun", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            username_baru = st.text_input("Username (Tanpa Spasi) *", help="Contoh: rt05_rw02")
            password_baru = st.text_input("Password *", type="password")
            nama_wilayah_baru = st.text_input("Nama Wilayah *", help="Contoh: Pengurus RT 005 / RW 002")
        
        with col2:
            pilihan_role = ["operator_rt"] if role == "admin_rw" else ["operator_rt", "admin_rw", "super_admin"]
            role_baru = st.selectbox("Tingkat Akses (Role) *", pilihan_role)
            
            # --- PENGATURAN BATAS WILAYAH SPESIFIK ---
            pilihan_rw = [f"{i:03}" for i in range(1, 11)] # Menghasilkan daftar 001 sampai 010
            pilihan_rt = ["-"] + [f"{i:03}" for i in range(1, 6)] # Menghasilkan daftar - lalu 001 sampai 005
            
            rw_default = st.session_state.get("rw_akses", "001") if role == "admin_rw" else "001"
            kunci_rw = True if role == "admin_rw" else False
            
            # Memastikan rw_default selalu valid sesuai rentang
            if rw_default not in pilihan_rw:
                rw_default = "001"
                
            rw_baru = st.selectbox("Akses RW", pilihan_rw, index=pilihan_rw.index(rw_default), disabled=kunci_rw)
            rt_baru = st.selectbox("Akses RT (Abaikan jika membuat akun RW/Desa)", pilihan_rt)

        st.markdown("*(Tanda * wajib diisi)*")
        submit_baru = st.form_submit_button("Simpan Akun Baru", type="primary")
        
        if submit_baru:
            if not username_baru or not password_baru or not nama_wilayah_baru:
                st.warning("⚠️ Username, Password, dan Nama Wilayah wajib diisi!")
            elif " " in username_baru:
                st.warning("⚠️ Username tidak boleh menggunakan spasi.")
            else:
                data_akun_baru = {
                    "username": username_baru.lower(),
                    "password": password_baru,
                    "role": role_baru,
                    "nama_wilayah": nama_wilayah_baru,
                    "rw_akses": rw_baru,
                    "rt_akses": None if rt_baru == "-" else rt_baru
                }
                
                try:
                    supabase.table("data_admin").insert(data_akun_baru).execute()
                    st.success(f"✅ Akun untuk '{nama_wilayah_baru}' berhasil dibuat! Silakan bagikan username dan password kepada yang bersangkutan.")
                except Exception as e:
                    if "duplicate key" in str(e).lower() or "23505" in str(e):
                        st.error(f"❌ Username '{username_baru}' sudah dipakai. Silakan gunakan username lain.")
                    else:
                        st.error(f"⚠️ Terjadi kesalahan: {e}")