import streamlit as st
import requests
import datetime
import random
import time
import base64
import hashlib
import json
import re
import streamlit.components.v1 as components
from io import BytesIO

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
# SISTEMA DE OFUSCAÇÃO CORPORATIVA
# ==============================
def generate_corporate_id(text):
    """Gera IDs que parecem códigos de documento corporativo"""
    hash_obj = hashlib.md5(text.encode())
    return f"DOC-{hash_obj.hexdigest()[:8].upper()}"

def obfuscate_data(data):
    """Ofusca dados para parecerem metadados de documentos"""
    if isinstance(data, dict):
        return {f"meta_{k}": f"corp_{v}" if isinstance(v, str) else v for k, v in data.items()}
    return data

def create_stealth_audio_player(song):
    """
    Cria um player de áudio que parece um visualizador de documentos
    usando técnicas avançadas de ofuscação
    """
    # Gerar ID corporativo
    doc_id = generate_corporate_id(song['id'])
    
    # Ofuscar metadados
    title_parts = song['title'].split()
    obfuscated_title = " ".join([f"{part[:3]}-{part[3:]}".upper() if len(part) > 3 else part.upper() 
                               for part in title_parts])
    
    # Player que parece um visualizador de documentos
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
            
            <div style="width:80px; height:80px; background:#e5e7eb; border-radius:6px; 
                        display:flex; align-items:center; justify-content:center; font-size:12px; color:#6b7280;">
                ÁUDIO
            </div>
        </div>
        
        <div style="background:#ffffff; border:1px solid #e5e7eb; border-radius:6px; padding:10px;">
            <audio controls style="width:100%; height:40px;">
                <source src="{song.get('audio_url', '')}" type="audio/mpeg">
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

