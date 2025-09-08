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
            "artist": "!",
            "duration": "3:45",
            "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
            "platform": "wave",
            "album": "!",
            "genre": "!"
        }]
    except Exception as e:
        return []

@st.cache_data(ttl=600)  # cache por 10 minutos
def get_all_songs_cached():
    return get_all_songs()

def add_song_to_db(song_data):
    try:
        if st.session_state.firebase_connected:
            ref = db.reference("/songs")
            # Verificar se a música já existe no banco
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


# Função para converter URL do Google Drive
def convert_google_drive_url(url):
    if "drive.google.com" in url and "/file/d/" in url:
        file_id = url.split("/file/d/")[1].split("/")[0]
        return f"https://lh3.googleusercontent.com/d/{file_id}=s500"
    return url

# Função para carregar imagem com tratamento de erro
def load_image(url):
    try:
        # Para URLs do Google Drive, use a conversão
        if "drive.google.com" in url:
            url = convert_google_drive_url(url)
        
        # Tenta carregar a imagem
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
    # Define play_count 0 se não existir
    for s in songs:
        if "play_count" not in s:
            s["play_count"] = 0
    # Ordena decrescente
    sorted_songs = sorted(songs, key=lambda x: x["play_count"], reverse=True)
    return sorted_songs[:6]

def get_daily_random_songs(all_songs, top6_songs):
    now = datetime.datetime.now()
    
    # Se não existe ou passou mais de 24h, gerar nova lista
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
    if not st.session_state.is_playing:
        st.session_state.is_playing = True

    if st.session_state.firebase_connected:
        try:
            ref = db.reference(f"/songs/{song['id']}/play_count")
            current_count = ref.get() or 0
            ref.set(current_count + 1)
        except Exception as e:
            st.error(f"Erro ao atualizar play_count: {e}")


def show_add_music_page():
    st.header("Adicionar Nova Música")
    
    # Verificar autenticação
    if not st.session_state.admin_authenticated:
        password = st.text_input("Senha de Administrador", type="password")
        if st.button("Acessar"):
            if password == ADMIN_PASSWORD: 
                st.session_state.admin_authenticated = True
                st.success("✅ Acesso concedido!")
                #st.rerun()
            else:
                st.error("❌ Senha incorreta!")
        return
    
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
                    return
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
            st.rerun()

def show_request_music_section():
    st.markdown("---")
    st.subheader("Não encontrou a música que procura?")
    
    if st.button("Pedir Música +", use_container_width=True):
        st.session_state.show_request_form = True
        
    if st.session_state.show_request_form:
        with st.form("request_music_form", clear_on_submit=True):
            st.write("### Solicitar Nova Música")
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
                    return
                    
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

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.title("🌊 Wave Song")
    st.success("✅ Online" if st.session_state.firebase_connected else "⚠️ Offline")

    if st.session_state.current_track:
        song = st.session_state.current_track
        st.subheader("🎧 Tocando agora")
        if song.get("image_url"):
            img = load_image_cached(song["image_url"])
            if img:
                st.image(img)
            else:
                st.image("https://via.placeholder.com/200x200/1DB954/FFFFFF?text=Imagem+Não+Carregada", caption="Imagem não carregada")
        else:
            st.image("https://via.placeholder.com/200x200/1DB954/FFFFFF?text=Sem+Imagem", caption="Imagem não disponível")
        st.write(f"**{song['title']}**")
        st.write(f"*{song['artist']}*")
        st.caption(f"Duração: {song.get('duration', 'N/A')}")

        if st.session_state.is_playing:
            if st.button("Pausar", use_container_width=True):
                st.session_state.is_playing = False
        else:
            if st.button("Tocar (2 clique)", use_container_width=True):
                st.session_state.is_playing = True

        if song.get("audio_url"):
            render_player()

    else:
        st.info("🔍 Escolha uma música")

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



