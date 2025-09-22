import streamlit as st
from config.settings import get_backend_url, get_page_config
from styles.css import get_css_styles
from utils.session_state import initialize_session_state
from utils.helpers import handle_retry_logic
from services.api_client import BackendAPIClient
from components.header import render_header
from components.sidebar import render_sidebar
from components.message_display import display_chat_messages
from components.chat_interface import handle_chat_input

def main():
    # Set page config
    page_config = get_page_config()
    st.set_page_config(**page_config)
    
    # Apply CSS styles
    st.markdown(get_css_styles(), unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize API client
    backend_url = get_backend_url()
    api_client = BackendAPIClient(backend_url)
    
    # Handle retry logic
    if handle_retry_logic():
        st.rerun()
    
    # Render components
    render_header()  # This was missing!
    render_sidebar(api_client)
    display_chat_messages()
    handle_chat_input(api_client)
    
    # Show current status
    if st.session_state.query_in_progress:
        st.info("🔄 Query in progress...")

if __name__ == "__main__":
    main()