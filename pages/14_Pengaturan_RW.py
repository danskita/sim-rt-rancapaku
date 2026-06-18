import streamlit as st
import pandas as pd
import numpy as np
import io
import datetime
import time
from supabase import create_client, Client
from menu import tampilkan_menu

# Aturan Streamlit: set_page_config harus dipanggil paling awal
st.set_page_config(page_title="Pengaturan Data RW", page_icon="⚙️", layout="centered")

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# Gembok Keamanan Berlapis (HANYA ADMIN RW)
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("⚠️ Akses Ditolak! Silakan login melalui halaman utama terlebih dahulu.")
    st.stop()

role = st.session_state.get("role", "")
rw_akses = st.session_state.get("rw_akses", "")

if role != "admin_rw":
    st.error("⛔ AKSES DITOLAK! Halaman ini dikhususkan bagi Ketua/Admin RW untuk mengelola wilayahnya.")
    st.stop()

# Tampilkan menu
tampilkan_menu()
# ---------------------------

st.title(f"⚙️ Pusat Kelola Data RW {rw_akses}")
st.markdown(f"Halaman pemeliharaan data khusus untuk wilayah **RW {rw_akses}**. Anda hanya dapat mengakses, menghapus, dan memasukkan data di lingkup RW Anda.")

tab_backup, tab_reset, tab_import = st.tabs(["💾 Backup Data RW", "⚠️ Kosongkan Data RW", "📥 Import Excel Baru"])

# ==========================================
# TAB 1: BACKUP DATA KHUSUS RW
# ==========================================
with tab_backup:
    st.subheader(f"💾 Backup Data Wilayah RW {rw_akses}")
    st.info("Fitur ini akan mengunduh seluruh data warga yang berada di wilayah RW Anda ke dalam satu file Excel.")
    
    if st.button("Siapkan File Backup RW", type="primary", width="stretch"):
        with st.spinner("Sedang menarik data dari server Cloud... (Mohon tunggu)"):
            try:
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
                
                hasil_df = {}
                
                # Menarik data dengan filter khusus RW yang sedang login
                for nama_tabel, nama_sheet in daftar_tabel:
                    try:
                        res = supabase.table(nama_tabel).select("*").eq("rw", rw_akses).execute()
                        hasil_df[nama_sheet] = pd.DataFrame(res.data) if res.data else pd.DataFrame()
                    except Exception as err_tabel:
                        st.warning(f"⚠️ Melewati tabel {nama_tabel} (Mungkin kosong/tidak ada kolom RW)")
                        hasil_df[nama_sheet] = pd.DataFrame()
                    
                    time.sleep(0.5) # Jeda untuk menjaga kestabilan koneksi

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    for nama_sheet, df in hasil_df.items():
                        if not df.empty:
                            df.to_excel(writer, index=False, sheet_name=nama_sheet)
                
                excel_data = buffer.getvalue()
                tgl_backup = datetime.date.today().strftime("%Y-%m-%d")
                
                st.success("✅ File Backup RW berhasil disiapkan!")
                st.download_button(
                    label="📥 Unduh File Backup (.xlsx)",
                    data=excel_data,
                    file_name=f"Backup_RW_{rw_akses}_{tgl_backup}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch"
                )
            except Exception as e:
                st.error(f"⚠️ Terjadi kesalahan: {e}")

# ==========================================
# TAB 2: KOSONGKAN DATA (RESET KHUSUS RW)
# ==========================================
with tab_reset:
    st.subheader(f"⚠️ Kosongkan Data Wilayah RW {rw_akses}")
    st.error("PERINGATAN: Tindakan ini akan menghapus data warga di wilayah RW Anda. Data dari RW lain tidak akan terpengaruh.")
    
    with st.form("form_reset_data_rw"):
        konfirmasi_teks = st.text_input("Ketik persis: HAPUS DATA RW")
        yakin_1 = st.checkbox("Saya sadar data RW ini akan dihapus permanen.")
        
        submit_reset = st.form_submit_button("🚨 KOSONGKAN DATA RW SEKARANG 🚨", use_container_width=False)
        
        if submit_reset:
            if konfirmasi_teks != "HAPUS DATA RW":
                st.warning("❌ Konfirmasi gagal! Kalimat yang diketik tidak sesuai.")
            elif not yakin_1:
                st.warning("❌ Anda harus mencentang kotak persetujuan di atas.")
            else:
                with st.spinner("Sedang menghapus data wilayah Anda..."):
                    try:
                        # Menghapus data hanya yang memiliki nilai RW sama dengan rw_akses
                        # Tabel anak dihapus terlebih dahulu
                        supabase.table("data_lahir").delete().eq("rw", rw_akses).execute()
                        supabase.table("data_mati").delete().eq("rw", rw_akses).execute()
                        supabase.table("data_pindah").delete().eq("rw", rw_akses).execute()
                        supabase.table("data_datang").delete().eq("rw", rw_akses).execute()
                        supabase.table("data_bansos").delete().eq("rw", rw_akses).execute()
                        
                        # Hapus data master penduduk RW tersebut
                        supabase.table("data_penduduk").delete().eq("rw", rw_akses).execute()
                        
                        st.success(f"✅ Data warga untuk RW {rw_akses} berhasil dikosongkan.")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"⚠️ Terjadi kesalahan saat menghapus data: {e}")

# ==========================================
# TAB 3: IMPORT DATA MASAL (EXCEL BARU)
# ==========================================
with tab_import:
    st.subheader(f"📥 Import Data Penduduk RW {rw_akses}")
    st.markdown("Masukkan daftar warga baru. Sistem akan secara otomatis mengunci data ini sebagai warga RW Anda.")

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
        file_name=f'Template_Data_RW_{rw_akses}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        width="stretch"
    )

    st.markdown("---")
    
    file_import_upload = st.file_uploader("Pilih file Excel (.xlsx) yang sudah diisi", type=['xlsx'], key="import_rw")

    if file_import_upload is not None:
        try:
            df_import = pd.read_excel(file_import_upload)
            
            # Pembersih kolom
            df_import.columns = df_import.columns.str.strip().str.lower()
            
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
            
            if 'nik' in df_import.columns:
                df_import['nik'] = df_import['nik'].astype(str).str.replace(r'\.0$', '', regex=True)
            if 'no_kk' in df_import.columns:
                df_import['no_kk'] = df_import['no_kk'].astype(str).str.replace(r'\.0$', '', regex=True)
                
            if 'rt' in df_import.columns:
                df_import['rt'] = df_import['rt'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(3)
                
            # FITUR KEAMANAN: Memaksa kolom RW menjadi RW milik Admin yang sedang login
            df_import['rw'] = str(rw_akses).zfill(3)

            if 'tanggal_lahir' in df_import.columns:
                df_import['tanggal_lahir'] = pd.to_datetime(df_import['tanggal_lahir'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')

            df_import = df_import.replace({np.nan: None})

            st.write("Preview Data yang siap diimpor:")
            st.dataframe(df_import, width="stretch")

            if st.button("🚀 Eksekusi Import ke Database", width="stretch", type="primary"):
                with st.spinner("Sedang menyimpan data ke cloud..."):
                    data_import_records = df_import.to_dict(orient="records")
                    
                    supabase.table("data_penduduk").insert(data_import_records).execute()
                    
                    st.success(f"✅ Mantap! {len(df_import)} data warga berhasil diimpor khusus ke RW {rw_akses}.")
                    st.cache_data.clear()
                    
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat membaca file: {e}")