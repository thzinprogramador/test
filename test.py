import streamlit as st
import firebase_admin
import requests
import datetime
import random
import time
from firebase_admin import credentials, db, firestore
from io import BytesIO
from PIL import Image
import base64
from datetime import datetime

# ==============================
# CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
    page_title="Wave 2.0",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# ESTADO DA SESSÃO
# ==============================
if "current_track" not in st.session_state:
    st.session_state.current_track = None
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False
if "volume" not in st.session_state:
    st.session_state.volume = 100
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "music_history" not in st.session_state:
    st.session_state.music_history = []
if "all_songs" not in st.session_state:
    st.session_state.all_songs = []
if "show_add_form" not in st.session_state:
    st.session_state.show_add_form = False
if "firebase_connected" not in st.session_state:
    st.session_state.firebase_connected = False
if "show_request_form" not in st.session_state:
    st.session_state.show_request_form = False
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False
if "random_songs" not in st.session_state:
    st.session_state.random_songs = []
if "random_songs_timestamp" not in st.session_state:
    st.session_state.random_songs_timestamp = None
if "modal_open" not in st.session_state:
    st.session_state.modal_open = None

# ==============================
# CONFIGURAÇÕES DE SEGURANÇA
# ==============================
ADMIN_PASSWORD = "wavesong9090" 

