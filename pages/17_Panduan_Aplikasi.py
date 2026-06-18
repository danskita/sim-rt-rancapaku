import streamlit as st
from menu import tampilkan_menu

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Panduan & Akun Demo", page_icon="📖", layout="centered")

# Gembok Keamanan
if "role" not in st.session_state:
    st.warning("⚠️ Akses Ditolak! Silakan login melalui halaman utama terlebih dahulu.")
    st.stop()

tampilkan_menu()
# ---------------------------

st.title("📖 Panduan Penggunaan & Akun Demo")
st.markdown("Halaman ini berisi ringkasan fitur aplikasi serta draf pesan promosi yang siap disebarkan ke grup WhatsApp warga atau jajaran pengurus.")

# ==========================================
# JENDELA 1: RINGKASAN FITUR APLIKASI
# ==========================================
with st.expander("🌟 Lihat Ringkasan Fitur Aplikasi SIM RT/RW", expanded=True):
    st.markdown("""
    * 📊 **Dashboard Pintar:** Memantau statistik jumlah warga, Kepala Keluarga (KK), serta grafik demografi secara otomatis dan *real-time*.
    * 👥 **Buku Warga & LAMPID:** Pencatatan biodata lengkap warga beserta mutasi kependudukan (Lahir, Mati, Pindah, Datang).
    * ✉️ **Layanan Surat & Bansos:** Membuat Surat Pengantar resmi dalam hitungan detik dan mendata Keluarga Penerima Manfaat (KPM) Bansos.
    * 🗂️ **Aset & Arsip Cloud:** Pendataan inventaris barang RT/RW serta penyimpanan berkas digital yang dilengkapi sistem *Auto-Arsip* PDF.
    * 🖨️ **Laporan Instan:** Mencetak rekapitulasi data menjadi dokumen PDF resmi yang sudah ber-Kop Surat dan ber-Logo Desa.
    * 💬 **Forum Diskusi & Multimedia:** Ruang obrolan interaktif ala WhatsApp khusus pengurus. Mendukung pengiriman foto, dokumen PDF, rekaman suara/video, hingga fitur pelacak status *Online* secara *real-time*.
    """)

# ==========================================
# JENDELA 2: INFORMASI AKUN DEMO
# ==========================================
with st.expander("🔐 Informasi Pola Akun & Password Pengurus", expanded=False):
    st.markdown("""
    Semua akun pengurus di wilayah Rancapaku sudah terdaftar di sistem dengan kata sandi seragam:
    * 🔑 **Password untuk SEMUA akun:** `123456`
    
    **Pola Penulisan Username:**
    1. **Ketua RW (RW 01 s/d 06):** Ketik huruf `rw` diikuti nomor RW. *(Contoh: `rw01`, `rw06`)*
    2. **Ketua RT (RT 01 s/d 05):** Ketik `Nomor RT/Nomor RW`. *(Contoh: `01/01`, `03/06`, `05/10`)*
    """)

# ==========================================
# JENDELA 3: TEKS PROMOSI WHATSAPP (SIAP COPY)
# ==========================================
st.markdown("---")
st.subheader("📢 Teks Promosi WhatsApp")
st.write("Bapak/Ibu bisa menyalin (*copy*) teks di bawah ini untuk disebarkan ke grup koordinasi jajaran RT/RW:")

# Teks draf promosi digabungkan di dalam kotak text_area agar mudah di-copy dalam 1 klik
teks_promosi_wa = """👑 Menjadi pengurus adalah tugas mulia, jangan biarkan tumpukan administrasi membuat Anda pusing 🤯. 

Mari beralih ke **Aplikasi SIM RT/RW Rancapaku** dan rasakan bedanya: 📱👇

☁️ **Anti Hilang:** Data warga & inventaris tersimpan aman di sistem cloud.
🖨️ **Anti Ribet:** Cetak Surat Pengantar otomatis dalam hitungan detik.
💬 **Anti Miskomunikasi:** Tersedia Forum Diskusi khusus pengurus ala WhatsApp! Bisa kirim foto, dokumen, rekaman suara, dan pantau siapa yang sedang Online.
⏱️ **Anti Lama:** Warga terlayani dengan cepat, pengurus pun tenang.

✨ *Kerja Cerdas, Layanan Tuntas, Arsip Jelas.* ✨

🚀 Tinggalkan cara lama, mari sentuh kemudahan di ujung jari Anda. 
🌐 **Klik tautan ini untuk mencoba:** https://sim-rt-rancapaku.streamlit.app/

🔐 **INFORMASI LOGIN KHUSUS PENGURUS** 🔐
Akun Bapak/Ibu sudah kami siapkan dan bisa langsung digunakan! 
🔑 **Password untuk SEMUA akun:** 123456

👤 **1. Khusus Akun Ketua RW (RW 01 s/d RW 10):**
• Username: Ketik huruf rw disambung Nomor RW
• *Contoh:* Bapak/Ibu dari RW 01 ➡️ ketik: rw01

👤 **2. Khusus Akun Ketua RT (RT 01 s/d 05):**
• Username: Ketik Nomor RT garis miring Nomor RW
• *Contoh:* RT 01 di wilayah RW 01 ➡️ ketik: 01/01
• *Contoh:* RT 03 di wilayah RW 06 ➡️ ketik: 03/06

Selamat mencoba dan mengeksplorasi kemudahan baru ini, Bapak/Ibu hebat! Jika ada kendala saat login, jangan sungkan untuk membalas pesan ini ya. 💪"""

st.text_area("Salin teks di bawah ini:", value=teks_promosi_wa, height=450)