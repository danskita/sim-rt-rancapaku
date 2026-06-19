import streamlit as st
from supabase import create_client, Client
from menu import tampilkan_menu

# ========================================================
# 1. KONFIGURASI HALAMAN WAJIB PALING ATAS (Hanya Satu Kali)
# ========================================================
st.set_page_config(
    page_title="Profil Wilayah", 
    page_icon="🏢", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)
# ---------------------------

# 2. GEMBOK KEAMANAN MULTI-USER
if "role" not in st.session_state:
    st.warning("⚠️ Akses Ditolak! Silakan login melalui halaman utama terlebih dahulu.")
    st.stop()

# 3. TAMPILKAN MENU SIDEBAR
tampilkan_menu()

# Variabel Sesi Akses
role = st.session_state.get("role", "operator_rt")
rt_akses = st.session_state.get("rt_akses", "001")
rw_akses = st.session_state.get("rw_akses", "001")

st.title("🏢 Pusat Pengaturan Profil Wilayah")

# ==================================================
# LOGIKA PILIHAN PROFIL BERDASARKAN ROLE
# ==================================================
if role == "super_admin":
    opsi_pilihan = ["TINGKAT DESA (Master)"] + [f"RW {i:03}" for i in range(1, 11)]
    pilihan_wilayah = st.selectbox("Pilih Profil yang akan dikonfigurasi:", opsi_pilihan)
    
    if pilihan_wilayah == "TINGKAT DESA (Master)":
        nama_target = "TINGKAT DESA"
        rw_terpilih = "000"
        label_pimpinan = "Nama Kepala Desa *"
        label_alamat = "Alamat Kantor Desa / Sekretariat"
        jenis_form = "desa"
    else:
        nama_target = pilihan_wilayah
        rw_terpilih = pilihan_wilayah.replace("RW ", "")
        label_pimpinan = f"Nama Ketua {nama_target} *"
        label_alamat = f"Alamat Lengkap Sekretariat {nama_target}"
        jenis_form = "rw"
        
elif role == "admin_rw":
    # 💡 FITUR BARU: Admin RW kini bisa memilih mengatur RW-nya, atau mengatur RT di bawahnya
    opsi_pilihan = [f"RW {rw_akses} (Profil Utama RW)"] + [f"RT {i:03} / RW {rw_akses}" for i in range(1, 6)]
    pilihan_wilayah = st.selectbox("Pilih Profil yang akan dikonfigurasi:", opsi_pilihan)
    
    if "Profil Utama RW" in pilihan_wilayah:
        nama_target = f"RW {rw_akses}"
        rw_terpilih = rw_akses
        label_pimpinan = f"Nama Ketua RW {rw_akses} *"
        label_alamat = f"Alamat Lengkap Sekretariat RW {rw_akses}"
        jenis_form = "rw"
    else:
        nama_target = pilihan_wilayah
        rw_terpilih = rw_akses
        label_pimpinan = "Nama Ketua RT *"
        label_alamat = "Alamat Sekretariat RT"
        jenis_form = "rt"
        
else:
    # Operator RT tetap hanya bisa mengatur RT-nya sendiri secara spesifik
    nama_target = f"RT {rt_akses} / RW {rw_akses}"
    rw_terpilih = rw_akses
    label_pimpinan = "Nama Ketua RT *"
    label_alamat = "Alamat Sekretariat RT"
    jenis_form = "rt"
    st.info(f"Anda sedang mengelola profil untuk **{nama_target}**")
    st.markdown("ℹ️ *Catatan: Nama Desa, Kecamatan, dan Kabupaten dikelola terpusat oleh Admin RW/Desa dan telah disinkronkan otomatis.*")

# ==================================================
# MENGAMBIL DATA DARI DATABASE
# ==================================================
try:
    res_target = supabase.table("profil_rt").select("*").eq("nama_rt_rw", nama_target).execute()
    profil_data = res_target.data[0] if res_target.data else {}
except:
    profil_data = {}

