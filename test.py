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
import json
import gc
import re
import unicodedata
import streamlit.components.v1 as components
from firebase_admin import credentials, db
from io import BytesIO
from PIL import Image

# ==============================
# SISTEMA DE PERSISTÊNCIA DE LOGIN MELHORADO
# ==============================
def save_auth_session(username, user_id, is_admin):
    """Salva a sessão de autenticação usando múltiplos métodos"""
    auth_data = {
        'username': username,
        'user_id': str(user_id),  # Converte UUID para string
        'is_admin': is_admin,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    # Método 1: Query parameters (funciona imediatamente)
    # st.experimental_set_query_params(auth=json.dumps(auth_data))
    
    # Método 2: Session Storage (persiste entre recargas)
    js_code = f"""
    <script>
    // Salvar no sessionStorage
    sessionStorage.setItem('wave_auth', '{json.dumps(auth_data).replace("'", "\\'")}');
    
    // Salvar também no localStorage para persistência mais longa
    localStorage.setItem('wave_auth', '{json.dumps(auth_data).replace("'", "\\'")}');
    </script>
    """
    components.html(js_code, height=0)

def clear_auth_session():
    """Limpa a sessão de autenticação"""
    # Limpar query parameters
    st.experimental_set_query_params()
    
    # Limpar storage
    js_code = """
    <script>
    sessionStorage.removeItem('wave_auth');
    localStorage.removeItem('wave_auth');
    </script>
    """
    components.html(js_code, height=0)

def check_persistent_auth():
    """Verifica se há autenticação salva em múltiplas fontes"""
    # 1. Verificar query parameters primeiro (mais rápido)
    query_params = st.experimental_get_query_params()
    if 'auth' in query_params:
        try:
            auth_data = json.loads(query_params['auth'][0])
            if validate_auth_data(auth_data):
                return auth_data
        except:
            pass
    
    # 2. Verificar sessionStorage via JavaScript
    js_code = """
    <script>
    // Verificar sessionStorage primeiro, depois localStorage
    var authData = sessionStorage.getItem('wave_auth') || localStorage.getItem('wave_auth');
    if (authData) {
        window.parent.postMessage({
            type: 'AUTH_DATA',
            data: authData
        }, '*');
    }
    </script>
    """
    
    components.html(js_code, height=0)
    
    # 3. Tentar verificar se há mensagem do JavaScript
    try:
        if 'auth_data' in st.session_state and st.session_state.auth_data:
            auth_data = json.loads(st.session_state.auth_data)
            if validate_auth_data(auth_data):
                return auth_data
    except:
        pass
    
    return None

def validate_auth_data(auth_data):
    """Valida os dados de autenticação"""
    try:
        if not all(key in auth_data for key in ['username', 'user_id', 'is_admin', 'timestamp']):
            return False
        
        # UUID são strings de 36 caracteres, verifique se parece com um UUID
        user_id = auth_data['user_id']
        if not isinstance(user_id, str) or len(user_id) != 36:
            return False
            
        # Verificar se a sessão não expirou (30 dias)
        timestamp = datetime.datetime.fromisoformat(auth_data['timestamp'])
        if (datetime.datetime.now() - timestamp).days > 30:
            return False
            
        return True
    except:
        return False


# ----------------teste-------------------------------------------



# --------------------------------------------------------------------
def get_current_timestamp():
    """Retorna timestamp formatado corretamente para Firebase"""
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

@st.cache_data
def load_image_from_url(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content))

def resize_image(img, max_size=300):
    img.thumbnail((max_size, max_size))
    return img

def load_image(url):
    try:
        if "drive.google.com" in url:
            url = convert_google_drive_url(url)
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return resize_image(img)  # 🔧 reduz tamanho
        return None
    except:
        return None


def clear_memory():
    gc.collect()

def search_songs_in_firebase(query):
    ref = db.reference("/songs")
    songs = ref.order_by_child("title").start_at(query).end_at(query + "\uf8ff").get()
    return songs




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
if "user" not in st.session_state:
    st.session_state.user = None
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
if "unread_cache_timestamp" not in st.session_state:
    st.session_state.unread_cache_timestamp = 0
if "notifications_cache_timestamp" not in st.session_state:
    st.session_state.notifications_cache_timestamp = 0
if "notifications_cache" not in st.session_state:
    st.session_state.notifications_cache = None

