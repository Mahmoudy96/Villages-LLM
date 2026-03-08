import streamlit as st


def render_header(backend_connected: bool = False):
    status_class = "connected" if backend_connected else "disconnected"
    status_text = "Connected" if backend_connected else "Offline"
    
    st.markdown(f"""
    <div class="main-header">
        <div class="main-header-content">
            <h1><span class="title-english">Rahalah</span><span class="title-arabic">رحالة</span></h1>
            <p class="subtitle"><span class="subtitle-english">Your AI guide to Palestine</span><span class="subtitle-arabic">مرشد محوسب لبلاد فلسطين</span></p>
        </div>
        <span class="status-badge {status_class}">● {status_text}</span>
    </div>
    """, unsafe_allow_html=True)
