import streamlit as st
from services.api_client import BackendAPIClient
from utils.helpers import complete_stopped_request, is_error_message
import time

def handle_chat_input(api_client: BackendAPIClient):
    """Handle chat input and processing"""
    
    # Handle the case where a request was stopped
    if st.session_state.stop_requested and st.session_state.pending_user_message:
        complete_stopped_request()
        st.rerun()
    
    # Handle new user input
    if prompt := st.chat_input("Ask about villages, history, culture...", disabled=st.session_state.query_in_progress):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.last_query = prompt
        st.session_state.pending_user_message = prompt
        st.session_state.query_in_progress = True
        st.session_state.stop_requested = False
        st.rerun()
    
    # Process the query if we have a pending one
    if (st.session_state.query_in_progress and st.session_state.pending_user_message and 
        st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and
        st.session_state.messages[-1]["content"] == st.session_state.pending_user_message):
        
        process_user_query(api_client)

def process_user_query(api_client: BackendAPIClient):
    """Process a user query and get response from backend (supports streaming)"""
    user_message = st.session_state.messages[-1]["content"]
    session_id = st.session_state.session_id
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Show stop button
        if st.session_state.query_in_progress:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("⏹ Stop", key="chat_stop", use_container_width=True):
                    st.session_state.stop_requested = True
                    st.session_state.query_in_progress = False
                    st.rerun()
        
        full_response = ""
        if not st.session_state.stop_requested:
            with st.spinner("Thinking..."):
                try:
                    # Try streaming first
                    accumulated = ""
                    for token in api_client.stream_query(user_message, session_id):
                        if st.session_state.stop_requested:
                            break
                        accumulated += token
                        full_response = accumulated
                        
                        # Display with markdown (preserves spaces and formatting)
                        message_placeholder.markdown(accumulated)
                        time.sleep(0.01)
                
                except Exception as e:
                    # Fallback to non-streaming
                    full_response = api_client.query(user_message, session_id)
                    message_placeholder.markdown(full_response)
        else:
            full_response = "🛑 Request stopped by user."
            message_placeholder.markdown(f'<div class="stopped-message">{full_response}</div>', unsafe_allow_html=True)
        
        # Show retry button for errors
        if is_error_message(full_response) and "stopped by user" not in full_response.lower():
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔄 Retry", key="retry", use_container_width=True):
                    st.session_state.messages.pop()  # Remove failed response
                    st.rerun()
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.session_state.query_in_progress = False
    st.session_state.pending_user_message = None
    st.session_state.stop_requested = False
    st.rerun()