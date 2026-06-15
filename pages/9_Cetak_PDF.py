import streamlit as st
import pandas as pd
import datetime
from fpdf import FPDF
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

st.set_page_config(page_title="Cetak PDF Formal", page_icon="🖨️", layout="centered")

st.title("🖨️ Cetak Dokumen Resmi (PDF)")
st.markdown("Halaman ini digunakan untuk mencetak Surat Pengantar dan Dokumen Formal lainnya sesuai standar administrasi dengan format PDF.")

# ==========================================
# MENGAMBIL DATA PROFIL RT UNTUK KOP SURAT
# ==========================================
@st.cache_data(ttl=10)
def load_profil_rt():
    try:
        res = supabase.table("profil_rt").select("*").execute()
        return res.data[0] if res.data else None
    except:
        return None

profil = load_profil_rt()

# Menyiapkan variabel fallback jika profil belum diisi
nama_rt = profil['nama_rt_rw'] if profil else "PENGURUS RUKUN TETANGGA (RT)"
kelurahan = profil.get('kelurahan', 'Kelurahan') if profil else "Kelurahan"
kecamatan = profil.get('kecamatan', 'Kecamatan') if profil else "Kecamatan"
kota = profil.get('kota', 'Kota') if profil else "Kota"
kode_pos = profil.get('kode_pos', '') if profil else ""
alamat = profil.get('alamat_sekretariat', 'Alamat Sekretariat') if profil else "Alamat Sekretariat"
ketua_rt = profil.get('nama_ketua_rt', 'Ketua RT') if profil else "Ketua RT"

kel_kec_kota = f"Desa/Kelurahan {kelurahan}, Kecamatan {kecamatan}, {kota}"

tab_surat, tab_laporan = st.tabs(["✉️ Cetak Surat Pengantar", "📊 Laporan Demografi (Segera)"])

