# app.py (VERSÃO CORRIGIDA)
import streamlit as st
import firebase_admin
import requests
import datetime
import random
import time
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
    "current_track": None,        # dicionário com a música atual
    "is_playing": False,          # tocando?
    "should_autoplay": False,     # flag para só autoplay quando user seleciona música
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
# FIREBASE CONFIG (ATENÇÃO: secreta)
# ==============================
# Nota: Idealmente não deixe a chave aqui. Use variáveis de ambiente
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
        # fallback offline sample
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

# Função para converter URL do Google Drive (imagem)
def convert_google_drive_url(url):
    if "drive.google.com" in url and "/file/d/" in url:
        file_id = url.split("/file/d/")[1].split("/")[0]
        return f"https://lh3.googleusercontent.com/d/{file_id}=s500"
    return url

# Função para carregar imagem com tratamento de erro
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
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://wavesong-default-rtdb.firebaseio.com/"
        })
    st.session_state.firebase_connected = True
    if initialize_database():
        st.session_state.all_songs = get_all_songs_cached()
except Exception:
    st.session_state.firebase_connected = False
    st.session_state.all_songs = get_all_songs_cached()

# ==============================
# AÇÕES DO PLAYER (controladas centralmente)
# ==============================
def play_track(track):
    """Seleciona e inicia a track - usada por botões 'Tocar' nas listas."""
    # define current_track e marca should_autoplay para True
    st.session_state.current_track = track.copy()
    st.session_state.is_playing = True
    st.session_state.should_autoplay = True
    # aumenta play_count no Firebase
    if st.session_state.firebase_connected and track.get("id"):
        try:
            ref = db.reference(f"/songs/{track['id']}/play_count")
            current_count = ref.get() or 0
            ref.set(current_count + 1)
        except Exception:
            pass

def toggle_playpause():
    st.session_state.is_playing = not st.session_state.is_playing
    # não mudar should_autoplay aqui - apenas play/pause local

def stop_playback():
    st.session_state.current_track = None
    st.session_state.is_playing = False
    st.session_state.should_autoplay = False

