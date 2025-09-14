# main.py - APENAS PARA USUÁRIOS
import streamlit as st
from shared import *

# Configuração da página
st.set_page_config(
    page_title="Wave - Player de Música",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estado da sessão apenas para usuários
if "current_track" not in st.session_state:
    st.session_state.current_track = None
if "is_playing" not in st.session_state:
    st.session_state.is_playing = False
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# Inicializar Firebase
st.session_state.firebase_connected = initialize_firebase()
if st.session_state.firebase_connected:
    st.session_state.all_songs = get_all_songs()

# Sidebar para usuários
with st.sidebar:
    st.title("🌊 Wave Song")
    st.success("✅ Online" if st.session_state.firebase_connected else "⚠️ Offline")

    if st.session_state.current_track:
        # Mostrar música atual
        pass
    
    st.markdown("---")
    
    # Menu apenas para usuários
    unread_notifications = check_unread_notifications()
    notification_text = f"🔔 Notificações ({len(unread_notifications)})" if unread_notifications else "🔔 Notificações"

    if st.button(notification_text, use_container_width=True):
        st.session_state.current_page = "notifications"

    if st.button("Página Inicial", key="btn_home", use_container_width=True):
        st.session_state.current_page = "home"
        
    if st.button("Buscar Músicas", key="btn_search", use_container_width=True):
        st.session_state.current_page = "search"
        
    # Link para área admin (opcional)
    if st.button("🔐 Acesso Administrativo", key="admin_access"):
        st.switch_page("admin.py")

# Páginas para usuários
if st.session_state.current_page == "home":
    # Página inicial para usuários
    st.header("🌊 Bem-vindo ao Wave")
    # ... resto do código da página home

elif st.session_state.current_page == "search":
    # Página de busca para usuários
    st.header("Buscar Músicas")
    # ... resto do código da página search

elif st.session_state.current_page == "notifications":
    # Página de notificações para usuários
    st.header("🔔 Notificações")
    # ... resto do código