# ==============================
# VERIFICAÇÃO DE AUTENTICAÇÃO PERSISTENTE
# ==============================
if st.session_state.user is None:
    auth_data = check_persistent_auth()
    if auth_data:
        st.session_state.user = {
            'username': auth_data['username'],
            'id': auth_data['user_id'],  # Agora é UUID string
            'is_admin': auth_data['is_admin']
        }
        st.session_state.user_id = auth_data['user_id']  # UUID string
        st.session_state.username = auth_data['username']
        st.session_state.is_admin = auth_data['is_admin']
        st.session_state.show_login = False

# ==============================
# CONFIGURAÇÕES DO SUPABASE
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
    
    def execute_query(self, endpoint, method="GET", data=None, params=None):
        try:
            url = f"{self.url}/rest/v1/{endpoint}"
            request_params = params or {}
        
            if method == "GET":
                response = requests.get(url, headers=self.headers, params=request_params)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, params=request_params)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data, params=request_params)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, params=request_params)
        
            if response.status_code in [200, 201, 204]:
                try:
                    return response.json()
                except:
                    return response.text
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
        self.params = {}
    
    def select(self, columns="*"):
        self.params["select"] = columns
        return self
    
    def eq(self, column, value):
        self.params[column] = f"eq.{value}"
        return self
    
    def limit(self, count):
        self.params["limit"] = str(count)
        return self
    
    def execute(self):
        endpoint = self.table_name
        result = self.client.execute_query(endpoint, "GET", self.params)
        return {"data": result} if result else {"data": []}
    
    def insert(self, data):
        endpoint = self.table_name
        result = self.client.execute_query(endpoint, "POST", data)
        # Retorna um objeto que simula a resposta do Supabase
        return InsertResponse(result)
    
    def update(self, data):
        endpoint = self.table_name
        # Preserva os filtros para atualização
        result = self.client.execute_query(endpoint, "PUT", data, params=self.params)
        return {"data": [result]} if result else {"data": []}


class InsertResponse:
    def __init__(self, data):
        self.data = data
    
    def execute(self):
        # Simula o comportamento do Supabase
        if self.data:
            return {"data": [self.data]}
        else:
            return {"data": []}



# Inicializar cliente Supabase simplificado
supabase_client = SimpleSupabaseClient(SUPABASE_URL, SUPABASE_KEY)



def clear_dismissed_notifications():
    """Limpa a lista de notificações descartadas quando o usuário sai da página"""
    if "dismissed_notifications" in st.session_state:
        st.session_state.dismissed_notifications = set()


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

def check_password(password, hashed_password):
    """Verifica se a senha corresponde ao hash - versão corrigida"""
    try:
        # Primeiro, tenta verificar normalmente
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            return True
        
        # Se falhar, tenta normalizar o hash para versão 2a (mais compatível)
        if hashed_password.startswith('$2b$'):
            # Converte hash 2b para 2a (mais compatível)
            normalized_hash = '$2a$' + hashed_password[4:]
            if bcrypt.checkpw(password.encode('utf-8'), normalized_hash.encode('utf-8')):
                return True
                
        # Se ainda falhar, tenta o contrário (2a para 2b)
        if hashed_password.startswith('$2a$'):
            normalized_hash = '$2b$' + hashed_password[4:]
            if bcrypt.checkpw(password.encode('utf-8'), normalized_hash.encode('utf-8')):
                return True
                
        return False
        
    except Exception as e:
        print(f"Erro na verificação de senha: {e}")
        return False


def username_exists(username):
    """Verifica se o username já existe"""
    try:
        response = supabase_client.table("users").select("id, username").eq("username", username).execute()
        
        # Correção: verificar se há dados na resposta e se algum usuário tem o username exato
        if response.get("data"):
            # Verificar se algum usuário na lista tem exatamente o username fornecido
            for user in response["data"]:
                if user.get("username") == username:
                    return True
        return False
    except Exception as e:
        st.error(f"Erro ao verificar usuário: {e}")
        return False