# ==============================
# FIREBASE CONFIG (JSON DIRETO)
# ==============================
firebase_config = {
  "type": "service_account",
  "project_id": "wavesong",
  "private_key_id": "cad859e3cfb01dda66264cad60815296d83de54b",
  "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCb7iAb10GqiKgv
OefhrIQag1i9ejAoFSGK1vF1jUQCq6E/G3oA8Rck7+S39QKLF65835X/WsFGf8fz
M9nnMugcIW3DecDwruMwydW+cQNUPTXL3OaUTaGIXdocX+wV7fFFwe9cchOq9t5V
GD3TO6VJo2/Ul+UdPo7uWw1tUIXPFnoJfpTC0sJU7UJ5PClpHaUP3XkxgOT9fKyM
e/yYP5nK/08eKrwbmm2Sa7IFvLt7ClaW6arRf49EGEXAAgmxiQlvnDLSqDXbA1uJ
vQoCEVRsBDm6vaSkozfvoYdKqAEvL7NEXxEECY+SHdfldRtJLLiDokQihTob3oUd
Wj9rhAtpAgMBAAECggEAC/F+kJtZeoIqnalqBylTWgOG+8Zc42kQ72U8y+P02l6C
hIaqfuF4hBoC0wtHdVdsREDM6KjvJmL5sfld/p0x1ZvC4EbWXikLGkzPXB2kY2Kn
2PRTzfavQXZs0yEOwHQ/93eeCZ7sPjtX9r0bWS9Xnu8PjQFQaX/F62BahC23fg/M
Q9aIDKR9EXWqBp4tekS1nevN7COy7BtxtTMzlL42Anmf6td6hXEIrXSapzAF5Ook
F2b3qjdCN6ti58iOZxq+3n50Z2mvJX0GeuRJgH2LZczxGo6mSpYNDxjEvF+j4r8z
F+x80+mi17vXPuZLwnTxawAgBLUTfy1rGYLiUaeNLQKBgQDTZfUVOMaFnm1jetY/
e3H7C1lL6Ip7qhl/0fm32BIkXYswuP1yfTr+fWdqlt3Ik2kAcIsg0DeFiS+QZ/HY
216W6WQE1ddEqes/gblgAJEGtsmuGJr7rZd2GbMFQVLi2ciy/6rShVq6ScxgkrpA
D2TNWRfB6WgAfbJiLa5larLR5QKBgQC81DnBRHvcvHrfu0lPvK1KCB2gdJKntPRW
uzO0JamdUw4Te7X4fyvumsJBgJwCUoI233CnJC5Z07bqzqzSxjigVZNolDNuGpuZ
H0tV0Y9nosaAy9OYL+4bWylUoLPZC4oSGUzYLyCFefS57YImjOk23Rj44TngN5sb
ol7+HvbLNQKBgQCKYFwMNyzj/C9YhejGhzS2AtjB8obrqg2k+LqAmARQH5dkHkNw
9P5v5YCTagvlJnD+I60+nm0pkQI8gX3y2K3TFRUugRe3T4649F52tAg6n93mgx64
Dgpt+SaRExCBg9N3MBoOUdJwzKvmr0URd8IhFOeTPAijAaSJ1aMpqa1B7QKBgGeq
6/pbKtVI9PyXyevo3gpi4kERPuKryelD5WLlunURAA1aQdEnoGris/taLExqF+sg
SKy6hGf0f9vxk5g0EyqTUNZ9Zq7wFLTAJY/7+QsgpnJXdNd8mPCT3+ECSTrDxw2g
rjuRw/0Ds4PQDUA05GSmhes9W5TpclJ9lkFVppBxAoGBAKD9+MAOxFum63p3QP4E
rVYYnx1RsyrFIYylSg8Ukuuan94xP5WxayisJnHYKzoOrkhVJ6WMjgT9t3GJADOi
wrmWQJLtjkvYZN9JQUrobttHnhsL+9qKCUQu/T3/ZI3eJ54LLgZJrbbBr29SVsQo
7xthJjNZDB89 Ac7bZKGjp0ij
-----END PRIVATE KEY-----""",
  "client_email": "firebase-adminsdk-fbsvc@wavesong.iam.gserviceaccount.com",
  "client_id": "106672444799813732979",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40wavesong.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# ==============================
# CSS PERSONALIZADO
# ==============================
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Montserrat', sans-serif;
    }
    
    .main {
        background-color: #121212;
        color: #fff;
    }
    
    .stApp {
        background: linear-gradient(180deg, #000000 0%, #121212 100%);
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #000000 0%, #121212 100%);
        color: white;
    }
    
    .player-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 80px;
        background: linear-gradient(90deg, #1DB954 0%, #1ed760 100%);
        display: flex;
        align-items: center;
        padding: 0 20px;
        z-index: 999;
    }
    
    .card {
        background: #181818;
        border-radius: 8px;
        padding: 16px;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .card:hover {
        background: #282828;
        transform: translateY(-5px);
    }
    
    .search-input {
        background-color: #282828 !important;
        color: white !important;
        border-radius: 20px !important;
    }
    
    .btn-primary {
        background-color: #1DB954 !important;
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    .btn-primary:hover {
        background-color: #1ed760 !important;
        transform: scale(1.02);
    }
    
    .modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }
    
    .modal-content {
        background: linear-gradient(135deg, #121212 0%, #181818 100%);
        border-radius: 12px;
        padding: 24px;
        width: 90%;
        max-width: 500px;
    }
    
    .now-playing {
        background: #181818;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .featured-section {
        margin-bottom: 40px;
    }
    
    .section-title {
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 20px;
        color: white;
    }
    
    .grid-container {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
        gap: 16px;
        margin-bottom: 30px;
    }
    
    .top-bar {
        background-color: rgba(0, 0, 0, 0.3);
        padding: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .mobile-search {
        display: none;
    }
    
    @media (max-width: 768px) {
        .mobile-search {
            display: block;
            margin-bottom: 20px;
        }
        
        .grid-container {
            grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        }
    }
    
    .stButton > button {
        border-radius: 20px;
        height: 40px;
        margin: 2px;
        background-color: #1DB954;
        color: white;
        border: none;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #1ed760;
        color: white;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #000000 0%, #121212 100%);
        color: white;
    }
    
    .css-1d391kg {
        background-color: #000000;
    }
    
    .css-1v3fvcr {
        background-color: #121212;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: white;
    }
    
    .stTextInput > div > div > input {
        background-color: #282828;
        color: white;
        border-radius: 20px;
    }
    
    .stMarkdown {
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================
# FUNÇÕES FIREBASE
# ==============================
def initialize_database():
    try:
        ref = db.reference('/')
        ref.child("test").set({"test": True, "timestamp": datetime.now().isoformat()})
        ref.child("test").delete()
        return True
    except Exception as e:
        return False

def get_all_songs():
    try:
        if st.session_state.firebase_connected:
            ref = db.reference("/songs")
            songs_data = ref.get()
            songs = []
            if songs_data:
                for song_id, song_data in songs_data.items():
                    song_data["id"] = song_id
                    songs.append(song_data)
            return songs
        return [{
            "id": "1",
            "title": "ESTAMOS OFFLINE",
            "artist": "Wave",
            "duration": "3:45",
            "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            "platform": "wave",
            "album": "Demo Album",
            "genre": "Electronic",
            "image_url": "https://via.placeholder.com/200x200/1DB954/FFFFFF?text=Wave+Music"
        }]
    except Exception as e:
        return []

@st.cache_data(ttl=600)
def get_all_songs_cached():
    return get_all_songs()

def add_song_to_db(song_data):
    try:
        if st.session_state.firebase_connected:
            ref = db.reference("/songs")
            existing_songs = ref.order_by_child('title').equal_to(song_data['title']).get()
            if existing_songs:
                st.warning("⚠️ Música já existente no banco de dados!")
                return False
            song_data["created_at"] = datetime.now().isoformat()
            ref.push(song_data)
            return True
        return False
    except Exception as e:
        st.error(f"❌ Erro ao adicionar música: {e}")
        return False

def add_song_request(request_data):
    try:
        if st.session_state.firebase_connected:
            ref = db.reference("/song_requests")
            request_data["created_at"] = datetime.now().isoformat()
            request_data["status"] = "pending"
            ref.push(request_data)
            return True
        return False
    except Exception as e:
        st.error(f"❌ Erro ao enviar pedido: {e}")
        return False

def search_songs(query, songs=None):
    if songs is None:
        songs = st.session_state.all_songs
    if not songs or not query:
        return songs
    query = query.lower()
    return [
        s for s in songs
        if query in s.get("title", "").lower() or
        query in s.get("artist", "").lower() or
        query in s.get("album", "").lower() or
        query in s.get("genre", "").lower()
    ]

def convert_google_drive_url(url):
    if "drive.google.com" in url and "/file/d/" in url:
        file_id = url.split("/file/d/")[1].split("/")[0]
        return f"https://lh3.googleusercontent.com/d/{file_id}=s500"
    return url

def load_image(url):
    try:
        if "drive.google.com" in url:
            url = convert_google_drive_url(url)
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return img
        else:
            return None
    except Exception as e:
        return None

@st.cache_data
def load_image_cached(url):
    return load_image(url)

def get_top6_songs():
    songs = st.session_state.all_songs
    for s in songs:
        if "play_count" not in s:
            s["play_count"] = 0
    sorted_songs = sorted(songs, key=lambda x: x["play_count"], reverse=True)
    return sorted_songs[:6]

def get_daily_random_songs(all_songs, top6_songs):
    now = datetime.now()
    
    if (st.session_state.random_songs_timestamp is None or 
        (now - st.session_state.random_songs_timestamp).total_seconds() > 24*3600 or
        not st.session_state.random_songs):
        
        remaining_songs = [s for s in all_songs if s not in top6_songs]
        st.session_state.random_songs = random.sample(remaining_songs, min(6, len(remaining_songs)))
        st.session_state.random_songs_timestamp = now
    
    return st.session_state.random_songs

# ==============================
# CONEXÃO FIREBASE
# ==============================
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://wavesong-default-rtdb.firebaseio.com/"
        })
    st.session_state.firebase_connected = True
    if initialize_database():
        st.session_state.all_songs = get_all_songs_cached()
except Exception as e:
    st.session_state.firebase_connected = False
    st.session_state.all_songs = get_all_songs_cached()

# ==============================
# FUNÇÕES AUXILIARES
# ==============================
def play_song(song):
    st.session_state.current_track = song
    st.session_state.is_playing = True

    if st.session_state.firebase_connected:
        try:
            ref = db.reference(f"/songs/{song['id']}/play_count")
            current_count = ref.get() or 0
            ref.set(current_count + 1)
        except Exception as e:
            st.error(f"Erro ao atualizar play_count: {e}")

def show_request_modal():
    st.session_state.modal_open = "request"

def show_add_modal():
    st.session_state.modal_open = "add"

def close_modals():
    st.session_state.modal_open = None

def render_modals():
    if st.session_state.modal_open == "request":
        st.markdown("""
        <div class="modal">
            <div class="modal-content">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="font-size: 20px; font-weight: bold;">Request a Song</h3>
                    <button onclick="window.parent.postMessage({type: 'closeModal'}, '*')" style="background: none; border: none; color: #aaa; cursor: pointer; font-size: 20px;">×</button>
                </div>
                <div style="display: flex; flex-direction: column; gap: 16px;">
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px;">Song Title*</label>
                        <input type="text" style="width: 100%; padding: 8px 12px; border-radius: 4px; background: #282828; color: white; border: none;">
                    </div>
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px;">Artist*</label>
                        <input type="text" style="width: 100%; padding: 8px 12px; border-radius: 4px; background: #282828; color: white; border: none;">
                    </div>
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px;">Album (optional)</label>
                        <input type="text" style="width: 100%; padding: 8px 12px; border-radius: 4px; background: #282828; color: white; border: none;">
                    </div>
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px;">Your Name (optional)</label>
                        <input type="text" style="width: 100%; padding: 8px 12px; border-radius: 4px; background: #282828; color: white; border: none;">
                    </div>
                    <button style="background: #1DB954; color: white; border: none; padding: 10px; border-radius: 20px; font-weight: 600; cursor: pointer; margin-top: 10px;">
                        Submit Request
                    </button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    elif st.session_state.modal_open == "add":
        st.markdown("""
        <div class="modal">
            <div class="modal-content">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="font-size: 20px; font-weight: bold;">Add New Song</h3>
                    <button onclick="window.parent.postMessage({type: 'closeModal'}, '*')" style="background: none; border: none; color: #aaa; cursor: pointer; font-size: 20px;">×</button>
                </div>
                <div style="display: flex; flex-direction: column; gap: 16px;">
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px;">Admin Password*</label>
                        <input type="password" style="width: 100%; padding: 8px 12px; border-radius: 4px; background: #282828; color: white; border: none;">
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div>
                            <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px;">Song Title*</label>
                            <input type="text" style="width: 100%; padding: 8px 12px; border-radius: 4px; background: #282828; color: white; border: none;">
                        </div>
                        <div>
                            <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px;">Artist*</label>
                            <input type="text" style="width: 100%; padding: 8px 12px; border-radius: 4px; background: #282828; color: white; border: none;">
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div>
                            <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px;">Album</label>
                            <input type="text" style="width: 100%; padding: 8px 12px; border-radius: 4px; background: #282828; color: white; border: none;">
                        </div>
                        <div>
                            <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px;">Genre</label>
                            <input type="text" style="width: 100%; padding: 8px 12px; border-radius: 4px; background: #282828; color: white; border: none;">
                        </div>
                    </div>
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px;">Duration*</label>
                        <input type="text" placeholder="3:45" style="width: 100%; padding: 8px 12px; border-radius: 4px; background: #282828; color: white; border: none;">
                    </div>
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px;">Audio URL*</label>
                        <input type="text" placeholder="https://example.com/audio.mp3" style="width: 100%; padding: 8px 12px; border-radius: 4px; background: #282828; color: white; border: none;">
                    </div>
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; margin-bottom: 4px;">Cover Image URL*</label>
                        <input type="text" placeholder="https://example.com/image.jpg" style="width: 100%; padding: 8px 12px; border-radius: 4px; background: #282828; color: white; border: none;">
                    </div>
                    <button style="background: #1DB954; color: white; border: none; padding: 10px; border-radius: 20px; font-weight: 600; cursor: pointer; margin-top: 10px;">
                        Add Song
                    </button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================
# SIDEBAR
# ==============================
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 40px;">
            <span style="color: #1DB954; margin-right: 8px;">🎵</span>
            <h1 style="font-size: 20px; font-weight: bold;">Wave</h1>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <nav style="display: flex; flex-direction: column; gap: 16px; margin-bottom: 40px;">
            <a href="#" style="display: flex; align-items: center; gap: 12px; color: white; text-decoration: none;">
                <span>🏠</span>
                <span>Home</span>
            </a>
            <a href="#" style="display: flex; align-items: center; gap: 12px; color: #aaa; text-decoration: none;">
                <span>🔍</span>
                <span>Search</span>
            </a>
            <a href="#" style="display: flex; align-items: center; gap: 12px; color: #aaa; text-decoration: none;">
                <span>➕</span>
                <span>Add Music</span>
            </a>
        </nav>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="margin-top: 30px;">
            <h3 style="font-size: 14px; text-transform: uppercase; color: #666; margin-bottom: 16px;">Now Playing</h3>
            <div class="now-playing">
        """, unsafe_allow_html=True)
        
        if st.session_state.current_track:
            song = st.session_state.current_track
            if song.get("image_url"):
                img = load_image_cached(song["image_url"])
                if img:
                    st.image(img, use_column_width=True)
                else:
                    st.image("https://via.placeholder.com/200x200/1DB954/FFFFFF?text=No+Image", use_column_width=True)
            else:
                st.image("https://via.placeholder.com/200x200/1DB954/FFFFFF?text=No+Image", use_column_width=True)
            
            st.write(f"**{song['title']}**")
            st.write(f"*{song['artist']}*")
            
            if st.session_state.is_playing:
                if st.button("⏸️ Pause", use_container_width=True):
                    st.session_state.is_playing = False
            else:
                if st.button("▶️ Play", use_container_width=True):
                    st.session_state.is_playing = True
                    
            if st.session_state.is_playing and song.get("audio_url"):
                st.audio(song["audio_url"], format="audio/mp3")
        else:
            st.image("https://via.placeholder.com/200x200/1DB954/FFFFFF?text=Select+a+Song", use_column_width=True)
            st.write("**No song selected**")
            st.write("*Select a song to play*")
            st.button("▶️ Play", disabled=True, use_container_width=True)

        st.markdown("</div></div>", unsafe_allow_html=True)

# ==============================
# TOP BAR
# ==============================
def render_top_bar():
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        st.markdown("""
        <div style="display: flex; align-items: center;">
            <span style="margin-right: 16px;">☰</span>
            <h1 style="font-size: 20px; font-weight: bold;">Wave</h1>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        search_query = st.text_input("", placeholder="Search for songs, artists...", 
                                   key="search_input_top", label_visibility="collapsed")
        if search_query:
            st.session_state.search_query = search_query
            st.session_state.current_page = "search"
    
    with col3:
        st.markdown("""
        <div style="display: flex; align-items: center; justify-content: flex-end; gap: 12px;">
            <button style="background: #1DB954; color: white; border: none; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: 600; cursor: pointer;">
                Upgrade
            </button>
            <div style="width: 32px; height: 32px; border-radius: 50%; background: #333; display: flex; align-items: center; justify-content: center;">
                <span>👤</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================
# MAIN CONTENT
# ==============================
def render_home_page():
    st.header("Welcome to Wave")
    
    # Mobile search (hidden on desktop)
    st.markdown("""
    <div class="mobile-search">
    """, unsafe_allow_html=True)
    mobile_search = st.text_input("", placeholder="Search for songs...", 
                                key="search_input_mobile", label_visibility="collapsed")
    if mobile_search:
        st.session_state.search_query = mobile_search
        st.session_state.current_page = "search"
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Featured Section
    st.markdown('<div class="featured-section">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-title">Featured</h3>', unsafe_allow_html=True)
    
    if st.session_state.all_songs:
        # Display featured songs
        featured_songs = st.session_state.all_songs[:6]  # First 6 as featured
        
        cols = st.columns(6)
        for i, song in enumerate(featured_songs):
            with cols[i]:
                st.markdown('<div class="card" onclick="window.parent.postMessage({type: \'playSong\', data: \'' + str(i) + '\'}, \'*\')">', unsafe_allow_html=True)
                if song.get("image_url"):
                    img = load_image_cached(song["image_url"])
                    if img:
                        st.image(img, use_column_width=True)
                    else:
                        st.image("https://via.placeholder.com/150x150/1DB954/FFFFFF?text=No+Image", use_column_width=True)
                else:
                    st.image("https://via.placeholder.com/150x150/1DB954/FFFFFF?text=No+Image", use_column_width=True)
                
                st.write(f"**{song['title']}**")
                st.write(f"*{song['artist']}*")
                st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Recently Played Section
    st.markdown('<div class="featured-section">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-title">Recently Played</h3>', unsafe_allow_html=True)
    
    if st.session_state.all_songs:
        # Display recently played (last 6 from all songs for demo)
        recent_songs = st.session_state.all_songs[-6:] if len(st.session_state.all_songs) > 6 else st.session_state.all_songs
        
        cols = st.columns(6)
        for i, song in enumerate(recent_songs):
            with cols[i]:
                st.markdown('<div class="card" onclick="window.parent.postMessage({type: \'playSong\', data: \'' + str(i) + '\'}, \'*\')">', unsafe_allow_html=True)
                if song.get("image_url"):
                    img = load_image_cached(song["image_url"])
                    if img:
                        st.image(img, use_column_width=True)
                    else:
                        st.image("https://via.placeholder.com/150x150/1DB954/FFFFFF?text=No+Image", use_column_width=True)
                else:
                    st.image("https://via.placeholder.com/150x150/1DB954/FFFFFF?text=No+Image", use_column_width=True)
                
                st.write(f"**{song['title']}**")
                st.write(f"*{song['artist']}*")
                st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Request Music Section
    st.markdown("""
    <div style="background: #181818; border-radius: 8px; padding: 24px; margin-bottom: 30px;">
        <h3 style="font-size: 20px; font-weight: 600; margin-bottom: 8px;">Can't find what you're looking for?</h3>
        <p style="color: #aaa; margin-bottom: 16px;">Request a song and we'll add it to our library</p>
        <button onclick="window.parent.postMessage({type: 'showModal', data: 'request'}, '*')" style="background: #1DB954; color: white; border: none; padding: 10px 20px; border-radius: 20px; font-weight: 600; cursor: pointer;">
            Request Music
        </button>
    </div>
    """, unsafe_allow_html=True)
    
    # Add Music Section
    
