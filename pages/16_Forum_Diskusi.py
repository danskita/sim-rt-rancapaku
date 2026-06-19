import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import os
from supabase import create_client, Client
from menu import tampilkan_menu

# ========================================================
# 1. KONFIGURASI HALAMAN WAJIB PALING ATAS (Hanya Satu Kali)
# ========================================================
st.set_page_config(
    page_title="Forum Diskusi", 
    page_icon="💬", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- SUNTIKAN CSS UNTUK DESAIN WHATSAPP ---
st.markdown("""
    <style>
    /* 1. Memberi ruang kosong di bawah agar pesan tidak tertutup kotak input */
    .block-container {
        padding-bottom: 160px !important;
    }
    
    /* 2. Memaku (Fixed) kotak input ke dasar layar agar 100% SOLID */
    div[data-testid="stForm"] {
        position: fixed;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 46rem; 
        
        background-color: #0e1117 !important; 
        padding: 15px 20px 20px 20px !important;
        z-index: 999999 !important; 
        border-top: 2px solid #333 !important;
        border-radius: 15px 15px 0 0;
        height: max-content !important;
    }
    
    @media (prefers-color-scheme: light) {
        div[data-testid="stForm"] {
            background-color: #ffffff !important; 
            border-top: 2px solid #ddd !important;
        }
    }
    
    div[data-testid="stForm"] > div {
        background-color: transparent !important;
    }
    
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- KONEKSI KE SUPABASE ---
url: str = st.secrets["supabase"]["url"]
key: str = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

# Gembok Keamanan
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("⚠️ Akses Ditolak! Silakan login terlebih dahulu.")
    st.stop()

tampilkan_menu()
# ---------------------------

st.title("💬 Forum Diskusi Terpadu")
st.markdown("Bagikan informasi, tautan web, foto, dokumen, atau rekaman suara di sini.")

# ==========================================
# IDENTITAS OTOMATIS
# ==========================================
role = st.session_state.get("role", "")
rt_akses = st.session_state.get("rt_akses", "")
rw_akses = st.session_state.get("rw_akses", "")

if role == "super_admin":
    nama_pengirim = "Admin"
elif role == "admin_rw":
    nama_pengirim = f"Ketua RW {rw_akses}"
else:
    nama_pengirim = f"Ketua RT {rt_akses} / RW {rw_akses}"

# ==========================================
# 🟢 SISTEM PELACAK STATUS ONLINE 
# ==========================================
try:
    waktu_sekarang = datetime.now(timezone.utc).isoformat()
    supabase.table("status_online").upsert({
        "pengirim": nama_pengirim,
        "role": role,
        "terakhir_aktif": waktu_sekarang
    }).execute()
except Exception as e:
    pass

@st.cache_data(ttl=2)
def muat_data_online():
    try:
        res = supabase.table("status_online").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['terakhir_aktif'] = pd.to_datetime(df['terakhir_aktif'])
            waktu_kini = pd.Timestamp.now('UTC') 
            df['is_online'] = (waktu_kini - df['terakhir_aktif']).dt.total_seconds() <= 300
            return df[df['is_online'] == True]
    except:
        return pd.DataFrame()
    return pd.DataFrame()

df_online = muat_data_online()
jumlah_online = len(df_online) if not df_online.empty else 1

with st.expander(f"🟢 Lihat Siapa yang Sedang Online ({jumlah_online} Orang)"):
    if not df_online.empty:
        for _, baris in df_online.sort_values(by="role", ascending=False).iterrows():
            if baris['role'] == "super_admin": ikon = "🛡️"
            elif baris['role'] == "admin_rw": ikon = "👔"
            else: ikon = "👤"
            
            if baris['pengirim'] == nama_pengirim:
                st.write(f"🟢 {ikon} **{baris['pengirim']} (Anda)**")
            else:
                st.write(f"🟢 {ikon} {baris['pengirim']}")
    else:
        st.write(f"🟢 👤 **{nama_pengirim} (Anda)**")

# ==========================================
# FUNGSI MENARIK PESAN CHAT
# ==========================================
@st.cache_data(ttl=2)
def muat_obrolan():
    try:
        res = supabase.table("data_forum").select("*").order("waktu", desc=True).limit(50).execute()
        pesan_data = res.data if res.data else []
        pesan_data.reverse() 
        return pesan_data
    except:
        return []

col_title, col_btn = st.columns([3, 1])
with col_btn:
    if st.button("🔄 Segarkan", width="stretch"):
        muat_obrolan.clear()
        st.rerun()

st.markdown("---")
pesan_list = muat_obrolan()

# ==========================================
# KOTAK OBROLAN (LAYAR PENUH & DINAMIS)
# ==========================================
chat_container = st.container()

with chat_container:
    if not pesan_list:
        st.info("📭 Belum ada obrolan. Jadilah yang pertama mengirim pesan!")
    
    for msg in pesan_list:
        if msg['role'] == "super_admin": msg_avatar = "🛡️"
        elif msg['role'] == "admin_rw": msg_avatar = "👔"
        else: msg_avatar = "👤"
            
        is_me = (msg['pengirim'] == nama_pengirim)
        
        bg_color = "#dcf8c6" if is_me else "#ffffff"
        align_div = "flex-end" if is_me else "flex-start"
        
        bubble_html = f"""
        <div style='display: flex; justify-content: {align_div}; margin-bottom: 5px;'>
            <div style='background-color: {bg_color}; color: black; border-radius: 12px; padding: 8px 15px; max-width: 80%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); border: 1px solid #eee;'>
                <div style='font-size: 0.75em; color: gray; margin-bottom: 3px;'>{msg_avatar} <b>{msg['pengirim']}</b></div>
                <div style='font-size: 1em; white-space: pre-wrap;'>{msg.get('pesan', '')}</div>
            </div>
        </div>
        """
        st.markdown(bubble_html, unsafe_allow_html=True)
        
        url_lampiran = msg.get('url_lampiran')
        tipe_lampiran = msg.get('tipe_lampiran')
        
        if is_me:
            c1, c2 = st.columns([1, 4])
            target_col = c2
        else:
            c1, c2 = st.columns([4, 1])
            target_col = c1
            
        with target_col:
            if url_lampiran:
                if tipe_lampiran == "foto": st.image(url_lampiran, width="stretch")
                elif tipe_lampiran == "dokumen": st.markdown(f"📄 **[Unduh Dokumen]({url_lampiran})**")
                elif tipe_lampiran == "audio": st.audio(url_lampiran)
                elif tipe_lampiran == "video": st.video(url_lampiran)
            
            if role == "super_admin" or is_me:
                if st.button("🗑️hapus", key=f"del_{msg['id']}"):
                    supabase.table("data_forum").delete().eq("id", msg['id']).execute()
                    st.toast("✅ Pesan berhasil dihapus!")
                    muat_obrolan.clear()
                    st.rerun()

# --- SUNTIKAN JAVASCRIPT: AUTO SCROLL (BEBAS ERROR) ---
st.markdown(
    """<svg onload="window.parent.document.documentElement.scrollTop = window.parent.document.documentElement.scrollHeight;" style="display:none;"></svg>""",
    unsafe_allow_html=True
)

# ==========================================
# INPUT KIRIM PESAN & LAMPIRAN (STATIS DI BAWAH)
# ==========================================
with st.form("form_chat", clear_on_submit=True):
    isi_pesan = st.text_input("Pesan", label_visibility="collapsed", placeholder="Ketik pesan atau paste link di sini...")
    
    col_lampiran, col_kirim = st.columns([3, 1])
    
    with col_lampiran:
        with st.expander("📎 Lampirkan Media"):
            file_lampiran = st.file_uploader("Upload", label_visibility="collapsed", type=["png", "jpg", "jpeg", "pdf", "mp3", "wav", "mp4"])
            
    with col_kirim:
        kirim_btn = st.form_submit_button("🚀 Kirim", width="stretch")
    
    if kirim_btn:
        if not isi_pesan and not file_lampiran:
            st.warning("⚠️ Pesan atau lampiran tidak boleh kosong.")
        else:
            url_publik = None
            tipe_file = None
            
            if file_lampiran:
                waktu_unik = datetime.now().strftime("%Y%m%d%H%M%S")
                ekstensi = file_lampiran.name.split('.')[-1].lower()
                nama_file_baru = f"chat_{waktu_unik}.{ekstensi}"
                
                if ekstensi in ["png", "jpg", "jpeg"]: tipe_file = "foto"
                elif ekstensi == "pdf": tipe_file = "dokumen"
                elif ekstensi in ["mp3", "wav"]: tipe_file = "audio"
                elif ekstensi == "mp4": tipe_file = "video"
                
                try:
                    supabase.storage.from_("arsip_digital").upload(
                        path=f"forum/{nama_file_baru}", 
                        file=file_lampiran.getvalue(), 
                        file_options={"content-type": file_lampiran.type}
                    )
                    url_publik = supabase.storage.from_("arsip_digital").get_public_url(f"forum/{nama_file_baru}")
                except Exception as e:
                    st.error("Gagal mengunggah lampiran.")
            
            data_insert = {
                "pengirim": nama_pengirim,
                "pesan": isi_pesan if isi_pesan else "📎 Mengirim lampiran",
                "role": role,
                "tipe_lampiran": tipe_file,
                "url_lampiran": url_publik
            }
            supabase.table("data_forum").insert(data_insert).execute()
            
            muat_obrolan.clear()
            st.rerun()