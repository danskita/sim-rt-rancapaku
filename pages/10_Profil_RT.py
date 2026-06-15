import streamlit as st
from supabase import create_client, Client
from menu import tampilkan_menu

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

st.set_page_config(page_title="Profil Wilayah", page_icon="🏢", layout="centered")

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
st.markdown("Atur identitas tingkat RW di sini. **Data Desa/Kecamatan/Kota akan otomatis disinkronkan ke seluruh RT (001-005)** di bawah naungan RW yang dipilih.")

# Menentukan RW mana yang sedang diedit
if role == "super_admin":
    pilihan_rw = [f"{i:03}" for i in range(1, 11)]
    rw_terpilih = st.selectbox("Pilih RW yang akan dikonfigurasi (Khusus Kepala Desa)", pilihan_rw)
else:
    rw_terpilih = rw_akses
    st.info(f"Anda sedang mengonfigurasi profil induk untuk **RW {rw_terpilih}**")

nama_target_rw = f"RW {rw_terpilih}"

# Mengambil data profil RW jika sudah ada sebelumnya
try:
    res_rw = supabase.table("profil_rt").select("*").eq("nama_rt_rw", nama_target_rw).execute()
    profil_rw = res_rw.data[0] if res_rw.data else {}
except:
    profil_rw = {}

with st.form("form_profil_rw"):
    st.subheader(f"Identitas Induk {nama_target_rw}")
    
    desa_kelurahan = st.text_input("Nama Desa / Kelurahan *", value=profil_rw.get("kelurahan", "Desa Maju Bersama"))
    
    col1, col2 = st.columns(2)
    with col1:
        kecamatan = st.text_input("Kecamatan", value=profil_rw.get("kecamatan", ""))
    with col2:
        kota = st.text_input("Kabupaten / Kota", value=profil_rw.get("kota", ""))
        
    st.markdown("---")
    st.subheader("Detail Sekretariat & Pengurus RW")
    alamat_sekretariat = st.text_area("Alamat Lengkap Sekretariat RW", value=profil_rw.get("alamat_sekretariat", ""))
    kode_pos = st.text_input("Kode Pos", value=profil_rw.get("kode_pos", ""))
    nama_ketua_rw = st.text_input("Nama Ketua RW *", value=profil_rw.get("nama_ketua_rt", "")) 
    
    submit_profil = st.form_submit_button("Simpan & Sinkronkan ke Data RT", type="primary")
    
    if submit_profil:
        if not desa_kelurahan or not nama_ketua_rw:
            st.warning("⚠️ Mohon lengkapi Nama Desa dan Nama Ketua RW.")
        else:
            with st.spinner("Sedang merakit profil RW dan menyebar data sinkronisasi ke seluruh RT..."):
                try:
                    # A. Menyiapkan Data Profil RW (Induk)
                    data_rw_update = {
                        "nama_rt_rw": nama_target_rw,
                        "kelurahan": desa_kelurahan.title().strip(),
                        "kecamatan": kecamatan.title().strip(),
                        "kota": kota.title().strip(),
                        "kode_pos": kode_pos.strip(),
                        "alamat_sekretariat": alamat_sekretariat.title().strip(),
                        "nama_ketua_rt": nama_ketua_rw.title().strip()
                    }
                    
                    # B. Simpan atau Perbarui Profil RW
                    if profil_rw:
                        supabase.table("profil_rt").update(data_rw_update).eq("nama_rt_rw", nama_target_rw).execute()
                    else:
                        supabase.table("profil_rt").insert(data_rw_update).execute()
                        
                    # C. LAKUKAN SINKRONISASI OTOMATIS KE RT 001 - 005
                    for i in range(1, 6):
                        rt_str = f"{i:03}"
                        nama_rt_target = f"RT {rt_str} / RW {rw_terpilih}"
                        
                        # Cek apakah RT ini sudah punya profil sendiri atau belum
                        res_rt = supabase.table("profil_rt").select("id").eq("nama_rt_rw", nama_rt_target).execute()
                        
                        if res_rt.data:
                            # Jika RT sudah ada, KITA HANYA UPDATE DESA/KECAMATAN/KOTA SAJA.
                            # Kita TIDAK menimpa Nama Ketua RT-nya agar data spesifik mereka tidak hilang.
                            supabase.table("profil_rt").update({
                                "kelurahan": desa_kelurahan.title().strip(),
                                "kecamatan": kecamatan.title().strip(),
                                "kota": kota.title().strip(),
                                "kode_pos": kode_pos.strip()
                            }).eq("nama_rt_rw", nama_rt_target).execute()
                        else:
                            # Jika RT belum ada di database, buatkan profil dasarnya secara otomatis!
                            data_rt_baru = {
                                "nama_rt_rw": nama_rt_target,
                                "kelurahan": desa_kelurahan.title().strip(),
                                "kecamatan": kecamatan.title().strip(),
                                "kota": kota.title().strip(),
                                "kode_pos": kode_pos.strip(),
                                "alamat_sekretariat": alamat_sekretariat.title().strip(), # Turunan dari alamat RW
                                "nama_ketua_rt": f"Ketua RT {rt_str}" # Placeholder sementara
                            }
                            supabase.table("profil_rt").insert(data_rt_baru).execute()
                            
                    st.success(f"✅ Sempurna! Profil **{nama_target_rw}** berhasil disimpan. Data Desa/Kelurahan telah otomatis didistribusikan ke RT 001 hingga RT 005.")
                except Exception as e:
                    st.error(f"⚠️ Terjadi kesalahan saat sinkronisasi profil: {e}")