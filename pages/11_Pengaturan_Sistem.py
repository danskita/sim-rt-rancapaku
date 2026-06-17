import streamlit as st
import pandas as pd
import numpy as np # WAJIB DITAMBAHKAN UNTUK PEMBERSIH NaN
import io
import datetime
import time
from supabase import create_client, Client
from menu import tampilkan_menu

# Aturan Streamlit: set_page_config harus dipanggil paling awal
st.set_page_config(page_title="Pengaturan Sistem", page_icon="⚙️", layout="centered")

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# Gembok Keamanan Berlapis (HANYA KEPALA DESA / SUPER ADMIN)
if "role" not in st.session_state:
    st.warning("⚠️ Akses Ditolak! Silakan login melalui halaman utama terlebih dahulu.")
    st.stop()

if st.session_state["role"] != "super_admin":
    st.error("⛔ AKSES DITOLAK! Halaman 'Pengaturan Sistem' ini hanya boleh diakses oleh Kepala Desa (Super Admin).")
    st.stop()

# Tampilkan menu setelah dipastikan dia adalah Super Admin
tampilkan_menu()
# ---------------------------

st.title("⚙️ Pengaturan & Pemeliharaan Sistem")
st.markdown("Halaman khusus administrator untuk melakukan pencadangan (Backup), reset, pemulihan data (Restore), dan Import data baru.")

# Menambahkan 4 Tab (Tab Import ditambahkan di akhir)
tab_backup, tab_reset, tab_restore, tab_import = st.tabs(["💾 Backup Data", "⚠️ Kosongkan Data", "🔄 Restore Database", "📥 Import Excel Baru"])

# ==========================================
# TAB 1: BACKUP DATA (EXCEL MULTI-SHEET)
# ==========================================
with tab_backup:
    st.subheader("💾 Backup Seluruh Database")
    st.info("Fitur ini akan mengunduh seluruh data dari semua tabel ke dalam satu file Excel yang rapi.")
    
    if st.button("Siapkan File Backup", type="primary", width="stretch"):
        with st.spinner("Sedang menarik data dari server Cloud... (Mohon tunggu, jangan tutup halaman ini)"):
            try:
                # 1. Siapkan daftar tabel yang akan ditarik
                daftar_tabel = [
                    ("data_penduduk", "Data_Penduduk"),
                    ("data_lahir", "Data_Lahir"),
                    ("data_mati", "Data_Mati"),
                    ("data_pindah", "Data_Pindah"),
                    ("data_datang", "Data_Datang"),
                    ("data_bansos", "Data_Bansos"),
                    ("data_surat", "Data_Surat"),
                    ("data_aset", "Data_Aset")
                ]
                
                # Dictionary untuk menyimpan hasil dataframe
                hasil_df = {}
                
                # 2. Tarik data satu per satu dengan jeda waktu yang sopan agar server tidak memutus koneksi
                for nama_tabel, nama_sheet in daftar_tabel:
                    try:
                        res = supabase.table(nama_tabel).select("*").execute()
                        hasil_df[nama_sheet] = pd.DataFrame(res.data) if res.data else pd.DataFrame()
                    except Exception as err_tabel:
                        st.warning(f"⚠️ Gagal menarik tabel {nama_tabel}: {err_tabel}")
                        hasil_df[nama_sheet] = pd.DataFrame()
                    
                    # Jeda setengah detik agar koneksi aman (mencegah WinError 10054)
                    time.sleep(0.5)

                # 3. Masukkan semua data ke dalam Excel
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    for nama_sheet, df in hasil_df.items():
                        if not df.empty:
                            df.to_excel(writer, index=False, sheet_name=nama_sheet)
                
                excel_data = buffer.getvalue()
                tgl_backup = datetime.date.today().strftime("%Y-%m-%d")
                
                st.success("✅ File Backup berhasil disiapkan tanpa hambatan!")
                st.download_button(
                    label="📥 Unduh File Backup (.xlsx)",
                    data=excel_data,
                    file_name=f"Backup_SIM_RT_{tgl_backup}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch"
                )
            except Exception as e:
                st.error(f"⚠️ Terjadi kesalahan kritis saat menyiapkan backup: {e}")

