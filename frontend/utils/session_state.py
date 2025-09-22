import streamlit as st

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
        "session_id": "default_session"
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

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