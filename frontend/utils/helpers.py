def complete_stopped_request():
    """Complete a stopped request properly"""
    import streamlit as st
    
    if (st.session_state.pending_user_message and 
        st.session_state.messages and 
        st.session_state.messages[-1]["role"] == "user" and
        st.session_state.messages[-1]["content"] == st.session_state.pending_user_message):
        
        # Add the stopped response
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "🛑 **Request stopped by user.**"
        })
        
        # Clear the pending state
        st.session_state.pending_user_message = None
        st.session_state.query_in_progress = False
        st.session_state.stop_requested = False

def handle_retry_logic():
    """Handle message retry logic"""
    import streamlit as st
    
    if st.session_state.retry_triggered and st.session_state.messages_to_retry is not None:
        message_index = st.session_state.messages_to_retry
        if message_index > 0 and st.session_state.messages[message_index]["role"] == "assistant":
            user_message_index = message_index - 1
            user_question = st.session_state.messages[user_message_index]["content"]
            
            # Remove everything from the user message onward
            st.session_state.messages = st.session_state.messages[:user_message_index]
            st.session_state.last_query = user_question
            st.session_state.pending_user_message = user_question
            st.session_state.query_in_progress = True
            st.session_state.retry_triggered = False
            st.session_state.messages_to_retry = None
            return True  # Indicate that a rerun is needed
    return False

def is_error_message(message_content):
    """Check if message content indicates an error"""
    error_indicators = ["error:", "connection error:", "timed out", "cannot connect"]
    return any(indicator in message_content.lower() for indicator in error_indicators)