def sign_up(username, password):
    """Registra um novo usuário apenas com username e senha"""
    try:
        # Debug: verificar se usuário já existe
        print(f"DEBUG: Tentando criar usuário: {username}")
        
        # Verificar se usuário já existe
        if username_exists(username):
            return False, "Usuário já existe!"
        
        # Criar hash da senha
        hashed_password = hash_password(password)
        print(f"DEBUG: Senha hash gerada: {hashed_password}")
        
        # Criar novo usuário
        user_data = {
            "username": username,
            "password_hash": hashed_password,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "is_admin": False
        }
        
        print(f"DEBUG: Dados do usuário: {user_data}")
        
        # Inserir usuário
        response_obj = supabase_client.table("users").insert(user_data)
        response = response_obj.execute()
        
        print(f"DEBUG: Resposta do insert: {response}")
        
        # Verificação da resposta
        if response and isinstance(response, dict) and response.get("data"):
            if len(response["data"]) > 0:
                user_data = response["data"][0]
                user_id = user_data.get('id')
                
                if user_id:
                    print(f"DEBUG: Conta criada com ID: {user_id}")
                    telegram_message = f"👤 Nova conta: {username}"
                    send_telegram_notification(telegram_message)
                    return True, "✅ Login criado com sucesso!"
        
        # Verificação final
        time.sleep(1)  # Dar tempo para o banco processar
        if username_exists(username):
            return True, "✅ Login criado com sucesso!"
        else:
            return False, "Erro ao criar conta - usuário não encontrado após tentativa"
            
    except Exception as e:
        error_msg = f"Erro completo: {traceback.format_exc()}"
        print(f"DEBUG: {error_msg}")
        return False, f"Erro: {str(e)}"


