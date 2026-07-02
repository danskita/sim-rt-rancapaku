import streamlit as st
import pandas as pd
from datetime import datetime
import io
import tempfile
import os
from fpdf import FPDF
from PIL import Image
from supabase import create_client, Client
from menu import tampilkan_menu

# ========================================================
# 1. KONFIGURASI HALAMAN WAJIB PALING ATAS
# ========================================================
st.set_page_config(
    page_title="Modul Proposal", 
    page_icon="🏢", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# Gembok Keamanan
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("⚠️ Akses Ditolak! Silakan login melalui halaman utama terlebih dahulu.")
    st.stop()

# Ambil profil akses yang sedang login
role = st.session_state.get("role", "operator_rt")
rt_akses = st.session_state.get("rt_akses", "001")
rw_akses = st.session_state.get("rw_akses", "001")

tampilkan_menu()
# ---------------------------

st.title("🏢 Pembuatan Proposal Bantuan")
st.markdown("Fasilitas otomatis untuk mencetak Proposal Permohonan Bantuan atau Kegiatan (RUTILAHU / Infrastruktur RT & RW).")
st.markdown("---")

# ========================================================
# FUNGSI CETAK PDF: 1. RUTILAHU
# ========================================================
def buat_dokumen_pdf_rutilahu(instansi_tujuan, kota_kab, tanggal, nama_sasaran, ttl, pekerjaan, alamat, kontak_warga, deskripsi, total_rab, rab_df, nama_desa, kades_nama, nomor_rw, ketua_rw, kontak_rw, foto_kondisi):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- BAGIAN A: SURAT PENGANTAR ---
    pdf.add_page()
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "PROPOSAL", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 6, "PERMOHONAN BANTUAN PERBAIKAN RUMAH TIDAK LAYAK HUNI (RUTILAHU)", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    pdf.cell(0, 6, "A. SURAT PENGANTAR / PERMOHONAN", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, f"{kota_kab.title()}, {tanggal}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(25, 6, "Nomor")
    pdf.cell(5, 6, ":")
    pdf.cell(0, 6, f"01/RTLH/RW-{nomor_rw}/{datetime.now().month}/{datetime.now().year}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(25, 6, "Lampiran")
    pdf.cell(5, 6, ":")
    pdf.cell(0, 6, "1 (Satu) Bendel", new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(25, 6, "Perihal")
    pdf.cell(5, 6, ":")
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, "Permohonan Bantuan Perbaikan Rumah Tidak Layak Huni (Rutilahu)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    
    pdf.ln(5)
    pdf.multi_cell(0, 6, f"Kepada Yth.\n{instansi_tujuan}\nDi -\n        {kota_kab.title()}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.multi_cell(0, 6, "Dengan hormat,", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 6, "Puji syukur kita panjatkan kehadirat Tuhan Yang Maha Esa atas segala limpahan rahmat dan karunia-Nya. Melalui surat ini, kami sampaikan bahwa di wilayah kami terdapat warga yang memiliki tempat tinggal dalam kondisi sangat memprihatinkan dan tidak layak huni, serta keluarga tersebut termasuk dalam golongan masyarakat berpenghasilan rendah (Keluarga Pra-Sejahtera).", align='J', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.multi_cell(0, 6, "Sehubungan dengan hal tersebut, kami mewakili warga memohon bantuan dana perbaikan Rumah Tidak Layak Huni (Rutilahu) untuk warga kami:", align='J', new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(3)
    data_warga = [
        ("Nama", nama_sasaran),
        ("Tempat/Tgl Lahir", ttl),
        ("Pekerjaan", pekerjaan),
        ("Alamat Lengkap", alamat),
        ("No. HP/WA", kontak_warga if kontak_warga else "-")
    ]
    for label, value in data_warga:
        pdf.set_x(25)
        pdf.cell(35, 6, label)
        pdf.cell(5, 6, ":")
        pdf.multi_cell(0, 6, str(value), new_x="LMARGIN", new_y="NEXT")
        
    pdf.ln(3)
    pdf.multi_cell(0, 6, "Sebagai bahan pertimbangan Bapak/Ibu, bersama ini kami lampirkan proposal dan kelengkapan administrasi lainnya.", align='J', new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 6, "Demikian surat permohonan ini kami buat. Atas perhatian dan bantuan Bapak/Ibu, kami ucapkan terima kasih.", align='J', new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(15)
    y_ttd = pdf.get_y()
    
    pdf.set_xy(20, y_ttd)
    pdf.multi_cell(70, 6, f"Mengetahui,\nKepala Desa {nama_desa.title()}\n\n\n\n\n({kades_nama})", align='C')
    
    pdf.set_xy(120, y_ttd)
    kontak_text = f"\nHP/WA: {kontak_rw}" if kontak_rw else ""
    pdf.multi_cell(70, 6, f"Pengaju,\nKetua RW {nomor_rw}\n\n\n\n\n({ketua_rw}){kontak_text}", align='C', new_x="LMARGIN", new_y="NEXT")

    # --- BAGIAN B: ISI PROPOSAL ---
    pdf.add_page()
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "B. ISI PROPOSAL", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(3)
    pdf.cell(0, 6, "1. Latar Belakang", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(0, 6, "Rumah merupakan kebutuhan pokok dasar bagi manusia sebagai tempat bernaung, berlindung, dan berkumpul bersama keluarga. Namun, kondisi perekonomian yang terbatas membuat sebagian masyarakat tidak mampu membangun atau memperbaiki rumahnya agar memenuhi standar kelayakan, kesehatan, dan keamanan.", align='J', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.multi_cell(0, 6, f"Bapak/Ibu {nama_sasaran} adalah warga Desa {nama_desa.title()} yang bekerja sebagai {pekerjaan} dengan penghasilan yang tidak menentu dan hanya cukup untuk memenuhi kebutuhan makan sehari-hari. Saat ini, kondisi rumah beliau sangat memprihatinkan dengan rincian sebagai berikut:", align='J', new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(2)
    for line in deskripsi.split('\n'):
        if line.strip():
            pdf.multi_cell(0, 6, line.strip(), align='J', new_x="LMARGIN", new_y="NEXT")
            
    pdf.ln(3)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "2. Maksud dan Tujuan", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    
    tujuan_list = [
        f"Membantu meringankan beban keluarga Bapak/Ibu {nama_sasaran} untuk mendapatkan tempat tinggal yang layak, aman, dan sehat.",
        f"Meningkatkan kualitas hidup dan kesejahteraan keluarga warga Desa {nama_desa.title()}.",
        "Mencegah risiko rumah roboh akibat kondisi material yang sudah rapuh."
    ]
    for tj in tujuan_list:
        pdf.cell(7, 6, "-")
        pdf.multi_cell(0, 6, tj, align='J', new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "3. Rencana Anggaran Biaya (RAB)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, "Berikut adalah perkiraan kebutuhan biaya untuk perbaikan rumah tersebut:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(10, 8, "No", border=1, align='C')
    pdf.cell(80, 8, "Uraian Kebutuhan", border=1, align='C')
    pdf.cell(45, 8, "Harga Satuan (Rp)", border=1, align='C')
    pdf.cell(45, 8, "Jumlah Harga (Rp)", border=1, align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 10)
    for i, row in rab_df.iterrows():
        pdf.cell(10, 8, str(i + 1), border=1, align='C')
        pdf.cell(80, 8, str(row['Uraian Kebutuhan'])[:45], border=1, align='L')
        pdf.cell(45, 8, f"{row['Harga Satuan (Rp)']:,.0f}".replace(",", "."), border=1, align='R')
        pdf.cell(45, 8, f"{row['Jumlah Harga (Rp)']:,.0f}".replace(",", "."), border=1, align='R', new_x="LMARGIN", new_y="NEXT")
        
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(135, 8, "TOTAL KEBUTUHAN (Rp)  ", border=1, align='R')
    pdf.cell(45, 8, f"{total_rab:,.0f}".replace(",", "."), border=1, align='R', new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(3)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "4. Penutup", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(0, 6, "Demikian proposal permohonan bantuan perbaikan Rumah Tidak Layak Huni (Rutilahu) ini kami susun. Kami sangat mengharapkan uluran tangan dan kebijakan dari Bapak/Ibu agar warga kami dapat tinggal di rumah yang sehat dan layak.", align='J', new_x="LMARGIN", new_y="NEXT")

    # --- BAGIAN C: LAMPIRAN FOTO ---
    if foto_kondisi:
        pdf.add_page()
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "LAMPIRAN DOKUMENTASI FOTO", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(5)
        
        y_pos_atas = 30
        y_pos_bawah = 155
        
        for i, foto in enumerate(foto_kondisi):
            if i % 2 == 0 and i != 0:
                pdf.add_page()
                pdf.set_font("helvetica", "B", 12)
                pdf.cell(0, 8, "LAMPIRAN DOKUMENTASI FOTO (Lanjutan)", new_x="LMARGIN", new_y="NEXT", align="C")
                pdf.ln(5)
            
            try:
                img = Image.open(foto).convert("RGB")
                y_target = y_pos_atas if i % 2 == 0 else y_pos_bawah
                pdf.image(img, x=25, y=y_target, w=160, h=110)
            except Exception as e:
                pass

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp_path = tmp.name
        
    with open(tmp_path, "rb") as f:
        pdf_bytes = f.read()
        
    os.remove(tmp_path)
    return pdf_bytes

# ========================================================
# FUNGSI CETAK PDF: 2. KEGIATAN RT/RW
# ========================================================
def buat_dokumen_pdf_rtrw(instansi_tujuan, kota_kab, tanggal, nama_kegiatan, latar_belakang, tujuan_kegiatan, sasaran_kegiatan, total_rab, rab_df, nama_desa, kades_nama, nomor_rw, nomor_rt, ketua_rt, ketua_rw, foto_kondisi):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- BAGIAN A: SURAT PENGANTAR ---
    pdf.add_page()
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "PROPOSAL", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 6, str(nama_kegiatan).upper(), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    pdf.cell(0, 6, "A. SURAT PENGANTAR / PERMOHONAN", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, f"{kota_kab.title()}, {tanggal}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(25, 6, "Nomor")
    pdf.cell(5, 6, ":")
    wilayah_surat = f"RW-{nomor_rw}" if nomor_rt == "-" else f"RT-{nomor_rt}/RW-{nomor_rw}"
    pdf.cell(0, 6, f"01/PROP/{wilayah_surat}/{datetime.now().month}/{datetime.now().year}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(25, 6, "Lampiran")
    pdf.cell(5, 6, ":")
    pdf.cell(0, 6, "1 (Satu) Bendel", new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(25, 6, "Perihal")
    pdf.cell(5, 6, ":")
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, f"Permohonan Bantuan Dana {nama_kegiatan}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    
    pdf.ln(5)
    pdf.multi_cell(0, 6, f"Kepada Yth.\n{instansi_tujuan}\nDi -\n        {kota_kab.title()}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.multi_cell(0, 6, "Dengan hormat,", align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 6, f"Puji syukur kehadirat Tuhan Yang Maha Esa atas segala rahmat-Nya. Bersama surat ini, kami sampaikan bahwa pengurus beserta warga bermaksud untuk melaksanakan kegiatan/pengadaan infrastruktur yaitu {nama_kegiatan}.", align='J', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.multi_cell(0, 6, "Sehubungan dengan keterbatasan dana swadaya warga, maka dengan kerendahan hati kami memohon bantuan dana dari Bapak/Ibu untuk kelancaran kegiatan tersebut. Sebagai bahan pertimbangan, bersama ini kami lampirkan proposal rincian kegiatan dan Rencana Anggaran Biaya (RAB).", align='J', new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.multi_cell(0, 6, "Demikian surat permohonan ini kami sampaikan. Atas perhatian, dukungan, dan bantuan Bapak/Ibu, kami ucapkan terima kasih.", align='J', new_x="LMARGIN", new_y="NEXT")
    
    # 3 TANDA TANGAN (RT, RW, KADES)
    pdf.ln(15)
    y_ttd = pdf.get_y()
    
    pdf.set_xy(10, y_ttd)
    pdf.multi_cell(60, 6, f"Ketua Panitia / RT {nomor_rt}\n\n\n\n\n({ketua_rt})", align='C')
    
    pdf.set_xy(75, y_ttd)
    pdf.multi_cell(60, 6, f"Mengetahui,\nKetua RW {nomor_rw}\n\n\n\n\n({ketua_rw})", align='C')
    
    pdf.set_xy(140, y_ttd)
    pdf.multi_cell(60, 6, f"Menyetujui,\nKepala Desa {nama_desa.title()}\n\n\n\n\n({kades_nama})", align='C', new_x="LMARGIN", new_y="NEXT")

    # --- BAGIAN B: ISI PROPOSAL ---
    pdf.add_page()
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "B. ISI PROPOSAL", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(3)
    pdf.cell(0, 6, "1. Latar Belakang", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    for line in latar_belakang.split('\n'):
        if line.strip():
            pdf.multi_cell(0, 6, line.strip(), align='J', new_x="LMARGIN", new_y="NEXT")
            
    pdf.ln(3)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "2. Maksud dan Tujuan", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    for line in tujuan_kegiatan.split('\n'):
        if line.strip():
            pdf.multi_cell(0, 6, line.strip(), align='J', new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "3. Sasaran Kegiatan", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(0, 6, sasaran_kegiatan, align='J', new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "4. Rencana Anggaran Biaya (RAB)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, "Estimasi rincian anggaran yang dibutuhkan adalah sebagai berikut:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(10, 8, "No", border=1, align='C')
    pdf.cell(80, 8, "Uraian Kebutuhan", border=1, align='C')
    pdf.cell(45, 8, "Harga Satuan (Rp)", border=1, align='C')
    pdf.cell(45, 8, "Jumlah Harga (Rp)", border=1, align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "", 10)
    for i, row in rab_df.iterrows():
        pdf.cell(10, 8, str(i + 1), border=1, align='C')
        pdf.cell(80, 8, str(row['Uraian Kebutuhan'])[:45], border=1, align='L')
        pdf.cell(45, 8, f"{row['Harga Satuan (Rp)']:,.0f}".replace(",", "."), border=1, align='R')
        pdf.cell(45, 8, f"{row['Jumlah Harga (Rp)']:,.0f}".replace(",", "."), border=1, align='R', new_x="LMARGIN", new_y="NEXT")
        
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(135, 8, "TOTAL KEBUTUHAN (Rp)  ", border=1, align='R')
    pdf.cell(45, 8, f"{total_rab:,.0f}".replace(",", "."), border=1, align='R', new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "5. Penutup", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(0, 6, "Demikian proposal ini disusun sebagai acuan pelaksanaan kegiatan dan bahan pertimbangan bagi pihak-pihak yang bersedia berpartisipasi dan memberikan bantuan. Atas kerjasamanya, kami haturkan terima kasih.", align='J', new_x="LMARGIN", new_y="NEXT")

    # --- BAGIAN C: LAMPIRAN FOTO ---
    if foto_kondisi:
        pdf.add_page()
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "LAMPIRAN DOKUMENTASI", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(5)
        
        y_pos_atas = 30
        y_pos_bawah = 155
        
        for i, foto in enumerate(foto_kondisi):
            if i % 2 == 0 and i != 0:
                pdf.add_page()
                pdf.set_font("helvetica", "B", 12)
                pdf.cell(0, 8, "LAMPIRAN DOKUMENTASI (Lanjutan)", new_x="LMARGIN", new_y="NEXT", align="C")
                pdf.ln(5)
            
            try:
                img = Image.open(foto).convert("RGB")
                y_target = y_pos_atas if i % 2 == 0 else y_pos_bawah
                pdf.image(img, x=25, y=y_target, w=160, h=110)
            except Exception as e:
                pass

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp_path = tmp.name
        
    with open(tmp_path, "rb") as f:
        pdf_bytes = f.read()
        
    os.remove(tmp_path)
    return pdf_bytes

# ========================================================
# ANTARMUKA (UI) UTAMA
# ========================================================
kategori = st.selectbox("Pilih Kategori Pembuatan Proposal *", ["-- Pilih Kategori --", "1. Perbaikan RUTILAHU Warga", "2. Kegiatan / Infrastruktur RT & RW"])

# TATA LETAK UNTUK RUTILAHU
if kategori == "1. Perbaikan RUTILAHU Warga":
    with st.form("form_proposal_rutilahu"):
        st.write("### Form Proposal RUTILAHU")
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Info Pengaju", "👤 Data Penerima", "📍 Kondisi & RAB", "📎 Lampiran"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                nama_desa = st.text_input("Nama Desa *", placeholder="Contoh: Sukamaju")
                kades_nama = st.text_input("Nama Kepala Desa *")
                instansi_tujuan = st.text_input("Ditujukan Kepada (Instansi) *", placeholder="Contoh: BAZNAS / Dinas Sosial")
            with col2:
                nomor_rw = st.text_input("Nomor RW Pengaju *", value=rw_akses)
                ketua_rw = st.text_input("Nama Ketua RW *")
                kontak_rw = st.text_input("No. HP / WA Ketua RW *")
                kota_kab = st.text_input("Kota / Kabupaten *")

        with tab2:
            nama_sasaran = st.text_input("Nama Pemilik Rumah (Penerima Bantuan) *")
            ttl = st.text_input("Tempat, Tanggal Lahir *", placeholder="Contoh: Bandung, 17 Agustus 1975")
            pekerjaan = st.text_input("Pekerjaan *", placeholder="Contoh: Buruh Tani / Serabutan")
            kontak_warga = st.text_input("No. HP / WA Warga (Opsional)")
            alamat = st.text_area("Alamat Lengkap (RT/RW, Jalan, dll) *")

        with tab3:
            st.info("Gambarkan rincian kerusakan untuk dimasukkan ke bagian Latar Belakang Proposal.")
            deskripsi = st.text_area("Rincian Kerusakan (Atap, Dinding, Lantai, dll) *", 
                                     value="- Atap: Bocor di berbagai sisi dan penyangga lapuk.\n- Dinding: Bilik bambu berlubang.\n- Lantai: Masih berupa tanah liat.", height=120)
            
            st.markdown("---")
            st.write("**Rencana Anggaran Biaya (RAB)**")
            rab_default = pd.DataFrame([
                {"Uraian Kebutuhan": "Semen", "Harga Satuan (Rp)": 55000, "Jumlah Harga (Rp)": 1100000},
                {"Uraian Kebutuhan": "Pasir", "Harga Satuan (Rp)": 800000, "Jumlah Harga (Rp)": 800000},
                {"Uraian Kebutuhan": "Batu Bata / Batako", "Harga Satuan (Rp)": 3500, "Jumlah Harga (Rp)": 7000000},
                {"Uraian Kebutuhan": "Ongkos Tukang", "Harga Satuan (Rp)": 300000, "Jumlah Harga (Rp)": 3000000},
            ])
            # Menggunakan parameter use_container_width=True karena st.data_editor belum sepenuhnya support width="stretch"
            rab_diisi = st.data_editor(rab_default, num_rows="dynamic", use_container_width=True)

        with tab4:
            st.write("Silakan unggah foto asli kondisi rumah warga.")
            foto_kondisi = st.file_uploader("Upload Foto Kondisi (Bisa lebih dari satu) *", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
            pernyataan = st.checkbox("Saya menyatakan bahwa data yang diinputkan adalah benar dan dapat dipertanggungjawabkan.")
            
        st.markdown("---")
        submitted = st.form_submit_button("💾 Simpan & Susun PDF Proposal RUTILAHU", width="stretch", type="primary")

    if submitted:
        if not nama_desa or not kades_nama or not ketua_rw or not nama_sasaran or not alamat or not instansi_tujuan:
            st.error("❌ Gagal! Pastikan semua kolom bertanda bintang (*) sudah diisi.")
        elif not foto_kondisi:
            st.error("❌ Anda wajib mengunggah minimal 1 Foto Kondisi Rumah di Tab Lampiran.")
        elif not pernyataan:
            st.warning("⚠️ Centang kotak pernyataan kebenaran data terlebih dahulu.")
        else:
            total_rab = rab_diisi['Jumlah Harga (Rp)'].sum()
            tanggal_sekarang = datetime.now().strftime("%d %B %Y")
            
            with st.spinner("Membangun dokumen PDF..."):
                file_pdf = buat_dokumen_pdf_rutilahu(
                    instansi_tujuan, kota_kab, tanggal_sekarang, nama_sasaran, ttl, 
                    pekerjaan, alamat, kontak_warga, deskripsi, total_rab, rab_diisi, 
                    nama_desa, kades_nama, nomor_rw, ketua_rw, kontak_rw, foto_kondisi
                )
            
            st.success("✅ Proposal RUTILAHU berhasil dibuat!")
            st.download_button("⬇️ Unduh PDF Proposal RUTILAHU", data=file_pdf, file_name=f"Proposal_RUTILAHU_{nama_sasaran.replace(' ', '_')}.pdf", mime="application/pdf", width="stretch")

# TATA LETAK UNTUK KEGIATAN RT/RW
elif kategori == "2. Kegiatan / Infrastruktur RT & RW":
    with st.form("form_proposal_rtrw"):
        st.write("### Form Proposal Kegiatan / Infrastruktur")
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Info Pengaju", "📝 Detail Kegiatan", "💰 RAB", "📎 Lampiran"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                nama_desa = st.text_input("Nama Desa *")
                kades_nama = st.text_input("Nama Kepala Desa *")
                instansi_tujuan = st.text_input("Ditujukan Kepada (Instansi/Donatur) *", placeholder="Contoh: Bapak Bupati / Donatur")
            with col2:
                nomor_rw = st.text_input("Nomor RW *", value=rw_akses)
                nomor_rt = st.text_input("Nomor RT (Isi '-' jika pengaju adalah RW)", value=rt_akses)
                ketua_rw = st.text_input("Nama Ketua RW *")
                ketua_rt = st.text_input("Nama Ketua RT / Ketua Panitia *")
                kota_kab = st.text_input("Kota / Kabupaten *")

        with tab2:
            nama_kegiatan = st.text_input("Nama / Judul Kegiatan *", placeholder="Contoh: Pembangunan Gapura Utama RW 05")
            latar_belakang = st.text_area("Latar Belakang *", value="Infrastruktur yang memadai adalah kunci kenyamanan warga...", height=100)
            tujuan_kegiatan = st.text_area("Maksud dan Tujuan *", value="- Meningkatkan keamanan lingkungan.\n- Memperindah tata ruang wilayah.", height=100)
            sasaran_kegiatan = st.text_input("Sasaran / Target Kegiatan *", placeholder="Contoh: Seluruh warga RW 05 dan pengguna jalan")

        with tab3:
            st.write("**Rencana Anggaran Biaya (RAB)**")
            rab_default_kegiatan = pd.DataFrame([
                {"Uraian Kebutuhan": "Material Bahan Bangunan", "Harga Satuan (Rp)": 5000000, "Jumlah Harga (Rp)": 5000000},
                {"Uraian Kebutuhan": "Konsumsi Gotong Royong", "Harga Satuan (Rp)": 500000, "Jumlah Harga (Rp)": 1500000},
            ])
            rab_diisi_kegiatan = st.data_editor(rab_default_kegiatan, num_rows="dynamic", use_container_width=True)

        with tab4:
            st.write("Silakan unggah foto pendukung (Lokasi kegiatan, desain, dll).")
            foto_kondisi_keg = st.file_uploader("Upload Foto Dokumentasi *", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
            pernyataan_keg = st.checkbox("Saya menyatakan bahwa rincian kegiatan ini diajukan dengan sebenar-benarnya.")
            
        st.markdown("---")
        submitted_keg = st.form_submit_button("💾 Simpan & Susun PDF Proposal Kegiatan", width="stretch", type="primary")

    if submitted_keg:
        if not nama_kegiatan or not latar_belakang or not tujuan_kegiatan or not instansi_tujuan:
            st.error("❌ Gagal! Pastikan Nama Kegiatan, Tujuan, Latar Belakang, dan Tujuan Instansi sudah diisi.")
        elif not foto_kondisi_keg:
            st.error("❌ Anda wajib mengunggah minimal 1 Foto Lokasi/Kegiatan di Tab Lampiran.")
        elif not pernyataan_keg:
            st.warning("⚠️ Centang kotak pernyataan terlebih dahulu.")
        else:
            total_rab_keg = rab_diisi_kegiatan['Jumlah Harga (Rp)'].sum()
            tanggal_sekarang = datetime.now().strftime("%d %B %Y")
            
            with st.spinner("Membangun dokumen PDF..."):
                file_pdf_keg = buat_dokumen_pdf_rtrw(
                    instansi_tujuan, kota_kab, tanggal_sekarang, nama_kegiatan, latar_belakang, 
                    tujuan_kegiatan, sasaran_kegiatan, total_rab_keg, rab_diisi_kegiatan, 
                    nama_desa, kades_nama, nomor_rw, nomor_rt, ketua_rt, ketua_rw, foto_kondisi_keg
                )
            
            st.success("✅ Proposal Kegiatan berhasil dibuat!")
            st.download_button("⬇️ Unduh PDF Proposal Kegiatan", data=file_pdf_keg, file_name=f"Proposal_{nama_kegiatan.replace(' ', '_')}.pdf", mime="application/pdf", width="stretch")