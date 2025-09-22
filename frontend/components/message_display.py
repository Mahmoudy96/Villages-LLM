import streamlit as st
from utils.helpers import is_error_message

def display_chat_messages():
    """Display all chat messages with retry buttons for errors"""
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            # Use different styling for stopped messages
            if "stopped by user" in message["content"].lower():
                st.markdown(f'<div class="stopped-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(message["content"])
            
            # Add retry button for failed assistant messages
            if (message["role"] == "assistant" and 
                is_error_message(message["content"]) and
                i > 0 and st.session_state.messages[i-1]["role"] == "user"):
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("🔄 Retry", key=f"retry_{i}", use_container_width=True):
                        st.session_state.retry_triggered = True
                        st.session_state.messages_to_retry = i
                        st.rerun()