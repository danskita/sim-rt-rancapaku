import streamlit as st
from supabase import create_client, Client
from menu import tampilkan_menu

# 1. ATURAN STREAMLIT: set_page_config HARUS PALING ATAS!
st.set_page_config(page_title="Profil Wilayah", page_icon="🏢", layout="centered")

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)
# ---------------------------

# 2. GEMBOK KEAMANAN MULTI-USER (Sistem Baru)
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

# 1. BLOKIR OPERATOR RT (Agar diurus oleh RW/Desa)
if role == "operator_rt":
    st.info("ℹ️ Pengaturan identitas Desa, Kecamatan, dan Kabupaten dikelola terpusat oleh Admin RW atau Kepala Desa. Data Anda sudah otomatis disinkronkan.")
    
    # Menampilkan profil RT-nya sendiri jika ingin melihat
    nama_rt_rw_sendiri = f"RT {rt_akses} / RW {rw_akses}"
    res = supabase.table("profil_rt").select("*").eq("nama_rt_rw", nama_rt_rw_sendiri).execute()
    if res.data:
        st.json(res.data[0])
    st.stop()

# 2. LOGIKA UNTUK ADMIN RW & KEPALA DESA
st.markdown("Atur identitas profil kewilayahan di sini. **Perubahan Data Desa/Kecamatan/Kota akan otomatis disinkronkan ke seluruh bawahan.**")

# Menentukan profil mana yang sedang diedit
if role == "super_admin":
    opsi_pilihan = ["TINGKAT DESA (Master)"] + [f"RW {i:03}" for i in range(1, 11)]
    pilihan_wilayah = st.selectbox("Pilih Profil yang akan dikonfigurasi:", opsi_pilihan)
    
    if pilihan_wilayah == "TINGKAT DESA (Master)":
        nama_target_rw = "TINGKAT DESA"
        rw_terpilih = "000"
        label_pimpinan = "Nama Kepala Desa *"
        label_alamat = "Alamat Kantor Desa / Sekretariat"
    else:
        nama_target_rw = pilihan_wilayah
        rw_terpilih = pilihan_wilayah.replace("RW ", "")
        label_pimpinan = "Nama Ketua RW *"
        label_alamat = "Alamat Lengkap Sekretariat RW"
else:
    rw_terpilih = rw_akses
    nama_target_rw = f"RW {rw_terpilih}"
    label_pimpinan = "Nama Ketua RW *"
    label_alamat = "Alamat Lengkap Sekretariat RW"
    st.info(f"Anda sedang mengonfigurasi profil induk untuk **{nama_target_rw}**")

# Mengambil data profil jika sudah ada sebelumnya
try:
    res_rw = supabase.table("profil_rt").select("*").eq("nama_rt_rw", nama_target_rw).execute()
    profil_rw = res_rw.data[0] if res_rw.data else {}
except:
    profil_rw = {}

with st.form("form_profil_rw"):
    st.subheader(f"Identitas {nama_target_rw}")
    
    desa_kelurahan = st.text_input("Nama Desa / Kelurahan *", value=profil_rw.get("kelurahan", "Desa Maju Bersama"))
    
    col1, col2 = st.columns(2)
    with col1:
        kecamatan = st.text_input("Kecamatan", value=profil_rw.get("kecamatan", ""))
    with col2:
        kota = st.text_input("Kabupaten / Kota", value=profil_rw.get("kota", ""))
        
    st.markdown("---")
    st.subheader("Detail Sekretariat & Pimpinan")
    alamat_sekretariat = st.text_area(label_alamat, value=profil_rw.get("alamat_sekretariat", ""))
    kode_pos = st.text_input("Kode Pos", value=profil_rw.get("kode_pos", ""))
    nama_ketua_rw = st.text_input(label_pimpinan, value=profil_rw.get("nama_ketua_rt", "")) 
    
    teks_tombol = "Simpan & Sinkronkan ke Seluruh Data" if nama_target_rw == "TINGKAT DESA" else "Simpan & Sinkronkan ke Data RT"
    submit_profil = st.form_submit_button(teks_tombol, type="primary")
    
    if submit_profil:
        if not desa_kelurahan or not nama_ketua_rw:
            st.warning("⚠️ Mohon lengkapi Nama Desa dan Nama Pimpinan.")
        else:
            with st.spinner("Sedang merakit profil dan menyebar data sinkronisasi..."):
                try:
                    # A. Menyiapkan Data Profil
                    data_rw_update = {
                        "nama_rt_rw": nama_target_rw,
                        "kelurahan": desa_kelurahan.title().strip(),
                        "kecamatan": kecamatan.title().strip(),
                        "kota": kota.title().strip(),
                        "kode_pos": kode_pos.strip(),
                        "alamat_sekretariat": alamat_sekretariat.title().strip(),
                        "nama_ketua_rt": nama_ketua_rw.title().strip(),
                        "rw": rw_terpilih,
                        "rt": "000" if nama_target_rw == "TINGKAT DESA" else ""
                    }
                    
                    # B. Simpan atau Perbarui Profil
                    if profil_rw:
                        supabase.table("profil_rt").update(data_rw_update).eq("nama_rt_rw", nama_target_rw).execute()
                    else:
                        supabase.table("profil_rt").insert(data_rw_update).execute()
                        
                    # C. LAKUKAN SINKRONISASI OTOMATIS
                    if nama_target_rw == "TINGKAT DESA":
                        # Update NAMA DESA ke semua baris di profil_rt agar sinkron dari atas ke bawah
                        supabase.table("profil_rt").update({
                            "kelurahan": desa_kelurahan.title().strip(),
                            "kecamatan": kecamatan.title().strip(),
                            "kota": kota.title().strip(),
                            "kode_pos": kode_pos.strip()
                        }).neq("nama_rt_rw", "x").execute()
                    else:
                        # Jika yang disimpan adalah RW, sinkronkan ke RT 001 - 005 di bawahnya
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
                                    "alamat_sekretariat": alamat_sekretariat.title().strip(), 
                                    "nama_ketua_rt": f"Ketua RT {rt_str}",
                                    "rt": rt_str,        
                                    "rw": rw_terpilih    
                                }
                                supabase.table("profil_rt").insert(data_rt_baru).execute()
                            
                    st.success(f"✅ Sempurna! Profil **{nama_target_rw}** berhasil disimpan dan disinkronkan.")
                    st.cache_data.clear() # Membersihkan cache agar sapaan Dashboard terganti otomatis
                except Exception as e:
                    st.error(f"⚠️ Terjadi kesalahan saat sinkronisasi profil: {e}")