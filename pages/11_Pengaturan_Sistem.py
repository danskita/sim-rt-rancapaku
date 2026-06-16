import streamlit as st
import pandas as pd
import io
import datetime
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
st.markdown("Halaman khusus administrator untuk melakukan pencadangan (Backup), reset, dan pemulihan data (Restore).")

# Menambahkan 3 Tab
tab_backup, tab_reset, tab_restore = st.tabs(["💾 Backup Data", "⚠️ Kosongkan Data", "🔄 Restore Database"])

# ==========================================
# TAB 1: BACKUP DATA (EXCEL MULTI-SHEET)
# ==========================================
with tab_backup:
    st.subheader("💾 Backup Seluruh Database")
    st.info("Fitur ini akan mengunduh seluruh data dari semua tabel ke dalam satu file Excel yang rapi.")
    
    if st.button("Siapkan File Backup", type="primary"):
        with st.spinner("Sedang menarik data dari server Cloud..."):
            try:
                df_penduduk = pd.DataFrame(supabase.table("data_penduduk").select("*").execute().data)
                df_lahir = pd.DataFrame(supabase.table("data_lahir").select("*").execute().data)
                df_mati = pd.DataFrame(supabase.table("data_mati").select("*").execute().data)
                df_pindah = pd.DataFrame(supabase.table("data_pindah").select("*").execute().data)
                df_datang = pd.DataFrame(supabase.table("data_datang").select("*").execute().data)
                df_bansos = pd.DataFrame(supabase.table("data_bansos").select("*").execute().data)
                df_surat = pd.DataFrame(supabase.table("data_surat").select("*").execute().data)
                df_aset = pd.DataFrame(supabase.table("data_aset").select("*").execute().data)
                
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    if not df_penduduk.empty: df_penduduk.to_excel(writer, index=False, sheet_name='Data_Penduduk')
                    if not df_lahir.empty: df_lahir.to_excel(writer, index=False, sheet_name='Data_Lahir')
                    if not df_mati.empty: df_mati.to_excel(writer, index=False, sheet_name='Data_Mati')
                    if not df_pindah.empty: df_pindah.to_excel(writer, index=False, sheet_name='Data_Pindah')
                    if not df_datang.empty: df_datang.to_excel(writer, index=False, sheet_name='Data_Datang')
                    if not df_bansos.empty: df_bansos.to_excel(writer, index=False, sheet_name='Data_Bansos')
                    if not df_surat.empty: df_surat.to_excel(writer, index=False, sheet_name='Data_Surat')
                    if not df_aset.empty: df_aset.to_excel(writer, index=False, sheet_name='Data_Aset')
                
                excel_data = buffer.getvalue()
                tgl_backup = datetime.date.today().strftime("%Y-%m-%d")
                
                st.success("✅ File Backup berhasil disiapkan!")
                st.download_button(
                    label="📥 Unduh File Backup (.xlsx)",
                    data=excel_data,
                    file_name=f"Backup_SIM_RT_{tgl_backup}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"⚠️ Terjadi kesalahan saat menarik data: {e}")

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
        
        submit_reset = st.form_submit_button("🚨 KOSONGKAN DATABASE SEKARANG 🚨")
        
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
                        supabase.table("data_aset").delete().neq("id_aset", 0).execute() 
                        
                        supabase.table("data_penduduk").delete().neq("nik", "0").execute()
                        
                        st.success("✅ Seluruh database berhasil dikosongkan.")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"⚠️ Terjadi kesalahan saat menghapus data: {e}")

# ==========================================
# TAB 3: RESTORE DATABASE (PEMULIHAN)
# ==========================================
with tab_restore:
    st.subheader("🔄 Restore Database (Pemulihan)")
    st.info("Unggah file Backup (.xlsx) yang pernah Anda unduh sebelumnya. Sistem akan otomatis mendistribusikan datanya kembali ke tabel yang tepat.")
    
    file_backup_upload = st.file_uploader("Pilih file Backup Excel Anda", type=['xlsx'])
    
    if file_backup_upload is not None:
        if st.button("Mulai Proses Restore", type="primary"):
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
                                
                                df = df.where(pd.notnull(df), None)
                                
                                records = df.to_dict(orient='records')
                                supabase.table(nama_tabel).insert(records).execute()
                                
                                st.write(f"✅ Tabel **{nama_sheet}** berhasil dipulihkan ({len(records)} baris data).")
                    
                    st.success("🎉 Seluruh database berhasil dipulihkan secara otomatis ke kondisi semula!")
                    st.cache_data.clear()
                    
                except Exception as e:
                    st.error(f"⚠️ Terjadi kesalahan saat memulihkan data: {e}")