# ==========================================
# TAB 2: KOSONGKAN DATA (DANGER ZONE)
# ==========================================
with tab_reset:
    st.subheader("⚠️ Kosongkan Seluruh Database (Reset Factory)")
    st.error("PERINGATAN KERAS: Tindakan ini akan menghapus SELURUH data warga. Pastikan Anda sudah melakukan Backup terlebih dahulu!")
    
    with st.form("form_reset_data"):
        konfirmasi_teks = st.text_input("Ketik persis: HAPUS SEMUA DATA")
        yakin_1 = st.checkbox("Saya sadar bahwa data tidak bisa dikembalikan kecuali melalui proses Restore.")
        yakin_2 = st.checkbox("Saya sudah mengunduh file Backup hari ini.")
        
        submit_reset = st.form_submit_button("🚨 KOSONGKAN DATABASE SEKARANG 🚨", use_container_width=True)
        
        if submit_reset:
            if konfirmasi_teks != "HAPUS SEMUA DATA":
                st.warning("❌ Konfirmasi gagal! Kalimat yang diketik tidak sesuai.")
            elif not (yakin_1 and yakin_2):
                st.warning("❌ Anda harus mencentang kedua kotak persetujuan di atas.")
            else:
                with st.spinner("Sedang membumihanguskan data..."):
                    try:
                        # Menghapus tabel anak (transaksional) dulu, baru master
                        supabase.table("data_lahir").delete().neq("id_lahir", "0").execute()
                        supabase.table("data_mati").delete().neq("id_mati", "0").execute()
                        supabase.table("data_pindah").delete().neq("id_pindah", "0").execute()
                        supabase.table("data_datang").delete().neq("id_datang", "0").execute()
                        supabase.table("data_bansos").delete().neq("id_bansos", "0").execute()
                        supabase.table("data_surat").delete().neq("id_surat", "0").execute()
                        supabase.table("data_aset").delete().neq("id_aset", "0").execute() 
                        
                        supabase.table("data_penduduk").delete().neq("nik", "0").execute()
                        
                        st.success("✅ Seluruh database berhasil dikosongkan. Anda siap mengimpor data baru.")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"⚠️ Terjadi kesalahan saat menghapus data: {e}")

# ==========================================
# TAB 3: RESTORE DATABASE (PEMULIHAN)
# ==========================================
with tab_restore:
    st.subheader("🔄 Restore Database (Pemulihan)")
    st.info("Unggah file Backup (.xlsx) yang pernah Anda unduh sebelumnya. Sistem akan mendistribusikan datanya kembali ke tabel yang tepat.")
    
    file_backup_upload = st.file_uploader("Pilih file Backup Excel Anda", type=['xlsx'], key="restore_file")
    
    if file_backup_upload is not None:
        if st.button("Mulai Proses Restore", type="primary", width="stretch"):
            with st.spinner("Sedang merakit ulang database Anda... Mohon tunggu!"):
                try:
                    xls = pd.read_excel(file_backup_upload, sheet_name=None, engine='openpyxl')
                    
                    # URUTAN SANGAT PENTING: Master (Penduduk) & Standalone (Aset) masuk duluan agar tidak error Foreign Key
                    urutan_tabel = [
                        ('Data_Penduduk', 'data_penduduk'),
                        ('Data_Aset', 'data_aset'),
                        ('Data_Lahir', 'data_lahir'),
                        ('Data_Mati', 'data_mati'),
                        ('Data_Pindah', 'data_pindah'),
                        ('Data_Datang', 'data_datang'),
                        ('Data_Bansos', 'data_bansos'),
                        ('Data_Surat', 'data_surat')
                    ]
                    
                    for nama_sheet, nama_tabel in urutan_tabel:
                        if nama_sheet in xls:
                            df = xls[nama_sheet]
                            if not df.empty:
                                if 'nik' in df.columns:
                                    df['nik'] = df['nik'].astype(str).str.replace(r'\.0$', '', regex=True)
                                if 'no_kk' in df.columns:
                                    df['no_kk'] = df['no_kk'].astype(str).str.replace(r'\.0$', '', regex=True)
                                
                                for col in df.select_dtypes(include=['datetime64']).columns:
                                    df[col] = df[col].dt.strftime('%Y-%m-%d')
                                
                                # Membersihkan NaN menjadi None untuk Supabase JSON
                                df = df.replace({np.nan: None})
                                
                                records = df.to_dict(orient='records')
                                supabase.table(nama_tabel).insert(records).execute()
                                
                                st.write(f"✅ Tabel **{nama_sheet}** berhasil dipulihkan ({len(records)} baris data).")
                    
                    st.success("🎉 Seluruh database berhasil dipulihkan secara otomatis ke kondisi semula!")
                    st.cache_data.clear()
                    
                except Exception as e:
                    st.error(f"⚠️ Terjadi kesalahan saat memulihkan data: {e}")

