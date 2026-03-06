import streamlit as st


def render_header(backend_connected: bool = False):
    status_class = "connected" if backend_connected else "disconnected"
    status_text = "Connected" if backend_connected else "Offline"
    
    st.markdown(f"""
    <div class="main-header">
        <div class="main-header-content">
            <h1>Rahalah <span class="arabic">رحالة</span></h1>
            <p class="subtitle">مرشد محوسب لبلاد فلسطين · Your AI guide to Palestine</p>
        </div>
        <span class="status-badge {status_class}">● {status_text}</span>
    </div>
    """, unsafe_allow_html=True)
