import streamlit as st

def tampilkan_menu():
    # Jika belum login, hanya tampilkan menu Login
    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        st.sidebar.page_link("App.py", label="Halaman Login", icon="🔐")
        return

    # Mengambil data profil yang login
    role = st.session_state.get("role", "")
    nama_wilayah = st.session_state.get("nama_wilayah", "Pengurus")

    # Header Sidebar
    st.sidebar.header(f"👋 Halo,")
    st.sidebar.markdown(f"**{nama_wilayah}**")
    st.sidebar.markdown("---")

    # 1. MENU KHUSUS OPERATOR RT
    if role == "operator_rt":
        st.sidebar.subheader("📋 Menu Operasional")
        st.sidebar.page_link("pages/0_Dashboard.py", label="Dashboard Utama", icon="📊")
        st.sidebar.page_link("pages/1_Data_Penduduk.py", label="Data Penduduk", icon="👥")
        st.sidebar.page_link("pages/2_Data_Lampid.py", label="Data Lampid", icon="🔄")
        st.sidebar.page_link("pages/3_Data_Bansos.py", label="Data Bansos", icon="📦")
        st.sidebar.page_link("pages/4_Data_Surat.py", label="Layanan Surat", icon="✉️")
        st.sidebar.page_link("pages/5_Data_Aset.py", label="Sarpras & Aset", icon="🏢")
        st.sidebar.page_link("pages/7_Kelola_Data.py", label="Kelola Data Warga", icon="⚙️")
        st.sidebar.page_link("pages/8_Import_Data.py", label="Import Data Excel", icon="📥")
        st.sidebar.page_link("pages/15_Data_Arsip.py", label="Arsip Digital", icon="🗂️")
        st.sidebar.page_link("pages/16_Forum_Diskusi.py", label="Forum Diskusi", icon="💬") 
        st.sidebar.page_link("pages/17_Panduan_Aplikasi.py", label="Panduan & Akun", icon="📖")

    # 2. MENU KHUSUS ADMIN RW & KEPALA DESA
    elif role in ["admin_rw", "super_admin"]:
        st.sidebar.subheader("📊 Menu Manajemen")
        st.sidebar.page_link("pages/6_Cetak_Laporan.py", label="Dashboard & Laporan", icon="📊")
        st.sidebar.page_link("pages/10_Profil_RT.py", label="Profil Wilayah", icon="🏢")
        st.sidebar.page_link("pages/12_Manajemen_Akun.py", label="Manajemen Akun", icon="🔐")
        st.sidebar.page_link("pages/15_Data_Arsip.py", label="Arsip Digital", icon="🗂️")
        st.sidebar.page_link("pages/16_Forum_Diskusi.py", label="Forum Diskusi", icon="💬")
        st.sidebar.page_link("pages/17_Panduan_Aplikasi.py", label="Panduan & Akun", icon="📖") 
        
        # --- SINKRONISASI PENGATURAN RW vs DESA ---
        if role == "super_admin":
            st.sidebar.page_link("pages/11_Pengaturan_Sistem.py", label="Pengaturan Sistem", icon="⚠️")
        elif role == "admin_rw":
            # Ganti "14_Pengaturan_RW.py" dengan nama file yang baru saja Anda buat untuk RW
            st.sidebar.page_link("pages/14_Pengaturan_RW.py", label="Kelola Data RW", icon="⚙️")

    # =========================================================
    # 3. MENU PUSAT CETAK (DIBUKA UNTUK SEMUA ROLE)
    # =========================================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("🖨️ Pusat Cetak Dokumen")
    st.sidebar.page_link("pages/9_Cetak_PDF.py", label="Cetak Surat & Kegiatan", icon="✉️")
    st.sidebar.page_link("pages/13_Cetak_Laporan_PDF.py", label="Cetak Laporan Massal", icon="📊")

    # =========================================================
    # 4. LOGIKA KONFIRMASI KELUAR (LOGOUT)
    # =========================================================
    st.sidebar.markdown("---")
    
    # Inisialisasi state konfirmasi jika belum ada
    if "konfirmasi_keluar" not in st.session_state:
        st.session_state.konfirmasi_keluar = False

    # Kondisi 1: Jika tombol utama BELUM ditekan
    if not st.session_state.konfirmasi_keluar:
        if st.sidebar.button("🚪 Logout dari Sistem", use_container_width=True, key="btn_logout_utama"): 
            st.session_state.konfirmasi_keluar = True
            st.rerun()
            
    # Kondisi 2: Jika tombol utama SUDAH ditekan (Tampilkan Peringatan & Pilihan)
    else:
        st.sidebar.warning("❓ Yakin ingin keluar dari aplikasi?")
        
        # Membagi layar sidebar menjadi 2 kolom untuk tombol Ya dan Batal
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("Ya", use_container_width=True, type="primary", key="btn_ya"):
                st.session_state.clear()
                st.switch_page("App.py")
        
        with col2:
            if st.button("Batal", use_container_width=True, type="secondary", key="btn_batal"):
                st.session_state.konfirmasi_keluar = False
                st.rerun()