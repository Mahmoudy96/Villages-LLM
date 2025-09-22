import streamlit as st
from services.api_client import BackendAPIClient
from utils.helpers import complete_stopped_request, is_error_message

def handle_chat_input(api_client: BackendAPIClient):
    """Handle chat input and processing"""
    
    # Handle the case where a request was stopped - complete it first
    if st.session_state.stop_requested and st.session_state.pending_user_message:
        complete_stopped_request()
        st.rerun()
    
    # Handle new user input
    if prompt := st.chat_input("What would you like to ask?", disabled=st.session_state.query_in_progress):
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
    """Process a user query and get response from backend"""
    user_message = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Show stop button during query execution
        if st.session_state.query_in_progress:
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🛑", key="chat_stop", use_container_width=True):
                    st.session_state.stop_requested = True
                    st.session_state.query_in_progress = False
                    st.rerun()
        
        # Only make the API call if stop hasn't been requested
        if not st.session_state.stop_requested:
            with st.spinner("Thinking..."):
                full_response = api_client.query(user_message, st.session_state.session_id)
        else:
            full_response = "🛑 Request stopped by user."
        
        # Display response
        if "stopped by user" in full_response.lower():
            message_placeholder.markdown(f'<div class="stopped-message">{full_response}</div>', unsafe_allow_html=True)
        else:
            message_placeholder.markdown(full_response)
        
        # Show retry button for errors (but not for stopped messages)
        if (is_error_message(full_response) and
            "stopped by user" not in full_response.lower()):
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("🔄 Retry", key="new_error_retry", use_container_width=True):
                    st.session_state.retry_triggered = True
                    st.session_state.messages_to_retry = len(st.session_state.messages)
                    st.rerun()
    
    # Add assistant response to chat history and clean up state
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.session_state.query_in_progress = False
    st.session_state.pending_user_message = None
    st.session_state.stop_requested = False
    st.rerun()