def sign_in(username, password):
    """Autentica um usuário usando username e senha"""
    try:
        # Buscar usuário no banco
        response = supabase_client.table("users").select("*").eq("username", username).execute()
        
        # Debug: verificar o que está retornando
        print(f"DEBUG: Resposta do Supabase: {response}")
        
        if not response.get("data") or len(response.get("data", [])) == 0:
            return False, "Usuário não encontrado!"
        else:
            user_data = response["data"][0]
            print(f"DEBUG: Dados do usuário: {user_data}")
        
        # Verificar se a senha existe no user_data
        if "password_hash" not in user_data:
            return False, "Erro: usuário não tem senha configurada"
        
        # DEBUG: Mostrar informações da senha
        print(f"DEBUG: Senha fornecida: {password}")
        print(f"DEBUG: Hash armazenado: {user_data['password_hash']}")
        print(f"DEBUG: Tipo do hash: {user_data['password_hash'][:4]}")
        
        # Verificar senha - CORREÇÃO AQUI
        if check_password(password, user_data["password_hash"]):
            st.session_state.user = user_data
            st.session_state.user_id = user_data.get("id")
            st.session_state.username = user_data.get("username")
            st.session_state.is_admin = user_data.get("is_admin", False)
            st.session_state.show_login = False
            
            # SALVAR A SESSÃO
            save_auth_session(
                st.session_state.username, 
                st.session_state.user_id,
                st.session_state.is_admin
            )
            
            return True, "Login realizado com sucesso!"
        else:
            print(f"DEBUG: Falha na verificação da senha")
            return False, "Senha incorreta!"
            
    except Exception as e:
        error_msg = f"Erro no login: {str(e)}"
        print(f"DEBUG: {error_msg}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return False, error_msg

def sign_out():
    """Desconecta o usuário"""
    st.session_state.user = None
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.is_admin = False
    
    # LIMPAR SESSÃO - USANDO O NOVO MÉTODO
    clear_auth_session()
    
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
            "updated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
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


def direct_sql_query(sql):
    """Executa SQL diretamente na API do Supabase"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Para consultas SELECT
        if sql.strip().lower().startswith("select"):
            response = requests.get(url + f"?sql={sql}", headers=headers)
            return response.json()
        # Para INSERT/UPDATE
        else:
            response = requests.post(url, headers=headers, json={"query": sql})
            return response.json()
            
    except Exception as e:
        st.error(f"Erro no SQL direto: {e}")
        return None


# ==============================
# JAVASCRIPT MESSAGE HANDLER
# ==============================
# Adicionar este código para capturar mensagens do JavaScript
js_message_handler = """
<script>
window.addEventListener('message', function(event) {
    if (event.data.type === 'AUTH_DATA') {
        window.parent.postMessage({
            type: 'STREAMLIT_AUTH_DATA',
            data: event.data.data
        }, '*');
    }
});
</script>
"""

components.html(js_message_handler, height=0)

# Verificar se há mensagens do JavaScript
try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    ctx = get_script_run_ctx()
    if ctx and hasattr(ctx, 'request') and hasattr(ctx.request, '_request_data'):
        request_data = ctx.request._request_data
        if 'type' in request_data and request_data['type'] == 'STREAMLIT_AUTH_DATA':
            st.session_state.auth_data = request_data['data']
except:
    pass




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
        ref.child("test").set({"test": True, "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")})
        ref.child("test").delete()
        return True
    except Exception as e:
        return False

def get_all_songs(limit=100):
    try:
        if st.session_state.firebase_connected:
            ref = db.reference("/songs")
            songs_data = ref.order_by_key().limit_to_first(limit).get()
            songs = []
            if songs_data:
                for song_id, song_data in songs_data.items():
                    song_data["id"] = song_id
                    songs.append(song_data)
            return songs
        return []
    except:
        return []


@st.cache_data(ttl=600) # 10 minutos 
def get_all_songs_cached():
    return get_all_songs()


def get_user_notifications():
    """Busca notificações pessoais do usuário atual"""
    if not st.session_state.firebase_connected or not st.session_state.user_id:
        return []
    
    try:
        ref = db.reference(f"/user_notifications/{st.session_state.user_id}")
        notifications_data = ref.get()
        
        notifications = []
        if notifications_data:
            for note_id, note_data in notifications_data.items():
                notifications.append({
                    "id": note_id,
                    "type": "personal",
                    "message": note_data.get("message", ""),
                    "timestamp": note_data.get("timestamp", ""),
                    "read": note_data.get("read", False),
                    "sent_by": note_data.get("sent_by", "Sistema")
                })
        
        # Ordenar por timestamp (mais recente primeiro)
        try:
            notifications.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        except:
            pass
        
        return notifications
    except Exception as e:
        st.error(f"❌ Erro ao buscar notificações pessoais: {e}")
        return []

def get_all_notifications():
    """Busca todas as notificações NÃO LIDAS do usuário"""
    all_notifications = []
    
    if not st.session_state.firebase_connected or not st.session_state.user_id:
        return all_notifications
    
    user_id = st.session_state.user_id
    
    # DEBUG: Verificar se está conectado
    print(f"DEBUG: Buscando notificações para usuário {user_id}")
    
    # Buscar notificações globais
    try:
        global_ref = db.reference("/global_notifications")
        global_notifications = global_ref.get() or {}
        
        for note_id, note_data in global_notifications.items():
            read_by = note_data.get("read_by", {})
            is_read = user_id in read_by and read_by[user_id]
            
            if not is_read:
                all_notifications.append({
                    "id": note_id,
                    "type": "global",
                    "title": "Notificação Global",
                    "message": note_data.get("message", ""),
                    "admin": note_data.get("admin", "Admin"),
                    "timestamp": note_data.get("timestamp", ""),
                    "is_read": is_read
                })
    except Exception as e:
        print(f"DEBUG: Erro em notificações globais: {e}")
    
    # Buscar notificações do sistema
    try:
        system_ref = db.reference("/system_notifications")
        system_notifications = system_ref.get() or {}
        
        for note_id, note_data in system_notifications.items():
            read_by = note_data.get("read_by", {})
            is_read = user_id in read_by and read_by[user_id]
            
            if not is_read:
                all_notifications.append({
                    "id": note_id,
                    "type": "music",
                    "title": note_data.get("title", "Nova Música"),
                    "message": note_data.get("formatted_message", ""),
                    "artist": note_data.get("artist", ""),
                    "timestamp": note_data.get("timestamp", ""),
                    "is_read": is_read
                })
    except Exception as e:
        print(f"DEBUG: Erro em notificações do sistema: {e}")
    
    # Buscar notificações pessoais
    try:
        personal_ref = db.reference(f"/user_notifications/{user_id}")
        personal_notifications = personal_ref.get() or {}
        
        for note_id, note_data in personal_notifications.items():
            is_read = note_data.get("read", False)
            
            if not is_read:
                all_notifications.append({
                    "id": note_id,
                    "type": "personal",
                    "title": f"Notificação Pessoal - {note_data.get('sent_by', 'Sistema')}",
                    "message": note_data.get("message", ""),
                    "timestamp": note_data.get("timestamp", ""),
                    "is_read": is_read
                })
    except Exception as e:
        print(f"DEBUG: Erro em notificações pessoais: {e}")
    
    # Ordenar por timestamp (mais recente primeiro)
    try:
        all_notifications.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    except:
        pass
    
    print(f"DEBUG: Encontradas {len(all_notifications)} notificações não lidas")
    return all_notifications[:20]

def send_user_notification(user_id, message, notification_type="info"):
    """Envia uma notificação para um usuário específico"""
    # Primeiro envia para Telegram
    user_response = supabase_client.table("users").select("username").eq("id", user_id).execute()
    username = user_response["data"][0]["username"] if user_response.get("data") else str(user_id)
    
    telegram_msg = f"📨 Notificação para {username}:\n{message}"
    telegram_success = send_telegram_notification(telegram_msg)
    
    if not telegram_success:
        st.error("❌ Erro ao enviar notificação para Telegram")
        return False
    
    # Depois salva no Firebase
    if st.session_state.firebase_connected:
        try:
            ref = db.reference(f"/user_notifications/{user_id}")
            
            # Gera chave personalizada
            notification_key = generate_firebase_key(f"user_{username}_{message[:15]}_{datetime.datetime.now().strftime('%H%M%S')}")
            
            notification_data = {
                "message": message,
                "type": notification_type,
                "timestamp": get_current_timestamp(),
                "read": False,
                "sent_by": st.session_state.username if st.session_state.username else "Sistema"
            }
            
            ref.child(notification_key).set(notification_data)
            return True
        except Exception as e:
            st.error(f"❌ Erro ao enviar notificação para usuário: {e}")
            return False
    else:
        return True

def mark_notification_as_read(notification_id, notification_type):
    """Marca uma notificação como lida apenas para o usuário atual"""
    if not st.session_state.firebase_connected or not st.session_state.user_id:
        return False
    
    try:
        user_id = st.session_state.user_id
        
        if notification_type == "global":
            ref = db.reference(f"/global_notifications/{notification_id}/read_by/{user_id}")
        elif notification_type == "music":
            ref = db.reference(f"/system_notifications/{notification_id}/read_by/{user_id}")
        elif notification_type == "personal":
            ref = db.reference(f"/user_notifications/{user_id}/{notification_id}/read")
        else:
            st.error(f"Tipo de notificação desconhecido: {notification_type}")
            return False
        
        # Marcar como lida para este usuário
        ref.set(True)
        
        # Forçar atualização imediata dos caches
        st.session_state.unread_notifications_cache = None
        st.session_state.notifications_cache = None
        st.session_state.notifications_cache_timestamp = 0
        
        # DEBUG: Verificar se realmente foi marcado
        time.sleep(0.5)  # Pequeno delay para o Firebase atualizar
        check_ref = db.reference(ref.path)
        is_read = check_ref.get()
        print(f"DEBUG: Notificação {notification_id} marcada como lida: {is_read}")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Erro ao marcar notificação como lida: {e}")
        return False

def show_admin_management():
    """Interface simplificada para admin"""
    if not st.session_state.is_admin:
        st.error("Acesso restrito a administradores")
        return
    
    st.subheader("👥 Gerenciamento de Usuários")
    
    # Listar usuários
    try:
        users = supabase_client.table("users").select("id, username, is_admin, created_at").execute()
        
        if users.get("data"):
            # Mostrar contagem
            total_users = len(users["data"])
            admin_count = sum(1 for user in users["data"] if user.get("is_admin"))
            regular_count = total_users - admin_count
            
            st.metric("👥 Total de Usuários", total_users)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🛡️ Administradores", admin_count)
            with col2:
                st.metric("👤 Usuários Regulares", regular_count)
            
            st.markdown("---")
            st.subheader("Lista de Usuários")
            
            for user in users["data"]:
                status = "🛡️ Admin" if user.get("is_admin") else "👤 Usuário"
                col1, col2, col3 = st.columns([3, 2, 2])
                
                with col1:
                    st.write(f"**{user['username']}**")
                with col2:
                    st.write(status)
                with col3:
                    st.write(f"{user['created_at'][:10]}")
                
                # Botão para promover/remover admin (apenas para super admin)
                if is_super_admin() and not user.get("is_admin"):
                    if st.button(f"Promover Admin", key=f"promote_{user['id']}"):
                        if promote_to_admin(user['username']):
                            st.rerun()
                
                st.markdown("---")
        else:
            st.info("Nenhum usuário encontrado")
            
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {e}")


def send_specific_user_notification():
    """Interface para enviar notificação para usuário específico"""
    st.subheader("📨 Enviar Notificação para Usuário Específico")
    
    # Buscar todos os usuários do Supabase
    try:
        users_response = supabase_client.table("users").select("id, username").execute()
        
        if users_response.get("data"):
            users = {user["username"]: user["id"] for user in users_response["data"]}
            
            with st.form("specific_notification_form", clear_on_submit=True):
                selected_user = st.selectbox(
                    "Selecionar usuário:",
                    options=list(users.keys())
                )
                
                message = st.text_area("Mensagem:", placeholder="Digite a mensagem para o usuário...", height=100)
                
                # Adicionar tipo de notificação
                notification_type = st.selectbox(
                    "Tipo de notificação:",
                    options=["info", "alert", "success", "warning"]
                )
                
                submitted = st.form_submit_button("📨 Enviar Notificação")
                
                if submitted:
                    if not message.strip():
                        st.error("A mensagem não pode estar vazia!")
                        return
                    
                    user_id = users[selected_user]
                    if send_user_notification(user_id, message, notification_type):
                        st.success(f"✅ Notificação enviada para {selected_user}!")
                        # Telegram notification
                        telegram_msg = f"📨 Notificação enviada para {selected_user}:\n{message}"
                        send_telegram_notification(telegram_msg)
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

def generate_firebase_key(name):
    """Gera uma chave amigável para o Firebase baseada no nome"""
    # Remove acentos e caracteres especiais
    name = unicodedata.normalize('NFKD', str(name)).encode('ASCII', 'ignore').decode('ASCII')
    
    # Substitui espaços e caracteres inválidos por underscores
    name = re.sub(r'[^\w\s-]', '', name.lower())
    name = re.sub(r'[-\s]+', '_', name)
    
    # Limita o tamanho para evitar chaves muito longas
    return name[:50]  # Limite de 50 caracteres

def add_system_notification(title, artist, image_url, song_id):
    """Adiciona notificação ao sistema interno de notificações e envia para Telegram"""
    try:
        # Primeiro envia para o Telegram
        telegram_message = f"""🎵 Nova música adicionada!

{title}
{artist}"""

        if not send_telegram_notification(telegram_message):
            st.error("❌ Erro ao enviar notificação para Telegram")
            return False

        # Depois salva no Firebase (se estiver conectado)
        if st.session_state.firebase_connected:
            ref = db.reference("/system_notifications")
            
            # Gera chave personalizada baseada no nome da música
            notification_key = generate_firebase_key(f"{title}_{artist}")
            
            notification_data = {
                "type": "new_song",
                "title": title,
                "artist": artist,
                "image_url": image_url,
                "song_id": song_id,
                "timestamp": get_current_timestamp(),
                "read_by": {},
                "formatted_message": telegram_message
            }
            
            # Usa set() em vez de push() para controlar a chave
            ref.child(notification_key).set(notification_data)
            return True
        else:
            return True
            
    except Exception as e:
        st.error(f"❌ Erro ao adicionar notificação do sistema: {e}")
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
            
            # Garantir campos obrigatórios
            title = request_data.get("title", "Sem título")
            artist = request_data.get("artist", "Artista desconhecido")
            requested_by = request_data.get("requested_by", st.session_state.username or "Anônimo")
            
            # Gera chave personalizada no formato "titulo_artista_usuario"
            request_key = generate_firebase_key(f"{title}_{artist}_{requested_by}")
            
            # Verifica se já existe um pedido igual
            existing_request = ref.child(request_key).get()
            if existing_request:
                st.warning("⚠️ Já existe um pedido igual para esta música!")
                return False
            
            # Prepara dados completos
            request_data["created_at"] = get_current_timestamp()
            request_data["status"] = "pending"
            request_data["requested_by"] = requested_by
            
            # Usa set() com chave personalizada
            ref.child(request_key).set(request_data)
            
            # Enviar notificação para Telegram
            album = request_data.get("album", "Álbum desconhecido")
            
            notification_message = f"""🎵 Novo pedido de música:

{artist} - {title} - {album}

🎼 Música: {title}
🎙️ Artista: {artist}
💿 Álbum: {album}
👤 Solicitado por: {requested_by}"""

            send_telegram_notification(notification_message)
            
            st.success("✅ Pedido enviado com sucesso!")
            return True
            
        return False
        
    except Exception as e:
        st.error(f"❌ Erro ao enviar pedido: {e}")
        return False

def check_existing_request(title, artist, username):
    """Verifica se já existe um pedido igual"""
    try:
        if st.session_state.firebase_connected:
            ref = db.reference("/song_requests")
            
            # Gera a chave que seria usada
            expected_key = generate_firebase_key(f"{title}_{artist}_{username}")
            
            # Verifica se já existe
            existing = ref.child(expected_key).get()
            return existing is not None
            
    except Exception as e:
        print(f"Erro ao verificar pedido existente: {e}")
        
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
    """Envia notificação global para todos os usuários e para o Telegram"""
    # Primeiro envia para Telegram
    telegram_success = send_telegram_notification(f"📢 Notificação Global:\n{message}")
    
    if not telegram_success:
        st.error("❌ Erro ao enviar notificação para Telegram")
        return False
    
    # Depois salva no Firebase
    if st.session_state.firebase_connected:
        try:
            ref = db.reference("/global_notifications")
            
            # Gera chave baseada no conteúdo da mensagem e timestamp
            notification_key = generate_firebase_key(f"global_{message[:20]}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}")
            
            notification_data = {
                "message": message,
                "admin": st.session_state.username if st.session_state.username else "Admin",
                "timestamp": get_current_timestamp(),
                "read_by": {}
            }
            
            ref.child(notification_key).set(notification_data)
            return True
        except Exception as e:
            st.error(f"❌ Erro ao salvar notificação global: {e}")
            return False
    else:
        return True


def check_unread_notifications():
    """Verifica se há notificações novas - versão simplificada"""
    if not st.session_state.firebase_connected or not st.session_state.user_id:
        return 0
    
    # Usar cache para melhor performance
    current_time = time.time()
    if (st.session_state.unread_notifications_cache is not None and 
        current_time - st.session_state.unread_cache_timestamp < 30):
        return st.session_state.unread_notifications_cache
    
    try:
        # Contagem simplificada - verifica apenas se há notificações recentes
        count = 0
        
        # Verificar notificações globais
        try:
            global_ref = db.reference("/global_notifications")
            global_data = global_ref.order_by_child("timestamp").limit_to_last(1).get()
            if global_data:
                count += 1
        except:
            pass
        
        # Verificar notificações de sistema
        try:
            system_ref = db.reference("/system_notifications")
            system_data = system_ref.order_by_child("timestamp").limit_to_last(1).get()
            if system_data:
                count += 1
        except:
            pass
        
        # Verificar notificações pessoais
        try:
            personal_ref = db.reference(f"/user_notifications/{st.session_state.user_id}")
            personal_data = personal_ref.order_by_child("timestamp").limit_to_last(1).get()
            if personal_data:
                count += len(personal_data)
        except:
            pass
        
        # Atualizar cache
        st.session_state.unread_notifications_cache = count
        st.session_state.unread_cache_timestamp = current_time
        
        return count
        
    except Exception as e:
        return 0


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
            # Agora usa a chave personalizada diretamente
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
    """Seção para pedir músicas - apenas para usuários logados"""
    with st.container():
        st.markdown("---")
        st.subheader("Não encontrou a música que procura?")
        
        if not st.session_state.user_id:
            st.warning("⚠️ Faça login para solicitar músicas")
            return
        
        # Usar estado único para controlar o formulário
        if st.button("Pedir Música +", key="request_music_btn", use_container_width=True):
            st.session_state.show_request_form = True
            
        if st.session_state.show_request_form:
            with st.form("request_music_form", clear_on_submit=True):
                st.write("### Solicitar Nova Música")
                col1, col2 = st.columns(2)
                with col1:
                    req_title = st.text_input("Título da Música*", placeholder="Ex: Boate Azul", key="req_title")
                    req_artist = st.text_input("Artista*", placeholder="Ex: Bruno & Marrone", key="req_artist")
                with col2:
                    req_album = st.text_input("Álbum (se conhecido)", key="req_album")
                    # Campo de nome preenchido automaticamente com o username
                    st.text_input("Solicitado por:", value=st.session_state.username, disabled=True, key="req_username")
                
                submitted = st.form_submit_button("Enviar Pedido")
                if submitted:
                    if not all([req_title, req_artist]):
                        st.error("⚠️ Preencha pelo menos o título e artista!")
                    else:
                        request_data = {
                            "title": req_title,
                            "artist": req_artist,
                            "album": req_album,
                            "requested_by": st.session_state.username  # Usa o username automaticamente
                        }
                        
                        if add_song_request(request_data):
                            st.success("✅ Pedido enviado com sucesso! Adicionaremos em breve.")
                            st.session_state.show_request_form = False
                            st.rerun()
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
            #if st.button("✕ Fechar", key="close_login", use_container_width=True):
                #st.session_state.show_login = False
                #st.rerun()
        
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
        # Atualizar cache de notificações não lidas a cada 10 segundos
        if ("unread_notifications_cache" not in st.session_state or 
            time.time() - st.session_state.get("unread_cache_timestamp", 0) > 10):
            st.session_state.unread_notifications_cache = check_unread_notifications()
            st.session_state.unread_cache_timestamp = time.time()
    
        unread_notifications = st.session_state.unread_notifications_cache
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
    
    #if st.button("Voltar"):
        #st.session_state.current_page = "home"


elif st.session_state.current_page == "notifications":
    st.markdown(f"<h1 style='text-align:center;'>🔔 Notificações</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    if not st.session_state.user_id:
        st.warning("⚠️ Faça login para ver suas notificações")
        #if st.button("Fazer Login", key="goto_login_notifications"):
            #st.session_state.show_login = True
            #st.rerun()
        st.stop()
    
    # Botão para recarregar
    #if st.button("🔄 Atualizar Notificações", key="refresh_notifications"):
        #st.session_state.notifications_cache = None
        #st.rerun()
    
    try:
        # Buscar TODAS as notificações (sem filtrar por lidas)
        all_notifications = []
        
        # Notificações globais
        try:
            global_ref = db.reference("/global_notifications")
            global_data = global_ref.get() or {}
            for note_id, note_data in global_data.items():
                all_notifications.append({
                    "id": note_id,
                    "type": "global",
                    "title": "📢 Notificação Global",
                    "message": note_data.get("message", ""),
                    "timestamp": note_data.get("timestamp", ""),
                    "admin": note_data.get("admin", "Admin")
                })
        except:
            pass
        
        # Notificações de música
        try:
            system_ref = db.reference("/system_notifications")
            system_data = system_ref.get() or {}
            for note_id, note_data in system_data.items():
                all_notifications.append({
                    "id": note_id,
                    "type": "music",
                    "title": "🎵 Nova Música",
                    "message": f"{note_data.get('title', '')} - {note_data.get('artist', '')}",
                    "timestamp": note_data.get("timestamp", "")
                })
        except:
            pass
        
        # Notificações pessoais
        try:
            personal_ref = db.reference(f"/user_notifications/{st.session_state.user_id}")
            personal_data = personal_ref.get() or {}
            for note_id, note_data in personal_data.items():
                all_notifications.append({
                    "id": note_id,
                    "type": "personal",
                    "title": f"📨 {note_data.get('sent_by', 'Sistema')}",
                    "message": note_data.get("message", ""),
                    "timestamp": note_data.get("timestamp", "")
                })
        except:
            pass
        
        # Ordenar por timestamp
        try:
            all_notifications.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        except:
            pass
        
        if not all_notifications:
            st.info("📝 Não há notificações no momento.")
            #if st.button("Voltar para o Início", key="back_from_notifications_empty"):
                #st.session_state.current_page = "home"
            st.stop()
        
        # Exibir notificações
        for notification in all_notifications[:20]:  # Limitar a 20 mais recentes
            timestamp = notification.get("timestamp", "")
            if timestamp:
                try:
                    dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp_display = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    timestamp_display = timestamp[:10]
            else:
                timestamp_display = "Data não disponível"
            
            st.markdown(f"""
            <div style='
                background-color: #1f2937;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 15px;
                border-left: 4px solid #1DB954;
            '>
                <p style='color: #9ca3af; font-size: 12px; margin: 0;'>
                    <strong>{notification['title']}</strong> • {timestamp_display}
                </p>
                <p style='color: white; font-size: 16px; margin: 8px 0 0 0;'>
                    {notification['message']}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        #if st.button("Voltar para o Início", key="back_from_notifications"):
            #st.session_state.current_page = "home"
            
    except Exception as e:
        st.error(f"❌ Erro ao carregar notificações: {e}")
        #if st.button("Voltar para o Início", key="back_from_notifications_error"):
            #st.session_state.current_page = "home"


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
.stButton > button:disabled {
    background-color: #666;
    color: #999;
    cursor: not-allowed;
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
/* Corrigir o botão de pedir música */
div[data-testid="stVerticalBlock"] > div:has(button:contains("Pedir Música +")) {
    margin-top: 20px;
    padding: 10px;
    background: linear-gradient(135deg, #1DB954 0%, #1ed760 100%);
    border-radius: 15px;
}
</style>
""", unsafe_allow_html=True)