# ==============================
# PÁGINAS
# ==============================
if st.session_state.current_page == "home":
    st.header("🌊 Bem-vindo ao Wave")
    
    if not st.session_state.all_songs:
        st.session_state.all_songs = get_all_songs_cached()

    # Caixa de busca
    new_query = st.text_input("Buscar música:", placeholder="Digite o nome da música ou artista...")
    if new_query.strip():
        st.session_state.search_input = new_query.strip()
        st.session_state.current_page = "search"
        st.rerun()

    total_musicas = len(st.session_state.all_songs)
    st.markdown(f"### Temos {total_musicas} Músicas Disponíveis")
    st.markdown("### Músicas em destaque:")
    
    if st.session_state.all_songs:
        # 6 músicas mais ouvidas
        top6_songs = get_top6_songs()

        # 6 aleatórias fixas por 24h
        random6 = get_daily_random_songs(st.session_state.all_songs, top6_songs)

        songs_to_show = top6_songs + random6

        for row in range(2):
            cols = st.columns(6)
            for i in range(6):
                idx = row*6 + i
                if idx >= len(songs_to_show):
                    break
                song = songs_to_show[idx]
                with cols[i]:
                    if song.get("image_url"):
                        img = load_image_cached(song["image_url"])
                        if img:
                            st.image(img, width=150)
                        else:
                            st.image("https://via.placeholder.com/150x150/1DB954/FFFFFF?text=Imagem+Não+Carregada")
                    else:
                        st.image("https://via.placeholder.com/150x150/1DB954/FFFFFF?text=Sem+Imagem")

                    st.write(f"**{song['title']}**")
                    st.write(f"*{song['artist']}*")

                    song_key = song.get("id", f"home_{idx}")
                    if st.button("Tocar (2 clique)", key=f"play_{song_key}", use_container_width=True):
                        play_song(song)
                        
        # Mostrar seção de pedidos de música
        show_request_music_section()
    else:
        st.info("Nenhuma música encontrada.")
        show_request_music_section()

elif st.session_state.current_page == "search":
    st.header("Buscar Músicas")

    if "search_input" not in st.session_state:
        st.session_state.search_input = ""

    search_input = st.text_input("Digite o nome da música ou artista...", key="search_input")

    if st.session_state.all_songs:
        results = search_songs(st.session_state.search_input)
        if results:
            cols = st.columns(4)
            for i, song in enumerate(results):
                with cols[i % 4]:
                    if song.get("image_url"):
                        img = load_image_cached(song["image_url"])
                        if img:
                            st.image(img)
                        else:
                            st.image("https://via.placeholder.com/150x150/1DB954/FFFFFF?text=Imagem+Não+Carregada", caption="Imagem não carregada")
                    else:
                        st.image("https://via.placeholder.com/150x150/1DB954/FFFFFF?text=Sem+Imagem", caption="Imagem não disponível")
                    st.write(f"**{song['title']}**")
                    st.write(f"*{song['artist']}*")
                    if st.button("Tocar (2 clique)", key=f"search_{i}", use_container_width=True):
                        play_song(song)
                        #st.rerun()
                        
            # Mostrar seção de pedidos de música
            show_request_music_section()
            
        else:
            st.warning("Nenhuma música encontrada.")
            show_request_music_section()
    else:
        st.info("Nenhuma música cadastrada.")
        show_request_music_section()

elif st.session_state.current_page == "add":
    show_add_music_page()



# ==============================
# FOOTER + CSS
# ==============================
st.markdown("---")
st.caption("🌊 Wave - Sua música, seu mundo • Site em Protótipo ")
st.markdown("""
<style>
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
# RENDER PLAYER COM AUTOPLAY
# ==============================
def render_player():
    track = st.session_state.current_track
    if not track:
        st.info("🔍 Escolha uma música para tocar.")
        return

    audio_src = track.get("audio_url", "")
    cover = track.get("image_url", "https://via.placeholder.com/80x80?text=Sem+Imagem")
    title = track.get("title", "Sem título")
    artist = track.get("artist", "Sem artista")
    duration = track.get("duration", "0:00")
    autoplay_attr = "autoplay" if st.session_state.is_playing else ""

    player_html = f"""
    <div style="position:fixed;bottom:10px;left:10px;right:10px;background:rgba(0,0,0,0.5);
                padding:10px;border-radius:12px;display:flex;align-items:center;gap:10px;z-index:999;">
        <img src="{cover}" width="50" height="50" style="border-radius:8px"/>
        <div>
            <div style="font-weight:bold;color:white">{title}</div>
            <div style="color:#ccc;font-size:12px">{artist}</div>
        </div>
        <audio controls {autoplay_attr} style="margin-left:auto;">
            <source src="{audio_src}" type="audio/mpeg">
            Seu navegador não suporta o elemento de áudio.
        </audio>
    </div>
    """
    st.markdown(player_html, unsafe_allow_html=True)

