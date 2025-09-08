# app.py (COMPLETO E FUNCIONAL)
import streamlit as st
import firebase_admin
import requests
import datetime
import random
from firebase_admin import credentials, db
from io import BytesIO
from PIL import Image

# ==============================
# CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
    page_title="Wave - Sua Música, Seu Mundo",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# SESSION STATE PADRÃO
# ==============================
defaults = {
    "current_track": None,
    "is_playing": False,
    "should_autoplay": False,
    "volume": 100,
    "search_query": "",
    "current_page": "home",
    "music_history": [],
    "all_songs": [],
    "show_add_form": False,
    "firebase_connected": False,
    "show_request_form": False,
    "admin_authenticated": False,
    "random_songs": [],
    "random_songs_timestamp": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==============================
# CONFIGURAÇÕES DE SEGURANÇA
# ==============================
ADMIN_PASSWORD = "wavesong9090"

# ==============================
# FUNÇÕES FIREBASE
# ==============================
def initialize_database():
    try:
        ref = db.reference('/')
        ref.child("test").set({"test": True, "timestamp": datetime.datetime.now().isoformat()})
        ref.child("test").delete()
        return True
    except Exception:
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
            "artist": "!",
            "duration": "3:45",
            "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            "image_url": "",
            "platform": "wave",
            "album": "!",
            "genre": "!"
        }]
    except Exception:
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
            song_data["created_at"] = datetime.datetime.now().isoformat()
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
            request_data["created_at"] = datetime.datetime.now().isoformat()
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
        if not url:
            return None
        if "drive.google.com" in url:
            url = convert_google_drive_url(url)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return img
        else:
            return None
    except Exception:
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
    now = datetime.datetime.now()
    if (st.session_state.random_songs_timestamp is None or
        (now - st.session_state.random_songs_timestamp).total_seconds() > 24*3600 or
        not st.session_state.random_songs):
        remaining_songs = [s for s in all_songs if s not in top6_songs]
        if remaining_songs:
            st.session_state.random_songs = random.sample(remaining_songs, min(6, len(remaining_songs)))
        else:
            st.session_state.random_songs = []
        st.session_state.random_songs_timestamp = now
    return st.session_state.random_songs

# ==============================
# CONEXÃO FIREBASE
# ==============================
try:
    if not firebase_admin._apps:
        # Coloque aqui seu arquivo de credenciais JSON
        cred = credentials.Certificate("firebase_credentials.json")
        firebase_admin.initialize_app(cred, {"databaseURL": "https://wavesong-default-rtdb.firebaseio.com/"})
    st.session_state.firebase_connected = True
    if initialize_database():
        st.session_state.all_songs = get_all_songs_cached()
except Exception:
    st.session_state.firebase_connected = False
    st.session_state.all_songs = get_all_songs_cached()

# ==============================
# FUNÇÕES DE PLAYER
# ==============================
def play_track(track):
    st.session_state.current_track = track.copy()
    st.session_state.is_playing = True
    st.session_state.should_autoplay = True
    if st.session_state.firebase_connected and track.get("id"):
        try:
            ref = db.reference(f"/songs/{track['id']}/play_count")
            current_count = ref.get() or 0
            ref.set(current_count + 1)
        except Exception:
            pass

def toggle_playpause():
    st.session_state.is_playing = not st.session_state.is_playing

def stop_playback():
    st.session_state.current_track = None
    st.session_state.is_playing = False
    st.session_state.should_autoplay = False

def play_next():
    cur = st.session_state.current_track
    if not cur or not st.session_state.all_songs:
        return
    ids = [s.get("id") for s in st.session_state.all_songs]
    try:
        idx = ids.index(cur.get("id"))
        next_idx = (idx + 1) % len(ids)
        play_track(st.session_state.all_songs[next_idx])
    except ValueError:
        play_track(st.session_state.all_songs[0])

def play_prev():
    cur = st.session_state.current_track
    if not cur or not st.session_state.all_songs:
        return
    ids = [s.get("id") for s in st.session_state.all_songs]
    try:
        idx = ids.index(cur.get("id"))
        prev_idx = (idx - 1) % len(ids)
        play_track(st.session_state.all_songs[prev_idx])
    except ValueError:
        play_track(st.session_state.all_songs[0])

# ==============================
# CSS PERSONALIZADO
# ==============================
PAGE_CSS = """
<style>
:root{
  --bg:#0f1114;
  --panel:#121214;
  --muted:#b7c1c7;
  --accent:#1DB954;
  --card:#181818;
}
body { background: linear-gradient(180deg,#071119 0%,#081421 60%, #000 100%); color: #e6eef2; font-family: 'Montserrat', sans-serif; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #000000 0%, #0f1114 100%); color: #fff; }
.stButton>button { border-radius:20px; height:40px; margin:2px; background-color: var(--accent); color:white; border:none; font-weight:bold; }
.stButton>button:hover { background-color:#17b44a; color:white; }
</style>
"""
st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("### 🌊 Wave")
    status_msg = "✅ Online" if st.session_state.firebase_connected else "⚠️ Offline"
    st.markdown(f"**Status:** {status_msg}")
    if st.button("Página Inicial", key="btn_home"):
        st.session_state.current_page = "home"
    if st.button("Buscar Músicas", key="btn_search"):
        st.session_state.current_page = "search"
    if st.button("Adicionar Música", key="btn_add"):
        st.session_state.current_page = "add"