def play_next():
    """Tenta tocar próxima música na lista all_songs (se houver)."""
    cur = st.session_state.current_track
    if not cur or not st.session_state.all_songs:
        return
    ids = [s.get("id") for s in st.session_state.all_songs]
    try:
        idx = ids.index(cur.get("id"))
        next_idx = (idx + 1) % len(ids)
        play_track(st.session_state.all_songs[next_idx])
    except ValueError:
        # cur não está na lista — tocar primeiro
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
# LAYOUT E CSS (estilo spotify-like)
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
.sidebar-title { font-weight:800; font-size:20px; display:flex; align-items:center; gap:8px; }
.sidebar-section { margin-top:18px; }
.menu-item { display:flex; align-items:center; gap:10px; padding:10px; border-radius:10px; color:#bfc9cf; }
.menu-item:hover { background: rgba(255,255,255,0.02); color: white; cursor:pointer; transform: translateX(4px); transition: all .12s ease; }
.search-input { background-color: #282828 !important; border-radius:20px !important; color: #e6eef2 !important; padding: 10px 14px !important; }
.card { background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); border-radius:12px; padding:10px; transition: transform .15s ease, box-shadow .15s ease; box-shadow: 0 6px 14px rgba(0,0,0,0.6); }
.card:hover { transform: translateY(-8px); box-shadow: 0 14px 30px rgba(0,0,0,0.6); }
.card img { border-radius:8px; }
.player-bar {
  position: fixed;
  left: 24px;
  right: 24px;
  bottom: 14px;
  margin: auto;
  max-width: 1200px;
  background: rgba(255,255,255,0.03);
  padding: 10px 14px;
  border-radius: 14px;
  display:flex;
  align-items:center;
  gap:12px;
  z-index: 9999;
  backdrop-filter: blur(6px);
}
.player-left { display:flex; align-items:center; gap:12px; min-width:220px; }
.player-middle { flex:1; display:flex; flex-direction:column; gap:6px; align-items:center; }
.player-controls { display:flex; align-items:center; gap:12px; }
.play-btn { background:white; color:black; width:40px; height:40px; border-radius:999px; display:flex; align-items:center; justify-content:center; font-weight:700; }
.progress { width:100%; height:6px; background: rgba(255,255,255,0.05); border-radius:12px; overflow:hidden; }
.progress-inner { height:6px; background: linear-gradient(90deg,var(--accent), #7be6c2); width: 0%; transition: width .2s linear; }
.footer-space { height:96px; } /* evita sobreposição com conteúdo */
.stButton > button { border-radius: 20px; height: 40px; margin: 2px; background-color: var(--accent); color: white; border: none; font-weight: bold; }
.stButton > button:hover { background-color: #17b44a; color: white; }
</style>
"""

st.markdown(PAGE_CSS, unsafe_allow_html=True)

# ==============================
# SIDEBAR (menu)
# ==============================
with st.sidebar:
    st.markdown("<div class='sidebar-title'>🌊 <span>Wave</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-section'>Uma plataforma protótipo com visual inspirado no Spotify.</div>", unsafe_allow_html=True)
    st.markdown("---")
    status_msg = "✅ Online" if st.session_state.firebase_connected else "⚠️ Offline"
    st.markdown(f"**Status:** {status_msg}")
    st.markdown("---")

    if st.button("Página Inicial", key="btn_home", use_container_width=True):
        st.session_state.current_page = "home"
        st.session_state.show_request_form = False
    if st.button("Buscar Músicas", key="btn_search", use_container_width=True):
        st.session_state.current_page = "search"
        st.session_state.show_request_form = False
    if st.button("Adicionar Música", key="btn_add", use_container_width=True):
        st.session_state.current_page = "add"
        st.session_state.show_request_form = False

    st.markdown("---")
    st.write("🎧 Tocando agora")
    # Sidebar mostra apenas a música que está realmente tocando (current_track)
    if st.session_state.current_track:
        c = st.session_state.current_track
        img_obj = None
        if c.get("image_url"):
            img_obj = load_image_cached(c["image_url"])
        if img_obj:
            st.image(img_obj, use_column_width=True)
        else:
            st.image(c.get("image_url") or "https://via.placeholder.com/200x200/1DB954/FFFFFF?text=Sem+Imagem", use_column_width=True)
        st.markdown(f"**{c.get('title','-')}**")
        st.markdown(f"*{c.get('artist','-')}*")
        st.caption(f"Duração: {c.get('duration','-')}")
        if st.session_state.is_playing:
            if st.button("Pausar", use_container_width=True, key="sidebar_pause"):
                toggle_playpause()
        else:
            if st.button("Tocar", use_container_width=True, key="sidebar_play"):
                toggle_playpause()
    else:
        st.info("🔍 Escolha uma música")

# ==============================
# PÁGINAS PRINCIPAIS
# ==============================
def show_request_music_section():
    st.markdown("### 🎵 Não encontrou a música que procura?")
    if st.button("Pedir Música +", use_container_width=True):
        st.session_state.show_request_form = True

    if st.session_state.show_request_form:
        with st.form("request_music_form", clear_on_submit=True):
            st.write("#### Solicitar Nova Música")
            col1, col2 = st.columns(2)
            with col1:
                req_title = st.text_input("Título da Música*", placeholder="Ex: Boate Azul")
                req_artist = st.text_input("Artista*", placeholder="Ex: Bruno & Marrone")
            with col2:
                req_album = st.text_input("Álbum (se conhecido)")
                req_username = st.text_input("Seu nome (opcional)")
            submitted = st.form_submit_button("Enviar Pedido")
            if submitted:
                if not all([req_title, req_artist]):
                    st.error("⚠️ Preencha pelo menos o título e artista!")
                else:
                    request_data = {
                        "title": req_title,
                        "artist": req_artist,
                        "album": req_album,
                        "requested_by": req_username or "Anônimo"
                    }
                    if add_song_request(request_data):
                        st.success("✅ Pedido enviado com sucesso! Adicionaremos em breve.")
                        st.session_state.show_request_form = False
                    else:
                        st.error("❌ Erro ao enviar pedido. Tente novamente.")

def page_home():
    st.markdown("<h2 style='margin-top:6px'>🌊 Bem-vindo ao Wave</h2>", unsafe_allow_html=True)
    if not st.session_state.all_songs:
        st.session_state.all_songs = get_all_songs_cached()

    # Caixa de busca
    cols_search = st.columns([3,1])
    with cols_search[0]:
        new_query = st.text_input("Buscar música:", placeholder="Digite o nome da música ou artista...")
    with cols_search[1]:
        if st.button("Pesquisar"):
            st.session_state.search_query = new_query.strip()
            st.session_state.current_page = "search"
            st.experimental_rerun()

    total_musicas = len(st.session_state.all_songs)
    st.markdown(f"### Temos {total_musicas} Músicas Disponíveis")
    st.markdown("### Músicas em destaque:")

    if st.session_state.all_songs:
        top6_songs = get_top6_songs()
        random6 = get_daily_random_songs(st.session_state.all_songs, top6_songs)
        songs_to_show = top6_songs + random6

        # grid responsivo: 6 por linha
        rows = (len(songs_to_show) + 5) // 6
        idx = 0
        for r in range(rows):
            cols = st.columns(6, gap="small")
            for ccol in cols:
                if idx >= len(songs_to_show):
                    break
                s = songs_to_show[idx]
                with ccol:
                    # cover
                    cover = s.get("image_url")
                    if cover:
                        img = load_image_cached(cover)
                        if img:
                            st.image(img, width=150)
                        else:
                            st.image("https://via.placeholder.com/150x150/1DB954/FFFFFF?text=Imagem+Não+Carregada")
                    else:
                        st.image("https://via.placeholder.com/150x150/1DB954/FFFFFF?text=Sem+Imagem")
                    st.markdown(f"**{s.get('title','-')}**")
                    st.markdown(f"*{s.get('artist','-')}*")
                    btn_key = f"home_play_{s.get('id','h_'+str(idx))}"
                    if st.button("▶️ Tocar", key=btn_key, use_container_width=True):
                        play_track(s)
                idx += 1

        st.markdown("---")
        show_request_music_section()
    else:
        st.info("Nenhuma música encontrada.")
        show_request_music_section()

def page_search():
    st.markdown("<h2>🔎 Buscar Músicas</h2>", unsafe_allow_html=True)
    query = st.text_input("Digite o nome do artista, música ou gênero:", value=st.session_state.search_query or "")
    if st.button("Pesquisar"):
        st.session_state.search_query = query.strip()

    results = []
    if st.session_state.all_songs and st.session_state.search_query:
        results = search_songs(st.session_state.search_query)
    elif st.session_state.all_songs and query:
        results = search_songs(query)

    if results:
        cols = st.columns(4, gap="large")
        for i, s in enumerate(results):
            with cols[i % 4]:
                if s.get("image_url"):
                    img = load_image_cached(s["image_url"])
                    if img:
                        st.image(img, width=160)
                    else:
                        st.image("https://via.placeholder.com/150x150/1DB954/FFFFFF?text=Imagem+Não+Carregada")
                else:
                    st.image("https://via.placeholder.com/150x150/1DB954/FFFFFF?text=Sem+Imagem")
                st.markdown(f"**{s.get('title','-')}**")
                st.markdown(f"*{s.get('artist','-')}*")
                if st.button("▶️ Tocar", key=f"search_play_{i}", use_container_width=True):
                    play_track(s)
        st.markdown("---")
        show_request_music_section()
    else:
        st.info("Nenhuma música encontrada com essa pesquisa.")
        show_request_music_section()

def page_add():
    st.markdown("<h2>➕ Adicionar Música (Admin)</h2>", unsafe_allow_html=True)
    if not st.session_state.admin_authenticated:
        password = st.text_input("Senha de Administrador", type="password")
        if st.button("Acessar"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("✅ Acesso concedido!")
            else:
                st.error("❌ Senha incorreta!")
        return
    # admin authenticated
    if st.session_state.show_add_form:
        with st.form("add_music_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input("Título*", placeholder="Ex: Boate Azul")
                artist = st.text_input("Artista*", placeholder="Ex: Bruno & Marrone")
                album = st.text_input("Álbum")
                genre = st.text_input("Gênero")
            with col2:
                duration = st.text_input("Duração*", placeholder="Ex: 3:45")
                audio_url = st.text_input("URL do áudio*", placeholder="https://exemplo.com/audio.mp3")
                image_url = st.text_input("URL da Capa*", placeholder="https://drive.google.com/...")
            submitted = st.form_submit_button("🌊 Adicionar Música")
            if submitted:
                if not all([title, artist, duration, audio_url, image_url]):
                    st.error("⚠️ Preencha todos os campos obrigatórios (*)")
                else:
                    new_song = {
                        "title": title,
                        "artist": artist,
                        "duration": duration,
                        "audio_url": audio_url,
                        "image_url": image_url,
                        "platform": "wave",
                        "album": album,
                        "genre": genre
                    }
                    if add_song_to_db(new_song):
                        st.success("✅ Música adicionada com sucesso!")
                        st.session_state.show_add_form = False
                        st.session_state.all_songs = get_all_songs_cached()
                    else:
                        st.error("❌ Erro ao adicionar música.")
    else:
        st.info("Clique abaixo para adicionar uma nova música")
        if st.button("Mostrar Formulário"):
            st.session_state.show_add_form = True
        if st.button("🔒 Sair do Modo Admin"):
            st.session_state.admin_authenticated = False
            st.session_state.show_add_form = False

# Render pages
if st.session_state.current_page == "home":
    page_home()
elif st.session_state.current_page == "search":
    page_search()
elif st.session_state.current_page == "add":
    page_add()
else:
    page_home()

# ==============================
# FOOTER / PLAYER (fixo)
# ==============================
# espaço para não cobrir o conteúdo
st.markdown("<div class='footer-space'></div>", unsafe_allow_html=True)

current = st.session_state.current_track
if current:
    # Preferir campo audio_url (compatibilidade com seu DB)
    audio_src = current.get("audio_url") or current.get("url") or ""
    # image: prefira image_url para compatibilidade com seu DB
    cover = current.get("image_url") or current.get("cover") or ""
    title = current.get("title", "Sem título")
    artist = current.get("artist", "Sem artista")
    duration = current.get("duration", "0:00")

    # autoplay somente se should_autoplay estiver True (quando o usuário clicou em 'Tocar' agora)
    autoplay_attr = "autoplay" if st.session_state.should_autoplay and st.session_state.is_playing else ""

    # Render player HTML (uso do audio nativo)
    player_html = f"""
    <div class="player-bar" role="region" aria-label="player-bar">
      <div class="player-left">
        <img src="{cover or 'https://via.placeholder.com/80x80/1DB954/FFFFFF?text=Sem+Imagem'}" width="56" height="56" style="border-radius:8px;object-fit:cover"/>
        <div>
          <div style="font-weight:700">{title}</div>
          <div style="color:#bcd3df;font-size:13px">{artist}</div>
        </div>
      </div>
      <div class="player-middle">
        <div class="player-controls">
          <button id="prevBtnClient" style="background:transparent;border:none;color:white;cursor:pointer">⏮️</button>
          <button id="playPauseBtnClient" class="play-btn">{'▶' if not st.session_state.is_playing else '❚❚'}</button>
          <button id="nextBtnClient" style="background:transparent;border:none;color:white;cursor:pointer">⏭️</button>
        </div>
        <div style="width:100%;display:flex;align-items:center;gap:8px">
          <span style="font-size:12px;">0:00</span>
          <div style="flex:1;">
            <div class="progress"><div class="progress-inner" style="width:0%"></div></div>
          </div>
          <span style="font-size:12px;">{duration}</span>
        </div>
      </div>
      <div style="min-width:160px;display:flex;gap:10px;align-items:center;justify-content:flex-end">
        <audio id="wave_audio" controls {autoplay_attr} style="width:260px;">
          <source src="{audio_src}" type="audio/mpeg">
          Seu navegador não suporta o elemento de áudio.
        </audio>
      </div>
    </div>

    player_html = f"""
<script>
function findAndClickHiddenBtn(textMatch) {{
    // procura buttons do Streamlit com o label correspondente e "clica" (simula).
    const buttons = window.parent.document.querySelectorAll('button');
    for (let b of buttons) {{
        if (b.innerText && b.innerText.trim().includes(textMatch)) {{
            b.click();
            return true;
        }}
    }}
    return false;
}}
</script>
"""


    """

    st.markdown(player_html, unsafe_allow_html=True)

# Hidden server-side hooks: pequenos botões que o JS acima "clica" para enviar eventos ao servidor.
# Nome dos botões: 'Prev', 'Next', 'PLAYPAUSE_HOOK'
col_hook1, col_hook2, col_hook3 = st.columns([1,1,6])
with col_hook1:
    if st.button("Prev", key="prev_hook"):
        play_prev()
with col_hook2:
    if st.button("Next", key="next_hook"):
        play_next()
with col_hook3:
    # botao invisivel para JS acionar pausa/play
    if st.button("PLAYPAUSE_HOOK", key="playpause_hook", help="hook playpause"):
        toggle_playpause()

# Após renderizar o player, se should_autoplay foi True, consumimos a flag
# (evita que futuros reruns façam autoplay novamente automaticamente).
if st.session_state.should_autoplay:
    # Definimos para False — isso provoca um rerun, porém agora autoplay flag está consumida.
    st.session_state.should_autoplay = False
    # NOTA: isso causará um rerun imediato para sincronizar o estado; o áudio iniciado pelo navegador NÃO será interrompido
    # porque o audio já recebeu o comando 'autoplay' no render anterior. Isso evita reiniciar em navegações subsequentes.
    st.experimental_rerun()

# ==============================
# RODAPÉ
# ==============================
st.markdown("---")
st.caption("🌊 Wave - Sua música, seu mundo • Protótipo ")
