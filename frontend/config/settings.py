import os
import streamlit as st

def get_backend_url():
    """Get backend URL from secrets, environment, or default"""
    try:
        if hasattr(st, 'secrets') and st.secrets.get("BACKEND_URL"):
            return st.secrets["BACKEND_URL"]
    except:
        pass
    
    env_url = os.environ.get("BACKEND_URL")
    if env_url:
        return env_url
    
    return "http://127.0.0.1:8080"

def get_page_config():
    """Return page configuration"""
    return {
        "page_title": "Rahalah - رحالة",
        "page_icon": "🌿",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }