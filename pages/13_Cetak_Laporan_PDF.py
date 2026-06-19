import streamlit as st
import pandas as pd
import requests
import os
from fpdf import FPDF
from datetime import datetime
from supabase import create_client, Client
from menu import tampilkan_menu

# ========================================================
# 1. KONFIGURASI HALAMAN WAJIB PALING ATAS (Hanya Satu Kali)
# ========================================================
st.set_page_config(
    page_title="Cetak Laporan PDF", 
    page_icon="🖨️", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Proteksi Hak Akses Multi-User
if "role" not in st.session_state:
    st.warning("⚠️ Silakan login terlebih dahulu.")
    st.stop()

# Menampilkan Sidebar Menu
tampilkan_menu()

# 3. Koneksi Supabase
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

st.title("🖨️ Pusat Cetak & Pratinjau Laporan")
st.write("Pilih jenis laporan untuk melihat pratinjau data secara langsung sebelum mencetaknya ke dokumen PDF resmi.")

# Pilihan Jenis Laporan
jenis_laporan = st.selectbox("Pilih Jenis Laporan yang akan dicetak:", [
    "1. Laporan Data Penduduk",
    "2. Laporan Pergerakan Warga (LAMPID)",
    "3. Laporan Layanan Surat",
    "4. Laporan Penerima Bantuan Sosial (Bansos)",
    "5. Laporan Sarpras & Aset RT"
])

# ==========================================
# MENGAMBIL DATA PROFIL YANG SINKRON
# ==========================================
role = st.session_state.get("role")
rt_akses = st.session_state.get("rt_akses", "")
rw_akses = st.session_state.get("rw_akses", "")

try:
    if role == "super_admin":
        res_prof = supabase.table("profil_rt").select("*").eq("nama_rt_rw", "TINGKAT DESA").execute()
    elif role == "admin_rw":
        res_prof = supabase.table("profil_rt").select("*").eq("nama_rt_rw", f"RW {rw_akses}").execute()
    else:
        res_prof = supabase.table("profil_rt").select("*").eq("nama_rt_rw", f"RT {rt_akses} / RW {rw_akses}").execute()
    
    profil_data = res_prof.data[0] if res_prof.data else {}
except:
    profil_data = {}

# Sinkronisasi Variabel Kop
nama_desa = profil_data.get('kelurahan') or profil_data.get('desa') or "Desa Maju Bersama"
kecamatan = profil_data.get('kecamatan', 'Kecamatan')
kota = profil_data.get('kota', 'Kabupaten/Kota')
alamat = profil_data.get('alamat_sekretariat', 'Alamat Sekretariat')
kode_pos = profil_data.get('kode_pos', '')
penandatangan_nama = profil_data.get('nama_ketua_rt', '........................................')

if role == "super_admin":
    wilayah_teks = "TINGKAT DESA"
    penandatangan_jabatan = "Kepala Desa"
elif role == "admin_rw":
    wilayah_teks = f"RW {rw_akses}"
    penandatangan_jabatan = f"Ketua RW {rw_akses}"
else:
    wilayah_teks = f"RT {rt_akses} / RW {rw_akses}"
    penandatangan_jabatan = f"Ketua RT {rt_akses}"

st.markdown("---")

# ==========================================
# MESIN SINKRONISASI LOGO OTOMATIS
# ==========================================
@st.cache_data(ttl=300) 
def unduh_logo_sinkron():
    try:
        url_logo = supabase.storage.from_("arsip_digital").get_public_url("logo_desa_resmi.png")
        respon = requests.get(url_logo)
        if respon.status_code == 200:
            with open("logo_temp_laporan.png", "wb") as f:
                f.write(respon.content)
            return "logo_temp_laporan.png"
    except:
        return None
    return None

# ==========================================
# LOGIKA TARIK DATA & PRATINJAU LIVE DI LAYAR
# ==========================================
df_preview = pd.DataFrame()

if "Penduduk" in jenis_laporan:
    st.subheader(f"🔍 Pratinjau Live: Data Penduduk ({wilayah_teks})")
    res = supabase.table("data_penduduk").select("*").execute()
    df_preview = pd.DataFrame(res.data)
    if role == "admin_rw":
        df_preview = df_preview[df_preview['rw'] == rw_akses]
    elif role == "operator_rt":
        df_preview = df_preview[(df_preview['rt'] == rt_akses) & (df_preview['rw'] == rw_akses)]
    
    if not df_preview.empty:
        st.dataframe(df_preview[['nik', 'no_kk', 'nama_lengkap', 'jenis_kelamin', 'pekerjaan', 'rt', 'rw']], width="stretch")
    else:
        st.info("ℹ️ Tidak ada data penduduk untuk wilayah Anda.")

elif "LAMPID" in jenis_laporan:
    st.subheader(f"🔍 Pratinjau Live: Data Pergerakan (LAMPID)")
    st.write("Ringkasan jumlah kasus pergerakan warga saat ini:")
    
    lahir = supabase.table("data_lahir").select("*").execute()
    df_l = pd.DataFrame(lahir.data)
    mati = supabase.table("data_mati").select("*").execute()
    df_m = pd.DataFrame(mati.data)
    pindah = supabase.table("data_pindah").select("*").execute()
    df_p = pd.DataFrame(pindah.data)
    datang = supabase.table("data_datang").select("*").execute()
    df_d = pd.DataFrame(datang.data)
    
    if role == "operator_rt":
        if 'rt' in df_l.columns: df_l = df_l[df_l['rt'] == rt_akses]
        if 'rt' in df_m.columns: df_m = df_m[df_m['rt'] == rt_akses]
        if 'rt' in df_p.columns: df_p = df_p[df_p['rt'] == rt_akses]
        if 'rt' in df_d.columns: df_d = df_d[df_d['rt'] == rt_akses]

    summary_data = {
        "Kategori Pergerakan": ["Kelahiran Baru", "Kematian Warga", "Warga Pindah Keluar", "Pendatang Baru"],
        "Jumlah Kasus (Jiwa)": [len(df_l), len(df_m), len(df_p), len(df_d)]
    }
    df_preview = pd.DataFrame(summary_data)
    st.table(df_preview)

elif "Surat" in jenis_laporan:
    st.subheader(f"🔍 Pratinjau Live: Riwayat Layanan Surat ({wilayah_teks})")
    res = supabase.table("data_surat").select("*").execute()
    df_preview = pd.DataFrame(res.data)
    
    if not df_preview.empty:
        st.dataframe(df_preview[['id_surat', 'created_at', 'nik_pemohon', 'jenis_surat', 'keperluan']], width="stretch")
    else:
        st.info("ℹ️ Belum ada riwayat pengajuan surat.")

elif "Bansos" in jenis_laporan:
    st.subheader(f"🔍 Pratinjau Live: Daftar Penerima Bansos ({wilayah_teks})")
    try:
        res = supabase.table("data_bansos").select("*").execute()
        df_preview = pd.DataFrame(res.data)
        
        if not df_preview.empty:
            if 'rw' in df_preview.columns and role == "admin_rw":
                df_preview = df_preview[df_preview['rw'] == rw_akses]
            elif role == "operator_rt":
                if 'rt' in df_preview.columns and 'rw' in df_preview.columns:
                    df_preview = df_preview[(df_preview['rt'] == rt_akses) & (df_preview['rw'] == rw_akses)]
            
            kolom_pilihan = []
            
            if 'nik_penerima' in df_preview.columns: kolom_pilihan.append('nik_penerima')
            elif 'nik' in df_preview.columns: kolom_pilihan.append('nik')
            
            if 'nama_lengkap' in df_preview.columns: kolom_pilihan.append('nama_lengkap')
            elif 'nama' in df_preview.columns: kolom_pilihan.append('nama')
            
            if 'jenis_bansos' in df_preview.columns: kolom_pilihan.append('jenis_bansos')
            elif 'nama_bansos' in df_preview.columns: kolom_pilihan.append('nama_bansos')
            elif 'bantuan' in df_preview.columns: kolom_pilihan.append('bantuan')
            
            if len(kolom_pilihan) == 0:
                kolom_pilihan = df_preview.columns.tolist()
                
            kolom_pilihan = list(dict.fromkeys(kolom_pilihan))
            st.dataframe(df_preview[kolom_pilihan], width="stretch")
        else:
            st.info("ℹ️ Database penerima bantuan sosial (Bansos) masih kosong.")
    except Exception as e:
        st.error(f"Gagal memuat pratinjau bansos: {e}")

elif "Aset" in jenis_laporan:
    st.subheader(f"🔍 Pratinjau Live: Inventaris Sarpras & Aset ({wilayah_teks})")
    res = supabase.table("data_aset").select("*").execute()
    df_preview = pd.DataFrame(res.data)
    
    if not df_preview.empty:
        if role == "admin_rw" and 'rw' in df_preview.columns:
            df_preview = df_preview[df_preview['rw'] == rw_akses]
        elif role == "operator_rt" and 'rt' in df_preview.columns and 'rw' in df_preview.columns:
            df_preview = df_preview[(df_preview['rt'] == rt_akses) & (df_preview['rw'] == rw_akses)]

        kolom_nama = 'nama_aset' if 'nama_aset' in df_preview.columns else 'nama_barang'
        kolom_jml = 'jumlah' if 'jumlah' in df_preview.columns else 'qty'
        kolom_kndsi = 'kondisi' if 'kondisi' in df_preview.columns else 'status'
        
        kolom_tampil = [kol_n for kol_n in [kolom_nama, kolom_jml, kolom_kndsi, 'lokasi_penyimpanan'] if kol_n in df_preview.columns]
        st.dataframe(df_preview[kolom_tampil], width="stretch")
    else:
        st.info("ℹ️ Database aset kosong.")

st.markdown("---")

# ==========================================
# TOMBOL EKSEKUSI CETAK PDF
# ==========================================
if st.button("🖨️ Cetak ke PDF Resmi Sekarang", type="primary", width="stretch"):
    if df_preview.empty and "LAMPID" not in jenis_laporan and role != "super_admin":
        st.error("❌ Gagal mencetak! Tidak ada data yang tersedia untuk dimuat ke dalam dokumen PDF.")
    else:
        with st.spinner("Sedang merangkai lembar PDF resmi..."):
            
            class PDF(FPDF):
                def header(self):
                    # KOP SURAT HANYA MUNCUL DI HALAMAN PERTAMA (HALAMAN 1)
                    if self.page_no() == 1:
                        # --- FITUR MENAMPILKAN LOGO ---
                        logo_path = unduh_logo_sinkron()
                        if logo_path and os.path.exists(logo_path):
                            self.image(logo_path, x=15, y=10, w=22)
                            
                        self.set_font("helvetica", "B", 14)
                        self.cell(0, 7, f"PEMERINTAH KABUPATEN/KOTA {kota.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
                        self.cell(0, 7, f"KECAMATAN {kecamatan.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
                        self.cell(0, 7, f"DESA/KELURAHAN {nama_desa.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
                        self.set_font("helvetica", "", 10)
                        
                        teks_alt = f"Alamat Sekretariat: {alamat}"
                        if kode_pos: teks_alt += f", Kode Pos: {kode_pos}"
                        
                        self.cell(0, 6, teks_alt, align="C", new_x="LMARGIN", new_y="NEXT")
                        
                        # Garis kop surat
                        y_pos = self.get_y() + 2
                        self.set_line_width(0.8)
                        self.line(10, y_pos, 200, y_pos)
                        self.set_line_width(0.2)
                        self.line(10, y_pos + 1.2, 200, y_pos + 1.2)
                        
                        self.ln(10)
                    else:
                        # Memberikan jarak margin atas pada halaman kedua dan seterusnya
                        # agar tabel tidak menabrak ujung atas kertas
                        self.ln(15)

            pdf = PDF()
            pdf.add_page()
            pdf.set_font("helvetica", "B", 12)

            # =========================================================================
            # 1. MODUL: LAPORAN DATA PENDUDUK (DEMOGRAFI KOMPREHENSIF)
            # =========================================================================
            if "Penduduk" in jenis_laporan:
                if role == "operator_rt":
                    # --- LEVEL RT: CETAK RINCIAN DETAIL DATA WARGA ---
                    pdf.cell(0, 10, f"LAPORAN RINCIAN DETAIL DATA PENDUDUK", align="C", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("helvetica", "", 11)
                    pdf.cell(0, 6, f"WILAYAH: RT {rt_akses} / RW {rw_akses}", align="C", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(5)

                    res = supabase.table("data_penduduk").select("*").eq("rw", rw_akses).eq("rt", rt_akses).order("nama_lengkap").execute()
                    df_warga = pd.DataFrame(res.data)

                    if not df_warga.empty:
                        pdf.set_font("helvetica", "B", 9)
                        pdf.set_fill_color(220, 230, 241) 
                        
                        # Total Width: 10+35+35+50+25+35 = 190mm
                        w_no, w_nik, w_kk, w_nama, w_jk, w_kerja = 10, 35, 35, 50, 25, 35
                        pdf.cell(w_no, 8, "No", border=1, align="C", fill=True)
                        pdf.cell(w_nik, 8, "NIK", border=1, align="C", fill=True)
                        pdf.cell(w_kk, 8, "No. KK", border=1, align="C", fill=True)
                        pdf.cell(w_nama, 8, "Nama Lengkap", border=1, align="C", fill=True)
                        pdf.cell(w_jk, 8, "L/P", border=1, align="C", fill=True)
                        pdf.cell(w_kerja, 8, "Pekerjaan", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
                        
                        pdf.set_font("helvetica", "", 9)
                        for i, row_data in enumerate(df_warga.to_dict(orient="records"), 1):
                            nama_pendek = str(row_data.get('nama_lengkap', ''))[:24]
                            jk_singkat = "L" if row_data.get('jenis_kelamin') == "Laki-laki" else "P"
                            kerja_teks = str(row_data.get('pekerjaan', '-'))

                            pdf.cell(w_no, 7, str(i), border=1, align="C")
                            pdf.cell(w_nik, 7, str(row_data.get('nik', '')), border=1, align="C")
                            pdf.cell(w_kk, 7, str(row_data.get('no_kk', '')), border=1, align="C")
                            pdf.cell(w_nama, 7, nama_pendek, border=1, align="L")
                            pdf.cell(w_jk, 7, jk_singkat, border=1, align="C")
                            pdf.cell(w_kerja, 7, kerja_teks[:18], border=1, align="L", new_x="LMARGIN", new_y="NEXT")
                            
                        pdf.ln(5)
                        pdf.set_font("helvetica", "I", 9)
                        pdf.cell(0, 6, f"Total data tercetak: {len(df_warga)} Jiwa.", new_x="LMARGIN", new_y="NEXT")
                    else:
                        pdf.cell(190, 8, "Tidak ada data rincian warga di RT ini.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

                elif role in ["admin_rw", "super_admin"]:
                    # --- LEVEL RW & DESA: CETAK REKAPITULASI STATISTIK DEMOGRAFI ---
                    judul_laporan = "LAPORAN STATISTIK DEMOGRAFI TINGKAT RW" if role == "admin_rw" else "LAPORAN MASTER DEMOGRAFI TINGKAT DESA"
                    pdf.cell(0, 10, judul_laporan, align="C", new_x="LMARGIN", new_y="NEXT")
                    pdf.set_font("helvetica", "", 11)
                    cakupan = f"RW {rw_akses}" if role == "admin_rw" else "SATU DESA"
                    pdf.cell(0, 6, f"WILAYAH CAKUPAN: {cakupan}", align="C", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(5)

                    res = supabase.table("data_penduduk").select("*").execute()
                    df_all = pd.DataFrame(res.data)

                    if not df_all.empty:
                        if role == "admin_rw":
                            df_all = df_all[df_all['rw'] == rw_akses]

                        if not df_all.empty:
                            df_all['tanggal_lahir'] = pd.to_datetime(df_all['tanggal_lahir'], errors='coerce')
                            sekarang = pd.Timestamp(datetime.now())
                            df_all['usia'] = (sekarang - df_all['tanggal_lahir']).dt.days // 365
                            
                            def kelompok_usia(umur):
                                if pd.isna(umur): return "Tidak Diketahui"
                                if umur <= 5: return "1. Balita (0-5 Thn)"
                                elif umur <= 12: return "2. Anak-anak (6-12 Thn)"
                                elif umur <= 17: return "3. Remaja (13-17 Thn)"
                                elif umur <= 59: return "4. Dewasa (18-59 Thn)"
                                else: return "5. Lansia (60+ Thn)"
                                
                            df_all['Kategori Usia'] = df_all['usia'].apply(kelompok_usia)

                            res_bansos = supabase.table("data_bansos").select("nik_penerima").execute()
                            df_b = pd.DataFrame(res_bansos.data)
                            list_penerima = df_b['nik_penerima'].tolist() if not df_b.empty else []
                            df_all['Status Bansos'] = df_all['nik'].apply(lambda x: "Penerima Bansos Aktif" if x in list_penerima else "Bukan Penerima Bansos")

                            if role == "super_admin":
                                df_all['Wilayah'] = "RW " + df_all['rw'] + " / RT " + df_all['rt']
                            else:
                                df_all['Wilayah'] = "RT " + df_all['rt']

                            def gambar_tabel_demografi(judul_tabel, nama_kolom_df):
                                if pdf.get_y() > 220: 
                                    pdf.add_page()
                                    
                                pdf.set_font("helvetica", "B", 10)
                                pdf.set_fill_color(200, 215, 235)
                                pdf.cell(0, 8, judul_tabel, new_x="LMARGIN", new_y="NEXT")
                                
                                # PERBAIKAN: Total Width disesuaikan menjadi 190mm (15+135+40)
                                pdf.cell(15, 7, "No", border=1, align="C", fill=True)
                                pdf.cell(135, 7, "Kategori / Kelompok", border=1, align="C", fill=True)
                                pdf.cell(40, 7, "Jumlah (Jiwa)", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
                                
                                pdf.set_font("helvetica", "", 10)
                                
                                if nama_kolom_df in ['Wilayah', 'Kategori Usia']:
                                    rekap = df_all[nama_kolom_df].value_counts().sort_index()
                                else:
                                    rekap = df_all[nama_kolom_df].fillna('Tidak Diketahui / Belum Bekerja').value_counts()

                                for idx, (kategori, jumlah) in enumerate(rekap.items(), 1):
                                    pdf.cell(15, 7, str(idx), border=1, align="C")
                                    pdf.cell(135, 7, str(kategori)[:65], border=1) # Diperpanjang agar tidak terpotong
                                    pdf.cell(40, 7, str(jumlah), border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                                
                                pdf.set_font("helvetica", "B", 10)
                                pdf.set_fill_color(240, 240, 240)
                                # PERBAIKAN: Lebar Sub-Total diubah dari 115 ke 150 (15+135)
                                pdf.cell(150, 7, "TOTAL PENDUDUK", border=1, align="C", fill=True)
                                pdf.cell(40, 7, str(rekap.sum()), border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
                                pdf.ln(8)

                            gambar_tabel_demografi("A. PERSEBARAN PENDUDUK BERDASARKAN WILAYAH", "Wilayah")
                            gambar_tabel_demografi("B. DEMOGRAFI BERDASARKAN JENIS KELAMIN", "jenis_kelamin")
                            gambar_tabel_demografi("C. DEMOGRAFI BERDASARKAN KELOMPOK USIA", "Kategori Usia")
                            gambar_tabel_demografi("D. PROFIL KESEJAHTERAAN (STATUS BANSOS)", "Status Bansos")
                            
                            if 'pendidikan' in df_all.columns:
                                gambar_tabel_demografi("E. DEMOGRAFI BERDASARKAN TINGKAT PENDIDIKAN", "pendidikan")
                            if 'pekerjaan' in df_all.columns:
                                gambar_tabel_demografi("F. DEMOGRAFI BERDASARKAN MATA PENCAHARIAN", "pekerjaan")

                        else:
                            pdf.cell(190, 8, "Data kependudukan wilayah ini masih kosong.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                    else:
                        pdf.cell(190, 8, "Belum ada master data kependudukan.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

                pdf.ln(10)

            # =========================================================================
            # 2. MODUL: LAPORAN PERGERAKAN WARGA (LAMPID)
            # =========================================================================
            elif "LAMPID" in jenis_laporan:
                pdf.cell(0, 10, f"LAPORAN KEPENDUDUKAN (LAMPID)", align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 11)
                pdf.cell(0, 6, f"WILAYAH: {wilayah_teks.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(5)

                df_p = pd.DataFrame(supabase.table("data_penduduk").select("nik, nama_lengkap, rt, rw, jenis_kelamin").execute().data)
                df_l = pd.DataFrame(supabase.table("data_lahir").select("*").execute().data)
                df_m = pd.DataFrame(supabase.table("data_mati").select("*").execute().data)
                df_pindah = pd.DataFrame(supabase.table("data_pindah").select("*").execute().data)
                df_datang = pd.DataFrame(supabase.table("data_datang").select("*").execute().data)

                if not df_p.empty:
                    df_map = df_p[['nik', 'rt', 'rw', 'nama_lengkap']]
                    if not df_l.empty and 'nik_ibu' in df_l.columns:
                        df_l = df_l.merge(df_map.rename(columns={'nama_lengkap': 'nama_ibu'}), left_on='nik_ibu', right_on='nik', how='left')
                    if not df_m.empty and 'nik_jenazah' in df_m.columns:
                        df_m = df_m.merge(df_map, left_on='nik_jenazah', right_on='nik', how='left')
                    if not df_pindah.empty and 'nik_pindah' in df_pindah.columns:
                        df_pindah = df_pindah.merge(df_map, left_on='nik_pindah', right_on='nik', how='left')
                    if not df_datang.empty and 'nik_datang' in df_datang.columns:
                        df_datang = df_datang.merge(df_map, left_on='nik_datang', right_on='nik', how='left')

                if role == "operator_rt":
                    pdf.set_font("helvetica", "I", 10)
                    pdf.cell(0, 6, "Rincian Detail Pergerakan Warga Tingkat RT", new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(2)

                    if not df_l.empty and 'rt' in df_l.columns: df_l = df_l[(df_l['rt'] == rt_akses) & (df_l['rw'] == rw_akses)]
                    if not df_m.empty and 'rt' in df_m.columns: df_m = df_m[(df_m['rt'] == rt_akses) & (df_m['rw'] == rw_akses)]

                    def gambar_tabel_rincian(judul, df_data, col_nama, col_tgl, col_ket, w_nama, w_tgl, w_ket):
                        # Total Width: 10+70+30+80 = 190mm
                        pdf.set_font("helvetica", "B", 10)
                        pdf.cell(0, 8, f">> {judul}", new_x="LMARGIN", new_y="NEXT")
                        pdf.set_fill_color(220, 230, 241)
                        pdf.set_font("helvetica", "B", 9)
                        pdf.cell(10, 7, "No", border=1, align="C", fill=True)
                        pdf.cell(w_nama, 7, "Nama / Subjek", border=1, align="C", fill=True)
                        pdf.cell(w_tgl, 7, "Tanggal", border=1, align="C", fill=True)
                        pdf.cell(w_ket, 7, "Keterangan", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
                        
                        pdf.set_font("helvetica", "", 9)
                        if not df_data.empty:
                            for i, r in enumerate(df_data.to_dict(orient="records"), 1):
                                pdf.cell(10, 7, str(i), border=1, align="C")
                                pdf.cell(w_nama, 7, str(r.get(col_nama, '-'))[:35], border=1)
                                pdf.cell(w_tgl, 7, str(r.get(col_tgl, '-'))[:10], border=1, align="C")
                                pdf.cell(w_ket, 7, str(r.get(col_ket, '-'))[:35], border=1, new_x="LMARGIN", new_y="NEXT")
                        else:
                            pdf.cell(10 + w_nama + w_tgl + w_ket, 7, "Nihil (Tidak ada data)", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                        pdf.ln(5)

                    gambar_tabel_rincian("Kelahiran Baru", df_l, 'nama_bayi', 'tanggal_lahir', 'nama_ibu', 70, 30, 80)
                    gambar_tabel_rincian("Kematian Warga", df_m, 'nama_lengkap', 'tanggal_wafat', 'penyebab', 70, 30, 80)

                elif role in ["admin_rw", "super_admin"]:
                    if role == "admin_rw":
                        df_p = df_p[df_p['rw'] == rw_akses]

                    daftar_wilayah = df_p[['rw', 'rt']].dropna().drop_duplicates().sort_values(['rw', 'rt']).to_dict(orient='records')
                    data_rekap = []

                    for wil in daftar_wilayah:
                        w_rw, w_rt = wil['rw'], wil['rt']
                        warga_rt = df_p[(df_p['rw'] == w_rw) & (df_p['rt'] == w_rt)]
                        
                        label_wilayah = f"RT {w_rt}" if role == "admin_rw" else f"RW {w_rw} / RT {w_rt}"
                        
                        jml_l = len(warga_rt[warga_rt['jenis_kelamin'] == 'Laki-laki'])
                        jml_p = len(warga_rt[warga_rt['jenis_kelamin'] == 'Perempuan'])
                        total_warga = len(warga_rt)
                        
                        def hitung_kasus(df, col_jk=None, val_jk=None):
                            if df.empty or 'rt' not in df.columns or 'rw' not in df.columns: return 0
                            kondisi = (df['rt'] == w_rt) & (df['rw'] == w_rw)
                            if col_jk: kondisi = kondisi & (df[col_jk] == val_jk)
                            return len(df[kondisi])

                        data_rekap.append({
                            "Wilayah": label_wilayah, "Total": total_warga, "L": jml_l, "P": jml_p,
                            "Lahir_L": hitung_kasus(df_l, 'jenis_kelamin', 'Laki-laki'),
                            "Lahir_P": hitung_kasus(df_l, 'jenis_kelamin', 'Perempuan'),
                            "Mati": hitung_kasus(df_m), "Pindah": hitung_kasus(df_pindah), "Datang": hitung_kasus(df_datang)
                        })

                    pdf.set_font("helvetica", "B", 8)
                    pdf.set_fill_color(220, 230, 241)
                    
                    # PERBAIKAN: Total Lebar Disetel Akurat 190mm untuk menyeimbangkan kertas
                    # 25 + 15 + 15 + 15 + 15 + 15 + 30 + 30 + 30 = 190
                    w_wil = 25 
                    w_tot, w_lp, w_lp_lahir, w_lampid = 15, 15, 15, 30
                    
                    y_awal = pdf.get_y()
                    x_awal = pdf.get_x()
                    
                    pdf.cell(w_wil, 10, "Wilayah", border=1, align="C", fill=True)
                    
                    x_sub = pdf.get_x()
                    pdf.cell(w_tot + (w_lp*2), 5, "Penduduk Awal", border=1, align="C", fill=True)
                    pdf.cell(w_lp_lahir*2, 5, "Kelahiran", border=1, align="C", fill=True)
                    
                    x_sisa = pdf.get_x()
                    pdf.set_xy(x_sisa, y_awal)
                    pdf.cell(w_lampid, 10, "Kematian", border=1, align="C", fill=True)
                    pdf.cell(w_lampid, 10, "Pindah", border=1, align="C", fill=True)
                    pdf.cell(w_lampid, 10, "Datang", border=1, align="C", fill=True)
                    
                    pdf.set_xy(x_sub, y_awal + 5)
                    pdf.cell(w_tot, 5, "Total", border=1, align="C", fill=True)
                    pdf.cell(w_lp, 5, "L", border=1, align="C", fill=True)
                    pdf.cell(w_lp, 5, "P", border=1, align="C", fill=True)
                    pdf.cell(w_lp_lahir, 5, "L", border=1, align="C", fill=True)
                    pdf.cell(w_lp_lahir, 5, "P", border=1, align="C", fill=True)
                    
                    pdf.set_xy(x_awal, y_awal + 10)
                    
                    pdf.set_font("helvetica", "", 8)
                    for item in data_rekap:
                        pdf.cell(w_wil, 7, str(item['Wilayah']), border=1, align="C")
                        pdf.cell(w_tot, 7, str(item['Total']), border=1, align="C")
                        pdf.cell(w_lp, 7, str(item['L']), border=1, align="C")
                        pdf.cell(w_lp, 7, str(item['P']), border=1, align="C")
                        pdf.cell(w_lp_lahir, 7, str(item['Lahir_L']), border=1, align="C")
                        pdf.cell(w_lp_lahir, 7, str(item['Lahir_P']), border=1, align="C")
                        pdf.cell(w_lampid, 7, str(item['Mati']), border=1, align="C")
                        pdf.cell(w_lampid, 7, str(item['Pindah']), border=1, align="C")
                        pdf.cell(w_lampid, 7, str(item['Datang']), border=1, align="C", new_x="LMARGIN", new_y="NEXT")

                    pdf.set_font("helvetica", "B", 8)
                    pdf.set_fill_color(240, 240, 240) 
                    pdf.cell(w_wil, 7, "TOTAL", border=1, align="C", fill=True)
                    pdf.cell(w_tot, 7, str(sum(d['Total'] for d in data_rekap)), border=1, align="C", fill=True)
                    pdf.cell(w_lp, 7, str(sum(d['L'] for d in data_rekap)), border=1, align="C", fill=True)
                    pdf.cell(w_lp, 7, str(sum(d['P'] for d in data_rekap)), border=1, align="C", fill=True)
                    pdf.cell(w_lp_lahir, 7, str(sum(d['Lahir_L'] for d in data_rekap)), border=1, align="C", fill=True)
                    pdf.cell(w_lp_lahir, 7, str(sum(d['Lahir_P'] for d in data_rekap)), border=1, align="C", fill=True)
                    pdf.cell(w_lampid, 7, str(sum(d['Mati'] for d in data_rekap)), border=1, align="C", fill=True)
                    pdf.cell(w_lampid, 7, str(sum(d['Pindah'] for d in data_rekap)), border=1, align="C", fill=True)
                    pdf.cell(w_lampid, 7, str(sum(d['Datang'] for d in data_rekap)), border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
                
                pdf.ln(10)

            # =========================================================================
            # 3. MODUL: LAPORAN LAYANAN SURAT
            # =========================================================================
            elif "Surat" in jenis_laporan:
                pdf.cell(0, 10, f"LAPORAN LAYANAN ADMINISTRASI SURAT", align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 11)
                pdf.cell(0, 6, f"WILAYAH: {wilayah_teks.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(5)

                df_p = pd.DataFrame(supabase.table("data_penduduk").select("nik, nama_lengkap, rt, rw").execute().data)
                df_s = pd.DataFrame(supabase.table("data_surat").select("*").execute().data)
                
                if not df_s.empty and not df_p.empty:
                    df_s = df_s.merge(df_p, left_on='nik_pemohon', right_on='nik', how='left')
                    df_s['nama_lengkap'] = df_s['nama_lengkap'].fillna('Bukan Warga/Tidak Ditemukan')

                if role == "operator_rt":
                    if 'rt' in df_s.columns:
                        df_s = df_s[(df_s['rt'] == rt_akses) & (df_s['rw'] == rw_akses)]
                    
                    # Total Width: 10+25+60+95 = 190mm
                    pdf.set_font("helvetica", "B", 10)
                    pdf.set_fill_color(220, 230, 241)
                    pdf.cell(10, 8, "No", border=1, align="C", fill=True)
                    pdf.cell(25, 8, "Tanggal", border=1, align="C", fill=True)
                    pdf.cell(60, 8, "Nama Pemohon", border=1, align="C", fill=True)
                    pdf.cell(95, 8, "Jenis Surat & Keperluan", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
                    
                    pdf.set_font("helvetica", "", 9)
                    if not df_s.empty:
                        for i, r in enumerate(df_s.to_dict(orient="records"), 1):
                            pdf.cell(10, 8, str(i), border=1, align="C")
                            tgl = str(r.get('tanggal_pengajuan', r.get('created_at', '')))[:10]
                            pdf.cell(25, 8, tgl, border=1, align="C")
                            pdf.cell(60, 8, str(r.get('nama_lengkap', '-'))[:30], border=1)
                            teks_jenis = f"{r.get('jenis_surat','')} - {r.get('keperluan','')}"
                            pdf.cell(95, 8, teks_jenis[:50], border=1, new_x="LMARGIN", new_y="NEXT")
                    else:
                        pdf.cell(190, 8, "Tidak ada data pengajuan surat di wilayah ini.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

                elif role in ["admin_rw", "super_admin"]:
                    if role == "admin_rw" and not df_p.empty: 
                        df_p = df_p[df_p['rw'] == rw_akses]

                    # Total Width: 15+45+65+65 = 190mm
                    pdf.set_font("helvetica", "B", 10)
                    pdf.set_fill_color(200, 215, 235)
                    pdf.cell(15, 8, "No", border=1, align="C", fill=True)
                    pdf.cell(45, 8, "Wilayah", border=1, align="C", fill=True)
                    pdf.cell(65, 8, "Total Pengajuan Surat", border=1, align="C", fill=True)
                    pdf.cell(65, 8, "Keterangan", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

                    pdf.set_font("helvetica", "", 10)
                    if not df_p.empty:
                        daftar_wil = df_p[['rw', 'rt']].dropna().drop_duplicates().sort_values(['rw', 'rt']).to_dict(orient='records')
                        tot_surat_all = 0
                        
                        for i, wil in enumerate(daftar_wil, 1):
                            w_rw, w_rt = wil['rw'], wil['rt']
                            lbl = f"RT {w_rt}" if role == "admin_rw" else f"RW {w_rw} / RT {w_rt}"
                            
                            c_surat = 0
                            if not df_s.empty and 'rt' in df_s.columns:
                                c_surat = len(df_s[(df_s['rt'] == w_rt) & (df_s['rw'] == w_rw)])
                            
                            tot_surat_all += c_surat
                            
                            pdf.cell(15, 8, str(i), border=1, align="C")
                            pdf.cell(45, 8, lbl, border=1, align="C")
                            pdf.cell(65, 8, f"{c_surat} Dokumen", border=1, align="C")
                            pdf.cell(65, 8, "-", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                            
                        pdf.set_font("helvetica", "B", 10)
                        pdf.set_fill_color(240, 240, 240)
                        pdf.cell(60, 8, "TOTAL KESELURUHAN", border=1, align="C", fill=True)
                        pdf.cell(65, 8, f"{tot_surat_all} Dokumen", border=1, align="C", fill=True)
                        pdf.cell(65, 8, "", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
                    else:
                        pdf.cell(190, 8, "Data Kosong.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

            # =========================================================================
            # 4. MODUL: LAPORAN PENERIMA BANSOS
            # =========================================================================
            elif "Bansos" in jenis_laporan:
                pdf.cell(0, 10, f"LAPORAN DISTRIBUSI BANTUAN SOSIAL (BANSOS)", align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 11)
                pdf.cell(0, 6, f"WILAYAH: {wilayah_teks.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(5)

                df_p = pd.DataFrame(supabase.table("data_penduduk").select("nik, nama_lengkap, rt, rw").execute().data)
                df_b = pd.DataFrame(supabase.table("data_bansos").select("*").execute().data)
                
                if not df_b.empty and not df_p.empty:
                    df_b = df_b.merge(df_p, left_on='nik_penerima', right_on='nik', how='left')
                    df_b['nama_lengkap'] = df_b['nama_lengkap'].fillna('Bukan Warga/Tidak Ditemukan')

                if role == "operator_rt":
                    if 'rt' in df_b.columns:
                        df_b = df_b[(df_b['rt'] == rt_akses) & (df_b['rw'] == rw_akses)]
                        
                    # Total Width: 10+30+70+80 = 190mm
                    pdf.set_font("helvetica", "B", 10)
                    pdf.set_fill_color(220, 230, 241)
                    pdf.cell(10, 8, "No", border=1, align="C", fill=True)
                    pdf.cell(30, 8, "Tanggal", border=1, align="C", fill=True)
                    pdf.cell(70, 8, "Nama Penerima", border=1, align="C", fill=True)
                    pdf.cell(80, 8, "Jenis Bantuan", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
                    
                    pdf.set_font("helvetica", "", 9)
                    if not df_b.empty:
                        for i, r in enumerate(df_b.to_dict(orient="records"), 1):
                            pdf.cell(10, 8, str(i), border=1, align="C")
                            tgl = str(r.get('tanggal_terima', ''))[:10]
                            pdf.cell(30, 8, tgl, border=1, align="C")
                            pdf.cell(70, 8, str(r.get('nama_lengkap', '-'))[:35], border=1)
                            pdf.cell(80, 8, str(r.get('jenis_bansos', '-'))[:45], border=1, new_x="LMARGIN", new_y="NEXT")
                    else:
                        pdf.cell(190, 8, "Belum ada data penerima Bansos di wilayah ini.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

                elif role in ["admin_rw", "super_admin"]:
                    if role == "admin_rw" and not df_p.empty: 
                        df_p = df_p[df_p['rw'] == rw_akses]

                    # Total Width: 15+45+65+65 = 190mm
                    pdf.set_font("helvetica", "B", 10)
                    pdf.set_fill_color(200, 215, 235)
                    pdf.cell(15, 8, "No", border=1, align="C", fill=True)
                    pdf.cell(45, 8, "Wilayah", border=1, align="C", fill=True)
                    pdf.cell(65, 8, "Total Penerima (KPM)", border=1, align="C", fill=True)
                    pdf.cell(65, 8, "Keterangan", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

                    pdf.set_font("helvetica", "", 10)
                    if not df_p.empty:
                        daftar_wil = df_p[['rw', 'rt']].dropna().drop_duplicates().sort_values(['rw', 'rt']).to_dict(orient='records')
                        tot_bansos_all = 0
                        
                        for i, wil in enumerate(daftar_wil, 1):
                            w_rw, w_rt = wil['rw'], wil['rt']
                            lbl = f"RT {w_rt}" if role == "admin_rw" else f"RW {w_rw} / RT {w_rt}"
                            
                            c_bansos = 0
                            if not df_b.empty and 'rt' in df_b.columns:
                                c_bansos = len(df_b[(df_b['rt'] == w_rt) & (df_b['rw'] == w_rw)])
                            
                            tot_bansos_all += c_bansos
                            
                            pdf.cell(15, 8, str(i), border=1, align="C")
                            pdf.cell(45, 8, lbl, border=1, align="C")
                            pdf.cell(65, 8, f"{c_bansos} Keluarga", border=1, align="C")
                            pdf.cell(65, 8, "-", border=1, align="C", new_x="LMARGIN", new_y="NEXT")
                            
                        pdf.set_font("helvetica", "B", 10)
                        pdf.set_fill_color(240, 240, 240)
                        pdf.cell(60, 8, "TOTAL KESELURUHAN", border=1, align="C", fill=True)
                        pdf.cell(65, 8, f"{tot_bansos_all} Keluarga", border=1, align="C", fill=True)
                        pdf.cell(65, 8, "", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
                    else:
                        pdf.cell(190, 8, "Data Kosong.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

            # =========================================================================
            # 5. MODUL: LAPORAN SARPRAS & ASET RT
            # =========================================================================
            elif "Aset" in jenis_laporan:
                pdf.cell(0, 10, f"LAPORAN INVENTARIS SARPRAS & ASET", align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("helvetica", "", 11)
                pdf.cell(0, 6, f"WILAYAH: {wilayah_teks.upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(5)
                
                df_a = pd.DataFrame(supabase.table("data_aset").select("*").execute().data)

                if role == "operator_rt":
                    if not df_a.empty and 'rt' in df_a.columns and 'rw' in df_a.columns:
                        df_a = df_a[(df_a['rt'] == rt_akses) & (df_a['rw'] == rw_akses)]

                    # Total Width: 10+65+20+35+60 = 190mm
                    pdf.set_font("helvetica", "B", 10)
                    pdf.set_fill_color(220, 230, 241)
                    pdf.cell(10, 8, "No", border=1, align="C", fill=True)
                    pdf.cell(65, 8, "Nama Barang / Aset", border=1, align="C", fill=True)
                    pdf.cell(20, 8, "Jumlah", border=1, align="C", fill=True)
                    pdf.cell(35, 8, "Kondisi", border=1, align="C", fill=True)
                    pdf.cell(60, 8, "Lokasi Penyimpanan", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
                    
                    pdf.set_font("helvetica", "", 9)
                    if not df_a.empty:
                        for i, r in enumerate(df_a.to_dict(orient="records"), 1):
                            pdf.cell(10, 8, str(i), border=1, align="C")
                            
                            kol_n = str(r.get('nama_aset') or r.get('nama_barang') or '-')
                            kol_j = str(r.get('jumlah') or r.get('qty') or '0')
                            kol_k = str(r.get('kondisi') or r.get('status') or '-')
                            lokasi = str(r.get('lokasi_penyimpanan', '-'))
                            
                            pdf.cell(65, 8, kol_n[:35], border=1)
                            pdf.cell(20, 8, kol_j, border=1, align="C")
                            pdf.cell(35, 8, kol_k[:15], border=1, align="C")
                            pdf.cell(60, 8, lokasi[:30], border=1, new_x="LMARGIN", new_y="NEXT")
                    else:
                        pdf.cell(190, 8, "Belum ada inventaris aset tercatat di wilayah ini.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

                elif role in ["admin_rw", "super_admin"]:
                    if role == "admin_rw" and not df_a.empty and 'rw' in df_a.columns:
                        df_a = df_a[df_a['rw'] == rw_akses]

                    # Total Width: 15+45+65+65 = 190mm
                    pdf.set_font("helvetica", "B", 10)
                    pdf.set_fill_color(200, 215, 235)
                    pdf.cell(15, 8, "No", border=1, align="C", fill=True)
                    pdf.cell(45, 8, "Wilayah", border=1, align="C", fill=True)
                    pdf.cell(65, 8, "Total Jenis/Item Barang", border=1, align="C", fill=True)
                    pdf.cell(65, 8, "Total Kuantitas (Unit)", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

                    pdf.set_font("helvetica", "", 10)
                    if not df_a.empty and 'rt' in df_a.columns and 'rw' in df_a.columns:
                        daftar_wil = df_a[['rw', 'rt']].dropna().drop_duplicates().sort_values(['rw', 'rt']).to_dict(orient='records')
                        
                        grand_item = 0
                        grand_qty = 0

                        for i, wil in enumerate(daftar_wil, 1):
                            w_rw, w_rt = wil['rw'], wil['rt']
                            lbl = f"RT {w_rt}" if role == "admin_rw" else f"RW {w_rw} / RT {w_rt}"
                            
                            sub_a = df_a[(df_a['rt'] == w_rt) & (df_a['rw'] == w_rw)]
                            c_item = len(sub_a)
                            
                            qty_col = 'jumlah' if 'jumlah' in sub_a.columns else 'qty'
                            c_qty = pd.to_numeric(sub_a[qty_col], errors='coerce').fillna(0).sum()
                            
                            grand_item += c_item
                            grand_qty += c_qty

                            pdf.cell(15, 8, str(i), border=1, align="C")
                            pdf.cell(45, 8, lbl, border=1, align="C")
                            pdf.cell(65, 8, f"{c_item} Jenis", border=1, align="C")
                            pdf.cell(65, 8, f"{int(c_qty)} Unit", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

                        pdf.set_font("helvetica", "B", 10)
                        pdf.set_fill_color(240, 240, 240)
                        pdf.cell(60, 8, "TOTAL KESELURUHAN", border=1, align="C", fill=True)
                        pdf.cell(65, 8, f"{grand_item} Jenis", border=1, align="C", fill=True)
                        pdf.cell(65, 8, f"{int(grand_qty)} Unit", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")
                    else:
                        pdf.cell(190, 8, "Data inventaris aset kosong atau belum mencakup data wilayah.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

            # ==========================================
            # BAGIAN TANDA TANGAN RESMI
            # ==========================================
            pdf.ln(20)
            pdf.set_font("helvetica", "", 11)
            
            bulan_indo = {
                1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                9: "September", 10: "Oktober", 11: "November", 12: "Desember"
            }
            hari_ini = datetime.now()
            tanggal = f"{hari_ini.day} {bulan_indo[hari_ini.month]} {hari_ini.year}"
            
            # 130 + 60 = 190mm (Posisi tepat di kanan halaman)
            pdf.cell(130)
            # UBAHAN: Alamat titimangsa menggunakan nama desa
            pdf.cell(60, 6, f"{nama_desa.title()}, {tanggal}", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(130)
            pdf.cell(60, 6, penandatangan_jabatan, align="C", new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(20)
            pdf.cell(130)
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(60, 6, f"({penandatangan_nama})", align="C", new_x="LMARGIN", new_y="NEXT")
            
            pdf_bytes = bytes(pdf.output())
            st.success("🎉 Dokumen PDF Berhasil Dirangkai!")
            st.download_button(
                label="⬇️ Unduh Dokumen PDF Hasil Cetak",
                data=pdf_bytes,
                file_name=f"Laporan_{jenis_laporan[:8]}_{wilayah_teks.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                width="stretch"
            )