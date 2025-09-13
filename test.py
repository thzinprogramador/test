import streamlit as st
import firebase_admin
import requests 
import datetime
import random
import time
import base64
from firebase_admin import credentials, db
from io import BytesIO
from PIL import Image


# ==============================
# CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
    page_title="Wave",
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
if "search_input" not in st.session_state:
    st.session_state.search_input = ""
if "player_timestamp" not in st.session_state:
    st.session_state.player_timestamp = time.time()
if "popup_closed" not in st.session_state:
    st.session_state.popup_closed = False
if "popup_shown" not in st.session_state:
    st.session_state.popup_shown = False


# ==============================
# CONFIGURAÇÕES DE SEGURANÇA
# ==============================
ADMIN_PASSWORD = "wavesong9090" 

# ==============================
# FUNÇÃO PARA O POP-UP DE BOAS-VINDAS (CORRIGIDA)
# ==============================
def show_welcome_popup():
    # Verifica se o popup já foi fechado ou já foi mostrado
    if st.session_state.popup_closed or st.session_state.popup_shown:
        return

    # Usar container vazio para evitar renderização duplicada
    with st.empty():
        # CSS do popup
        st.markdown("""
            <style>
            .ws-overlay {
                position: fixed;
                top: 0; left: 0;
                width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.7);
                z-index: 9998;
            }
            .ws-popup {
                position: fixed;
                top: 50%; left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.4);
                backdrop-filter: blur(12px);
                border: 2px solid #1DB954;
                border-radius: 15px;
                padding: 25px;
                width: 45%;
                color: white;
                text-align: center;
                z-index: 9999;
            }
            .ws-popup h2 { margin-top: 0; }
            .ws-instructions {
                background: rgba(0,0,0,0.5);
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: left;
            }
            .ws-close {
                position: absolute;
                top: 8px; right: 12px;
                font-size: 20px;
                font-weight: bold;
                color: white;
                cursor: pointer;
            }
            .ws-close:hover { color: #1DB954; }
            </style>
        """, unsafe_allow_html=True)

        # HTML do popup com botão de fechar
        st.markdown(f"""
            <div class="ws-overlay"></div>
            <div class="ws-popup">
                <span class="ws-close" onclick="window.parent.document.querySelector('[data-testid=\\'stMarkdown\\'] iframe').contentWindow.closePopup()">×</span>
                <h2>🌊 Bem-vindo ao Wave!</h2>
                <p style="opacity:0.8; font-size:14px;">Site em desenvolvimento!</p>

                <div class="ws-instructions">
                    <h4>🎯 Instruções Importantes:</h4>
                    <ol>
                        <li>Clique nos <b>'3 pontinhos'</b> no canto superior direito</li>
                        <li>Vá em <b>Settings</b></li>
                        <li>Escolha <b>"Dark theme"</b> para melhor experiência</li>
                    </ol>
                </div>

                <div style="font-size:12px; opacity:0.7; margin-top:20px;">
                    Shutz agradece, bom proveito!!! 🎵
                </div>

                <p style="font-size:12px; opacity:0.6;">Este pop-up será fechado automaticamente em 5 segundos...</p>
            </div>
        """, unsafe_allow_html=True)

        # JavaScript para fechar o popup
        st.markdown("""
            <script>
            function closePopup() {
                window.parent.document.querySelectorAll('.ws-overlay, .ws-popup').forEach(el => el.remove());
            }
            
            // Fechar automaticamente após 5 segundos
            setTimeout(closePopup, 5000);
            </script>
        """, unsafe_allow_html=True)
        
        # Marcar como mostrado
        st.session_state.popup_shown = True
        
        # Aguardar um pouco e então limpar
        time.sleep(5.1)
        
    # Limpar completamente após o tempo
    st.session_state.popup_closed = True

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
        ref.child("test").set({"test": True, "timestamp": datetime.datetime.now().isoformat()})
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
            "audio_url": "www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
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
# FUNÇÃO DE CONVERSÃO DE URL CORRIGIDA
# ==============================
def convert_github_to_jsdelivr(url):
    """
    Converte URLs do github.com para cdn.jsdelivr.net
    Suporta dois formatos:
    1. https://github.com/usuario/repo/raw/ramo/caminho/arquivo
    2. https://raw.githubusercontent.com/usuario/repo/ramo/caminho/arquivo
    """
    if "github.com" in url:
        if "/raw/" in url:
            # Formato 1: github.com/.../raw/...
            parts = url.split("/")
            user = parts[3]
            repo = parts[4]
            branch = parts[6]
            file_path = "/".join(parts[7:])
            return f"https://cdn.jsdelivr.net/gh/{user}/{repo}@{branch}/{file_path}"
        elif "raw.githubusercontent.com" in url:
            # Formato 2: raw.githubusercontent.com/...
            parts = url.split("/")
            user = parts[3]
            repo = parts[4]
            branch = parts[5]
            file_path = "/".join(parts[6:])
            return f"https://cdn.jsdelivr.net/gh/{user}/{repo}@{branch}/{file_path}"
    return url

