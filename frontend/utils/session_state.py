import streamlit as st
import uuid
import requests

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        "messages": [],
        "last_query": "",
        "query_in_progress": False,
        "stop_requested": False,
        "retry_triggered": False,
        "messages_to_retry": None,
        "pending_user_message": None,
        "session_id": None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Generate or fetch session ID from backend
    if st.session_state.session_id is None:
        try:
            from config.settings import get_backend_url_with_fallback
            backend_url = get_backend_url_with_fallback()
            response = requests.post(f"{backend_url.rstrip('/')}/session", timeout=3)
            response.raise_for_status()
            st.session_state.session_id = response.json()["session_id"]
        except Exception as e:
            # Fallback to local UUID if backend unavailable
            st.session_state.session_id = str(uuid.uuid4())

def update_session_state(**kwargs):
    """Update session state variables"""
    for key, value in kwargs.items():
        st.session_state[key] = value

def get_session_state():
    """Get current session state"""
    return {
        "messages": st.session_state.messages,
        "last_query": st.session_state.last_query,
        "query_in_progress": st.session_state.query_in_progress,
        "stop_requested": st.session_state.stop_requested,
        "retry_triggered": st.session_state.retry_triggered,
        "messages_to_retry": st.session_state.messages_to_retry,
        "pending_user_message": st.session_state.pending_user_message,
        "session_id": st.session_state.session_id
    }

def clear_session():
    """Clear current session and generate a new one"""
    st.session_state.messages = []
    st.session_state.last_query = ""
    st.session_state.pending_user_message = None
    st.session_state.session_id = None
    initialize_session_state()  # Generate new session ID