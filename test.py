import streamlit as st
import firebase_admin
import requests 
import datetime
import telebot 
import random
import time
import base64
import threading
import traceback
import bcrypt
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
if "unread_notifications_cache" not in st.session_state:
    st.session_state.unread_notifications_cache = None
if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False
if "show_login" not in st.session_state:
    st.session_state.show_login = False


# ==============================
# CONFIGURAÇÕES DO SUPABASE (SIMPLIFICADO)
# ==============================
SUPABASE_URL = "https://wvouegbuvuairukkupit.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind2b3VlZ2J1dnVhaXJ1a2t1cGl0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0NzM3NjAsImV4cCI6MjA3MzA0OTc2MH0.baLFbRTaMM8FCFG2a-Yb80Sg7JqhdQ6EMld8h7BABiE"

class SimpleSupabaseClient:
    def __init__(self, url, key):
        self.url = url
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
    
    def execute_query(self, endpoint, method="GET", data=None):
        try:
            url = f"{self.url}/rest/v1/{endpoint}"
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=data)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"Erro Supabase: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Erro ao conectar com Supabase: {e}")
            return None
    
    def table(self, table_name):
        return SupabaseTable(self, table_name)

class SupabaseTable:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
    
    def select(self, columns="*"):
        self.columns = columns
        return self
    
    def eq(self, column, value):
        self.filter_column = column
        self.filter_value = value
        return self
    
    def execute(self):
        endpoint = self.table_name
        params = {"select": self.columns}
        
        if hasattr(self, 'filter_column') and hasattr(self, 'filter_value'):
            params[self.filter_column] = f"eq.{self.filter_value}"
        
        result = self.client.execute_query(endpoint, "GET", params)
        return {"data": result} if result else {"data": []}
    
    def insert(self, data):
        endpoint = self.table_name
        result = self.client.execute_query(endpoint, "POST", data)
        return {"data": [result]} if result else {"data": []}
    
    def update(self, data):
        endpoint = self.table_name
        if hasattr(self, 'filter_column') and hasattr(self, 'filter_value'):
            endpoint = f"{self.table_name}?{self.filter_column}=eq.{self.filter_value}"
        result = self.client.execute_query(endpoint, "PUT", data)
        return {"data": [result]} if result else {"data": []}

# Inicializar cliente Supabase simplificado
supabase_client = SimpleSupabaseClient(SUPABASE_URL, SUPABASE_KEY)


# teste 
def check_supabase_connection():
    """Verifica a conexão com Supabase"""
    try:
        response = supabase_client.table("users").select("count").execute()
        st.info(f"Resposta do Supabase: {response}")
        return True
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {e}")
        return False

# Chame esta função em algum lugar para testar
check_supabase_connection()

def debug_supabase_users():
    """Debug da tabela users"""
    try:
        response = supabase_client.table("users").select("*").execute()
        st.info(f"Estrutura completa da tabela users: {response}")
        
        if response.get("data"):
            for user in response["data"]:
                st.info(f"Usuário encontrado: {user}")
                # Verificar se tem as colunas necessárias
                if "password_hash" not in user:
                    st.error("❌ A coluna 'password_hash' não existe na tabela users!")
                if "username" not in user:
                    st.error("❌ A coluna 'username' não existe na tabela users!")
                    
        return True
    except Exception as e:
        st.error(f"Erro ao debuggar tabela users: {e}")
        return False

# Chame esta função em algum lugar para verificar
debug_supabase_users()


# Verificação completa da estrutura
if "full_debug_done" not in st.session_state:
    st.session_state.full_debug_done = True
    
    st.sidebar.info("🔍 Verificação completa da estrutura...")
    
    # Verificar estrutura da tabela users
    try:
        # Verificar colunas
        users_columns = supabase_client.table("users").select("count").execute()
        st.sidebar.info(f"Estrutura users: {users_columns}")
        
        # Verificar usuários individualmente
        all_users = supabase_client.table("users").select("*").execute()
        if all_users.get("data"):
            for user in all_users["data"]:
                st.sidebar.info(f"Usuário: {user.get('username')} - ID: {user.get('id')} - Admin: {user.get('is_admin')}")
        
    except Exception as e:
        st.sidebar.error(f"Erro na verificação: {e}")

# ==============================
# SISTEMA DE AUTENTICAÇÃO SIMPLIFICADO (SEM EMAIL)
# ==============================
def init_auth():
    """Inicializa o sistema de autenticação"""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False

def hash_password(password):
    """Gera hash da senha usando bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password, hashed_password):
    """Verifica se a senha corresponde ao hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def username_exists(username):
    """Verifica se o username já existe"""
    try:
        response = supabase_client.table("users").select("username").eq("username", username).execute()
        return len(response.get("data", [])) > 0  # Corrigido aqui
    except Exception as e:
        st.error(f"Erro ao verificar usuário: {e}")
        return False

def sign_up(username, password):
    """Registra um novo usuário apenas com username e senha"""
    try:
        # Verificar se usuário já existe
        if username_exists(username):
            return False, "Usuário já existe!"
        
        # Criar novo usuário
        user_data = {
            "username": username,
            "password_hash": hash_password(password),
            "created_at": datetime.datetime.now().isoformat(),
            "is_admin": False
        }
        
        response = supabase_client.table("users").insert(user_data).execute()
        
        # Debug: verificar a resposta completa
        st.info(f"Resposta do sign_up: {response}")
        
        if response and response.get("data"):
            # ENVIAR NOTIFICAÇÃO PARA TELEGRAM
            telegram_message = f"👤 Nova conta criada!\n\nUsuário: {username}\nData: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}"
            send_telegram_notification(telegram_message)
            
            return True, "Conta criada com sucesso!"
        else:
            st.error(f"Erro na resposta: {response}")
            return False, "Erro ao criar conta"
            
    except Exception as e:
        st.error(f"Erro no sign_up: {str(e)}")
        return False, f"Erro: {str(e)}"

