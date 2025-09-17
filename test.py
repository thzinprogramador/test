import streamlit as st
import base64
import json
import time
from io import BytesIO

# ==============================
# SISTEMA STEALTH DE ÁUDIO
# ==============================

def text_to_audio_data(text):
    """Converte texto em dados que parecem normais (esteganografia)"""
    # Esta é uma simulação - na prática usaria uma biblioteca de esteganografia
    return base64.b64encode(text.encode()).decode()

def audio_data_to_text(data):
    """Reverte os dados para texto"""
    return base64.b64decode(data.encode()).decode()

def get_stealth_audio_url():
    """
    Gera URLs que parecem normais mas contêm áudio
    Usa serviços whitelisted pela empresa
    """
    # Serviços comumente permitidos em empresas
    whitelisted_services = [
        "https://docs.google.com/document/d/",  # Google Docs
        "https://company.sharepoint.com/",      # SharePoint
        "https://confluence.company.com/",      # Confluence
        "https://drive.google.com/file/d/",     # Google Drive
        "https://teams.microsoft.com/",         # Microsoft Teams
    ]
    
    return random.choice(whitelisted_services) + "placeholder_id"

def create_stealth_player(audio_url, title, artist):
    """Cria um player de áudio que parece conteúdo normal"""
    
    # HTML que parece um documento normal mas é um player
    stealth_html = f"""
    <div style="padding:15px; border:1px solid #ddd; border-radius:5px; background:#f9f9f9;">
        <h4 style="margin:0 0 10px 0;">📄 Documento: {title} - {artist}</h4>
        <p style="color:#666; font-size:12px; margin:0 0 15px 0;">
            Este documento contém informações importantes sobre procedimentos corporativos.
            Clique no link abaixo para acessar o conteúdo.
        </p>
        <a href="#" onclick="playStealthAudio('{audio_url}'); return false;"
           style="display:inline-block; padding:8px 15px; background:#1E88E5; color:white; 
                  text-decoration:none; border-radius:4px; font-size:14px;">
           🔗 Abrir Documento
        </a>
        <div id="audioContainer" style="display:none;">
            <audio id="stealthAudio" controls style="width:100%">
                <source src="{audio_url}" type="audio/mpeg">
            </audio>
        </div>
    </div>
    <script>
    function playStealthAudio(url) {{
        var container = document.getElementById('audioContainer');
        var audio = document.getElementById('stealthAudio');
        
        if (container.style.display === 'none') {{
            container.style.display = 'block';
            audio.src = url;
            audio.play().catch(function(e) {{
                console.log('Reprodução automática bloqueada:', e);
            }});
        }} else {{
            container.style.display = 'none';
            audio.pause();
        }}
    }}
    </script>
    """
    
    return stealth_html

# ==============================
# SISTEMA DE OFUSCAÇÃO DE DADOS
# ==============================

def obfuscate_data(data):
    """Ofusca dados para parecerem normais"""
    if isinstance(data, dict):
        return {k: f"config_{v}" if isinstance(v, str) else v for k, v in data.items()}
    return data

def deobfuscate_data(data):
    """Reverte a ofuscação"""
    if isinstance(data, dict):
        return {k: v.replace("config_", "") if isinstance(v, str) and v.startswith("config_") else v 
                for k, v in data.items()}
    return data

# ==============================
# ARMAZENAMENTO LOCAL STEALTH
# ==============================

def save_stealth_data(key, value):
    """Salva dados de forma stealth no session_state"""
    obfuscated_key = f"config_{key}"
    obfuscated_value = obfuscate_data(value)
    st.session_state[obfuscated_key] = obfuscated_value

def load_stealth_data(key, default=None):
    """Carrega dados stealth do session_state"""
    obfuscated_key = f"config_{key}"
    if obfuscated_key in st.session_state:
        return deobfuscate_data(st.session_state[obfuscated_key])
    return default

# ==============================
# SISTEMA DE CACHE DISFARÇADO
# ==============================

def get_disguised_songs():
    """Obtém músicas de forma disfarçada"""
    # Nomes de chaves que parecem configurações de sistema
    disguised_songs = load_stealth_data("system_config", [])
    
    if not disguised_songs:
        # Simular carregamento de "configurações"
        disguised_songs = [
            {
                "config_title": "config_Relatório Trimestral",
                "config_artist": "config_Departamento Financeiro", 
                "config_duration": "config_30:00",
                "config_audio": "config_https://docs.google.com/document/d/abc123"
            },
            {
                "config_title": "config_Apresentação de Resultados", 
                "config_artist": "config_Gerência",
                "config_duration": "config_45:00",
                "config_audio": "config_https://company.sharepoint.com/doc456"
            }
        ]
        save_stealth_data("system_config", disguised_songs)
    
    return disguised_songs