# ==============================
# FUNÇÕES DE PLAYER
# ==============================
def play_song(song):
    st.session_state.current_track = song
    st.session_state.is_playing = True
    st.session_state.player_timestamp = time.time()
    # Adicionar ao histórico
    if song not in st.session_state.music_history:
        st.session_state.music_history.append(song)

def pause_song():
    st.session_state.is_playing = False

def resume_song():
    st.session_state.is_playing = True

def format_time(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

# ==============================
# LAYOUT PRINCIPAL
# ==============================
def main():
    # Mostrar popup de boas-vindas
    if not st.session_state.popup_closed and not st.session_state.popup_shown:
        show_welcome_popup()
    
    # ==============================
    # SIDEBAR
    # ==============================
    with st.sidebar:
        st.title("🌊 Wave")
        st.markdown("---")
        
        # Navegação
        nav_options = ["🏠 Home", "🎵 Player", "🔍 Buscar", "📊 Estatísticas", "⚙️ Admin"]
        selected_nav = st.radio("Navegação", nav_options)
        
        # Atualizar página atual
        if "🏠 Home" in selected_nav:
            st.session_state.current_page = "home"
        elif "🎵 Player" in selected_nav:
            st.session_state.current_page = "player"
        elif "🔍 Buscar" in selected_nav:
            st.session_state.current_page = "search"
        elif "📊 Estatísticas" in selected_nav:
            st.session_state.current_page = "stats"
        elif "⚙️ Admin" in selected_nav:
            st.session_state.current_page = "admin"
        
        st.markdown("---")
        
        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎤 Pedir Música", use_container_width=True):
                st.session_state.show_request_form = True
        with col2:
            if st.button("➕ Adicionar", use_container_width=True):
                st.session_state.show_add_form = True
        
        # Formulário de pedido de música
        if st.session_state.show_request_form:
            with st.form("song_request_form"):
                st.subheader("🎤 Pedir Música")
                req_title = st.text_input("Título da Música*")
                req_artist = st.text_input("Artista*")
                req_notes = st.text_area("Observações")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Enviar Pedido"):
                        if req_title and req_artist:
                            if add_song_request({
                                "title": req_title,
                                "artist": req_artist,
                                "notes": req_notes,
                                "requested_by": "Anonymous"
                            }):
                                st.success("✅ Pedido enviado com sucesso!")
                                st.session_state.show_request_form = False
                                st.rerun()
                        else:
                            st.error("❌ Preencha título e artista!")
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        st.session_state.show_request_form = False
                        st.rerun()
        
        # Formulário de adição de música
        if st.session_state.show_add_form:
            with st.form("add_song_form"):
                st.subheader("➕ Adicionar Música")
                add_title = st.text_input("Título*")
                add_artist = st.text_input("Artista*")
                add_album = st.text_input("Álbum")
                add_genre = st.text_input("Gênero")
                add_duration = st.text_input("Duração (ex: 3:45)")
                add_audio_url = st.text_input("URL do Áudio*")
                add_image_url = st.text_input("URL da Imagem")
                add_platform = st.selectbox("Plataforma", ["spotify", "youtube", "soundcloud", "wave"])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Adicionar"):
                        if add_title and add_artist and add_audio_url:
                            if add_song_to_db({
                                "title": add_title,
                                "artist": add_artist,
                                "album": add_album,
                                "genre": add_genre,
                                "duration": add_duration,
                                "audio_url": add_audio_url,
                                "image_url": add_image_url,
                                "platform": add_platform,
                                "play_count": 0
                            }):
                                st.success("✅ Música adicionada com sucesso!")
                                st.session_state.show_add_form = False
                                st.rerun()
                        else:
                            st.error("❌ Preencha os campos obrigatórios!")
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        st.session_state.show_add_form = False
                        st.rerun()
        
        st.markdown("---")
        st.markdown("### 🎵 Tocando Agora")
        
        if st.session_state.current_track:
            current = st.session_state.current_track
            img_url = current.get("image_url", "")
            if img_url:
                img = load_image_cached(img_url)
                if img:
                    st.image(img, use_column_width=True)
            
            st.markdown(f"**{current.get('title', 'Unknown')}**")
            st.markdown(f"*{current.get('artist', 'Unknown')}*")
            
            # Controles do player
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.session_state.is_playing:
                    if st.button("⏸️ Pausar", use_container_width=True):
                        pause_song()
                        st.rerun()
                else:
                    if st.button("▶️ Reproduzir", use_container_width=True):
                        resume_song()
                        st.rerun()
            with col2:
                if st.button("⏭️ Próxima", use_container_width=True):
                    # Lógica para próxima música
                    pass
            
            # Volume
            new_volume = st.slider("🔊 Volume", 0, 100, st.session_state.volume)
            if new_volume != st.session_state.volume:
                st.session_state.volume = new_volume
        
        else:
            st.info("🎵 Nenhuma música tocando")
        
        st.markdown("---")
        st.markdown("### 📜 Histórico")
        
        if st.session_state.music_history:
            for i, song in enumerate(reversed(st.session_state.music_history[-5:])):
                st.markdown(f"{i+1}. **{song.get('title', 'Unknown')}** - *{song.get('artist', 'Unknown')}*")
        else:
            st.info("📝 Nenhuma música no histórico")
    
    # ==============================
    # CONTEÚDO PRINCIPAL
    # ==============================
    
    # Carregar músicas
    if not st.session_state.all_songs:
        st.session_state.all_songs = get_all_songs_cached()
    
    # Página Home
    if st.session_state.current_page == "home":
        st.title("🎵 Bem-vindo ao Wave!")
        st.markdown("---")
        
        # Top 6 Músicas
        st.subheader("🔥 Top 6 Músicas")
        top6_songs = get_top6_songs()
        
        if top6_songs:
            cols = st.columns(3)
            for i, song in enumerate(top6_songs):
                with cols[i % 3]:
                    with st.container():
                        img_url = song.get("image_url", "")
                        if img_url:
                            img = load_image_cached(img_url)
                            if img:
                                st.image(img, use_column_width=True)
                        
                        st.markdown(f"**{song.get('title', 'Unknown')}**")
                        st.markdown(f"*{song.get('artist', 'Unknown')}*")
                        st.markdown(f"🎵 {song.get('play_count', 0)} plays")
                        
                        if st.button("▶️ Tocar", key=f"play_top_{i}", use_container_width=True):
                            play_song(song)
                            st.rerun()
            
            st.markdown("---")
        
        # Músicas Aleatórias do Dia
        st.subheader("🎲 Músicas Aleatórias do Dia")
        random_songs = get_daily_random_songs(st.session_state.all_songs, top6_songs)
        
        if random_songs:
            cols = st.columns(3)
            for i, song in enumerate(random_songs):
                with cols[i % 3]:
                    with st.container():
                        img_url = song.get("image_url", "")
                        if img_url:
                            img = load_image_cached(img_url)
                            if img:
                                st.image(img, use_column_width=True)
                        
                        st.markdown(f"**{song.get('title', 'Unknown')}**")
                        st.markdown(f"*{song.get('artist', 'Unknown')}*")
                        
                        if st.button("▶️ Tocar", key=f"play_random_{i}", use_container_width=True):
                            play_song(song)
                            st.rerun()
        
        else:
            st.info("🎵 Nenhuma música disponível")
    
    # Página Player
    elif st.session_state.current_page == "player":
        st.title("🎵 Player de Música")
        st.markdown("---")
        
        if st.session_state.current_track:
            current = st.session_state.current_track
            
            col1, col2 = st.columns([1, 2])
            with col1:
                img_url = current.get("image_url", "")
                if img_url:
                    img = load_image_cached(img_url)
                    if img:
                        st.image(img, use_column_width=True)
            
            with col2:
                st.markdown(f"## {current.get('title', 'Unknown')}")
                st.markdown(f"### *{current.get('artist', 'Unknown')}*")
                
                if current.get("album"):
                    st.markdown(f"**Álbum:** {current.get('album')}")
                if current.get("genre"):
                    st.markdown(f"**Gênero:** {current.get('genre')}")
                if current.get("duration"):
                    st.markdown(f"**Duração:** {current.get('duration')}")
                
                # Controles do player
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.session_state.is_playing:
                        if st.button("⏸️ Pausar", use_container_width=True):
                            pause_song()
                            st.rerun()
                    else:
                        if st.button("▶️ Reproduzir", use_container_width=True):
                            resume_song()
                            st.rerun()
                with col2:
                    if st.button("⏭️ Próxima", use_container_width=True):
                        # Lógica para próxima música
                        pass
                with col3:
                    if st.button("🔀 Aleatório", use_container_width=True):
                        # Lógica para música aleatória
                        pass
                
                # Barra de progresso simulada
                st.progress(0.5)
                st.markdown("2:30 / 4:15")
        
        else:
            st.info("🎵 Selecione uma música para reproduzir")
        
        st.markdown("---")
        st.subheader("📜 Sua Biblioteca")
        
        # Lista de músicas
        for i, song in enumerate(st.session_state.all_songs):
            col1, col2, col3 = st.columns([6, 2, 1])
            with col1:
                st.markdown(f"**{song.get('title', 'Unknown')}** - *{song.get('artist', 'Unknown')}*")
            with col2:
                st.markdown(song.get("duration", "0:00"))
            with col3:
                if st.button("▶️", key=f"play_lib_{i}"):
                    play_song(song)
                    st.rerun()
    
    # Página Buscar
    elif st.session_state.current_page == "search":
        st.title("🔍 Buscar Músicas")
        st.markdown("---")
        
        # Barra de busca
        search_query = st.text_input("🔍 Buscar por título, artista, álbum ou gênero...", 
                                   value=st.session_state.search_input,
                                   key="search_input_main")
        
        if search_query:
            st.session_state.search_input = search_query
            filtered_songs = search_songs(search_query)
            
            st.markdown(f"**{len(filtered_songs)}** músicas encontradas")
            
            for i, song in enumerate(filtered_songs):
                col1, col2, col3, col4 = st.columns([5, 2, 2, 1])
                with col1:
                    st.markdown(f"**{song.get('title', 'Unknown')}** - *{song.get('artist', 'Unknown')}*")
                with col2:
                    if song.get("album"):
                        st.markdown(f"*{song.get('album')}*")
                with col3:
                    if song.get("genre"):
                        st.markdown(f"`{song.get('genre')}`")
                with col4:
                    if st.button("▶️", key=f"play_search_{i}"):
                        play_song(song)
                        st.rerun()
        
        else:
            st.info("🔍 Digite algo para buscar...")
    
    # Página Estatísticas
    elif st.session_state.current_page == "stats":
        st.title("📊 Estatísticas")
        st.markdown("---")
        
        total_songs = len(st.session_state.all_songs)
        total_artists = len(set(song.get("artist", "") for song in st.session_state.all_songs))
        total_plays = sum(song.get("play_count", 0) for song in st.session_state.all_songs)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎵 Total de Músicas", total_songs)
        with col2:
            st.metric("👤 Artistas Únicos", total_artists)
        with col3:
            st.metric("▶️ Total de Plays", total_plays)
        
        st.markdown("---")
        st.subheader("🔥 Top 10 Músicas")
        
        top_songs = sorted(st.session_state.all_songs, 
                          key=lambda x: x.get("play_count", 0), 
                          reverse=True)[:10]
        
        for i, song in enumerate(top_songs):
            st.markdown(f"{i+1}. **{song.get('title', 'Unknown')}** - *{song.get('artist', 'Unknown')}* ({song.get('play_count', 0)} plays)")
    
    # Página Admin
    elif st.session_state.current_page == "admin":
        st.title("⚙️ Painel Admin")
        st.markdown("---")
        
        if not st.session_state.admin_authenticated:
            password = st.text_input("🔒 Senha de Administrador", type="password")
            if st.button("🔓 Entrar"):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta!")
        else:
            st.success("✅ Autenticado como Administrador")
            
            if st.button("🚪 Sair"):
                st.session_state.admin_authenticated = False
                st.rerun()
            
            st.markdown("---")
            st.subheader("📊 Estatísticas do Sistema")
            
            # Aqui viriam mais funcionalidades admin...
            st.info("🚧 Painel Admin em desenvolvimento...")

    # ==============================
    # PLAYER FIXO NA PARTE INFERIOR
    # ==============================
    if st.session_state.current_track:
        st.markdown("---")
        st.markdown("### 🎵 Tocando Agora")
        
        current = st.session_state.current_track
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            img_url = current.get("image_url", "")
            if img_url:
                img = load_image_cached(img_url)
                if img:
                    st.image(img, width=60)
        
        with col2:
            st.markdown(f"**{current.get('title', 'Unknown')}**")
            st.markdown(f"*{current.get('artist', 'Unknown')}*")
            
            # Simular barra de progresso
            progress = st.progress(0.5)
            st.markdown("2:30 / 4:15")
        
        with col3:
            # Controles do player
            if st.session_state.is_playing:
                if st.button("⏸️", key="bottom_pause"):
                    pause_song()
                    st.rerun()
            else:
                if st.button("▶️", key="bottom_play"):
                    resume_song()
                    st.rerun()
            
            if st.button("⏭️", key="bottom_next"):
                # Lógica para próxima música
                pass

# ==============================
# INICIALIZAÇÃO DO FIREBASE
# ==============================
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://wavesong-default-rtdb.firebaseio.com/'
        })
    st.session_state.firebase_connected = initialize_database()
except Exception as e:
    st.session_state.firebase_connected = False

# ==============================
# EXECUÇÃO PRINCIPAL
# ==============================
if __name__ == "__main__":
    main()
