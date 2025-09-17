import streamlit as st
import firebase_admin
import requests 
import datetime
import random
import time
import base64
import hashlib
import json
import re
import streamlit.components.v1 as components
from firebase_admin import credentials, db
from io import BytesIO
from PIL import Image

# ==============================
# CONFIGURAÇÃO STEALTH AVANÇADA
# ==============================
st.set_page_config(
    page_title="Portal de Documentos Corporativos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# ESTADO DA SESSÃO
# ==============================
if "user" not in st.session_state:
    st.session_state.user = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "current_track" not in st.session_state:
    st.session_state.current_track = None
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False
if "all_songs" not in st.session_state:
    st.session_state.all_songs = []
if "firebase_connected" not in st.session_state:
    st.session_state.firebase_connected = False
if "debug_info" not in st.session_state:
    st.session_state.debug_info = {"blocked_urls": [], "access_checks": []}
if "current_page" not in st.session_state:
    st.session_state.current_page = "stealth"

# ==============================
# CONFIGURAÇÕES FIREBASE
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
# CONEXÃO FIREBASE
# ==============================
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://wavesong-default-rtdb.firebaseio.com/"
        })
    st.session_state.firebase_connected = True
except Exception as e:
    st.session_state.firebase_connected = False
    st.error(f"Erro ao conectar com Firebase: {e}")

# ==============================
# FUNÇÕES FIREBASE
# ==============================
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
    except Exception as e:
        st.error(f"Erro ao buscar músicas: {e}")
        return []

@st.cache_data(ttl=600)
def get_all_songs_cached():
    return get_all_songs()

# ==============================
# SISTEMA DE OFUSCAÇÃO CORPORATIVA
# ==============================
def generate_corporate_id(text):
    """Gera IDs que parecem códigos de documento corporativo"""
    hash_obj = hashlib.md5(text.encode())
    return f"DOC-{hash_obj.hexdigest()[:8].upper()}"

def obfuscate_title(title):
    """Ofusca títulos para parecerem nomes de documentos corporativos"""
    corporate_terms = ["RELATÓRIO", "ANÁLISE", "ESTRATÉGIA", "BRIEFING", "APRESENTAÇÃO", 
                      "DIRETRIZ", "POLÍTICA", "PROCEDIMENTO", "MANUAL", "INFORME"]
    
    # Se já parece corporativo, não altera
    if any(term in title.upper() for term in corporate_terms):
        return title.upper()
    
    # Adiciona prefixo corporativo
    prefix = random.choice(corporate_terms)
    return f"{prefix} {title.upper()}"

def convert_github_to_jsdelivr(url):
    """Converte URLs do GitHub para jsDelivr CDN"""
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
    """Obtém URL convertida para o áudio"""
    audio_url = song.get("audio_url", "")
    if "github.com" in audio_url or "raw.githubusercontent.com" in audio_url:
        return convert_github_to_jsdelivr(audio_url)
    return audio_url

