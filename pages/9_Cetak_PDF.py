import streamlit as st
import pandas as pd
import datetime
from fpdf import FPDF
from supabase import create_client, Client
from menu import tampilkan_menu

# 1. Aturan Streamlit: set_page_config harus dipanggil paling awal!
st.set_page_config(page_title="Pusat Cetak Dokumen", page_icon="🖨️", layout="centered")

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# 2. Gembok Keamanan Multi-User
if "role" not in st.session_state:
    st.warning("⚠️ Akses Ditolak! Silakan login melalui halaman utama terlebih dahulu.")
    st.stop()

tampilkan_menu()
# ---------------------------

st.title("🖨️ Pusat Cetak Dokumen Resmi")
st.markdown("Cetak Surat Pengantar, Undangan Rapat, hingga Laporan Kegiatan dengan **Kop Surat Standar Pemerintahan**.")

# ==========================================
# MENGAMBIL DATA PROFIL YANG SINKRON
# ==========================================
role = st.session_state.get("role", "operator_rt")
rt_akses = st.session_state.get("rt_akses", "001")
rw_akses = st.session_state.get("rw_akses", "001")

@st.cache_data(ttl=5)
def load_profil_sinkron(role, rt_akses, rw_akses):
    try:
        if role == "super_admin":
            res = supabase.table("profil_rt").select("*").eq("nama_rt_rw", "TINGKAT DESA").execute()
        elif role == "admin_rw":
            res = supabase.table("profil_rt").select("*").eq("nama_rt_rw", f"RW {rw_akses}").execute()
        else:
            res = supabase.table("profil_rt").select("*").eq("nama_rt_rw", f"RT {rt_akses} / RW {rw_akses}").execute()
        return res.data[0] if res.data else None
    except:
        return None

profil = load_profil_sinkron(role, rt_akses, rw_akses)

if profil:
    nama_desa = profil.get('kelurahan') or profil.get('desa') or "Desa Maju Bersama"
    kecamatan = profil.get('kecamatan', 'Kecamatan')
    kota = profil.get('kota', 'Kabupaten/Kota')
    kode_pos = profil.get('kode_pos', '')
    alamat = profil.get('alamat_sekretariat', 'Alamat Sekretariat')
    nama_pejabat = profil.get('nama_ketua_rt', 'Nama Pimpinan')
else:
    nama_desa = "Desa Maju Bersama"
    kecamatan = "Kecamatan"
    kota = "Kabupaten/Kota"
    kode_pos = ""
    alamat = "Alamat Sekretariat"
    nama_pejabat = "Nama Pimpinan"

# PENENTUAN JABATAN & KOP SURAT BERDASARKAN ROLE
if role == "super_admin":
    jabatan_resmi = f"Kepala Desa"
    nama_wilayah_kop = f"PEMERINTAH DESA {nama_desa.upper()}"
elif role == "admin_rw":
    jabatan_resmi = f"Ketua RW {rw_akses}"
    nama_wilayah_kop = f"RUKUN WARGA (RW) {rw_akses}"
else:
    jabatan_resmi = f"Ketua RT {rt_akses}"
    nama_wilayah_kop = f"RUKUN TETANGGA (RT) {rt_akses} / RW {rw_akses}"

# Kamus Bulan Indonesia
bulan_indo = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}
hari_ini = datetime.date.today()
tgl_cetak = f"{hari_ini.day} {bulan_indo[hari_ini.month]} {hari_ini.year}"
tahun_ini = hari_ini.year

# ==========================================
# KELAS PDF MASTER (KOP SURAT)
# ==========================================
class PDFMaster(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 13)
        self.cell(w=0, h=6, text=f"PEMERINTAH KABUPATEN/KOTA {kota.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(w=0, h=6, text=f"KECAMATAN {kecamatan.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(w=0, h=6, text=f"DESA/KELURAHAN {nama_desa.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("helvetica", "B", 16)
        self.cell(w=0, h=8, text=nama_wilayah_kop, align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("helvetica", "", 10)
        teks_alamat = f"Sekretariat: {alamat}"
        if kode_pos: teks_alamat += f" | Kode Pos: {kode_pos}"
        self.cell(w=0, h=5, text=teks_alamat, align="C", new_x="LMARGIN", new_y="NEXT")
        
        y_pos = self.get_y() + 2 
        self.set_line_width(0.8) 
        self.line(10, y_pos, 200, y_pos)
        self.set_line_width(0.2) 
        self.line(10, y_pos + 1.2, 200, y_pos + 1.2)
        
        self.ln(10)

# ==========================================
# MEMBUAT 3 TAB MENU CETAK
# ==========================================
tab_pengantar, tab_undangan, tab_kegiatan = st.tabs(["✉️ Cetak Surat Kependudukan", "📅 Cetak Undangan Rapat", "📝 Cetak Laporan Kegiatan"])

# ---------------------------------------------------------
# TAB 1: SURAT PENGANTAR / KETERANGAN WARGA
# ---------------------------------------------------------
with tab_pengantar:
    st.subheader("Cetak Surat Keterangan / Pengantar")
    try:
        # Isolasi data surat berdasarkan hak akses
        df_p = pd.DataFrame(supabase.table("data_penduduk").select("nik, rt, rw").execute().data)
        res_surat = supabase.table("data_surat").select("*").execute()
        df_surat = pd.DataFrame(res_surat.data)
        
        if not df_surat.empty and not df_p.empty:
            df_surat = df_surat.merge(df_p, left_on='nik_pemohon', right_on='nik', how='left')
            if role == "admin_rw":
                df_surat = df_surat[df_surat['rw'] == rw_akses]
            elif role == "operator_rt":
                df_surat = df_surat[(df_surat['rt'] == rt_akses) & (df_surat['rw'] == rw_akses)]
                
    except Exception as e:
        st.error(f"Gagal mengambil data surat: {e}")
        df_surat = pd.DataFrame()

    if df_surat.empty:
        st.info("Belum ada riwayat pengajuan surat di wilayah Anda.")
    else:
        pilihan_surat = []
        for _, row in df_surat.iterrows():
            nik_pemohon = row.get('nik_pemohon', row.get('nik_x', ''))
            pilihan_surat.append(f"{row['id_surat']} - NIK: {nik_pemohon} - {row.get('jenis_surat', 'Surat')}")
            
        surat_terpilih = st.selectbox("Pilih dokumen yang akan dicetak:", pilihan_surat)
        id_target = int(surat_terpilih.split(" - ")[0])
        nik_target = surat_terpilih.split(" - NIK: ")[1].split(" - ")[0]
        jenis_surat = surat_terpilih.split(" - ")[2]
        
        detail_warga = supabase.table("data_penduduk").select("*").eq("nik", nik_target).execute().data
        data_pengajuan = df_surat[df_surat['id_surat'] == id_target].iloc[0]

        if detail_warga:
            warga = detail_warga[0]
            st.markdown("---")
            st.write(f"**Pemohon:** {warga.get('nama_lengkap', '')} | **Keperluan:** {data_pengajuan.get('keperluan', '-')}")
            
            # --- LOGIKA REDAKSI BERDASARKAN ROLE ---
            keperluan = data_pengajuan.get('keperluan', '-')
            
            if role == "super_admin":
                judul_cetak = jenis_surat.replace("Pengantar", "Keterangan").upper()
                nomor_surat = f"Nomor: {id_target:03}/DS-{nama_desa.replace(' ', '').upper()[:5]}/{tahun_ini}"
                paragraf_1 = f"Yang bertanda tangan di bawah ini, {jabatan_resmi}, Kecamatan {kecamatan}, Kabupaten/Kota {kota.title()}, dengan ini menerangkan bahwa:"
                paragraf_2 = f"Orang tersebut di atas adalah benar warga yang berdomisili dan tercatat di Desa/Kelurahan {nama_desa}. Surat keterangan ini dibuat dengan sebenar-benarnya untuk keperluan: {keperluan}."
                jenis_dokumen = "Surat Keterangan"
            
            elif role == "admin_rw":
                judul_cetak = jenis_surat.replace("Keterangan", "Pengantar").upper()
                nomor_surat = f"Nomor: {id_target:03}/RW-{rw_akses}/{tahun_ini}"
                paragraf_1 = f"Yang bertanda tangan di bawah ini, {jabatan_resmi}, Desa/Kelurahan {nama_desa}, Kecamatan {kecamatan}, dengan ini menerangkan bahwa:"
                paragraf_2 = f"Orang tersebut di atas adalah benar warga yang berdomisili di lingkungan wilayah RW {rw_akses}. Surat pengantar ini dibuat untuk keperluan: {keperluan}."
                jenis_dokumen = "Surat Pengantar"
            
            else: # operator_rt
                judul_cetak = jenis_surat.replace("Keterangan", "Pengantar").upper()
                nomor_surat = f"Nomor: {id_target:03}/RT-{rt_akses}/{tahun_ini}"
                paragraf_1 = f"Yang bertanda tangan di bawah ini, {jabatan_resmi} / RW {rw_akses}, Desa/Kelurahan {nama_desa}, Kecamatan {kecamatan}, dengan ini menerangkan bahwa:"
                paragraf_2 = f"Orang tersebut di atas adalah benar warga yang berdomisili di lingkungan RT {rt_akses} / RW {rw_akses}. Surat pengantar ini dibuat untuk keperluan: {keperluan}."
                jenis_dokumen = "Surat Pengantar"
            
            if st.button(f"📄 Rangkai {jenis_dokumen}", type="primary", width="stretch"):
                with st.spinner("Merangkai PDF..."):
                    pdf = PDFMaster()
                    pdf.add_page()

                    # Judul Surat
                    pdf.set_font("helvetica", "BU", 13)
                    pdf.cell(w=0, h=6, text=judul_cetak, align="C", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("helvetica", "", 11)
                    pdf.cell(w=0, h=6, text=nomor_surat, align="C", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(8)

                    # Paragraf 1 (Pembuka)
                    pdf.set_font("helvetica", "", 11)
                    pdf.multi_cell(w=0, h=6, text=paragraf_1, new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(5)

                    # Tabel Biodata
                    left_margin, col_width, row_height = 25, 45, 7
                    def row_data(label, value):
                        pdf.set_x(left_margin)
                        pdf.cell(w=col_width, h=row_height, text=label)
                        pdf.cell(w=5, h=row_height, text=":")
                        pdf.multi_cell(w=0, h=row_height, text=str(value), new_x="LMARGIN", new_y="NEXT")

                    row_data("Nama Lengkap", warga.get('nama_lengkap', ''))
                    row_data("NIK", warga.get('nik', ''))
                    row_data("No. KK", warga.get('no_kk', ''))
                    row_data("Tempat, Tgl Lahir", f"{warga.get('tempat_lahir', '')}, {warga.get('tanggal_lahir', '')}")
                    row_data("Jenis Kelamin", warga.get('jenis_kelamin', ''))
                    row_data("Pekerjaan", warga.get('pekerjaan', ''))
                    alamat_lengkap = f"{warga.get('jalan_kampung', '')}, RT {warga.get('rt', '')}/RW {warga.get('rw', '')}"
                    row_data("Alamat", alamat_lengkap)
                    pdf.ln(5)

                    # Paragraf 2 (Tujuan)
                    pdf.multi_cell(w=0, h=6, text=paragraf_2, new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(2)
                    pdf.multi_cell(w=0, h=6, text="Demikian surat ini dibuat agar dapat dipergunakan sebagaimana mestinya oleh instansi yang berwenang.", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(15)

                    # Bagian Tanda Tangan
                    pdf.set_x(120)
                    pdf.cell(w=0, h=6, text=f"{kota.title()}, {tgl_cetak}", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(5)
                    pdf.set_x(20)
                    pdf.cell(w=60, h=6, text="Pemohon,", align="C")
                    pdf.set_x(120)
                    pdf.cell(w=60, h=6, text=f"Mengetahui, {jabatan_resmi},", align="C", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(25) 
                    pdf.set_font("helvetica", "BU", 11) 
                    pdf.set_x(20)
                    pdf.cell(w=60, h=6, text=warga.get('nama_lengkap', ''), align="C")
                    pdf.set_x(120)
                    pdf.cell(w=60, h=6, text=nama_pejabat, align="C", new_x="LMARGIN", new_y="NEXT")

                    st.session_state["pdf_pengantar"] = bytes(pdf.output())
                    st.session_state["nama_file_pengantar"] = f"{jenis_dokumen.replace(' ', '_')}_{warga.get('nik', '')}.pdf"
                    st.success(f"✅ {jenis_dokumen} berhasil dirangkai! Silakan unduh.")

            if "pdf_pengantar" in st.session_state:
                st.download_button(label=f"📥 Download Dokumen PDF", data=st.session_state["pdf_pengantar"], file_name=st.session_state["nama_file_pengantar"], mime="application/pdf", width="stretch")

# ---------------------------------------------------------
# TAB 2: SURAT UNDANGAN
# ---------------------------------------------------------
with tab_undangan:
    st.subheader("Cetak Surat Undangan Resmi")
    st.write("Isi detail agenda di bawah ini untuk membuat surat undangan rapat/kegiatan.")
    
    with st.form("form_undangan"):
        col1, col2 = st.columns(2)
        with col1:
            no_surat = st.text_input("Nomor Surat", value=f"001/UND/WIL/{tahun_ini}")
            perihal = st.text_input("Perihal Undangan", value="Undangan Rapat Rutin Bulanan")
        with col2:
            tujuan = st.text_input("Ditujukan Kepada (Yth.)", value="Bapak/Ibu Warga")
            lampiran = st.text_input("Lampiran", value="-")
            
        st.markdown("---")
        st.write("**Detail Acara:**")
        col3, col4 = st.columns(2)
        with col3:
            tgl_acara = st.date_input("Tanggal Acara")
            waktu_acara = st.text_input("Waktu (Pukul)", value="19:30 WIB - Selesai")
        with col4:
            tempat_acara = st.text_input("Tempat Pelaksanaan", value="Posko / Balai Pertemuan")
            agenda = st.text_input("Agenda / Acara", value="Membahas Keamanan & Ketertiban Lingkungan")
            
        submit_undangan = st.form_submit_button("📄 Rangkai Dokumen Undangan", type="primary", width="stretch")
        
    if submit_undangan:
        with st.spinner("Memproses Surat Undangan..."):
            pdf = PDFMaster()
            pdf.add_page()
            
            pdf.set_font("helvetica", "", 11)
            
            pdf.cell(w=25, h=6, text="Nomor", align="L")
            pdf.cell(w=5, h=6, text=":", align="C")
            pdf.cell(w=90, h=6, text=no_surat, align="L")
            pdf.cell(w=0, h=6, text=f"{kota.title()}, {tgl_cetak}", align="R", new_x="LMARGIN", new_y="NEXT")
            
            pdf.cell(w=25, h=6, text="Lampiran", align="L")
            pdf.cell(w=5, h=6, text=":", align="C")
            pdf.cell(w=0, h=6, text=lampiran, align="L", new_x="LMARGIN", new_y="NEXT")
            
            pdf.cell(w=25, h=6, text="Perihal", align="L")
            pdf.cell(w=5, h=6, text=":", align="C")
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(w=0, h=6, text=perihal, align="L", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            
            pdf.ln(10)
            pdf.cell(w=0, h=6, text="Kepada Yth.", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(w=0, h=6, text=tujuan, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            pdf.cell(w=0, h=6, text=f"di Tempat", new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(10)
            pdf.multi_cell(w=0, h=6, text="Dengan hormat,\nPuji syukur senantiasa kita panjatkan ke hadirat Tuhan Yang Maha Esa. Bersama surat ini, kami selaku pengurus mengharap kehadiran Bapak/Ibu/Sdr/i pada acara yang akan diselenggarakan pada:", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
            tgl_str = f"{tgl_acara.day} {bulan_indo[tgl_acara.month]} {tgl_acara.year}"
            
            left_m, col_w, r_h = 30, 40, 7
            def row_agenda(label, value):
                pdf.set_x(left_m)
                pdf.cell(w=col_w, h=r_h, text=label)
                pdf.cell(w=5, h=r_h, text=":")
                pdf.set_font("helvetica", "B", 11)
                pdf.multi_cell(w=0, h=r_h, text=str(value), new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 11)

            row_agenda("Hari / Tanggal", tgl_str)
            row_agenda("Waktu", waktu_acara)
            row_agenda("Tempat", tempat_acara)
            row_agenda("Agenda Acara", agenda)
            
            pdf.ln(5)
            pdf.multi_cell(w=0, h=6, text="Mengingat pentingnya acara tersebut, kami sangat mengharapkan kehadiran Bapak/Ibu tepat pada waktunya. Demikian undangan ini kami sampaikan, atas perhatian dan kehadirannya kami ucapkan terima kasih.", new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(20)
            pdf.set_x(120)
            pdf.cell(w=60, h=6, text=f"{jabatan_resmi},", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(25)
            pdf.set_font("helvetica", "BU", 11)
            pdf.set_x(120)
            pdf.cell(w=60, h=6, text=nama_pejabat, align="C", new_x="LMARGIN", new_y="NEXT")
            
            st.session_state["pdf_undangan"] = bytes(pdf.output())
            st.success("✅ Surat Undangan berhasil dirangkai! Silakan unduh.")

    if "pdf_undangan" in st.session_state:
        st.download_button(label="📥 Download Surat Undangan", data=st.session_state["pdf_undangan"], file_name="Surat_Undangan.pdf", mime="application/pdf", width="stretch")

# ---------------------------------------------------------
# TAB 3: LAPORAN KEGIATAN
# ---------------------------------------------------------
with tab_kegiatan:
    st.subheader("Cetak Laporan Kegiatan / Notulensi")
    st.write("Buat laporan pertanggungjawaban singkat atau notulensi rapat.")
    
    with st.form("form_laporan"):
        nama_kegiatan = st.text_input("Nama / Judul Kegiatan", value="Laporan Kegiatan Kerja Bakti Warga")
        col1, col2 = st.columns(2)
        with col1:
            tgl_kegiatan = st.date_input("Tanggal Pelaksanaan")
        with col2:
            tempat_kegiatan = st.text_input("Tempat Pelaksanaan", value="Lingkungan Wilayah")
            
        deskripsi = st.text_area("Deskripsi / Rangkaian Kegiatan", value="1. Pembersihan area publik.\n2. Pemangkasan ranting pohon rawan tumbang.", height=120)
        hasil = st.text_area("Hasil yang Dicapai / Notulensi", value="Lingkungan menjadi lebih bersih. Kegiatan berjalan dengan lancar.", height=120)
        
        submit_laporan = st.form_submit_button("📄 Rangkai Dokumen Laporan", type="primary", width="stretch")
        
    if submit_laporan:
        with st.spinner("Memproses Laporan Kegiatan..."):
            pdf = PDFMaster()
            pdf.add_page()
            
            pdf.set_font("helvetica", "BU", 14)
            pdf.cell(w=0, h=8, text="LAPORAN PELAKSANAAN KEGIATAN", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 12)
            pdf.cell(w=0, h=6, text=nama_kegiatan.upper(), align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(10)
            
            tgl_str = f"{tgl_kegiatan.day} {bulan_indo[tgl_kegiatan.month]} {tgl_kegiatan.year}"
            
            def row_laporan(label, value):
                pdf.set_x(15)
                pdf.cell(w=40, h=6, text=label)
                pdf.cell(w=5, h=6, text=":")
                pdf.multi_cell(w=0, h=6, text=str(value), new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("helvetica", "B", 11)
            pdf.cell(w=0, h=7, text="A. WAKTU & TEMPAT PELAKSANAAN", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            
            row_laporan("Hari / Tanggal", tgl_str)
            row_laporan("Tempat", tempat_kegiatan)
            pdf.ln(5)
            
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(w=0, h=7, text="B. DESKRIPSI & RANGKAIAN KEGIATAN", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            pdf.set_x(15) 
            pdf.multi_cell(w=0, h=6, text=deskripsi, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(w=0, h=7, text="C. HASIL YANG DICAPAI", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", "", 11)
            pdf.set_x(15) 
            pdf.multi_cell(w=0, h=6, text=hasil, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(10)
            
            pdf.multi_cell(w=0, h=6, text="Demikian laporan pelaksanaan kegiatan ini dibuat dengan sebenar-benarnya untuk dapat dipergunakan dan dipertanggungjawabkan sebagaimana mestinya.", new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(15)
            pdf.set_x(120)
            pdf.cell(w=60, h=6, text=f"{kota.title()}, {tgl_cetak}", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_x(120)
            pdf.cell(w=60, h=6, text=f"Pembuat Laporan, {jabatan_resmi},", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(25)
            pdf.set_font("helvetica", "BU", 11)
            pdf.set_x(120)
            pdf.cell(w=60, h=6, text=nama_pejabat, align="C", new_x="LMARGIN", new_y="NEXT")
            
            st.session_state["pdf_laporan"] = bytes(pdf.output())
            st.success("✅ Laporan Kegiatan berhasil dirangkai! Silakan unduh.")

    if "pdf_laporan" in st.session_state:
        st.download_button(label="📥 Download Laporan Kegiatan", data=st.session_state["pdf_laporan"], file_name="Laporan_Kegiatan.pdf", mime="application/pdf", width="stretch")