# ==============================
# INTERFACE STEALTH
# ==============================

def show_stealth_interface():
    """Interface que parece um sistema corporativo normal"""
    
    st.markdown("""
    <style>
    .corporate-header {
        background: linear-gradient(135deg, #1E88E5 0%, #0D47A1 100%);
        padding: 20px;
        border-radius: 5px;
        color: white;
        margin-bottom: 20px;
    }
    .document-card {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        background: #fafafa;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Cabeçalho que parece corporativo
    st.markdown("""
    <div class="corporate-header">
        <h1 style="margin:0; color:white;">📊 Portal de Documentos Corporativos</h1>
        <p style="margin:0; opacity:0.9;">Sistema de Gerenciamento de Conteúdo Empresarial</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Barra de pesquisa disfarçada
    search_term = st.text_input("🔍 Pesquisar documentos:", placeholder="Digite o nome do documento...")
    
    # Lista de "documentos" (músicas)
    st.markdown("### 📁 Documentos Disponíveis")
    
    songs = get_disguised_songs()
    for song in songs:
        # Desofuscar os dados para mostrar
        real_song = deobfuscate_data(song)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div class="document-card">
                <h4 style="margin:0;">{real_song['title']}</h4>
                <p style="margin:5px 0; color:#666;">Departamento: {real_song['artist']}</p>
                <p style="margin:0; color:#888; font-size:12px;">Duração: {real_song['duration']} • Última atualização: {time.strftime('%d/%m/%Y')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Player stealth
            audio_html = create_stealth_player(
                real_song['audio'], 
                real_song['title'], 
                real_song['artist']
            )
            st.components.v1.html(audio_html, height=150)
    
    # Seção de "estatísticas" (player normal disfarçado)
    st.markdown("---")
    st.markdown("### 📈 Painel de Análise de Dados")
    
    # Isso parece um painel de analytics mas é o player principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Reprodução de Relatório de Análise**")
        if st.session_state.get('current_track'):
            track = st.session_state.current_track
            st.write(f"**Documento Atual:** {track['title']}")
            st.write(f"**Departamento:** {track['artist']}")
            
            # Barra de progresso disfarçada
            progress = st.slider("Progresso da Análise", 0, 100, 50)
            st.progress(progress)
    
    with col2:
        st.markdown("**Controles de Análise**")
        if st.button("▶️ Iniciar Análise", key="play_btn"):
            st.success("Análise em andamento...")
        if st.button("⏸️ Pausar Análise", key="pause_btn"):
            st.info("Análise pausada")
        if st.button("⏭️ Próxima Análise", key="next_btn"):
            st.info("Carregando próximo relatório...")

# ==============================
# SISTEMA DE ATUALIZAÇÃO STEALTH
# ==============================

def stealth_update():
    """Atualiza dados de forma stealth"""
    try:
        # Tenta atualizar de forma muito discreta
        update_url = "https://raw.githubusercontent.com/username/repo/main/data.json"
        response = requests.get(update_url, timeout=2, headers={
            'User-Agent': 'Corporate-Data-Sync/1.0'
        })
        
        if response.status_code == 200:
            new_data = response.json()
            save_stealth_data("system_config", new_data)
            return True
    except:
        # Falha silenciosamente
        pass
    return False

# ==============================
# CONFIGURAÇÃO INICIAL STEALTH
# ==============================

def initialize_stealth_app():
    """Inicializa o app de forma stealth"""
    
    # Configuração que parece normal
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True
        st.session_state.current_track = None
        st.session_state.is_playing = False
        
        # Dados iniciais disfarçados
        initial_data = [
            {
                "config_title": "config_Relatório Trimestral de Vendas",
                "config_artist": "config_Departamento Comercial",
                "config_duration": "config_25:15",
                "config_audio": "config_https://example.com/audio1"
            },
            {
                "config_title": "config_Apresentação de Resultados Q2",
                "config_artist": "config_Diretoria Executiva", 
                "config_duration": "config_42:30",
                "config_audio": "config_https://example.com/audio2"
            }
        ]
        
        save_stealth_data("system_config", initial_data)

# ==============================
# EXECUÇÃO PRINCIPAL
# ==============================

def main():
    """Função principal do app stealth"""
    
    # Inicialização stealth
    initialize_stealth_app()
    
    # Mostrar interface corporativa
    show_stealth_interface()
    
    # Tentar atualização stealth em segundo plano
    if random.random() < 0.1:  # Apenas 10% das vezes
        stealth_update()

# Executar o app
if __name__ == "__main__":
    main()