def sign_in(username, password):
    """Autentica um usuário usando username e senha"""
    try:
        # Debug da busca
        debug_user = debug_user_search(username)
        
        # Buscar usuário no banco
        response = supabase_client.table("users").select("*").eq("username", username).execute()
        
        st.info(f"Resposta do login: {response}")  # Debug
        
        if not response.get("data") or len(response.get("data", [])) == 0:
            st.error(f"Usuário '{username}' não encontrado na tabela 'users'")
            
            # Tentar busca alternativa
            all_users_response = supabase_client.table("users").select("username, id").execute()
            if all_users_response.get("data"):
                st.info(f"Todos os usuários no sistema: {all_users_response['data']}")
                
                # Verificar se o usuário existe com busca manual
                for user in all_users_response["data"]:
                    if user.get("username") == username:
                        st.success(f"Usuário encontrado com busca manual: {user}")
                        # Buscar dados completos
                        user_id = user.get("id")
                        user_full_response = supabase_client.table("users").select("*").eq("id", user_id).execute()
                        if user_full_response.get("data"):
                            user_data = user_full_response["data"][0]
                            break
                else:
                    return False, "Usuário não encontrado!"
            else:
                return False, "Usuário não encontrado!"
        else:
            user_data = response["data"][0]
        
        # Debug: verificar estrutura do usuário
        st.info(f"Dados do usuário encontrado: {user_data}")
        
        # Verificar se a senha hash existe
        if "password_hash" not in user_data:
            st.error("Estrutura do usuário inválida: campo password_hash não encontrado")
            return False, "Erro: estrutura de usuário inválida!"
        
        # Verificar senha
        if check_password(password, user_data["password_hash"]):
            st.session_state.user = user_data
            st.session_state.user_id = user_data.get("id")
            st.session_state.username = user_data.get("username")
            st.session_state.is_admin = user_data.get("is_admin", False)
            st.session_state.show_login = False  # Fechar o formulário após login
            
            st.success(f"Login bem-sucedido! Admin: {st.session_state.is_admin}")
            return True, "Login realizado com sucesso!"
        else:
            st.error("Senha incorreta!")
            return False, "Senha incorreta!"
            
    except Exception as e:
        st.error(f"❌ Erro no login: {str(e)}")
        return False, f"Erro: {str(e)}"

def sign_out():
    """Desconecta o usuário"""
    st.session_state.user = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.is_admin = False
    return True

def get_current_user():
    """Retorna o usuário atual (simulado)"""
    if st.session_state.user:
        return st.session_state.user
    return None

