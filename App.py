import streamlit as st
from supabase import create_client, Client
from menu import tampilkan_menu

# 1. ATURAN STREAMLIT: set_page_config HARUS PALING ATAS!
st.set_page_config(page_title="SIM Desa / RW", page_icon="🏛️", layout="centered")

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)
# ---------------------------

# ==========================================
# PENYEDOT NAMA DESA OTOMATIS DARI PROFIL
# ==========================================
@st.cache_data(ttl=60)
def ambil_nama_instansi():
    try:
        # Sedot 1 data profil saja dari database
        res = supabase.table("profil_rt").select("desa, kelurahan").limit(1).execute()
        
        if len(res.data) > 0:
            # Cek apakah kolom desa atau kelurahan yang terisi
            nama_desa = res.data[0].get("desa") or res.data[0].get("kelurahan")
            if nama_desa:
                return f"Pemerintah Desa/Kelurahan {nama_desa.title()}"
    except Exception:
        pass
    
    # Jika profil masih kosong di database, gunakan nama default ini
    return "Sistem Informasi Manajemen Warga"
# ==========================================

def check_password():
    """Mengecek kredensial login langsung ke database Supabase"""
    def password_entered():
        input_username = st.session_state["username_input"]
        input_password = st.session_state["password_input"]
        
        try:
            # Mencari user di tabel data_admin Supabase
            response = supabase.table("data_admin").select("*").eq("username", input_username).execute()
            
            if response.data:
                user_data = response.data[0]
                # Jika password cocok
                if input_password == user_data["password"]:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_data["username"]
                    st.session_state["role"] = user_data["role"]
                    st.session_state["rt_akses"] = user_data["rt_akses"]
                    st.session_state["rw_akses"] = user_data["rw_akses"]
                    st.session_state["nama_wilayah"] = user_data["nama_wilayah"] # Nama wilayah tersimpan!
                    
                    del st.session_state["password_input"]
                    del st.session_state["username_input"]
                    return
            
            # Jika username tidak ditemukan atau password salah
            st.session_state["authenticated"] = False
            st.error("❌ Username atau Password salah!")
            
        except Exception as e:
            st.error(f"⚠️ Gagal terhubung ke server kredensial: {e}")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 Login Sistem Informasi")
        st.markdown("Silakan masukkan Username dan Password wilayah Anda.")
        
        st.text_input("Username", key="username_input")
        st.text_input("Password", type="password", key="password_input")
        st.button("Masuk Aplikasi", on_click=password_entered, type="primary")
        return False

    return True

if check_password():
    # Menampilkan Sidebar Menu HANYA JIKA SUDAH BERHASIL LOGIN
    tampilkan_menu()

    # --- TAMPILAN SETELAH BERHASIL LOGIN ---
    st.success(f"✅ Login Berhasil! Selamat datang, **{st.session_state['nama_wilayah']}**")
    
    # MEMANGGIL FUNGSI PENYEDOT NAMA DESA UNTUK JUDUL UTAMA
    nama_instansi_dinamis = ambil_nama_instansi()
    st.title(f"🏛️ {nama_instansi_dinamis}")
    
    # Menampilkan sapaan yang dinamis dan spesifik sesuai Role
    if st.session_state["role"] == "super_admin":
        st.info("👋 Anda login sebagai **Super Admin (Desa)**. Anda memiliki akses untuk memantau seluruh data dari 10 RW dan 45 RT.")
    elif st.session_state["role"] == "admin_rw":
        st.info(f"👋 Anda login sebagai **Admin RW**. Anda memiliki akses untuk memantau data seluruh RT di lingkungan RW {st.session_state['rw_akses']}.")
    else:
        st.info(f"👋 Anda login sebagai **Operator RT**. Layar Anda hanya akan menampilkan dan mengelola data warga untuk lingkungan {st.session_state['nama_wilayah']}.")
        
    st.markdown("---")
    st.markdown("""
    ### 📌 Petunjuk Penggunaan:
    1. Gunakan menu navigasi di **sidebar sebelah kiri** untuk berpindah antar modul.
    2. Semua data yang Anda masukkan akan otomatis dilabeli sesuai dengan wilayah akses Anda.
    3. Pastikan untuk *Logout* atau menutup browser jika sudah selesai menggunakan aplikasi.
    """)