import os
import streamlit as st
import requests  # Add this import

def get_backend_url():
    try:
        if hasattr(st, 'secrets') and st.secrets.get("BACKEND_URL"):
            return st.secrets["BACKEND_URL"]
    except:
        pass
    
    env_url = os.environ.get("BACKEND_URL")
    if env_url:
        return env_url
    
    return "http://127.0.0.1:8080"

BACKEND_URL = get_backend_url()

# Initialize Streamlit app
st.set_page_config(
    page_title="RAG LLM Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for configuration
with st.sidebar:
    st.title("LLM Configuration")
    
    # Backend connection status
    try:
        health_response = requests.get(f"{BACKEND_URL}/health")
        if health_response.status_code == 200:
            st.success("✅ Backend connected")
        else:
            st.error("❌ Backend connection failed")
    except:
        st.error("❌ Backend connection failed")
        
    # # Backend specific settings
    # else:
    model_name = st.text_input(
            "Backend Model Name",
             value="gpt-4.1-mini"
        )
    embedding_model = st.text_input(
        "Embedding Model",
        value="laBSE"
    )
    if st.button("Initialize Model"):
        try:
            response = requests.post(
                f"{BACKEND_URL}/initialize",
                json={"model_name": model_name,
                      "embedding_model": embedding_model,
                      "chunk_size": 800,
                      "chunk_overlap": 80}
            )
            if response.status_code == 200:
                st.success("Model initialized successfully")
            else:
                st.error(f"Initialization failed: {response.json()}")
        except Exception as e:
            st.error(f"Connection error: {str(e)}")

# Function to get response from backend
def get_backend_response(question):
    try:
        response = requests.post(
            f"{BACKEND_URL}/query",
            json={
                "question": question,
                "session_id": st.session_state.get("session_id", "default_session")
            }
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error: {response.json().get('detail', 'Unknown error')}"
    except Exception as e:
        return f"Connection error: {str(e)}"

# Main chat interface
st.title("Rahalah - رحالة")
st.subheader("مياومياو 🤖")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to ask?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Get response based on selected provider
        full_response = get_backend_response(prompt)

        
        # Display response
        message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