def show_auth_ui():
    """Interface de autenticação simplificada"""
    tab1, tab2 = st.tabs(["Login", "Cadastro"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Nome de usuário", key="login_username")
            password = st.text_input("Senha", type="password", key="login_password")
            submitted = st.form_submit_button("Entrar")
            
            if submitted:
                if not username or not password:
                    st.error("Preencha todos os campos!")
                else:
                    success, message = sign_in(username, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    with tab2:
        with st.form("signup_form"):
            username = st.text_input("Nome de usuário", key="signup_username")
            password = st.text_input("Senha", type="password", key="signup_password")
            confirm_password = st.text_input("Confirmar senha", type="password", key="signup_confirm")
            
            submitted = st.form_submit_button("Criar conta")
            
            if submitted:
                if not username or not password:
                    st.error("Preencha todos os campos!")
                elif password != confirm_password:
                    st.error("As senhas não coincidem")
                elif len(password) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres")
                elif len(username) < 3:
                    st.error("O nome de usuário deve ter pelo menos 3 caracteres")
                else:
                    success, message = sign_up(username, password)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

def is_admin():
    """Verifica se o usuário atual é administrador"""
    return st.session_state.is_admin

def is_super_admin():
    """Verifica se o usuário é um super administrador"""
    return st.session_state.username in ["schutz"]


def promote_to_admin(target_username):
    """Promove um usuário a administrador"""
    try:
        # Primeiro verificar se o usuário atual é super admin
        if not is_super_admin():
            st.error("❌ Apenas super administradores podem promover usuários")
            return False
        
        # Debug: verificar todos os usuários primeiro
        all_users = supabase_client.table("users").select("id, username, is_admin").execute()
        st.info(f"Todos os usuários: {all_users.get('data', [])}")
        
        # Buscar o ID do usuário pelo username
        user_response = supabase_client.table("users").select("id, username, is_admin").eq("username", target_username).execute()
        
        st.info(f"Resposta da busca por {target_username}: {user_response}")
        
        if not user_response.get("data") or len(user_response.get("data", [])) == 0:
            st.error("❌ Usuário não encontrado")
            
            # Tentar busca manual
            if all_users.get("data"):
                for user in all_users["data"]:
                    if user.get("username") == target_username:
                        user_id = user["id"]
                        username = user["username"]
                        break
                else:
                    return False
            else:
                return False
        else:
            user_data = user_response["data"][0]
            user_id = user_data["id"]
            username = user_data["username"]
        
        # Atualizar o campo is_admin para True
        update_response = supabase_client.table("users").update({
            "is_admin": True,
            "updated_at": datetime.datetime.now().isoformat()
        }).eq("id", user_id).execute()
        
        st.info(f"Resposta da atualização: {update_response}")
        
        if update_response.get("data"):
            st.success(f"✅ Usuário {username} promovido a administrador!")
            return True
        else:
            st.error("❌ Erro ao promover usuário")
            return False
            
    except Exception as e:
        st.error(f"❌ Erro ao promover usuário: {e}")
        return False

def debug_user_search(username):
    """Debug da busca de usuário"""
    try:
        st.info(f"Buscando usuário: {username}")
        
        # Tentar diferentes formas de buscar
        response1 = supabase_client.table("users").select("*").eq("username", username).execute()
        st.info(f"Busca 1 - eq: {response1}")
        
        response2 = supabase_client.table("users").select("*").execute()
        st.info(f"Todos os usuários: {response2}")
        
        # Verificar se o usuário está na lista
        if response2.get("data"):
            for user in response2["data"]:
                if user.get("username") == username:
                    st.success(f"Usuário encontrado na lista completa: {user}")
                    return user
        
        return None
    except Exception as e:
        st.error(f"Erro no debug: {e}")
        return None

# ==============================
# CONFIGURAÇÕES DE SEGURANÇA
# ==============================
admin_name = "Schutz"
ADMIN_PASSWORD = "wavesong9090" 

# ==============================
# CONFIGURAÇÕES DO TELEGRAM
# ==============================
TELEGRAM_BOT_TOKEN = "7680456440:AAFRmCOdehS13VjYY5qKttBbm-hDZRDFjP4"
TELEGRAM_ADMIN_CHAT_ID = "5919571280"
TELEGRAM_NOTIFICATIONS_ENABLED = True

# Inicializar bot do Telegram
telegram_bot = None
try:
    telegram_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    print("✅ Bot do Telegram inicializado com sucesso!")
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

@st.cache_data(ttl=30) # 10 minutos 
def get_all_songs_cached():
    return get_all_songs()

def get_all_notifications():
    """Busca todas as notificações (globais e de sistema) de forma unificada"""
    all_notifications = []
    
    # Buscar notificações globais
    try:
        global_ref = db.reference("/global_notifications")
        global_notifications = global_ref.get()
        
        if global_notifications:
            for note_id, note_data in global_notifications.items():
                all_notifications.append({
                    "id": note_id,
                    "type": "global",
                    "title": "Notificação Global",
                    "message": note_data.get("message", ""),
                    "admin": note_data.get("admin", "Admin"),
                    "timestamp": note_data.get("timestamp", ""),
                    "is_read": check_if_global_notification_read(note_id)
                })
    except Exception as e:
        st.error(f"❌ Erro ao buscar notificações globais: {e}")
    
    # Buscar notificações do sistema (músicas)
    try:
        system_ref = db.reference("/system_notifications")
        system_notifications = system_ref.get()
        
        if system_notifications:
            for note_id, note_data in system_notifications.items():
                all_notifications.append({
                    "id": note_id,
                    "type": "music",
                    "title": note_data.get("title", "Nova Música"),
                    "message": note_data.get("formatted_message", ""),
                    "artist": note_data.get("artist", ""),
                    "timestamp": note_data.get("timestamp", ""),
                    "is_read": check_if_system_notification_read(note_id)
                })
    except Exception as e:
        st.error(f"❌ Erro ao buscar notificações do sistema: {e}")
    
    # Ordenar por timestamp (mais recente primeiro)
    try:
        all_notifications.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    except:
        pass
    
    return all_notifications[:20]  # Limitar a 20 notificações

def send_user_notification(user_id, message, notification_type="info"):
    """Envia uma notificação para um usuário específico"""
    try:
        ref = db.reference(f"/user_notifications/{user_id}")
        notification_data = {
            "message": message,
            "type": notification_type,
            "timestamp": datetime.datetime.now().isoformat(),
            "read": False
        }
        ref.push(notification_data)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao enviar notificação para usuário: {e}")
        return False

def get_user_notifications():
    """Busca notificações pessoais do usuário atual"""
    if not st.session_state.user_id:
        return []
    
    try:
        ref = db.reference(f"/user_notifications/{st.session_state.user_id}")
        notifications = ref.get()
        
        user_notifications = []
        if notifications:
            for note_id, note_data in notifications.items():
                user_notifications.append({
                    "id": note_id,
                    "message": note_data.get("message", ""),
                    "type": note_data.get("type", "info"),
                    "timestamp": note_data.get("timestamp", ""),
                    "read": note_data.get("read", False)
                })
            
            # Ordenar por timestamp (mais recente primeiro)
            user_notifications.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return user_notifications
    except Exception as e:
        st.error(f"❌ Erro ao buscar notificações do usuário: {e}")
        return []


def mark_user_notification_as_read(notification_id):
    """Marca uma notificação pessoal como lida"""
    if not st.session_state.user_id:
        return False
    
    try:
        ref = db.reference(f"/user_notifications/{st.session_state.user_id}/{notification_id}/read")
        ref.set(True)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao marcar notificação como lida: {e}")
        return False

def check_if_global_notification_read(note_id):
    """Verifica se uma notificação global foi lida pelo usuário atual"""
    if not st.session_state.user_id:
        return False
    
    try:
        ref = db.reference(f"/global_notifications/{note_id}/read_by/{st.session_state.user_id}")
        return ref.get() or False
    except:
        return False

def check_if_system_notification_read(note_id):
    """Verifica se uma notificação do sistema foi lida pelo usuário atual"""
    if not st.session_state.user_id:
        return False
    
    try:
        ref = db.reference(f"/system_notifications/{note_id}/read_by/{st.session_state.user_id}")
        return ref.get() or False
    except:
        return False

def mark_notification_as_read(notification_id, notification_type):
    """Marca uma notificação como lida para o usuário atual"""
    if not st.session_state.firebase_connected or not st.session_state.user_id:
        return False
    
    try:
        user_key = st.session_state.user_id
        
        if notification_type == "global":
            ref = db.reference(f"/global_notifications/{notification_id}/read_by/{user_key}")
        elif notification_type == "music":
            ref = db.reference(f"/system_notifications/{notification_id}/read_by/{user_key}")
        else:
            st.error(f"Tipo de notificação desconhecido: {notification_type}")
            return False
        
        ref.set(True)
        
        # Atualizar o cache de notificações não lidas
        if "unread_notifications_cache" in st.session_state:
            st.session_state.unread_notifications_cache = None
            
        return True
        
    except Exception as e:
        st.error(f"❌ Erro ao marcar notificação como lida: {e}")
        return False


def show_admin_management():
    """Interface para gerenciamento de administradores"""
    if not is_super_admin():
        st.error("❌ Acesso restrito a super administradores")
        return
    
    st.subheader("👥 Gerenciamento de Administradores")
    
    # Formulário para promover usuários
    with st.form("promote_admin_form"):
        st.write("### Promover usuário a administrador")
        admin_username = st.text_input("Nome de usuário para promover:")
        
        submitted = st.form_submit_button("Promover a Admin")
        if submitted:
            if promote_to_admin(admin_username):
                st.rerun()
    
    # Listar administradores atuais - CORRIGIDO: usar tabela users em vez de profiles
    st.write("### Administradores atuais")
    try:
        response = supabase_client.table("users").select("username, is_admin").eq("is_admin", True).execute()
        
        if response.get("data"):
            for admin in response["data"]:
                status = "✅ Super Admin" if admin.get('username') in ["schutz", "admin"] else "✅ Admin"
                st.write(f"**{admin.get('username', 'N/A')}** - {status}")
        else:
            st.info("Nenhum administrador cadastrado.")
    except Exception as e:
        st.error(f"❌ Erro ao carregar administradores: {e}")


def send_specific_user_notification():
    """Interface para enviar notificação para usuário específico"""
    st.subheader("📨 Enviar Notificação para Usuário Específico")
    
    # Buscar todos os usuários
    try:
        users_response = supabase_client.table("users").select("id, username").execute()
        
        if users_response.get("data"):
            users = {user["username"]: user["id"] for user in users_response["data"]}
            
            with st.form("specific_notification_form"):
                selected_user = st.selectbox(
                    "Selecionar usuário:",
                    options=list(users.keys())
                )
                
                message = st.text_area("Mensagem:", placeholder="Digite a mensagem para o usuário...")
                
                submitted = st.form_submit_button("Enviar Notificação")
                
                if submitted:
                    if not message.strip():
                        st.error("A mensagem não pode estar vazia!")
                        return
                    
                    user_id = users[selected_user]
                    if send_user_notification(user_id, message):
                        st.success(f"✅ Notificação enviada para {selected_user}!")
                    else:
                        st.error("❌ Erro ao enviar notificação!")
        else:
            st.info("Nenhum usuário cadastrado.")
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar usuários: {e}")

# função para verificar o status do Telegram
def check_telegram_bot_status():
    if not TELEGRAM_NOTIFICATIONS_ENABLED:
        return "❌ Desativado"
    
    try:
        bot_info = telegram_bot.get_me()
        # Testar envio de mensagem
        test_msg = telegram_bot.send_message(TELEGRAM_ADMIN_CHAT_ID, "🤖 Bot está funcionando!", disable_notification=True)
        return f"✅ Conectado (@{bot_info.username})"
    except Exception as e:
        return f"❌ Erro: {str(e)[:50]}..."

def add_system_notification(title, artist, image_url, song_id):
    """Adiciona notificação ao sistema interno de notificações"""
    try:
        if st.session_state.firebase_connected:
            ref = db.reference("/system_notifications")
            notification_data = {
                "type": "new_song",
                "title": title,
                "artist": artist,
                "image_url": image_url,
                "song_id": song_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "read_by": {},
                "formatted_message": f"""🎵 Nova música adicionada!

{title}
{artist}"""
            }
            st.info(f"💾 Tentando salvar notificação para: {title} - {artist}")
            new_notification_ref = ref.push(notification_data)
            notification_key = new_notification_ref.key
            st.success(f"✅ Notificação salva com ID: {notification_key}")
            
            # Verificar imediatamente se foi salva
            try:
                check_ref = db.reference(f"/system_notifications/{notification_key}")
                saved_notification = check_ref.get()
                if saved_notification:
                    st.info("✅ Notificação verificada no banco de dados!")
                    return True
                else:
                    st.error("❌ Notificação não encontrada após salvar!")
                    return False
            except Exception as check_error:
                st.error(f"❌ Erro ao verificar notificação: {check_error}")
                return False
        else:
            st.error("❌ Firebase não conectado para salvar notificação")
            return False
    except Exception as e:
        st.error(f"❌ Erro ao adicionar notificação do sistema: {e}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return False

def check_firebase_rules():
    """Verifica se as regras do Firebase estão configuradas corretamente"""
    try:
        # Testar ordenação em system_notifications
        ref = db.reference("/system_notifications")
        test_data = ref.order_by_child("timestamp").limit_to_last(1).get()
        return "✅ Conectado"
    except Exception as e:
        if "indexOn" in str(e):
            return "⚠️ Regras não configuradas (usando fallback)"
        return f"❌ Erro: {str(e)[:100]}"



def add_song_request(request_data):
    try:
        if st.session_state.firebase_connected:
            ref = db.reference("/song_requests")
            request_data["created_at"] = datetime.datetime.now().isoformat()
            request_data["status"] = "pending"
            ref.push(request_data)
            
            # Enviar notificação para Telegram - FORMATO CORRIGIDO
            title = request_data.get("title", "Sem título")
            artist = request_data.get("artist", "Artista desconhecido")
            album = request_data.get("album", "Álbum desconhecido")
            req_username = request_data.get("requested_by", "Anônimo")
            
            # Mensagem formatada como solicitado
            notification_message = f"""Novo pedido de música:
            
{artist} - {title} - {album}

Música: {title}
Artista: {artist}
Álbum: {album}
Solicitado por: {req_username}"""

            send_telegram_notification(notification_message)
            
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
    now = datetime.datetime.now()
    
    if (st.session_state.random_songs_timestamp is None or 
        (now - st.session_state.random_songs_timestamp).total_seconds() > 24*3600 or
        not st.session_state.random_songs):
        
        remaining_songs = [s for s in all_songs if s not in top6_songs]
        st.session_state.random_songs = random.sample(remaining_songs, min(6, len(remaining_songs)))
        st.session_state.random_songs_timestamp = now
    
    return st.session_state.random_songs

# ==============================
# FUNÇÕES DE NOTIFICAÇÃO TELEGRAM (CORRIGIDAS)
# ==============================
def check_telegram_connection():
    if not TELEGRAM_NOTIFICATIONS_ENABLED:
        return False
    
    try:
        bot_info = telegram_bot.get_me()
        return True
    except Exception as e:
        st.error(f"❌ Bot do Telegram desconectado: {e}")
        return False


def setup_telegram_commands():
    if not TELEGRAM_NOTIFICATIONS_ENABLED:
        return
    
    @telegram_bot.message_handler(commands=['start', 'help'])
    def handle_start_help(message):
        response = """🌊 *Wave Song Bot* 🌊

*Comandos disponíveis:*
/status - Ver status do sistema
/notify [mensagem] - Enviar notificação global
/users - Estatísticas do sistema
/help - Mostra esta ajuda

*Desenvolvido por Schutz*"""
        telegram_bot.send_message(message.chat.id, response, parse_mode='Markdown')
    
    @telegram_bot.message_handler(commands=['status'])
    def handle_status(message):
        if str(message.chat.id) != TELEGRAM_ADMIN_CHAT_ID:
            telegram_bot.send_message(message.chat.id, "❌ Apenas administradores podem usar este comando.")
            return
        
        status = "✅ Online" if st.session_state.firebase_connected else "⚠️ Offline"
        total_songs = len(st.session_state.all_songs)
        response = f"""🌊 *Status do Wave Song*

{status}
🎵 Músicas no banco: {total_songs}
🔔 Notificações: {'✅ Ativas' if TELEGRAM_NOTIFICATIONS_ENABLED else '❌ Inativas'}
🛡️ Admin: {admin_name}"""
        telegram_bot.send_message(message.chat.id, response, parse_mode='Markdown')
    
    @telegram_bot.message_handler(commands=['notify'])
    def handle_notify(message):
        if str(message.chat.id) != TELEGRAM_ADMIN_CHAT_ID:
            telegram_bot.send_message(message.chat.id, "❌ Apenas administradores podem enviar notificações.")
            return
        
        parts = message.text.split(' ', 1)
        if len(parts) < 2:
            telegram_bot.send_message(message.chat.id, "❌ Uso: /notify [mensagem]")
            return
        
        notification_text = parts[1]
        if send_global_notification(notification_text):
            telegram_bot.send_message(message.chat.id, f"✅ Notificação enviada:\n{notification_text}")
        else:
            telegram_bot.send_message(message.chat.id, "❌ Falha ao enviar notificação.")
    
    @telegram_bot.message_handler(commands=['users'])
    def handle_users(message):
        if str(message.chat.id) != TELEGRAM_ADMIN_CHAT_ID:
            telegram_bot.send_message(message.chat.id, "❌ Apenas administradores podem ver estatísticas.")
            return
        
        total_songs = len(st.session_state.all_songs)
        response = f"""👥 *Estatísticas do Wave Song*

🎵 Músicas: {total_songs}
🔗 Firebase: {'✅ Conectado' if st.session_state.firebase_connected else '❌ Desconectado'}
🤖 Telegram: {'✅ Conectado' if TELEGRAM_NOTIFICATIONS_ENABLED else '❌ Desconectado'}
🛡️ Admin: {admin_name}"""
        telegram_bot.send_message(message.chat.id, response, parse_mode='Markdown')


def check_and_display_telegram_status():
    global telegram_bot, TELEGRAM_NOTIFICATIONS_ENABLED
    
    if not TELEGRAM_NOTIFICATIONS_ENABLED:
        st.error("❌ Telegram desativado")
        return False
    
    try:
        bot_info = telegram_bot.get_me()
        st.success(f"✅ Telegram conectado")
        st.info(f"🤖 Bot: @{bot_info.username}")
        st.info(f"🆔 ID: {bot_info.id}")
        st.info(f"📛 Nome: {bot_info.first_name}")
        st.info(f"💬 Chat ID do Admin: {TELEGRAM_ADMIN_CHAT_ID}")
        return True
    except Exception as e:
        st.error(f"❌ Telegram desconectado: {str(e)}")
        
        try:
            telegram_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
            TELEGRAM_NOTIFICATIONS_ENABLED = True
            st.success("✅ Reconectado ao Telegram!")
            setup_telegram_commands()
            return True
        except Exception as e2:
            st.error(f"❌ Falha ao reconectar: {e2}")
            TELEGRAM_NOTIFICATIONS_ENABLED = False
            return False

def send_telegram_notification(message, retry_count=2):
    if not TELEGRAM_NOTIFICATIONS_ENABLED:
        return False
    
    for attempt in range(retry_count):
        try:
            telegram_bot.send_message(TELEGRAM_ADMIN_CHAT_ID, message)
            return True
        except Exception as e:
            if attempt == retry_count - 1:
                st.error(f"❌ Erro ao enviar notificação para Telegram: {e}")
            time.sleep(1)
    return False

def send_global_notification(message):
    if not st.session_state.firebase_connected:
        return False
    
    try:
        ref = db.reference("/global_notifications")
        notification_data = {
            "message": message,
            "admin": "Schutz",
            "timestamp": datetime.datetime.now().isoformat(),
            "read_by": {}
        }
        ref.push(notification_data)
        
        send_telegram_notification(f"📢 Nova notificação global:\n{message}")
        return True
    except Exception as e:
        st.error(f"❌ Erro ao enviar notificação global: {e}")
        return False

def check_unread_notifications():
    """Verifica notificações não lidas para o usuário atual"""
    if not st.session_state.firebase_connected or not st.session_state.user_id:
        return 0
    
    try:
        all_notifications = []
        user_id = st.session_state.user_id
        
        # Verificar notificações globais
        global_ref = db.reference("/global_notifications")
        global_notifications = global_ref.get()
        if global_notifications:
            for note_id, note_data in global_notifications.items():
                read_by = note_data.get("read_by", {})
                if user_id not in read_by or not read_by[user_id]:
                    all_notifications.append(note_id)
        
        # Verificar notificações do sistema
        system_ref = db.reference("/system_notifications")
        system_notifications = system_ref.get()
        if system_notifications:
            for note_id, note_data in system_notifications.items():
                read_by = note_data.get("read_by", {})
                if user_id not in read_by or not read_by[user_id]:
                    all_notifications.append(note_id)
        
        return len(all_notifications)
    except Exception as e:
        st.error(f"❌ Erro ao verificar notificações: {e}")
        return 0


def mark_notification_as_read(notification_id, notification_type):
    """Marca uma notificação como lida"""
    if not st.session_state.firebase_connected:
        return False
    
    try:
        user_key = "anonymous"
        if notification_type == "global":
            ref = db.reference(f"/global_notifications/{notification_id}/read_by/{user_key}")
        else:
            ref = db.reference(f"/system_notifications/{notification_id}/read_by/{user_key}")
        
        ref.set(True)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao marcar notificação como lida: {e}")
        return False

def setup_telegram_webhook():
    if not TELEGRAM_NOTIFICATIONS_ENABLED:
        return False
    
    try:
        setup_telegram_commands()
        
        def start_polling():
            try:
                print("🤖 Iniciando bot do Telegram...")
                telegram_bot.infinity_polling()
            except Exception as e:
                print(f"❌ Erro no polling do Telegram: {e}")
        
        polling_thread = threading.Thread(target=start_polling, daemon=True)
        polling_thread.start()
        
        print("✅ Bot do Telegram configurado para receber comandos!")
        return True
        
    except Exception as e:
        st.error(f"❌ Erro ao configurar Telegram: {e}")
        return False

def handle_telegram_commands():
    pass

# Configurar Telegram para receber comandos
if TELEGRAM_NOTIFICATIONS_ENABLED:
    try:
        setup_telegram_commands()
        def start_bot():
            try:
                telegram_bot.infinity_polling()
            except Exception as e:
                print(f"Erro no bot do Telegram: {e}")
        
        bot_thread = threading.Thread(target=start_bot, daemon=True)
        bot_thread.start()
        print("✅ Bot do Telegram iniciado!")
    except Exception as e:
        st.error(f"❌ Erro ao iniciar bot: {e}")

def send_telegram_command_response(command, message=""):
    if not TELEGRAM_NOTIFICATIONS_ENABLED:
        st.error("❌ Telegram não está habilitado")
        return False
    
    try:
        if command == "/status":
            # Status real do sistema em vez de mensagem genérica
            status = "✅ Online" if st.session_state.firebase_connected else "⚠️ Offline"
            total_songs = len(st.session_state.all_songs)
            response = f"""🌊 *Status do Wave Song*

{status}
🎵 Músicas no banco: {total_songs}
🔔 Notificações: {'✅ Ativas' if TELEGRAM_NOTIFICATIONS_ENABLED else '❌ Inativas'}
🛡️ Admin: {admin_name}"""
            telegram_bot.send_message(TELEGRAM_ADMIN_CHAT_ID, response, parse_mode='Markdown')
            return True
            
        elif command == "/help":
            # Mensagem de ajuda real
            response = """🌊 *Wave Song Bot* 🌊

*Comandos disponíveis:*
/status - Ver status do sistema
/notify [mensagem] - Enviar notificação global
/users - Estatísticas do sistema
/help - Mostra esta ajuda

*Desenvolvido por Schutz*"""
            telegram_bot.send_message(TELEGRAM_ADMIN_CHAT_ID, response, parse_mode='Markdown')
            return True
            
        elif command == "/users":
            # Estatísticas reais
            total_songs = len(st.session_state.all_songs)
            response = f"""👥 *Estatísticas do Wave Song*

🎵 Músicas: {total_songs}
🔗 Firebase: {'✅ Conectado' if st.session_state.firebase_connected else '❌ Desconectado'}
🤖 Telegram: {'✅ Conectado' if TELEGRAM_NOTIFICATIONS_ENABLED else '❌ Desconectado'}
🛡️ Admin: {admin_name}"""
            telegram_bot.send_message(TELEGRAM_ADMIN_CHAT_ID, response, parse_mode='Markdown')
            return True
            
        else:
            st.error(f"❌ Comando desconhecido: {command}")
            return False
            
    except Exception as e:
        st.error(f"❌ Erro ao enviar comando: {e}")
        return False
# ==============================
# FUNÇÃO DE CONVERSÃO DE URL CORRIGIDA
# ==============================
def convert_github_to_jsdelivr(url):
    if not url:
        return url
    
    try:
        if "github.com" in url and "/raw/" in url:
            parts = url.split("/")
            github_index = parts.index("github.com")
            usuario = parts[github_index + 1]
            repo = parts[github_index + 2]
            
            raw_index = parts.index("raw")
            ramo = parts[raw_index + 1]
            caminho_arquivo = "/".join(parts[raw_index + 2:])
            
            nova_url = f"https://cdn.jsdelivr.net/gh/{usuario}/{repo}@{ramo}/{caminho_arquivo}"
            return nova_url
        
        elif "raw.githubusercontent.com" in url:
            parts = url.split("/")
            raw_index = parts.index("raw.githubusercontent.com")
            usuario = parts[raw_index + 1]
            repo = parts[raw_index + 2]
            ramo = parts[raw_index + 3]
            caminho_arquivo = "/".join(parts[raw_index + 4:])
            
            nova_url = f"https://cdn.jsdelivr.net/gh/{usuario}/{repo}@{ramo}/{caminho_arquivo}"
            return nova_url
        
        else:
            return url
            
    except Exception as e:
        print(f"Erro ao converter URL {url}: {e}")
        return url

def get_converted_audio_url(song):
    audio_url = song.get("audio_url", "")
    if "github.com" in audio_url or "raw.githubusercontent.com" in audio_url:
        return convert_github_to_jsdelivr(audio_url)
    return audio_url

def play_song(song):
    current_id = st.session_state.current_track["id"] if st.session_state.current_track else None
    new_id = song["id"]
    
    if "audio_url" in song and ("github.com" in song["audio_url"] or "raw.githubusercontent.com" in song["audio_url"]):
        song_copy = song.copy()
        song_copy["audio_url"] = convert_github_to_jsdelivr(song["audio_url"])
        song = song_copy
    
    st.session_state.current_track = song
    st.session_state.is_playing = True
    st.session_state.player_timestamp = time.time()
    
    if st.session_state.firebase_connected:
        try:
            ref = db.reference(f"/songs/{song['id']}/play_count")
            current_count = ref.get() or 0
            ref.set(current_count + 1)
        except Exception as e:
            st.error(f"Erro ao atualizar play_count: {e}")
    
    if current_id != new_id:
        st.rerun()


def show_notification_panel():
    st.header("🔔 Painel de Notificações")
    
    if not st.session_state.admin_authenticated:
        password = st.text_input("Senha de Administrador", type="password", key="notif_auth")
        if st.button("Acessar", key="notif_btn"):
            if password == ADMIN_PASSWORD: 
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")
        return
    
    # Abas para diferentes tipos de notificações
    tab1, tab2, tab3, tab4 = st.tabs(["📢 Notificações Globais", "🎵 Notificações de Músicas", "🤖 Status do Telegram", "📨 Notificações para Usuários"])
    
    with tab1:
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
        
        st.subheader("Histórico de Notificações Globais")
        try:
            ref = db.reference("/global_notifications")
            notifications = ref.get()
            
            if notifications:
                notifications_list = []
                for note_id, note_data in notifications.items():
                    notifications_list.append({
                        "id": note_id,
                        "admin": note_data.get("admin", "Admin"),
                        "message": note_data.get("message", ""),
                        "timestamp": note_data.get("timestamp", "")
                    })

                try:
                    notifications_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                except:
                    notifications_list.reverse()
                
                for note in notifications_list:
                    st.markdown(f"""
                    <div style='
                        background-color: #1f2937;
                        padding: 15px;
                        border-radius: 10px;
                        margin-bottom: 10px;
                        border-left: 4px solid #1DB954;
                    '>
                        <p style='color: #9ca3af; font-size: 12px; margin: 0;'>
                            🛡️ <strong>{note['admin']}</strong> • {note['timestamp'][:10] if note['timestamp'] else 'Data não disponível'}
                        </p>
                        <p style='color: white; font-size: 14px; margin: 5px 0 0 0;'>
                            {note['message']}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("📝 Nenhuma notificação global enviada ainda.")
        except Exception as e:
            st.error(f"❌ Erro ao carregar histórico: {e}")
    
    with tab3:
        st.subheader("🤖 Status do Telegram")
        
        if check_and_display_telegram_status():
            st.success("✅ Pronto para receber comandos via Telegram!")
            st.info("💡 Use os comandos diretamente no Telegram:")
            st.code("/start - Mostra ajuda\n/status - Status do sistema\n/notify [mensagem] - Enviar notificação\n/users - Estatísticas")
        else:
            st.error("❌ Não é possível receber comandos do Telegram")
            
        st.markdown("---")
        st.subheader("📋 Comandos Rápidos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Status do Sistema", help="Verificar status atual", key="status_btn"):
                send_telegram_command_response("/status", "")
                
            if st.button("👥 Estatísticas", help="Ver estatísticas", key="stats_btn"):
                send_telegram_command_response("/users", "")
        
        with col2:
            if st.button("❓ Ajuda", help="Mostrar ajuda", key="help_btn"):
                send_telegram_command_response("/help", "")
                
            if st.button("🔄 Reconectar", help="Tentar reconectar", key="reconnect_btn"):
                try:
                    global telegram_bot
                    telegram_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
                    setup_telegram_commands()
                    st.success("✅ Bot reconectado!")
                except Exception as e:
                    st.error(f"❌ Erro: {e}")

    with tab4:
        send_specific_user_notification()
    
    if st.button("🔒 Sair do Painel de Notificações"):
        st.session_state.admin_authenticated = False
        st.rerun()


def get_system_notifications_fallback():
    """Busca notificações sem ordenação para evitar erros de regras"""
    try:
        ref = db.reference("/system_notifications")
        notifications = ref.get()
        
        if notifications:
            notifications_list = []
            for note_id, note_data in notifications.items():
                notifications_list.append({
                    "id": note_id,
                    "title": note_data.get("title", ""),
                    "artist": note_data.get("artist", ""),
                    "image_url": note_data.get("image_url", ""),
                    "timestamp": note_data.get("timestamp", ""),
                    "formatted_message": note_data.get("formatted_message", "")
                })
            
            # Ordenar manualmente por timestamp
            try:
                notifications_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            except:
                pass
            
            return notifications_list[:10]  # Limitar a 10 mais recentes
        return []
    except Exception as e:
        st.error(f"❌ Erro ao buscar notificações: {e}")
        return []


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

    audio_src = get_converted_audio_url(track)
    
    cover = load_image_cached(track.get("image_url"))
    if cover is not None:
        cover_url = image_to_base64(cover)
    else:
        cover_url = "https://via.placeholder.com/80x80?text=Sem+Imagem"

    title = track.get("title", "Sem título")
    artist = track.get("artist", "Sem artista")
    
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
            document.addEventListener('DOMContentLoaded', function() {{
                const audio = document.querySelector('audio');
                if (audio && {str(st.session_state.is_playing).lower()}) {{
                    const playPromise = audio.play();
                    if (playPromise !== undefined) {{
                        playPromise.catch(error => {{
                            console.log('Autoplay prevented:', error);
                            audio.controls = true;
                        }});
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    '''
    
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
# SIDEBAR (MODIFICADA PARA INCLUIR LOGIN)
# ==============================
with st.sidebar:
    st.title("🌊 Wave Song")
    st.success("✅ Online" if st.session_state.firebase_connected else "⚠️ Offline")

    # Verificar autenticação
    init_auth()
    current_user = get_current_user()
    
    if current_user:
        # Usuário logado
        st.markdown(f"**👤 {st.session_state.username}**")
        if st.button("🚪 Sair", key="logout_btn"):
            if sign_out():
                st.success("Logout realizado!")
                st.session_state.show_login = False  # Resetar o estado de login
                st.rerun()
    else:
    # Usuário não logado - versão simplificada
        if not st.session_state.show_login:
            if st.button("🔐 Login/Cadastro", key="login_btn", use_container_width=True):
                st.session_state.show_login = True
                st.rerun()
        else:
            # Botão para fechar o formulário
            if st.button("✕ Fechar", key="close_login", use_container_width=True):
                st.session_state.show_login = False
                st.rerun()
        
            # Mostrar formulário de autenticação
            show_auth_ui()


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

    # Menu para usuários normais
    if not st.session_state.admin_mode:
        unread_notifications = check_unread_notifications()
        notification_text = f"🔔 Notificações ({unread_notifications})" if unread_notifications else "🔔 Notificações"

        if st.button(notification_text, use_container_width=True, key="btn_notifications"):
            st.session_state.current_page = "notifications"
            st.session_state.show_request_form = False

        if st.button("Página Inicial", key="btn_home", use_container_width=True):
            st.session_state.current_page = "home"
            st.session_state.show_request_form = False
            
        if st.button("Buscar Músicas", key="btn_search", use_container_width=True):
            st.session_state.current_page = "search"
            st.session_state.show_request_form = False


        # Menu para administradores
    if st.session_state.is_admin:
        st.markdown("---")
        st.subheader("🛡️ Painel de Administração")
        
        if st.button("👥 Gerenciar Administradores", key="btn_admin_manage", use_container_width=True):
            st.session_state.current_page = "admin_management"
            
        if st.button("📊 Estatísticas do Sistema", key="btn_admin_stats", use_container_width=True):
            st.session_state.current_page = "stats"
            
        if st.button("🔔 Painel de Notificações", key="btn_admin_notifications", use_container_width=True):
            st.session_state.current_page = "notification_panel"

# ==============================
# PÁGINAS PRINCIPAIS
# ==============================
if st.session_state.current_page == "home":
    st.header("🌊 Bem-vindo ao Wave")
    
    if not st.session_state.all_songs:
        st.session_state.all_songs = get_all_songs_cached()

    new_query = st.text_input("Buscar música:", placeholder="Digite o nome da música ou artista...")
    if new_query.strip():
        st.session_state.search_input = new_query.strip()
        st.session_state.current_page = "search"
        st.rerun()

    total_musicas = len(st.session_state.all_songs)
    st.markdown(f"### Temos {total_musicas} Músicas Disponíveis")
    st.markdown("### Músicas em destaque:")
    
    if st.session_state.all_songs:
        top6_songs = get_top6_songs()
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
                        
            show_request_music_section()
            
        else:
            st.warning("Nenhuma música encontrada.")
            show_request_music_section()
    else:
        st.info("Nenhuma música cadastrada.")
        show_request_music_section()

elif st.session_state.current_page == "admin_management":  # NOVO
    show_admin_management()

elif st.session_state.current_page == "notification_panel":
    show_notification_panel()

elif st.session_state.current_page == "stats":
    st.header("📊 Estatísticas do Sistema")
    
    if not st.session_state.admin_authenticated:
        password = st.text_input("Senha de Administrador", type="password", key="stats_auth")
        if st.button("Acessar", key="stats_btn"):
            if password == ADMIN_PASSWORD: 
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")
        st.stop()

    st.metric("Total de Músicas", len(st.session_state.all_songs))
    
    top_songs = get_top6_songs()
    st.subheader("🎵 Músicas Mais Tocadas")
    for i, song in enumerate(top_songs):
        st.write(f"{i+1}. **{song['title']}** - {song['artist']} ({song.get('play_count', 0)} plays)")
    
    st.subheader("🔗 Status das Conexões")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Firebase", "✅ Conectado" if st.session_state.firebase_connected else "❌ Desconectado")
    with col2:
        st.metric("Telegram", "✅ Conectado" if TELEGRAM_NOTIFICATIONS_ENABLED else "❌ Desconectado")
    with col3:
        st.metric("Regras Firebase", check_firebase_rules())
    
    if st.button("Voltar"):
        st.session_state.current_page = "home"


elif st.session_state.current_page == "notifications":
    st.markdown(f"<h1 style='text-align:center;'>🔔 Notificações</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not st.session_state.user_id:
        st.warning("⚠️ Faça login para ver suas notificações")
        if st.button("Fazer Login", key="goto_login_notifications"):
            st.session_state.show_login = True
            st.rerun()
        st.stop()
    
    # Buscar notificações
    try:
        all_notifications = get_all_notifications()
        
        if not all_notifications:
            st.info("📝 Não há notificações no momento.")
            if st.button("Voltar para o Início", key="back_from_notifications_empty"):
                st.session_state.current_page = "home"
            st.stop()
        
        # Contar notificações não lidas
        unread_count = sum(1 for note in all_notifications if not note.get("is_read", False))
        
        if unread_count > 0:
            st.success(f"📬 Você tem {unread_count} notificação(ões) não lida(s)")
            st.markdown("---")
        
        # Exibir notificações
        for i, notification in enumerate(all_notifications):
            is_unread = not notification.get("is_read", False)
            
            # Estilo diferente para notificações não lidas
            border_color = "#1DB954" if is_unread else "#555"
            background_color = "#1f2937" if is_unread else "#2d3748"
            
            with st.container():
                if notification.get("type") == "global":
                    # Notificação global
                    timestamp_display = notification.get("timestamp", "")[:10] if notification.get("timestamp") else "Data não disponível"
                    
                    st.markdown(f"""
                    <div style='
                        background-color: {background_color};
                        padding: 15px;
                        border-radius: 10px;
                        margin-bottom: 15px;
                        border-left: 4px solid {border_color};
                    '>
                        <p style='color: #9ca3af; font-size: 12px; margin: 0;'>
                            📢 <strong>{notification.get('admin', 'Admin')}</strong> • {timestamp_display}
                            {"<span style='color: #1DB954; margin-left: 10px;'>● NOVA</span>" if is_unread else ""}
                        </p>
                        <p style='color: white; font-size: 16px; margin: 8px 0 0 0;'>
                            {notification.get('message', '')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                else:
                    # Notificação de música
                    timestamp_display = notification.get("timestamp", "")[:10] if notification.get("timestamp") else "Data não disponível"
                    
                    st.markdown(f"""
                    <div style='
                        background-color: {background_color};
                        padding: 15px;
                        border-radius: 10px;
                        margin-bottom: 15px;
                        border-left: 4px solid {border_color};
                    '>
                        <p style='color: #9ca3af; font-size: 12px; margin: 0;'>
                            🎵 Nova Música • {timestamp_display}
                            {"<span style='color: #1DB954; margin-left: 10px;'>● NOVA</span>" if is_unread else ""}
                        </p>
                        <p style='color: white; font-size: 18px; font-weight: bold; margin: 8px 0 5px 0;'>
                            {notification.get('title', 'Sem título')}
                        </p>
                        <p style='color: #1DB954; font-size: 16px; margin: 0;'>
                            {notification.get('artist', 'Artista desconhecido')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Botão para marcar como lida (apenas para não lidas)
                if is_unread:
                    if st.button("✅ Marcar como lida", key=f"read_{i}_{notification.get('id', 'unknown')}"):
                        if mark_notification_as_read(notification.get('id'), notification.get('type', 'global')):
                            st.success("✅ Notificação lida!")
                            time.sleep(1)
                            st.experimental_rerun()
                
                st.markdown("---")
        
        if st.button("Voltar para o Início", key="back_from_notifications"):
            st.session_state.current_page = "home"
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar notificações: {e}")
        if st.button("Voltar para o Início", key="back_from_notifications_error"):
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