# ==========================================
# TAB 4: IMPORT DATA MASAL (EXCEL BARU)
# ==========================================
with tab_import:
    st.subheader("📥 Import Master Data Penduduk (Excel)")
    st.markdown("Fitur ini digunakan untuk memasukkan daftar warga baru dalam jumlah besar sekaligus.")

    # Tombol Unduh Template
    cols_template = [
        'nik', 'no_kk', 'nama_lengkap', 'tempat_lahir', 'tanggal_lahir', 
        'jenis_kelamin', 'golongan_darah', 'agama', 'pendidikan', 'pekerjaan', 
        'status_perkawinan', 'shdk', 'kewarganegaraan', 'jalan_kampung', 'rt', 'rw'
    ]
    df_template_import = pd.DataFrame(columns=cols_template)
    buffer_import = io.BytesIO()
    with pd.ExcelWriter(buffer_import, engine='openpyxl') as writer:
        df_template_import.to_excel(writer, index=False, sheet_name='Template_Warga')
    excel_data_import = buffer_import.getvalue()

    st.download_button(
        label="📥 Unduh Template Excel Kosong (.xlsx)",
        data=excel_data_import,
        file_name='Template_Data_Penduduk.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        width="stretch"
    )

    st.markdown("---")
    
    # Upload File Excel
    file_import_upload = st.file_uploader("Pilih file Excel (.xlsx) yang sudah diisi", type=['xlsx'], key="import_file")

    if file_import_upload is not None:
        try:
            df_import = pd.read_excel(file_import_upload)
            
            # >>> PEMBERSIH HURUF KECIL & SPASI <<<
            df_import.columns = df_import.columns.str.strip().str.lower()
            
            # >>> KAMUS PENERJEMAH KOLOM <<<
            kamus_kolom = {
                'no. kk': 'no_kk',
                'nama lengkap': 'nama_lengkap',
                'tempat lahir': 'tempat_lahir',
                'tanggal lahir (yyyy-mm-dd)': 'tanggal_lahir',
                'jenis kelamin': 'jenis_kelamin',
                'golongan darah': 'golongan_darah',
                'pendidikan terakhir': 'pendidikan',
                'status perkawinan': 'status_perkawinan',
                'jalan / kampung / perumahan': 'jalan_kampung'
            }
            df_import = df_import.rename(columns=kamus_kolom)
            
            # >>> PEMBERSIH FORMAT ANGKA & KOMA NOL (.0) <<<
            if 'nik' in df_import.columns:
                df_import['nik'] = df_import['nik'].astype(str).str.replace(r'\.0$', '', regex=True)
            if 'no_kk' in df_import.columns:
                df_import['no_kk'] = df_import['no_kk'].astype(str).str.replace(r'\.0$', '', regex=True)
                
            if 'rt' in df_import.columns:
                df_import['rt'] = df_import['rt'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(3)
            if 'rw' in df_import.columns:
                df_import['rw'] = df_import['rw'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(3)

            # >>> PENERJEMAH TANGGAL (Format Campuran DD/MM/YYYY atau YYYY-MM-DD) <<<
            if 'tanggal_lahir' in df_import.columns:
                df_import['tanggal_lahir'] = pd.to_datetime(df_import['tanggal_lahir'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')

            # >>> SAPU BERSIH DATA KOSONG (ANTI ERROR JSON) <<<
            df_import = df_import.replace({np.nan: None})

            st.write("Preview Data yang siap diimpor:")
            st.dataframe(df_import, width="stretch")

            if st.button("🚀 Eksekusi Import ke Database", width="stretch", type="primary"):
                with st.spinner("Sedang menyimpan data ke cloud..."):
                    data_import_records = df_import.to_dict(orient="records")
                    
                    # Eksekusi Insert ke Supabase
                    supabase.table("data_penduduk").insert(data_import_records).execute()
                    
                    st.success(f"✅ Mantap! {len(df_import)} data warga berhasil diimpor ke database.")
                    st.cache_data.clear()
                    
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat membaca atau menyimpan file: {e}")
            st.info("Pastikan judul kolom sesuai dengan template atau format yang disarankan.")