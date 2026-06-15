import streamlit as st
import pandas as pd
from fpdf import FPDF
from supabase import create_client, Client
from datetime import datetime

# 1. Proteksi Hak Akses
if "role" not in st.session_state:
    st.warning("Silakan login terlebih dahulu.")
    st.stop()

# 2. Koneksi Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

st.title("🖨️ Cetak Laporan Resmi (PDF)")
st.write("Cetak dokumen rekapitulasi operasional desa/RT ber-Kop Surat.")

# 3. Pilihan Jenis Laporan
jenis_laporan = st.selectbox("Pilih Jenis Laporan yang akan dicetak:", [
    "1. Laporan Data Penduduk",
    "2. Laporan Pergerakan Warga (LAMPID)",
    "3. Laporan Layanan Surat",
    "4. Laporan Sarpras & Aset RT"
])

# 4. Tarik Data Profil untuk Kop Surat
try:
    if st.session_state["role"] == "super_admin":
        profil_res = supabase.table("profil_rt").select("*").execute()
    elif st.session_state["role"] == "admin_rw":
        profil_res = supabase.table("profil_rt").select("*").eq("rw", st.session_state["rw_akses"]).execute()
    else:
        profil_res = supabase.table("profil_rt").select("*").eq("rt", st.session_state["rt_akses"]).eq("rw", st.session_state["rw_akses"]).execute()
    
    profil_data = profil_res.data[0] if len(profil_res.data) > 0 else {}
except:
    profil_data = {}

