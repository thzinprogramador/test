import streamlit as st
import firebase_admin
import requests 
import datetime
import telebot 
import random
import time
import base64
import threading
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
admin_name = "Schutz"
ADMIN_PASSWORD = "wavesong9090" 

# ==============================
# CONFIGURAÇÕES DO TELEGRAM
# ==============================
TELEGRAM_BOT_TOKEN = "7680456440:AAFRmCOdehS13VjYY5qKttBbm-hDZRDFjP4"  # Obtenha com @BotFather
TELEGRAM_ADMIN_CHAT_ID = "5919571280"  # Obtenha com @userinfobot
TELEGRAM_NOTIFICATIONS_ENABLED = False  # Inicialmente desativado

# Inicializar bot do Telegram
try:
    telegram_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    TELEGRAM_NOTIFICATIONS_ENABLED = True
except Exception as e:
    st.error(f"❌ Erro ao conectar com Telegram: {e}")
    TELEGRAM_NOTIFICATIONS_ENABLED = False
        

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
            
            # ENVIAR NOTIFICAÇÃO TELEGRAM - ADICIONE ESTA PARTE
            title = song_data.get("title", "Sem título")
            artist = song_data.get("artist", "Artista desconhecido")
            send_telegram_notification(f"🎵 Nova música adicionada:\n{title} - {artist}")
            
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
    if success:
        send_telegram_notification(f"🎵 Novo pedido de música:\n{title} - {artist}\nSolicitado por: {req_username or 'Anônimo'}")

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
# FUNÇÕES DE NOTIFICAÇÃO TELEGRAM
# ==============================
def send_telegram_notification(message):
    """Envia notificação para o administrador via Telegram"""
    if not TELEGRAM_NOTIFICATIONS_ENABLED:
        return False
    
    try:
        telegram_bot.send_message(TELEGRAM_ADMIN_CHAT_ID, message)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao enviar notificação: {e}")
        return False

def send_global_notification(message):
    """Envia notificação para todos os usuários (via banco de dados)"""
    if not st.session_state.firebase_connected:
        return False
    
    try:
        ref = db.reference("/global_notifications")
        notification_data = {
            "message": message,
            "timestamp": datetime.datetime.now().isoformat(),
            "read_by": {}  # Dicionário para controlar quem leu
        }
        ref.push(notification_data)
        
        # Também enviar para o admin via Telegram
        send_telegram_notification(f"📢 Nova notificação global:\n{message}")
        return True
    except Exception as e:
        st.error(f"❌ Erro ao enviar notificação global: {e}")
        return False

def check_unread_notifications():
    """Verifica se há notificações não lidas pelo usuário atual"""
    if not st.session_state.firebase_connected:
        return []
    
    try:
        ref = db.reference("/global_notifications")
        notifications = ref.get()
        unread = []
        
        if notifications:
            for note_id, note_data in notifications.items():
                # Verificar se o usuário atual já leu esta notificação
                read_by = note_data.get("read_by", {})
                user_key = st.experimental_user.get("email", "anonymous") if hasattr(st.experimental_user, "get") else "anonymous"
                
                if user_key not in read_by or not read_by[user_key]:
                    unread.append({
                        "id": note_id,
                        "message": note_data.get("message", ""),
                        "timestamp": note_data.get("timestamp", "")
                    })
        
        return unread
    except Exception as e:
        st.error(f"❌ Erro ao verificar notificações: {e}")
        return []

def mark_notification_as_read(notification_id):
    """Marca uma notificação como lida pelo usuário atual"""
    if not st.session_state.firebase_connected:
        return False
    
    try:
        user_key = st.experimental_user.get("email", "anonymous") if hasattr(st.experimental_user, "get") else "anonymous"
        ref = db.reference(f"/global_notifications/{notification_id}/read_by/{user_key}")
        ref.set(True)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao marcar notificação como lida: {e}")
        return False