def create_stealth_interface():
    """Interface completa que simula um portal de documentos corporativos"""
    
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
    </style>
    """, unsafe_allow_html=True)
    
    # Header corporativo
    st.markdown(f"""
    <div class="corporate-header">
        <h1 style="margin:0; font-size:28px;">📊 Portal de Documentos Corporativos</h1>
        <p style="margin:5px 0 0 0; opacity:0.9;">Sistema de Gerenciamento de Conteúdo Empresarial - Acesso Seguro</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas corporativas falsas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size:13px; color:#64748b;">Documentos Ativos</div>
            <div style="font-size:24px; font-weight:bold; color:#1e293b;">1,247</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size:13px; color:#64748b;">Departamentos</div>
            <div style="font-size:24px; font-weight:bold; color:#1e293b;">18</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size:13px; color:#64748b;">Usuários Online</div>
            <div style="font-size:24px; font-weight:bold; color:#1e293b;">{random.randint(80, 120)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div style="font-size:13px; color:#64748b;">Status do Sistema</div>
            <div style="font-size:24px; font-weight:bold; color:#22c55e;">Operacional</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Barra de pesquisa
    st.markdown("### 🔍 Pesquisar Documentos")
    search_term = st.text_input("", placeholder="Digite o código do documento, departamento ou palavras-chave...", 
                               label_visibility="collapsed")
    
    # Filtros corporativos
    col1, col2, col3 = st.columns(3)
    with col1:
        department_filter = st.selectbox("Departamento", ["Todos", "RH", "Financeiro", "TI", "Marketing", "Operações"])
    with col2:
        doc_type_filter = st.selectbox("Tipo de Documento", ["Todos", "Briefing", "Relatório", "Apresentação", "Audio"])
    with col3:
        status_filter = st.selectbox("Status", ["Todos", "Ativo", "Arquivado", "Revisão Pendente"])
    
    # Lista de documentos (músicas)
    st.markdown("### 📋 Documentos Disponíveis")
    
    # Dados de exemplo - substitua com suas músicas
    sample_documents = [
        {"id": "doc_001", "title": "Relatório Trimestral de Performance", "artist": "Financeiro", "duration": "3:45"},
        {"id": "doc_002", "title": "Estratégia de Marketing Digital Q3", "artist": "Marketing", "duration": "4:20"},
        {"id": "doc_003", "title": "Atualização de Políticas de RH", "artist": "Recursos Humanos", "duration": "2:55"},
        {"id": "doc_004", "title": "Análise de Infraestrutura de TI", "artist": "Tecnologia", "duration": "5:10"},
        {"id": "doc_005", "title": "Plano de Continuidade de Negócios", "artist": "Operações", "duration": "4:05"},
    ]
    
    # Aplicar filtros
    filtered_docs = sample_documents
    if department_filter != "Todos":
        filtered_docs = [doc for doc in filtered_docs if doc["artist"] == department_filter]
    if search_term:
        filtered_docs = [doc for doc in filtered_docs 
                        if search_term.lower() in doc["title"].lower() 
                        or search_term.lower() in doc["artist"].lower()]
    
    # Exibir documentos
    if not filtered_docs:
        st.warning("Nenhum documento encontrado com os critérios especificados.")
        
        # Sugerir alternativas
        st.info("💡 Sugestões de pesquisa:")
        st.write("- Tente termos mais gerais como 'relatório' ou 'análise'")
        st.write("- Verifique a ortografia dos termos pesquisados")
        st.write("- Utilize os filtros de departamento para refinar a busca")
        
    for doc in filtered_docs:
        # Adicionar URL de áudio de exemplo (substitua com suas URLs)
        doc["audio_url"] = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
        
        # Exibir como documento corporativo
        components.html(create_stealth_audio_player(doc), height=200)
    
    # Rodapé corporativo
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#6b7280; font-size:12px;">
        <p>© 2023 Sistema de Gerenciamento de Documentos Corporativos • v2.1.4</p>
        <p>Acesso seguro garantido por criptografia de ponta a ponta • Todos os direitos reservados</p>
    </div>
    """, unsafe_allow_html=True)

# ==============================
# TÉCNICAS DE EVASÃO AVANÇADAS
# ==============================
def rotate_user_agents():
    """Rotaciona user agents para evitar detecção"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    ]
    return random.choice(user_agents)

def make_stealth_request(url):
    """Faz requisições com técnicas de evasão"""
    try:
        headers = {
            'User-Agent': rotate_user_agents(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Adicionar delays aleatórios entre requisições
        time.sleep(random.uniform(0.5, 2.0))
        
        response = requests.get(url, headers=headers, timeout=10)
        return response
        
    except Exception as e:
        print(f"Erro na requisição stealth: {e}")
        return None

def obfuscate_urls(url):
    """Ofusca URLs para evitar bloqueios"""
    # Técnica 1: Usar URLs de serviços corporativos comumente permitidos
    corporate_proxies = [
        f"https://docs.google.com/viewer?url={url}",
        f"https://web.archive.org/web/{url}",
        f"https://translate.google.com/translate?sl=auto&tl=en&u={url}"
    ]
    
    # Técnica 2: Codificação em base64
    encoded_url = base64.b64encode(url.encode()).decode()
    corporate_proxies.append(f"https://company-proxy.com/b64/{encoded_url}")
    
    return random.choice(corporate_proxies)

# ==============================
# SISTEMA DE CACHE OFUSCADO
# ==============================
def stealth_cache_audio(audio_url, song_id):
    """
    Cache de áudio usando técnicas de ofuscação para evitar
    detecção de downloads em ambientes corporativos
    """
    cache_key = hashlib.md5(song_id.encode()).hexdigest()
    
    try:
        # Fazer requisição stealth
        response = make_stealth_request(audio_url)
        if response and response.status_code == 200:
            # Simular cache (em um ambiente real, isso seria salvo temporariamente)
            st.session_state[cache_key] = {
                'content': response.content,
                'timestamp': time.time(),
                'url': audio_url
            }
            return True
    except:
        pass
    
    return False

# ==============================
# EXECUÇÃO PRINCIPAL
# ==============================
if __name__ == "__main__":
    # Inicializar estado da sessão
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
    
    # Executar interface stealth
    create_stealth_interface()
    
    # Adicionar scripts de monitoramento stealth
    components.html("""
    <script>
    // Script de monitoramento corporativo falso
    setInterval(function() {
        console.log("Monitoramento de segurança ativo - Sistema estável");
    }, 30000);
    
    // Detectar ferramentas de desenvolvedor (e fechar)
    function detectDevTools() {
        var widthThreshold = 160;
        var heightThreshold = 160;
        
        if (window.outerWidth - window.innerWidth > widthThreshold || 
            window.outerHeight - window.innerHeight > heightThreshold) {
            console.log("Ferramentas de desenvolvedor detectadas - Modo de segurança ativado");
        }
    }
    setInterval(detectDevTools, 1000);
    </script>
    """, height=0)
