import os
import streamlit as st
import requests

# Set page config first as required by Streamlit
st.set_page_config(
    page_title="Rahalah - رحالة",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Custom CSS for nature theme with distinct message colors
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary: #2E8B57;
        --secondary: #3CB371;
        --accent: #8FBC8F;
        --background: #F5F5F5;
        --text: #2F4F4F;
        --light: #FFFFFF;
    }
    
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    
    /* Sidebar header */
    .sidebar-header {
        text-align: center;
        color: var(--primary);
        margin-bottom: 1.5rem;
        font-size: 1.5rem;
    }
    
    /* Button styling */
    .stButton button {
        background-color: var(--primary);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton button:hover {
        background-color: var(--secondary);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Input fields */
    .stTextInput input {
        border-radius: 0.5rem;
        border: 1px solid var(--accent);
    }
    
    /* Chat container */
    .stChatMessage {
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* User message - darker green with very dark text */
    div[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #C8E6C9;
        border-left: 4px solid #2E7D32;
    }
    
    /* Assistant message - earthy tone with very dark text */
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F5F5DC;  /* Beige tone */
        border-left: 4px solid #8D6E63;
    }
    
    /* Make all chat text much darker for better readability */
    .stChatMessage p, .stChatMessage div, .stChatMessage li {
        color: #1A1A1A !important;
        font-weight: 500;
    }
    
    /* Specific styling for user message text */
    div[data-testid="stChatMessage"]:nth-child(even) p,
    div[data-testid="stChatMessage"]:nth-child(even) div,
    div[data-testid="stChatMessage"]:nth-child(even) li {
        color: #0D47A1 !important;  /* Dark blue for user messages */
    }
    
    /* Specific styling for assistant message text */
    div[data-testid="stChatMessage"]:nth-child(odd) p,
    div[data-testid="stChatMessage"]:nth-child(odd) div,
    div[data-testid="stChatMessage"]:nth-child(odd) li {
        color: #4E342E !important;  /* Very dark brown for assistant messages */
    }
    
    /* Chat input area */
    .stChatInput {
        background-color: #E8F5E9;
        border-radius: 0.5rem;
        border: 1px solid var(--accent);
    }
    
    /* Success/error messages */
    .stAlert {
        border-radius: 0.5rem;
    }
    
    /* Divider styling */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, var(--accent) 50%, transparent 100%);
        margin: 1.5rem 0;
    }
    
    /* Debug info styling */
    .debug-info {
        background-color: #FFF3E0;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #FF9800;
        font-family: monospace;
        font-size: 0.8rem;
        color: #333333;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for configuration
with st.sidebar:
    st.markdown('<p class="sidebar-header">🌿 LLM Configuration</p>', unsafe_allow_html=True)
    
    # Backend connection status - simplified to avoid CSS conflicts
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ Backend connected")
            st.info(f"Backend URL: {BACKEND_URL}")
        else:
            st.error(f"❌ Backend connection failed (Status: {health_response.status_code})")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Backend connection error: {str(e)}")
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
        try:
            with st.spinner("Initializing model..."):
                response = requests.post(
                    f"{BACKEND_URL}/initialize",
                    json={"model_name": model_name,
                          "embedding_model": embedding_model,
                          "chunk_size": 800,
                          "chunk_overlap": 80},
                    timeout=30
                )
                if response.status_code == 200:
                    st.success("Model initialized successfully")
                else:
                    st.error(f"Initialization failed: {response.text}")
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
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error: {response.json().get('detail', 'Unknown error')}"
    except Exception as e:
        return f"Connection error: {str(e)}"

# Main chat interface
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0;">Rahalah - رحالة</h1>
    <p style="margin: 0; font-size: 1.4rem;">مرشد محوسب لبلاد فلسطين</p>
</div>
""", unsafe_allow_html=True)

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
        with st.spinner("Thinking..."):
            full_response = get_backend_response(prompt)
        
        # Display response
        message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})