def setup_telegram_commands():
    """Configura os comandos do Telegram para enviar notificações"""
    if not TELEGRAM_NOTIFICATIONS_ENABLED:
        return
    
    @telegram_bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        telegram_bot.reply_to(message, "🌊 Olá! Eu sou o bot do Wave Song.\n\n"
                              "Comandos disponíveis:\n"
                              "/status - Ver status do sistema\n"
                              "/notify [mensagem] - Enviar notificação global\n"
                              "/users - Ver estatísticas de usuários")
    
    @telegram_bot.message_handler(commands=['status'])
    def send_status(message):
        status = "✅ Online" if st.session_state.firebase_connected else "⚠️ Offline"
        total_songs = len(st.session_state.all_songs)
        telegram_bot.reply_to(message, f"🌊 Status do Wave Song:\n"
                              f"{status}\n"
                              f"Músicas no banco: {total_songs}\n"
                              f"Notificações ativas: {TELEGRAM_NOTIFICATIONS_ENABLED}")
    
    @telegram_bot.message_handler(commands=['notify'])
    def send_notification(message):
        # Verificar se é o administrador
        if str(message.chat.id) != TELEGRAM_ADMIN_CHAT_ID:
            telegram_bot.reply_to(message, "❌ Apenas administradores podem enviar notificações.")
            return
        
        # Extrair a mensagem do comando
        command_parts = message.text.split(' ', 1)
        if len(command_parts) < 2:
            telegram_bot.reply_to(message, "❌ Uso: /notify [mensagem]")
            return
        
        notification_text = command_parts[1]
        if send_global_notification(notification_text):
            telegram_bot.reply_to(message, "✅ Notificação enviada para todos os usuários!")
        else:
            telegram_bot.reply_to(message, "❌ Falha ao enviar notificação.")
    
    # Iniciar polling em thread separada para não bloquear o Streamlit
    import threading
    def start_bot():
        try:
            telegram_bot.infinity_polling()
        except Exception as e:
            st.error(f"Erro no bot do Telegram: {e}")
    
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()

# Chame esta função após inicializar o bot
if TELEGRAM_NOTIFICATIONS_ENABLED:
    setup_telegram_commands()

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
    if not url:
        return url
    
    try:
        # Formato 1: https://github.com/usuario/repo/raw/ramo/caminho/arquivo
        if "github.com" in url and "/raw/" in url:
            parts = url.split("/")
            # Encontra a posição do domínio github.com
            github_index = parts.index("github.com")
            usuario = parts[github_index + 1]
            repo = parts[github_index + 2]
            
            # Encontra a posição do "raw"
            raw_index = parts.index("raw")
            ramo = parts[raw_index + 1]
            caminho_arquivo = "/".join(parts[raw_index + 2:])
            
            nova_url = f"https://cdn.jsdelivr.net/gh/{usuario}/{repo}@{ramo}/{caminho_arquivo}"
            return nova_url
        
        # Formato 2: https://raw.githubusercontent.com/usuario/repo/ramo/caminho/arquivo
        elif "raw.githubusercontent.com" in url:
            parts = url.split("/")
            # Encontra a posição do domínio raw.githubusercontent.com
            raw_index = parts.index("raw.githubusercontent.com")
            usuario = parts[raw_index + 1]
            repo = parts[raw_index + 2]
            ramo = parts[raw_index + 3]
            caminho_arquivo = "/".join(parts[raw_index + 4:])
            
            nova_url = f"https://cdn.jsdelivr.net/gh/{usuario}/{repo}@{ramo}/{caminho_arquivo}"
            return nova_url
        
        # Se não for nenhum dos formatos suportados, retorna original
        else:
            return url
            
    except Exception as e:
        print(f"Erro ao converter URL {url}: {e}")
        return url

def get_converted_audio_url(song):
    """Retorna a URL do áudio convertida se for do GitHub"""
    audio_url = song.get("audio_url", "")
    if "github.com" in audio_url or "raw.githubusercontent.com" in audio_url:
        return convert_github_to_jsdelivr(audio_url)
    return audio_url


def play_song(song):
    # Verificar se é uma música diferente
    current_id = st.session_state.current_track["id"] if st.session_state.current_track else None
    new_id = song["id"]
    
    # Converter URL do GitHub para jsDelivr se necessário
    if "audio_url" in song and ("github.com" in song["audio_url"] or "raw.githubusercontent.com" in song["audio_url"]):
        song_copy = song.copy()  # Criar uma cópia para não modificar o original
        song_copy["audio_url"] = convert_github_to_jsdelivr(song["audio_url"])
        song = song_copy
    
    # Sempre forçar rerun quando uma nova música é selecionada
    st.session_state.current_track = song
    st.session_state.is_playing = True
    
    # Adicionar timestamp único para forçar reconstrução
    st.session_state.player_timestamp = time.time()
    
    if st.session_state.firebase_connected:
        try:
            ref = db.reference(f"/songs/{song['id']}/play_count")
            current_count = ref.get() or 0
            ref.set(current_count + 1)
        except Exception as e:
            st.error(f"Erro ao atualizar play_count: {e}")
    
    # Forçar rerun apenas se for música diferente
    if current_id != new_id:
        st.rerun()
    


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

