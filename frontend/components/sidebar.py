import streamlit as st
from services.api_client import BackendAPIClient

def render_sidebar(api_client: BackendAPIClient):
    """Render the sidebar with configuration options"""
    with st.sidebar:
        st.markdown('<p class="sidebar-header">🌿 LLM Configuration</p>', unsafe_allow_html=True)
        
        # Backend connection status
        if api_client.health_check():
            st.success("✅ Backend connected")
        else:
            st.error("❌ Backend connection failed")
            st.info("Please check if your backend server is running.")
        
        st.markdown("---")
        
        # Model configuration
        model_name = st.text_input(
            "Backend Model Name",
            value="gpt-4.1-mini",
            help="Enter the name of the model to use"
        )
        
        embedding_model = st.text_input(
            "Embedding Model",
            value="laBSE",
            help="Enter the name of the embedding model to use"
        )
        
        if st.button("🌱 Initialize Model", use_container_width=True):
            model_config = {
                "model_name": model_name,
                "embedding_model": embedding_model,
                "chunk_size": 800,
                "chunk_overlap": 80
            }
            
            result = api_client.initialize_model(model_config)
            if result["success"]:
                st.success("Model initialized successfully")
            else:
                st.error(f"Initialization failed: {result['message']}")
        
        st.markdown("---")
        st.markdown("### Action Controls")
        
        # Stop button in sidebar
        if st.session_state.query_in_progress:
            if st.button("🛑 Stop Current Request", use_container_width=True, key="sidebar_stop"):
                st.session_state.stop_requested = True
                st.session_state.query_in_progress = False
                st.success("Stop request sent!")
                st.rerun()