if st.button("📄 Buat Dokumen PDF Sekarang", use_container_width=True):
    with st.spinner("Sedang menarik data dari database dan merangkai dokumen PDF..."):
        # Fungsi pembuat Kop Surat PDF
        class PDF(FPDF):
            def header(self):
                self.set_font("helvetica", "B", 14)
                nama_desa = profil_data.get("desa", "NAMA DESA")
                kecamatan = profil_data.get("kecamatan", "KECAMATAN")
                kota = profil_data.get("kota", "KABUPATEN/KOTA")
                self.cell(0, 7, f"PEMERINTAH {kota.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
                self.cell(0, 7, f"KECAMATAN {kecamatan.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
                self.cell(0, 7, f"DESA/KELURAHAN {nama_desa.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
                self.set_font("helvetica", "", 10)
                alamat = profil_data.get("alamat_sekretariat", "Alamat Sekretariat: ....................................")
                self.cell(0, 6, alamat, align="C", new_x="LMARGIN", new_y="NEXT")
                self.line(10, 38, 200, 38)
                self.line(10, 39, 200, 39)
                self.ln(10)

        pdf = PDF()
        pdf.add_page()
        
        # Penentuan Penandatangan Sesuai Jabatan
        pdf.set_font("helvetica", "B", 12)
        if st.session_state["role"] == "super_admin":
            wilayah_teks = "TINGKAT DESA"
            penandatangan = "Kepala Desa"
        elif st.session_state["role"] == "admin_rw":
            wilayah_teks = f"RW {st.session_state['rw_akses']}"
            penandatangan = f"Ketua RW {st.session_state['rw_akses']}"
        else:
            wilayah_teks = f"RT {st.session_state['rt_akses']} / RW {st.session_state['rw_akses']}"
            penandatangan = f"Ketua RT {st.session_state['rt_akses']}"

        # --- LOGIKA ISI PDF BERDASARKAN PILIHAN ---
        if "Penduduk" in jenis_laporan:
            pdf.cell(0, 10, f"LAPORAN REKAPITULASI PENDUDUK {wilayah_teks}", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            res = supabase.table("data_penduduk").select("*").execute()
            df = pd.DataFrame(res.data)
            # Filter berdasarkan role
            if st.session_state["role"] == "admin_rw":
                df = df[df['rw'] == st.session_state['rw_akses']]
            elif st.session_state["role"] == "operator_rt":
                df = df[(df['rt'] == st.session_state['rt_akses']) & (df['rw'] == st.session_state['rw_akses'])]
            
            pdf.set_font("helvetica", "", 11)
            pdf.cell(0, 6, f"Total Warga Terdaftar : {len(df)} Jiwa", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(10, 8, "No", border=1, align="C")
            pdf.cell(40, 8, "NIK", border=1, align="C")
            pdf.cell(80, 8, "Nama Lengkap", border=1, align="C")
            pdf.cell(20, 8, "L/P", border=1, align="C")
            pdf.cell(40, 8, "Pekerjaan", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            
            pdf.set_font("helvetica", "", 9)
            for i, row in df.iterrows():
                pdf.cell(10, 8, str(i+1), border=1, align="C")
                pdf.cell(40, 8, str(row.get('nik','')), border=1, align="C")
                pdf.cell(80, 8, str(row.get('nama_lengkap',''))[:35], border=1)
                jk = "L" if row.get('jenis_kelamin') == 'Laki-laki' else "P"
                pdf.cell(20, 8, jk, border=1, align="C")
                pdf.cell(40, 8, str(row.get('pekerjaan',''))[:15], border=1, align="C", new_x="LMARGIN", new_y="NEXT")

        elif "LAMPID" in jenis_laporan:
            pdf.cell(0, 10, f"LAPORAN PERGERAKAN WARGA (LAMPID) {wilayah_teks}", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            # Tarik data dari ke-4 tabel LAMPID
            lahir = supabase.table("data_lahir").select("*", count='exact').execute()
            mati = supabase.table("data_mati").select("*", count='exact').execute()
            pindah = supabase.table("data_pindah").select("*", count='exact').execute()
            datang = supabase.table("data_datang").select("*", count='exact').execute()
            
            pdf.set_font("helvetica", "", 12)
            pdf.cell(0, 8, f"1. Total Kelahiran Baru : {len(lahir.data)} Kasus", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"2. Total Kematian Warga : {len(mati.data)} Kasus", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"3. Total Warga Pindah Keluar : {len(pindah.data)} Kasus", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 8, f"4. Total Pendatang Baru : {len(datang.data)} Kasus", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(10)
            pdf.set_font("helvetica", "I", 10)
            pdf.cell(0, 6, "* Rincian detail nama warga untuk tiap kategori tersedia di Unduhan Excel pada menu Dashboard.", new_x="LMARGIN", new_y="NEXT")

        elif "Surat" in jenis_laporan:
            pdf.cell(0, 10, f"LAPORAN REKAPITULASI LAYANAN SURAT {wilayah_teks}", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            res = supabase.table("data_surat").select("*").execute()
            df = pd.DataFrame(res.data)
            
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(10, 8, "No", border=1, align="C")
            pdf.cell(40, 8, "Tanggal", border=1, align="C")
            pdf.cell(50, 8, "NIK Pemohon", border=1, align="C")
            pdf.cell(90, 8, "Jenis Surat / Keperluan", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            
            pdf.set_font("helvetica", "", 9)
            if not df.empty:
                for i, row in df.iterrows():
                    pdf.cell(10, 8, str(i+1), border=1, align="C")
                    tgl = str(row.get('created_at',''))[:10]
                    pdf.cell(40, 8, tgl, border=1, align="C")
                    pdf.cell(50, 8, str(row.get('nik','')), border=1, align="C")
                    pdf.cell(90, 8, str(row.get('keperluan',''))[:45], border=1, new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(190, 8, "Belum ada data surat di database.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

        elif "Aset" in jenis_laporan:
            pdf.cell(0, 10, f"LAPORAN INVENTARIS SARPRAS & ASET {wilayah_teks}", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            res = supabase.table("data_aset").select("*").execute()
            df = pd.DataFrame(res.data)
            
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(10, 8, "No", border=1, align="C")
            pdf.cell(60, 8, "Nama Barang", border=1, align="C")
            pdf.cell(30, 8, "Jumlah", border=1, align="C")
            pdf.cell(40, 8, "Kondisi", border=1, align="C")
            pdf.cell(50, 8, "Lokasi Penyimpanan", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            
            pdf.set_font("helvetica", "", 9)
            if not df.empty:
                for i, row in df.iterrows():
                    pdf.cell(10, 8, str(i+1), border=1, align="C")
                    pdf.cell(60, 8, str(row.get('nama_barang',''))[:30], border=1)
                    pdf.cell(30, 8, str(row.get('jumlah','')), border=1, align="C")
                    pdf.cell(40, 8, str(row.get('kondisi','')), border=1, align="C")
                    pdf.cell(50, 8, str(row.get('lokasi_penyimpanan',''))[:20], border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            else:
                pdf.cell(190, 8, "Belum ada data aset di database.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

        # Bagian Penutup & Tanda Tangan
        pdf.ln(20)
        pdf.set_font("helvetica", "", 11)
        kota = profil_data.get("kota", "Kota").title()
        tanggal = datetime.now().strftime("%d-%m-%Y")
        
        pdf.cell(130) # Geser ke kanan
        pdf.cell(60, 6, f"{kota}, {tanggal}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(130)
        pdf.cell(60, 6, penandatangan, align="C", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(20) # Jarak Tanda Tangan
        pdf.cell(130)
        pdf.set_font("helvetica", "B", 11)
        nama_pejabat = profil_data.get("nama_ketua_rt", "........................................")
        if st.session_state["role"] != "operator_rt":
             nama_pejabat = "........................................" 
        pdf.cell(60, 6, f"({nama_pejabat})", align="C", new_x="LMARGIN", new_y="NEXT")
        
        # Eksekusi Download PDF
        pdf_bytes = bytes(pdf.output())
        st.success("✅ Dokumen berhasil dirangkai!")
        st.download_button(
            label="⬇️ Unduh Dokumen PDF Sekarang",
            data=pdf_bytes,
            file_name=f"Laporan_{jenis_laporan[:8]}_{wilayah_teks}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )