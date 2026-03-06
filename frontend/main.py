import streamlit as st
from utils.session_state import initialize_session_state, clear_session
from components.header import render_header
from components.chat_interface import handle_chat_input
from services.api_client import BackendAPIClient
from config.settings import get_backend_url_with_fallback, get_page_config
from styles.css import get_css_styles

# Page config - modern defaults
config = get_page_config()
st.set_page_config(
    page_title=config["page_title"],
    page_icon=config["page_icon"],
    layout="wide",
    initial_sidebar_state=config.get("initial_sidebar_state", "expanded"),
)

# Inject modern CSS
st.markdown(get_css_styles(), unsafe_allow_html=True)

# Initialize session state
initialize_session_state()

# Backend URL - try configured first, fall back to localhost if offline
backend_url = get_backend_url_with_fallback()
api_client = BackendAPIClient(base_url=backend_url)
backend_connected = api_client.health_check()

# Header with connection status
render_header(backend_connected=backend_connected)

# Sidebar - clean, minimal
with st.sidebar:
    st.markdown("### 💬 Chat")
    st.markdown('<p class="sidebar-section-title">Session</p>', unsafe_allow_html=True)
    
    if st.button("✨ New Chat", use_container_width=True, type="primary"):
        clear_session()
        st.rerun()
    
    st.caption(f"Session: `{st.session_state.session_id[:8]}...`")
    
    if not backend_connected:
        st.warning("Backend offline. Start the server to chat.")

# Main chat area
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">🫒</div>
        <p class="empty-state-title">Ask me anything about Palestine</p>
        <p class="empty-state-subtitle">
            I can help you explore villages, history, culture, and more. 
            Try asking in Arabic, English, or Hebrew.
        </p>
    </div>
    """, unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
handle_chat_input(api_client)
