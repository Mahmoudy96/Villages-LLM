import os
import streamlit as st
import requests

def get_backend_url():
    """Get backend URL from secrets, environment, or default"""
    try:
        if hasattr(st, 'secrets') and st.secrets.get("BACKEND_URL"):
            return st.secrets["BACKEND_URL"]
    except Exception:
        pass

    env_url = os.environ.get("BACKEND_URL")
    if env_url:
        return env_url

    return "http://127.0.0.1:8080"

def get_backend_url_with_fallback():
    """Try configured backend first; if offline, fall back to localhost"""
    primary = get_backend_url()
    if not primary.startswith("http"):
        primary = "http://" + primary
    localhost = "http://127.0.0.1:8080"

    # Try primary first
    try:
        r = requests.get(f"{primary.rstrip('/')}/health", timeout=2)
        if r.status_code == 200:
            return primary
    except Exception:
        pass

    # Fall back to localhost if primary is different
    if primary != localhost:
        try:
            r = requests.get(f"{localhost}/health", timeout=2)
            if r.status_code == 200:
                return localhost
        except Exception:
            pass

    return primary  # Return configured URL even if offline (user sees warning)

def get_page_config():
    """Return page configuration"""
    return {
        "page_title": "Rahalah - رحالة",
        "page_icon": "🫒",
        "layout": "wide",
        "initial_sidebar_state": "auto"
    }