# ==========================================
# TAB 1: CETAK SURAT PENGANTAR (PDF)
# ==========================================
with tab_surat:
    st.subheader("Daftar Pengajuan Surat Warga")
    
    # 1. Ambil data surat dari database
    try:
        res_surat = supabase.table("data_surat").select("*").execute()
        df_surat = pd.DataFrame(res_surat.data)
    except Exception as e:
        st.error(f"Gagal mengambil data surat: {e}")
        df_surat = pd.DataFrame()

    if df_surat.empty:
        st.info("Belum ada data pengajuan surat di sistem.")
    else:
        # 2. Buat Dropdown untuk memilih surat mana yang akan di-print
        pilihan_surat = []
        for _, row in df_surat.iterrows():
            pilihan_surat.append(f"{row['id_surat']} - NIK: {row['nik_pemohon']} - {row['jenis_surat']}")
            
        surat_terpilih = st.selectbox("Pilih surat yang ingin dicetak:", pilihan_surat)
        
        id_target = int(surat_terpilih.split(" - ")[0])
        nik_target = surat_terpilih.split(" - NIK: ")[1].split(" - ")[0]
        jenis_surat = surat_terpilih.split(" - ")[2]
        
        detail_warga = supabase.table("data_penduduk").select("*").eq("nik", nik_target).execute().data
        data_pengajuan = df_surat[df_surat['id_surat'] == id_target].iloc[0]

        if detail_warga:
            warga = detail_warga[0]
            
            st.markdown("---")
            st.write(f"**Pratinjau Pemohon:** {warga.get('nama_lengkap', '')}")
            st.write(f"**Keperluan:** {data_pengajuan['keperluan']}")
            
            if not profil:
                st.warning("⚠️ Profil RT belum diisi. Kop surat akan menggunakan data bawaan (default). Silakan isi menu **Profil RT** terlebih dahulu.")

            if st.button("📄 Buat Dokumen PDF", type="primary"):
                with st.spinner("Merangkai dokumen PDF..."):
                    
                    # --- KELAS UNTUK MENDESAIN TEMPLATE PDF ---
                    class PDFSurat(FPDF):
                        def header(self):
                            # KOP SURAT DINAMIS (Berdasarkan Database)
                            self.set_font("helvetica", "B", 14)
                            self.cell(w=0, h=6, txt=nama_rt.upper(), align="C", ln=1)
                            self.set_font("helvetica", "", 12)
                            self.cell(w=0, h=6, txt=kel_kec_kota, align="C", ln=1)
                            self.set_font("helvetica", "I", 10)
                            
                            teks_alamat = f"Alamat Sekretariat: {alamat}"
                            if kode_pos:
                                teks_alamat += f", Kode Pos: {kode_pos}"
                                
                            self.cell(w=0, h=5, txt=teks_alamat, align="C", ln=1)
                            # Garis bawah Kop Surat
                            self.line(10, 28, 200, 28)
                            self.line(10, 29, 200, 29)
                            self.ln(10)

                    # Inisialisasi PDF
                    pdf = PDFSurat()
                    pdf.add_page()

                    # JUDUL SURAT & NOMOR
                    pdf.set_font("helvetica", "BU", 12)
                    pdf.cell(w=0, h=6, txt=jenis_surat.upper(), align="C", ln=1)
                    pdf.set_font("helvetica", "", 11)
                    tahun_ini = datetime.date.today().year
                    pdf.cell(w=0, h=6, txt=f"Nomor: 001/RT/RW/{tahun_ini}", align="C", ln=1)
                    pdf.ln(10)

                    # KALIMAT PEMBUKA DINAMIS
                    pdf.set_font("helvetica", "", 11)
                    pembuka = f"Yang bertanda tangan di bawah ini, Ketua {nama_rt}, {kelurahan}, Kecamatan {kecamatan}, dengan ini menerangkan bahwa:"
                    pdf.multi_cell(w=0, h=6, txt=pembuka)
                    pdf.ln(5)

                    # BLOK IDENTITAS WARGA (Sesuai Standar SIAK)
                    left_margin = 25
                    col_width = 45
                    row_height = 7

                    def row_data(label, value):
                        pdf.set_x(left_margin)
                        pdf.cell(w=col_width, h=row_height, txt=label)
                        pdf.cell(w=5, h=row_height, txt=":")
                        pdf.multi_cell(w=0, h=row_height, txt=str(value))

                    row_data("Nama Lengkap", warga.get('nama_lengkap', ''))
                    row_data("NIK", warga.get('nik', ''))
                    row_data("Nomor KK", warga.get('no_kk', ''))
                    row_data("Tempat, Tgl Lahir", f"{warga.get('tempat_lahir', '')}, {warga.get('tanggal_lahir', '')}")
                    row_data("Jenis Kelamin", warga.get('jenis_kelamin', ''))
                    row_data("Agama", warga.get('agama', ''))
                    row_data("Pekerjaan", warga.get('pekerjaan', ''))
                    
                    alamat_lengkap = f"{warga.get('jalan_kampung', '')}, RT {warga.get('rt', '')}/RW {warga.get('rw', '')}"
                    row_data("Alamat", alamat_lengkap)

                    pdf.ln(5)

                    # BLOK KEPERLUAN & PENUTUP
                    keperluan = data_pengajuan['keperluan']
                    penutup1 = f"Orang tersebut di atas adalah benar warga yang berdomisili di lingkungan {nama_rt}. Surat pengantar ini dibuat untuk keperluan: {keperluan}."
                    pdf.multi_cell(w=0, h=6, txt=penutup1)
                    pdf.ln(2)
                    
                    penutup2 = "Demikian surat keterangan/pengantar ini dibuat agar dapat dipergunakan sebagaimana mestinya oleh instansi yang berwenang."
                    pdf.multi_cell(w=0, h=6, txt=penutup2)
                    pdf.ln(15)

                    # BLOK TANDA TANGAN KETUA RT DINAMIS
                    tgl_cetak = datetime.date.today().strftime('%d-%m-%Y')
                    pdf.set_x(120)
                    pdf.cell(w=0, h=6, txt=f"Dikeluarkan di : {kota}", ln=1)
                    pdf.set_x(120)
                    pdf.cell(w=0, h=6, txt=f"Pada tanggal  : {tgl_cetak}", ln=1)
                    pdf.ln(5)

                    pdf.set_x(20)
                    pdf.cell(w=60, h=6, txt="Pemohon,", align="C")
                    pdf.set_x(120)
                    pdf.cell(w=60, h=6, txt=f"Ketua {nama_rt},", align="C", ln=1)

                    pdf.ln(25) # Jarak kosong untuk tanda tangan pena

                    pdf.set_font("helvetica", "BU", 11)
                    pdf.set_x(20)
                    pdf.cell(w=60, h=6, txt=warga.get('nama_lengkap', ''), align="C")
                    pdf.set_x(120)
                    pdf.cell(w=60, h=6, txt=ketua_rt, align="C", ln=1)

                    # --- SIMPAN DAN UNDUH PDF ---
                    pdf_bytes = bytes(pdf.output())

                    st.success("✅ Dokumen PDF berhasil dirangkai menggunakan Profil RT Anda!")
                    
                    # Tombol unduh file PDF
                    nama_file = f"Surat_Pengantar_{warga.get('nama_lengkap', '').replace(' ', '_')}.pdf"
                    st.download_button(
                        label="📥 Download Surat PDF",
                        data=pdf_bytes,
                        file_name=nama_file,
                        mime="application/pdf"
                    )

# ==========================================
# TAB 2: LAPORAN (PENYEMPURNAAN BERIKUTNYA)
# ==========================================
with tab_laporan:
    st.info("Fitur cetak Laporan Formal Bulanan format PDF sedang disiapkan.")