def show_notification_panel():
    """Painel para enviar notificações globais"""
    st.header("🔔 Painel de Notificações")
    
    # Verificar autenticação
    if not st.session_state.admin_authenticated:
        password = st.text_input("Senha de Administrador", type="password", key="notif_auth")
        if st.button("Acessar", key="notif_btn"):
            if password == ADMIN_PASSWORD: 
                st.session_state.admin_authenticated = True
                st.success("✅ Acesso concedido!")
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")
        return
    
    # Formulário para enviar notificação
    with st.form("notification_form"):
        notification_message = st.text_area("Mensagem da notificação:", 
                                          placeholder="Digite a mensagem que será enviada para todos os usuários...",
                                          height=100)
        send_test = st.checkbox("Enviar teste para o administrador primeiro")
        
        submitted = st.form_submit_button("📢 Enviar Notificação Global")
        if submitted:
            if not notification_message.strip():
                st.error("⚠️ A mensagem não pode estar vazia!")
                return
                
            if send_test:
                if send_telegram_notification(f"🧪 Notificação de teste:\n{notification_message}"):
                    st.success("✅ Teste enviado para o administrador!")
                else:
                    st.error("❌ Falha ao enviar teste!")
                    return
            
            if send_global_notification(notification_message):
                st.success("✅ Notificação enviada para todos os usuários!")
            else:
                st.error("❌ Falha ao enviar notificação global!")
    
    # Histórico de notificações
    st.subheader("Histórico de Notificações")
    try:
        ref = db.reference("/global_notifications")
        notifications = ref.order_by_child("timestamp").limit_to_last(10).get()
        
        if notifications:
            for note_id, note_data in notifications.items():
                with st.expander(f"Notificação de {note_data.get('timestamp', '')}"):
                    st.write(note_data.get("message", ""))
                    st.caption(f"Lida por {len(note_data.get('read_by', {}))} usuários")
        else:
            st.info("Nenhuma notificação enviada ainda.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar histórico: {e}")
    
    if st.button("🔒 Sair do Painel de Notificações"):
        st.session_state.admin_authenticated = False
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
# FUNÇÕES DE TESTE
# ==============================
def test_github_conversion():
    """Testa a conversão de URLs do GitHub para JS Delivr com seu formato específico"""
    st.header("🔍 Teste de Conversão de URLs - Formato GitHub")
    
    # URLs nos formatos suportados
    test_urls = [
        # Formato antigo
        "https://github.com/thzinprogramador/songs/raw/refs/heads/main/albuns/matue/4TAL.mp3",
        "https://github.com/thzinprogramador/songs/raw/refs/heads/main/God's%20Plan%20-%20drake.mp3",
        
        # Formato novo
        "https://raw.githubusercontent.com/thzinprogramador/songUpdate/main/Matu%C3%AA%20-%20Maria%20-%20333.mp3",
        "https://raw.githubusercontent.com/thzinprogramador/songUpdate/main/album/nova_musica.mp3",
        
        # URL não GitHub (não deve ser convertida)
        "https://example.com/regular-audio.mp3",
    ]
    
    for i, url in enumerate(test_urls):
        original = url
        converted = convert_github_to_jsdelivr(url)
        
        st.subheader(f"Teste {i+1}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**URL Original:**")
            st.code(original, language="url")
        with col2:
            st.write("**URL Convertida:**")
            st.code(converted, language="url")
        
        # Verificar se a conversão foi bem-sucedida
        if "github.com" in original and "cdn.jsdelivr.net" in converted:
            st.success("✅ Conversão bem-sucedida")
            
            # Mostrar diferença
            st.write("**Diferença:**")
            st.info(f"Original: `{original}`")
            st.info(f"Convertido: `{converted}`")
        elif "github.com" not in original and original == converted:
            st.info("ℹ️ URL não GitHub - mantida original")
        else:
            st.error("❌ Erro na conversão")
        
        st.markdown("---")