# ==================================================
# FORMULIR PENGISIAN PROFIL
# ==================================================
with st.form("form_profil"):
    st.subheader(f"Identitas {nama_target}")
    
    # Aturan Kolom Desa/Kecamatan/Kota (Dikunci jika edit RT)
    if jenis_form == "rt":
        desa_kelurahan = st.text_input("Nama Desa / Kelurahan", value=profil_data.get("kelurahan", "Belum Diatur"), disabled=True)
        col1, col2 = st.columns(2)
        with col1:
            kecamatan = st.text_input("Kecamatan", value=profil_data.get("kecamatan", "Belum Diatur"), disabled=True)
        with col2:
            kota = st.text_input("Kabupaten / Kota", value=profil_data.get("kota", "Belum Diatur"), disabled=True)
        kode_pos = profil_data.get("kode_pos", "") 
    else:
        desa_kelurahan = st.text_input("Nama Desa / Kelurahan *", value=profil_data.get("kelurahan", "Desa Maju Bersama"))
        col1, col2 = st.columns(2)
        with col1:
            kecamatan = st.text_input("Kecamatan", value=profil_data.get("kecamatan", ""))
        with col2:
            kota = st.text_input("Kabupaten / Kota", value=profil_data.get("kota", ""))
        kode_pos = st.text_input("Kode Pos", value=profil_data.get("kode_pos", ""))
        
    st.markdown("---")
    st.subheader("Detail Sekretariat & Pimpinan")
    alamat_sekretariat = st.text_area(label_alamat, value=profil_data.get("alamat_sekretariat", ""))
    nama_pimpinan = st.text_input(label_pimpinan, value=profil_data.get("nama_ketua_rt", ""))
    
    # Label Tombol Simpan
    if jenis_form == "desa":
        teks_tombol = "Simpan & Sinkronkan ke Seluruh Wilayah"
    elif jenis_form == "rw":
        teks_tombol = "Simpan & Sinkronkan ke Data RT"
    else:
        teks_tombol = "Simpan Profil RT"
        
    submit_profil = st.form_submit_button(teks_tombol, type="primary", width="stretch")
    
    if submit_profil:
        if jenis_form in ["desa", "rw"] and not desa_kelurahan:
            st.warning("⚠️ Mohon lengkapi Nama Desa.")
        elif not nama_pimpinan:
            st.warning(f"⚠️ Mohon lengkapi {label_pimpinan.replace('*', '')}.")
        else:
            with st.spinner("Menyimpan data profil..."):
                try:
                    # 1. Update Khusus RT (Jika form yang sedang diedit adalah form RT)
                    if jenis_form == "rt":
                        data_update = {
                            "alamat_sekretariat": alamat_sekretariat.title().strip(),
                            "nama_ketua_rt": nama_pimpinan.title().strip()
                        }
                        supabase.table("profil_rt").update(data_update).eq("nama_rt_rw", nama_target).execute()
                        
                    # 2. Update Khusus RW / Desa (Disertai penyebaran data ke bawahnya)
                    else:
                        data_induk = {
                            "nama_rt_rw": nama_target,
                            "kelurahan": desa_kelurahan.title().strip(),
                            "kecamatan": kecamatan.title().strip(),
                            "kota": kota.title().strip(),
                            "kode_pos": kode_pos.strip(),
                            "alamat_sekretariat": alamat_sekretariat.title().strip(),
                            "nama_ketua_rt": nama_pimpinan.title().strip()
                        }
                        
                        if profil_data:
                            supabase.table("profil_rt").update(data_induk).eq("nama_rt_rw", nama_target).execute()
                        else:
                            supabase.table("profil_rt").insert(data_induk).execute()
                            
                        # Proses Sinkronisasi
                        if jenis_form == "desa":
                            supabase.table("profil_rt").update({
                                "kelurahan": desa_kelurahan.title().strip(),
                                "kecamatan": kecamatan.title().strip(),
                                "kota": kota.title().strip(),
                                "kode_pos": kode_pos.strip()
                            }).neq("nama_rt_rw", "x").execute()
                        elif jenis_form == "rw":
                            for i in range(1, 6):
                                rt_str = f"{i:03}"
                                nama_rt_target = f"RT {rt_str} / RW {rw_terpilih}"
                                
                                res_rt = supabase.table("profil_rt").select("id").eq("nama_rt_rw", nama_rt_target).execute()
                                
                                if res_rt.data:
                                    supabase.table("profil_rt").update({
                                        "kelurahan": desa_kelurahan.title().strip(),
                                        "kecamatan": kecamatan.title().strip(),
                                        "kota": kota.title().strip(),
                                        "kode_pos": kode_pos.strip()
                                    }).eq("nama_rt_rw", nama_rt_target).execute()
                                else:
                                    data_rt_baru = {
                                        "nama_rt_rw": nama_rt_target,
                                        "kelurahan": desa_kelurahan.title().strip(),
                                        "kecamatan": kecamatan.title().strip(),
                                        "kota": kota.title().strip(),
                                        "kode_pos": kode_pos.strip(),
                                        "alamat_sekretariat": "-", 
                                        "nama_ketua_rt": f"Ketua RT {rt_str}"
                                    }
                                    supabase.table("profil_rt").insert(data_rt_baru).execute()
                                    
                    st.success(f"✅ Sempurna! Profil **{nama_target}** berhasil disimpan.")
                except Exception as e:
                    st.error(f"⚠️ Terjadi kesalahan saat menyimpan profil: {e}")

# ==========================================
# FITUR SINKRONISASI LOGO KHUSUS ADMIN DESA
# ==========================================
if role == "super_admin":
    st.markdown("---")
    st.subheader("🖼️ Pengaturan Logo Resmi Desa")
    st.write("Logo yang diunggah di sini akan **otomatis tersinkronisasi** dan digunakan pada Kop Surat seluruh RT dan RW.")
    
    file_logo = st.file_uploader("Pilih file Logo (disarankan format PNG dengan latar transparan)", type=["png", "jpg", "jpeg"])
    
    if st.button("🚀 Unggah & Sinkronisasikan Logo", type="primary", width="stretch"):
        if file_logo is not None:
            with st.spinner("Sedang mengunggah dan menyinkronkan logo ke seluruh wilayah..."):
                try:
                    # Menggunakan upsert=true agar logo yang lama otomatis tertimpa dengan yang baru
                    supabase.storage.from_("arsip_digital").upload(
                        path="logo_desa_resmi.png",
                        file=file_logo.getvalue(),
                        file_options={"content-type": file_logo.type, "upsert": "true"}
                    )
                    st.success("✅ Sempurna! Logo resmi berhasil diperbarui dan siap digunakan oleh semua RT/RW.")
                except Exception as e:
                    st.error(f"⚠️ Gagal mengunggah logo. Pastikan koneksi aman. Error: {e}")
        else:
            st.warning("⚠️ Silakan pilih file gambar logo terlebih dahulu.")