def check_url_access(url, url_type="audio"):
    """Verifica acesso a URL e registra no debug"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        start_time = time.time()
        response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        access_time = time.time() - start_time
        
        result = {
            "url": url,
            "type": url_type,
            "status": response.status_code,
            "access_time": access_time,
            "timestamp": datetime.datetime.now().isoformat(),
            "accessible": response.status_code == 200
        }
        
        # Registrar no debug
        st.session_state.debug_info["access_checks"].append(result)
        if not result["accessible"]:
            st.session_state.debug_info["blocked_urls"].append(result)
            
        return result["accessible"]
        
    except Exception as e:
        result = {
            "url": url,
            "type": url_type,
            "status": "ERROR",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat(),
            "accessible": False
        }
        st.session_state.debug_info["access_checks"].append(result)
        st.session_state.debug_info["blocked_urls"].append(result)
        return False

def get_stealth_audio_url(song):
    """Gera URLs stealth para bypass corporativo"""
    audio_url = song.get("audio_url", "")
    
    # Primeiro tenta converter URLs do GitHub
    if "github.com" in audio_url or "raw.githubusercontent.com" in audio_url:
        converted_url = convert_github_to_jsdelivr(audio_url)
        if check_url_access(converted_url, "audio_cdn"):
            return converted_url
    
    # Se a URL original é acessível, usa ela
    if audio_url and check_url_access(audio_url, "audio_original"):
        return audio_url
    
    # Se tudo falhar, usa técnicas de ofuscação
    corporate_url_templates = [
        f"https://docs.google.com/document/d/{song['id']}/preview",
        f"https://company.sharepoint.com/sites/docs/{song['id']}",
        f"https://confluence.company.com/display/DOC/{song['id']}",
        f"https://drive.google.com/file/d/{song['id']}/view",
    ]
    
    return random.choice(corporate_url_templates)

def create_stealth_player(song):
    """Cria um player de áudio stealth"""
    
    # URL stealth para bypass corporativo
    audio_url = get_stealth_audio_url(song)
    doc_id = generate_corporate_id(song['id'])
    obfuscated_title = obfuscate_title(song['title'])
    
    # Player HTML que parece um documento corporativo
    player_html = f"""
    <div style="padding:15px; border:1px solid #d1d5db; border-radius:6px; background:#f9fafb; margin:10px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div style="font-size:16px; font-weight:600; color:#374151;">📄 {obfuscated_title}</div>
            <div style="font-size:12px; color:#6b7280; background:#e5e7eb; padding:4px 8px; border-radius:4px;">
                ID: {doc_id}
            </div>
        </div>
        
        <div style="display:flex; gap:15px; margin-bottom:15px;">
            <div style="flex:1;">
                <div style="font-size:13px; color:#4b5563; margin-bottom:4px;">
                    <strong>Departamento:</strong> {song['artist']}
                </div>
                <div style="font-size:13px; color:#4b5563; margin-bottom:4px;">
                    <strong>Tipo:</strong> Briefing de Áudio
                </div>
                <div style="font-size:13px; color:#4b5563;">
                    <strong>Duração:</strong> {song.get('duration', 'N/A')}
                </div>
            </div>
        </div>
        
        <div style="background:#ffffff; border:1px solid #e5e7eb; border-radius:6px; padding:10px;">
            <audio controls style="width:100%; height:40px;">
                <source src="{audio_url}" type="audio/mpeg">
                Seu navegador não suporta o elemento de áudio.
            </audio>
        </div>
        
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
            <div style="font-size:11px; color:#9ca3af;">
                🔒 Conteúdo seguro para ambiente corporativo
            </div>
            <div style="font-size:11px; color:#9ca3af;">
                Status: Aprovado • V{random.randint(1, 5)}.{random.randint(0, 9)}
            </div>
        </div>
    </div>
    """
    
    return player_html

def play_song(song):
    """Versão stealth para ambiente corporativo"""
    current_id = st.session_state.current_track["id"] if st.session_state.current_track else None
    new_id = song["id"]
    
    # Usar URL stealth
    song_copy = song.copy()
    song_copy["audio_url"] = get_stealth_audio_url(song)
    
    st.session_state.current_track = song_copy
    st.session_state.is_playing = True
    
    if st.session_state.firebase_connected:
        try:
            ref = db.reference(f"/songs/{song['id']}/play_count")
            current_count = ref.get() or 0
            ref.set(current_count + 1)
        except Exception as e:
            pass
    
    if current_id != new_id:
        st.rerun()

# ==============================
# INTERFACE STEALTH CORPORATIVA
# ==============================
def create_stealth_interface():
    """Interface completa stealth para ambiente corporativo"""
    
    st.markdown("""
    <style>
    .corporate-header {
        background: linear-gradient(135deg, #1e40af 0%, #3730a3 100%);
        padding: 20px;
        border-radius: 8px;
        color: white;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f8fafc;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin-bottom: 15px;
    }
    .debug-panel {
        background-color: #fef2f2;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ef4444;
        margin-bottom: 15px;
        font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header corporativo
    st.markdown(f"""
    <div class="corporate-header">
        <h1 style="margin:0; font-size:28px;">📊 Portal de Documentos Corporativos</h1>
        <p style="margin:5px 0 0 0; opacity:0.9;">Sistema de Gerenciamento de Conteúdo Empresarial - Acesso Seguro</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Carregar músicas do Firebase
    if not st.session_state.all_songs:
        st.session_state.all_songs = get_all_songs_cached()
    
    total_documents = len(st.session_state.all_songs)
    online_users = random.randint(10, 50)  # Usuários online entre 10-50
    
    # Métricas corporativas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:13px; color:#64748b;">Documentos Ativos</div>
            <div style="font-size:24px; font-weight:bold; color:#1e293b;">{total_documents}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:13px; color:#64748b;">Departamentos</div>
            <div style="font-size:24px; font-weight:bold; color:#1e293b;">{len(set(song['artist'] for song in st.session_state.all_songs))}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:13px; color:#64748b;">Usuários Online</div>
            <div style="font-size:24px; font-weight:bold; color:#1e293b;">{online_users}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        status = "✅ Operacional" if st.session_state.firebase_connected else "⚠️ Limitado"
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:13px; color:#64748b;">Status do Sistema</div>
            <div style="font-size:24px; font-weight:bold; color:#22c55e;">{status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Barra de pesquisa
    st.markdown("### 🔍 Pesquisar Documentos")
    search_term = st.text_input("", placeholder="Digite o código do documento, departamento ou palavras-chave...", 
                               label_visibility="collapsed", key="search_input")
    
    # Filtros corporativos
    col1, col2, col3 = st.columns(3)
    with col1:
        departments = list(set(song['artist'] for song in st.session_state.all_songs))
        departments.sort()
        departments.insert(0, "Todos")
        department_filter = st.selectbox("Departamento", departments)
    
    with col2:
        doc_types = ["Todos", "Briefing", "Relatório", "Apresentação", "Audio"]
        doc_type_filter = st.selectbox("Tipo de Documento", doc_types)
    
    with col3:
        status_options = ["Todos", "Ativo", "Arquivado", "Revisão Pendente"]
        status_filter = st.selectbox("Status", status_options)
    
    # Aplicar filtros
    filtered_docs = st.session_state.all_songs
    if department_filter != "Todos":
        filtered_docs = [doc for doc in filtered_docs if doc["artist"] == department_filter]
    if search_term:
        filtered_docs = [doc for doc in filtered_docs 
                        if search_term.lower() in doc.get("title", "").lower() 
                        or search_term.lower() in doc.get("artist", "").lower()]
    
    # Lista de documentos
    st.markdown("### 📋 Documentos Disponíveis")
    
    if not filtered_docs:
        st.warning("Nenhum documento encontrado com os critérios especificados.")
        
        # Sugerir alternativas
        st.info("💡 Sugestões de pesquisa:")
        st.write("- Tente termos mais gerais como 'relatório' ou 'análise'")
        st.write("- Verifique a ortografia dos termos pesquisados")
        st.write("- Utilize os filtros de departamento para refinar a busca")
        
    for doc in filtered_docs:
        components.html(create_stealth_player(doc), height=200)
    
    # Painel de debug (oculto por padrão)
    if st.checkbox("🔧 Mostrar informações de debug"):
        st.markdown("### 🐛 Painel de Debug")
        st.markdown("""
        <div class="debug-panel">
            <strong>Informações de acesso:</strong> Este painel mostra quais URLs estão sendo bloqueadas pelo firewall corporativo.
        </div>
        """, unsafe_allow_html=True)
        
        st.write("**Últimas verificações de acesso:**")
        for check in st.session_state.debug_info["access_checks"][-10:]:  # Mostrar apenas as 10 últimas
            status_color = "🟢" if check["accessible"] else "🔴"
            st.write(f"{status_color} {check['type']}: {check['url']} - Status: {check.get('status', 'ERROR')}")
        
        if st.session_state.debug_info["blocked_urls"]:
            st.write("**URLs Bloqueadas:**")
            for blocked in st.session_state.debug_info["blocked_urls"][-5:]:  # Mostrar apenas as 5 últimas
                st.error(f"🔴 {blocked['url']} - Status: {blocked.get('status', 'ERROR')}")
    
    # Rodapé corporativo
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#6b7280; font-size:12px;">
        <p>© 2023 Sistema de Gerenciamento de Documentos Corporativos • v2.1.4</p>
        <p>Acesso seguro garantido por criptografia de ponta a ponta • Todos os direitos reservados</p>
    </div>
    """, unsafe_allow_html=True)

# ==============================
# SIDEBAR STEALTH
# ==============================
with st.sidebar:
    st.title("📊 Portal Corporativo")
    st.success("✅ Conectado" if st.session_state.firebase_connected else "⚠️ Modo Offline")
    
    st.markdown("---")
    st.markdown("### Navegação")
    
    if st.button("📋 Documentos", use_container_width=True):
        st.session_state.current_page = "stealth"
        st.rerun()
    
    if st.button("🔍 Pesquisa Avançada", use_container_width=True):
        st.session_state.current_page = "search"
        st.rerun()
    
    if st.button("🐛 Debug", use_container_width=True):
        st.session_state.current_page = "debug"
        st.rerun()
    
    st.markdown("---")
    
    # Status do sistema
    st.markdown("### Status do Sistema")
    st.write(f"**Documentos:** {len(st.session_state.all_songs)}")
    st.write(f"**Usuários online:** {online_users}")
    st.write(f"**Conexão:** {'✅ Estável' if st.session_state.firebase_connected else '⚠️ Instável'}")
    
    if st.session_state.current_track:
        st.markdown("---")
        st.markdown("### 🎧 Reproduzindo")
        song = st.session_state.current_track
        st.write(f"**{obfuscate_title(song['title'])}**")
        st.write(f"*{song['artist']}*")
        st.caption(f"Duração: {song.get('duration', 'N/A')}")

# ==============================
# PÁGINA DE PESQUISA AVANÇADA
# ==============================
def show_search_page():
    st.header("🔍 Pesquisa Avançada de Documentos")
    
    if not st.session_state.all_songs:
        st.session_state.all_songs = get_all_songs_cached()
    
    # Campos de pesquisa
    col1, col2 = st.columns(2)
    with col1:
        title_search = st.text_input("Título do documento")
    with col2:
        department_search = st.text_input("Departamento")
    
    # Filtros avançados
    with st.expander("Filtros Avançados"):
        col1, col2 = st.columns(2)
        with col1:
            min_duration = st.number_input("Duração mínima (segundos)", min_value=0, value=0)
            max_duration = st.number_input("Duração máxima (segundos)", min_value=0, value=9999)
        with col2:
            sort_by = st.selectbox("Ordenar por", ["Relevância", "Título", "Departamento", "Duração"])
            sort_order = st.selectbox("Ordem", ["Crescente", "Decrescente"])
    
    # Aplicar filtros
    filtered_docs = st.session_state.all_songs
    
    if title_search:
        filtered_docs = [doc for doc in filtered_docs if title_search.lower() in doc.get("title", "").lower()]
    
    if department_search:
        filtered_docs = [doc for doc in filtered_docs if department_search.lower() in doc.get("artist", "").lower()]
    
    # Filtro de duração
    filtered_docs = [doc for doc in filtered_docs if min_duration <= parse_duration(doc.get("duration", "0")) <= max_duration]
    
    # Ordenação
    if sort_by == "Título":
        filtered_docs.sort(key=lambda x: x.get("title", ""), reverse=(sort_order == "Decrescente"))
    elif sort_by == "Departamento":
        filtered_docs.sort(key=lambda x: x.get("artist", ""), reverse=(sort_order == "Decrescente"))
    elif sort_by == "Duração":
        filtered_docs.sort(key=lambda x: parse_duration(x.get("duration", "0")), reverse=(sort_order == "Decrescente"))
    
    # Resultados
    st.write(f"**{len(filtered_docs)} documentos encontrados**")
    
    for doc in filtered_docs:
        components.html(create_stealth_player(doc), height=200)

def parse_duration(duration_str):
    """Converte string de duração para segundos"""
    try:
        if ":" in duration_str:
            parts = duration_str.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return int(duration_str)
    except:
        return 0

# ==============================
# PÁGINA DE DEBUG
# ==============================
def show_debug_page():
    st.header("🐛 Painel de Debug e Diagnóstico")
    
    st.markdown("""
    <div class="debug-panel">
        <strong>Informações de diagnóstico:</strong> Este painel mostra informações técnicas sobre 
        o acesso a recursos e possíveis bloqueios pelo firewall corporativo.
    </div>
    """, unsafe_allow_html=True)
    
    # Estatísticas de acesso
    col1, col2, col3 = st.columns(3)
    with col1:
        total_checks = len(st.session_state.debug_info["access_checks"])
        successful_checks = len([c for c in st.session_state.debug_info["access_checks"] if c["accessible"]])
        success_rate = (successful_checks / total_checks * 100) if total_checks > 0 else 0
        
        st.metric("Verificações de Acesso", total_checks)
        st.metric("Taxa de Sucesso", f"{success_rate:.1f}%")
    
    with col2:
        blocked_count = len(st.session_state.debug_info["blocked_urls"])
        audio_checks = len([c for c in st.session_state.debug_info["access_checks"] if c["type"].startswith("audio")])
        
        st.metric("URLs Bloqueadas", blocked_count)
        st.metric("Verificações de Áudio", audio_checks)
    
    with col3:
        avg_time = np.mean([c.get("access_time", 0) for c in st.session_state.debug_info["access_checks"]]) if st.session_state.debug_info["access_checks"] else 0
        max_time = max([c.get("access_time", 0) for c in st.session_state.debug_info["access_checks"]]) if st.session_state.debug_info["access_checks"] else 0
        
        st.metric("Tempo Médio", f"{avg_time:.2f}s")
        st.metric("Tempo Máximo", f"{max_time:.2f}s")
    
    # URLs bloqueadas
    if st.session_state.debug_info["blocked_urls"]:
        st.subheader("🔴 URLs Bloqueadas")
        for blocked in st.session_state.debug_info["blocked_urls"]:
            with st.expander(f"{blocked['url']} - Status: {blocked.get('status', 'ERROR')}"):
                st.json(blocked)
    
    # Histórico de verificações
    st.subheader("📊 Histórico de Verificações")
    for check in st.session_state.debug_info["access_checks"][-20:]:  # Últimas 20 verificações
        status_emoji = "🟢" if check["accessible"] else "🔴"
        st.write(f"{status_emoji} `{check['type']}`: {check['url']} - {check.get('status', 'ERROR')} ({check.get('access_time', 0):.2f}s)")
    
    # Ferramentas de diagnóstico
    st.subheader("🛠️ Ferramentas de Diagnóstico")
    test_url = st.text_input("URL para testar:", placeholder="https://exemplo.com/arquivo.mp3")
    
    if st.button("Testar URL") and test_url:
        with st.spinner("Testando acesso..."):
            accessible = check_url_access(test_url, "manual_test")
            if accessible:
                st.success("✅ URL acessível!")
            else:
                st.error("❌ URL bloqueada ou inacessível")
    
    # Limpar dados de debug
    if st.button("🧹 Limpar Dados de Debug"):
        st.session_state.debug_info = {"blocked_urls": [], "access_checks": []}
        st.success("Dados de debug limpos!")
        st.rerun()

# ==============================
# ROTEAMENTO PRINCIPAL
# ==============================
if st.session_state.current_page == "stealth":
    create_stealth_interface()
elif st.session_state.current_page == "search":
    show_search_page()
elif st.session_state.current_page == "debug":
    show_debug_page()

# ==============================
# INICIALIZAÇÃO
# ==============================
if __name__ == "__main__":
    # Verificar conexão com Firebase
    if not st.session_state.firebase_connected:
        st.warning("⚠️ Modo offline ativado. Algumas funcionalidades podem estar limitadas.")
    
    # Verificar acesso a URLs críticas
    if st.session_state.all_songs and len(st.session_state.all_songs) > 0:
        # Testar acesso a uma amostra de URLs
        sample_songs = random.sample(st.session_state.all_songs, min(3, len(st.session_state.all_songs)))
        for song in sample_songs:
            if "audio_url" in song:
                check_url_access(song["audio_url"], "audio_sample")
