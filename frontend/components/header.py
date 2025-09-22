import streamlit as st

def render_header():
    """Render the main header"""
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0;">Rahalah - رحالة</h1>
        <p style="margin: 0; font-size: 1.4rem;">مرشد محوسب لبلاد فلسطين</p>
    </div>
    """, unsafe_allow_html=True)