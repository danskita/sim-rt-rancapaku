import streamlit as st
import pandas as pd
from supabase import create_client, Client
from menu import tampilkan_menu

# ========================================================
# 1. KONFIGURASI HALAMAN WAJIB PALING ATAS (Hanya Satu Kali)
# ========================================================
st.set_page_config(
    page_title="Manajemen Akun", 
    page_icon="🔐", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

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

st.title("🔐 Manajemen Akun Pengurus")
st.markdown("Kelola hak akses (Username & Password) untuk pengurus di wilayah Anda.")

# ==========================================
# MENARIK DATA SEBELUM TAB (Agar bisa dibagikan ke semua Tab)
# ==========================================
try:
    if role == "super_admin":
        res = supabase.table("data_admin").select("*").execute()
    elif role == "admin_rw":
        rw_akses = st.session_state.get("rw_akses", "001")
        res = supabase.table("data_admin").select("*").eq("rw_akses", rw_akses).neq("role", "super_admin").execute()
        
    df_admin = pd.DataFrame(res.data)
except Exception as e:
    st.error(f"Gagal memuat data akun: {e}")
    df_admin = pd.DataFrame()

# Pembuatan 3 Tab
tab_daftar, tab_tambah, tab_edit = st.tabs(["📋 Daftar Akun Aktif", "➕ Tambah Akun Baru", "✏️ Edit Akun"])

# ==========================================
# TAB 1: DAFTAR AKUN AKTIF & HAPUS AKUN
# ==========================================
with tab_daftar:
    st.subheader("Daftar Pengurus Terdaftar")
    
    if not df_admin.empty:
        df_tampil = df_admin[['nama_wilayah', 'username', 'password', 'role', 'rt_akses', 'rw_akses']]
        st.dataframe(df_tampil, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 🗑️ Hapus Akun")
        with st.form("form_hapus_akun"):
            akun_dihapus = st.selectbox("Pilih Username yang akan dihapus:", df_admin['username'].tolist())
            submit_hapus = st.form_submit_button("Hapus Akun Permanen", type="primary", use_container_width=True)
            
            if submit_hapus:
                if akun_dihapus == st.session_state['username']:
                    st.error("❌ Anda tidak bisa menghapus akun Anda sendiri yang sedang digunakan!")
                else:
                    supabase.table("data_admin").delete().eq("username", akun_dihapus).execute()
                    st.success(f"✅ Akun dengan username '{akun_dihapus}' berhasil dihapus.")
                    st.rerun()
    else:
        st.info("Belum ada akun pengurus yang terdaftar.")

# ==========================================
# TAB 2: TAMBAH AKUN BARU
# ==========================================
with tab_tambah:
    st.subheader("Buat Akses Pengurus Baru")
    
    with st.form("form_tambah_akun", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            username_baru = st.text_input("Username (Tanpa Spasi) *", help="Contoh: rt05_rw02")
            password_baru = st.text_input("Password *") # Tanpa type="password" agar admin bisa melihat apa yang diketik
            nama_wilayah_baru = st.text_input("Nama Wilayah *", help="Contoh: Pengurus RT 005 / RW 002")
        
        with col2:
            pilihan_role = ["operator_rt"] if role == "admin_rw" else ["operator_rt", "admin_rw", "super_admin"]
            role_baru = st.selectbox("Tingkat Akses (Role) *", pilihan_role)
            
            pilihan_rw = [f"{i:03}" for i in range(1, 11)] 
            pilihan_rt = ["-"] + [f"{i:03}" for i in range(1, 6)] 
            
            rw_default = st.session_state.get("rw_akses", "001") if role == "admin_rw" else "001"
            kunci_rw = True if role == "admin_rw" else False
            
            if rw_default not in pilihan_rw:
                rw_default = "001"
                
            rw_baru = st.selectbox("Akses RW", pilihan_rw, index=pilihan_rw.index(rw_default), disabled=kunci_rw)
            rt_baru = st.selectbox("Akses RT (Abaikan jika membuat akun RW/Desa)", pilihan_rt)

        st.markdown("*(Tanda * wajib diisi)*")
        submit_baru = st.form_submit_button("Simpan Akun Baru", type="primary", use_container_width=True)
        
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
                    st.rerun() # Refresh agar data di Tab 1 & Tab 3 langsung update
                except Exception as e:
                    if "duplicate key" in str(e).lower() or "23505" in str(e):
                        st.error(f"❌ Username '{username_baru}' sudah dipakai. Silakan gunakan username lain.")
                    else:
                        st.error(f"⚠️ Terjadi kesalahan: {e}")

# ==========================================
# TAB 3: EDIT AKUN
# ==========================================
with tab_edit:
    st.subheader("Edit Data & Sandi Pengurus")
    
    if not df_admin.empty:
        # PENTING: Menu pilihan diletakkan di luar st.form agar kotak isian 
        # di bawahnya otomatis memuat data asli (real-time) saat nama akun diganti
        akun_diedit = st.selectbox("Pilih Username yang akan diedit:", df_admin['username'].tolist(), key="select_edit")
        
        # Mengekstrak data lama dari akun yang baru saja dipilih
        data_saat_ini = df_admin[df_admin['username'] == akun_diedit].iloc[0]
        
        with st.form("form_edit_akun"):
            st.info(f"Mengedit profil dan akses untuk pengguna: **{akun_diedit}**")
            
            col1, col2 = st.columns(2)
            with col1:
                # Username tidak boleh diubah karena berfungsi sebagai identitas utama (Primary Key)
                st.text_input("Username (Permanen / Tidak bisa diubah)", value=data_saat_ini['username'], disabled=True)
                password_edit = st.text_input("Password Baru *", value=data_saat_ini['password'])
                nama_wilayah_edit = st.text_input("Nama Wilayah *", value=data_saat_ini['nama_wilayah'])
            
            with col2:
                pilihan_role = ["operator_rt"] if role == "admin_rw" else ["operator_rt", "admin_rw", "super_admin"]
                # Memastikan role yang ditarik ada di dalam daftar pilihan
                role_awal = data_saat_ini['role'] if data_saat_ini['role'] in pilihan_role else pilihan_role[0]
                role_edit = st.selectbox("Tingkat Akses (Role) *", pilihan_role, index=pilihan_role.index(role_awal))
                
                pilihan_rw = [f"{i:03}" for i in range(1, 11)] 
                pilihan_rt = ["-"] + [f"{i:03}" for i in range(1, 6)] 
                
                kunci_rw = True if role == "admin_rw" else False
                
                # Memastikan nilai rt dan rw aman ditarik dari database
                rw_awal = data_saat_ini['rw_akses'] if pd.notna(data_saat_ini['rw_akses']) and data_saat_ini['rw_akses'] in pilihan_rw else "001"
                rt_awal = data_saat_ini['rt_akses'] if pd.notna(data_saat_ini['rt_akses']) and data_saat_ini['rt_akses'] in pilihan_rt else "-"
                
                rw_edit = st.selectbox("Akses RW", pilihan_rw, index=pilihan_rw.index(rw_awal), disabled=kunci_rw)
                rt_edit = st.selectbox("Akses RT", pilihan_rt, index=pilihan_rt.index(rt_awal))

            st.markdown("*(Tanda * wajib diisi)*")
            submit_edit = st.form_submit_button("Simpan Perubahan Akun", type="primary", use_container_width=True)
            
            if submit_edit:
                if not password_edit or not nama_wilayah_edit:
                    st.warning("⚠️ Password dan Nama Wilayah tidak boleh dikosongkan!")
                else:
                    data_update = {
                        "password": password_edit,
                        "role": role_edit,
                        "nama_wilayah": nama_wilayah_edit,
                        "rw_akses": rw_edit,
                        "rt_akses": None if rt_edit == "-" else rt_edit
                    }
                    
                    try:
                        # Mengupdate (menimpa) data di tabel Supabase
                        supabase.table("data_admin").update(data_update).eq("username", akun_diedit).execute()
                        st.success(f"✅ Data dan sandi untuk akun '{akun_diedit}' berhasil diperbarui!")
                        st.rerun() # Refresh agar halaman diperbarui dengan data terkini
                    except Exception as e:
                        st.error(f"⚠️ Terjadi kesalahan saat menyimpan perubahan: {e}")
    else:
        st.info("Belum ada akun yang terdaftar untuk diedit.")