# ==============================
# PÁGINAS
# ==============================
def show_request_music_section():
    st.markdown("### 🎵 Pedido de Música")
    if st.session_state.show_request_form:
        with st.form("request_music_form", clear_on_submit=True):
            title = st.text_input("Título da música*")
            artist = st.text_input("Artista*")
            album = st.text_input("Álbum")
            username = st.text_input("Seu nome (opcional)")
            submitted = st.form_submit_button("Enviar")
            if submitted:
                if not title or not artist:
                    st.error("Preencha título e artista!")
                else:
                    request_data = {
                        "title": title, "artist": artist,
                        "album": album, "requested_by": username or "Anônimo"
                    }
                    if add_song_request(request_data):
                        st.success("Pedido enviado!")
                        st.session_state.show_request_form = False

def page_home():
    st.markdown("## 🌊 Página Inicial")
    if st.session_state.all_songs:
        top6 = get_top6_songs()
        random6 = get_daily_random_songs(st.session_state.all_songs, top6)
        songs_to_show = top6 + random6
        rows = (len(songs_to_show)+5)//6
        idx = 0
        for _ in range(rows):
            cols = st.columns(6)
            for col in cols:
                if idx >= len(songs_to_show): break
                s = songs_to_show[idx]
                with col:
                    img = load_image_cached(s.get("image_url"))
                    if img:
                        st.image(img, width=120)
                    else:
                        st.image("https://via.placeholder.com/120")
                    st.markdown(f"**{s.get('title','-')}**")
                    st.markdown(f"*{s.get('artist','-')}*")
                    btn_key = f"home_play_{idx}"
                    if st.button("▶️ Tocar", key=btn_key):
                        play_track(s)
                idx += 1
    show_request_music_section()

def page_search():
    st.markdown("## 🔎 Buscar Músicas")
    query = st.text_input("Pesquisar:", value=st.session_state.search_query)
    if st.button("Pesquisar"):
        st.session_state.search_query = query
    results = search_songs(st.session_state.search_query)
    if results:
        cols = st.columns(4)
        for i, s in enumerate(results):
            with cols[i % 4]:
                img = load_image_cached(s.get("image_url"))
                if img:
                    st.image(img, width=120)
                else:
                    st.image("https://via.placeholder.com/120")
                st.markdown(f"**{s.get('title','-')}**")
                st.markdown(f"*{s.get('artist','-')}*")
                if st.button("▶️ Tocar", key=f"search_play_{i}"):
                    play_track(s)
    show_request_music_section()

def page_add():
    st.markdown("## ➕ Adicionar Música (Admin)")
    if not st.session_state.admin_authenticated:
        password = st.text_input("Senha Admin", type="password")
        if st.button("Acessar"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("Acesso permitido!")
            else:
                st.error("Senha incorreta!")
        return
    if st.session_state.show_add_form:
        with st.form("add_music_form", clear_on_submit=True):
            title = st.text_input("Título*")
            artist = st.text_input("Artista*")
            album = st.text_input("Álbum")
            genre = st.text_input("Gênero")
            duration = st.text_input("Duração*")
            audio_url = st.text_input("URL do áudio*")
            image_url = st.text_input("URL da capa*")
            submitted = st.form_submit_button("Adicionar Música")
            if submitted:
                if not all([title, artist, duration, audio_url, image_url]):
                    st.error("Preencha todos os campos obrigatórios")
                else:
                    song_data = {
                        "title": title, "artist": artist, "album": album,
                        "genre": genre, "duration": duration,
                        "audio_url": audio_url, "image_url": image_url,
                        "platform": "wave"
                    }
                    if add_song_to_db(song_data):
                        st.success("Música adicionada!")
                        st.session_state.show_add_form = False
                        st.session_state.all_songs = get_all_songs_cached()
    else:
        if st.button("Mostrar Formulário"):
            st.session_state.show_add_form = True
        if st.button("Sair do Modo Admin"):
            st.session_state.admin_authenticated = False

# ==============================
# RENDERIZAÇÃO DA PÁGINA ATUAL
# ==============================
if st.session_state.current_page == "home":
    page_home()
elif st.session_state.current_page == "search":
    page_search()
elif st.session_state.current_page == "add":
    page_add()
else:
    page_home()

# ==============================
# PLAYER FIXO (RODAPÉ)
# ==============================
st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
current = st.session_state.current_track
if current:
    audio_src = current.get("audio_url") or ""
    cover = current.get("image_url") or ""
    title = current.get("title","Sem título")
    artist = current.get("artist","Sem artista")
    duration = current.get("duration","0:00")
    autoplay = "autoplay" if st.session_state.should_autoplay and st.session_state.is_playing else ""
    st.markdown(f"""
    <div style="position:fixed;bottom:10px;left:10px;right:10px;background:rgba(0,0,0,0.5);padding:10px;border-radius:12px;display:flex;align-items:center;gap:10px;">
        <img src="{cover or 'https://via.placeholder.com/50'}" width="50" height="50" style="border-radius:6px"/>
        <div>
            <div style="font-weight:bold;color:white">{title}</div>
            <div style="color:#ccc;font-size:12px">{artist}</div>
        </div>
        <audio controls {autoplay} style="margin-left:auto;">
            <source src="{audio_src}" type="audio/mpeg">
        </audio>
    </div>
    """, unsafe_allow_html=True)