def test_audio_playback():
    """Testa a reprodução de áudio com URLs convertidas"""
    st.header("🎵 Teste de Reprodução de Áudio")
    
    # URLs de áudio de exemplo
    test_audios = [
        {
            "title": "Música Formato Antigo",
            "original_url": "https://github.com/thzinprogramador/songs/raw/refs/heads/main/Congratulations%20-%20post%20malone.mp3",
            "converted_url": convert_github_to_jsdelivr("https://github.com/thzinprogramador/songs/raw/refs/heads/main/Congratulations%20-%20post%20malone.mp3")
        },
        {
            "title": "Música Formato Novo", 
            "original_url": "https://raw.githubusercontent.com/thzinprogramador/songUpdate/main/Matu%C3%AA%20-%20Maria%20-%20333.mp3",
            "converted_url": convert_github_to_jsdelivr("https://raw.githubusercontent.com/thzinprogramador/songUpdate/main/Matu%C3%AA%20-%20Maria%20-%20333.mp3")
        }
    ]
    
    for audio in test_audios:
        st.subheader(audio["title"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**URL Original:**")
            st.code(audio["original_url"], language="url")
        with col2:
            st.write("**URL Convertida:**")
            st.code(audio["converted_url"], language="url")
        
        # Tentar reproduzir o áudio com a URL convertida
        st.write("**Teste de reprodução:**")
        
        # Verificar se a URL foi convertida corretamente
        if "cdn.jsdelivr.net" in audio["converted_url"]:
            st.success("✅ URL convertida com sucesso")
            
            # Tentar reproduzir o áudio
            try:
                st.audio(audio["converted_url"], format="audio/mp3")
                st.success("🎵 Áudio carregado com sucesso!")
            except Exception as e:
                st.warning(f"⚠️ Não foi possível carregar o áudio: {str(e)}")
                st.info("Isso pode ser normal se a URL for apenas um exemplo")
        else:
            st.error("❌ Falha na conversão da URL")
        
        st.markdown("---")



# ==============================
# RENDER PLAYER COM AUTOPLAY
# ==============================
def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def render_player():
    track = st.session_state.current_track
    if not track:
        st.info("🔍 Escolha uma música para tocar.")
        return

    # Converter URL do áudio se for do GitHub
    audio_src = get_converted_audio_url(track)
    
    cover = load_image_cached(track.get("image_url"))
    if cover is not None:
        cover_url = image_to_base64(cover)
    else:
        cover_url = "https://via.placeholder.com/80x80?text=Sem+Imagem"

    title = track.get("title", "Sem título")
    artist = track.get("artist", "Sem artista")
    
    # Criar HTML para o iframe com melhor estilização
    audio_html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: transparent;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 40px;
            }}
            audio {{
                width: 300px;
                height: 40px;
                outline: none;
            }}
            audio::-webkit-media-controls-panel {{
                background-color: #1DB954;
            }}
            audio::-webkit-media-controls-play-button {{
                background-color: #1DB954 !important;
                border-radius: 50%;
                box-shadow: 0 0 8px rgba(0,0,0,0.4);
                border: 1px solid #1ed760;
            }}

        </style>
    </head>
    <body>
        <audio controls {'autoplay' if st.session_state.is_playing else ''}>
            <source src="{audio_src}" type="audio/mpeg">
        </audio>
        <script>
            // Tentar forçar autoplay com interação simulada
            document.addEventListener('DOMContentLoaded', function() {{
                const audio = document.querySelector('audio');
                if (audio && {str(st.session_state.is_playing).lower()}) {{
                    // Tentar play com tratamento de erro
                    const playPromise = audio.play();
                    if (playPromise !== undefined) {{
                        playPromise.catch(error => {{
                            console.log('Autoplay prevented:', error);
                            // Mostrar botão de play se autoplay falhar
                            audio.controls = true;
                        }});
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    '''
    
    # Codificar para data URL
    audio_html_encoded = base64.b64encode(audio_html.encode()).decode()
    
    player_html = f"""
    <div style="position:fixed;bottom:10px;left:50%;transform:translateX(-50%);
                background:rgba(0,0,0,0.8);padding:15px;border-radius:15px;
                display:flex;align-items:center;gap:15px;z-index:999;
                box-shadow:0 4px 20px rgba(0,0,0,0.5);backdrop-filter:blur(10px);
                width:600px; max-width:90%;">
        <img src="{cover_url}" width="60" height="60" style="border-radius:10px;object-fit:cover"/>
        <div style="flex:1;">
            <div style="font-weight:bold;color:white;font-size:16px;margin-bottom:5px">{title}</div>
            <div style="color:#ccc;font-size:14px">{artist}</div>
        </div>
        <iframe src="data:text/html;base64,{audio_html_encoded}" 
                style="width:320px;height:50px;border:none;margin-left:auto;border-radius:8px;
                       overflow:hidden;"></iframe>
    </div>
    """
    
    st.markdown(player_html, unsafe_allow_html=True)
    
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


        if song.get("audio_url"):
            render_player()

    else:
        st.info("🔍 Escolha uma música")

    st.markdown("---")

    # Ícone de notificações com badge - MOVER PARA DENTRO DA SIDEBAR
    unread_notifications = check_unread_notifications()
    notification_text = f"🔔 Notificações ({len(unread_notifications)})" if unread_notifications else "🔔 Notificações"

    if st.button(notification_text, use_container_width=True, key="btn_notifications"):
        st.session_state.current_page = "notifications"
        st.session_state.show_request_form = False

    if st.button("📢 Painel de Notificações (Admin)", use_container_width=True, key="btn_notification_panel"):
        st.session_state.current_page = "notification_panel"
        st.session_state.show_request_form = False
    
    if st.button("Página Inicial", key="btn_home", use_container_width=True):
        st.session_state.current_page = "home"
        st.session_state.show_request_form = False
    if st.button("Buscar Músicas", key="btn_search", use_container_width=True):
        st.session_state.current_page = "search"
        st.session_state.show_request_form = False
    #if st.sidebar.button("🧪 Testar Conversão de URLs"):
        #st.session_state.current_page = "test_github_conversion"
        
    # Verificação de conversão em tempo real
    if st.checkbox("🔍 Verificar conversões em tempo real"):
        st.header("Status de Conversão das URLs")
        
        github_count = 0
        converted_count = 0
        problematic_urls = []
        
        for song in st.session_state.all_songs:
            audio_url = song.get("audio_url", "")
            if "github.com" in audio_url or "raw.githubusercontent.com" in audio_url:
                github_count += 1
                converted_url = convert_github_to_jsdelivr(audio_url)
                if "cdn.jsdelivr.net" in converted_url:
                    converted_count += 1
                else:
                    problematic_urls.append(audio_url)
        
        st.write(f"**Total de URLs do GitHub:** {github_count}")
        st.write(f"**URLs convertíveis:** {converted_count}")
        
        if github_count > 0 and converted_count == github_count:
            st.success("✅ Todas as URLs do GitHub podem be converted!")
        elif github_count > 0:
            st.warning(f"⚠️ Apenas {converted_count}/{github_count} URLs podem ser convertidas")
            st.write("**URLs com problemas:**")
            for url in problematic_urls:
                st.code(url)

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
                    if st.button("Tocar", key=f"play_{song_key}", use_container_width=True):
                        play_song(song)
                        
        # Mostrar seção de pedidos de música
        show_request_music_section()
    else:
        st.info("Nenhuma música encontrada.")
        show_request_music_section()

elif st.session_state.current_page == "search":
    st.header("Buscar Músicas")

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
                    if st.button("Tocar", key=f"search_{i}", use_container_width=True):
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

elif st.session_state.current_page == "test_github_conversion":
    st.header("🧪 Testes de Conversão URL")
    tab1, tab2 = st.tabs(["Teste de Conversão", "Teste de Reprodução"])

    with tab1:
        test_github_conversion()

    with tab2:
        test_audio_playback()

    if st.button("Voltar para o Player"):
        st.session_state.current_page = "home"

if st.session_state.current_page == "notifications":
    st.markdown(f"<h1 style='text-align:center;'>🔔 Notificações de {admin_name}</h1>", unsafe_allow_html=True)
    st.markdown("---")

    unread_notifications = check_unread_notifications()

    if unread_notifications:
        st.success(f"Você tem {len(unread_notifications)} notificação(ões) não lida(s)")

        for notification in unread_notifications:
            with st.container():
                st.markdown(
                    f"""
                    <div style='
                        background-color:#1f2937;
                        padding:15px;
                        border-radius:10px;
                        margin-bottom:10px;
                        color:#f9fafb;
                        box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
                    '>
                        <p style='font-size:12px;color:#9ca3af;'>{notification['timestamp']}</p>
                        <p style='font-size:16px;margin-top:5px;'>{notification['message']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button("✅ Marcar como lida", key=f"read_{notification['id']}"):
                    if mark_notification_as_read(notification['id']):
                        st.success("Notificação marcada como lida!")
                        st.rerun()
            st.markdown("---")
    else:
        st.info("Não há notificações não lidas.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Voltar para o Início", key="back_from_notifications"):
        st.session_state.current_page = "home"

# ==============================
# FOOTER + CSS
# ==============================
st.markdown("---")
st.caption("🌊 Wave - Sua música, seu mundo • Site em Desenvolvimento ")
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
