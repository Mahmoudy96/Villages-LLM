def get_css_styles():
    """Return the CSS styles for the application"""
    return """
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
    
    /* Retry button styling */
    .retry-button {
        background-color: #FF9800 !important;
    }
    
    .retry-button:hover {
        background-color: #F57C00 !important;
    }
    
    /* Stop button styling */
    .stop-button {
        background-color: #F44336 !important;
    }
    
    .stop-button:hover {
        background-color: #D32F2F !important;
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
        background-color: #F5F5DC;
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
        color: #0D47A1 !important;
    }
    
    /* Specific styling for assistant message text */
    div[data-testid="stChatMessage"]:nth-child(odd) p,
    div[data-testid="stChatMessage"]:nth-child(odd) div,
    div[data-testid="stChatMessage"]:nth-child(odd) li {
        color: #4E342E !important;
    }
    
    /* Stopped message styling */
    .stopped-message {
        color: #D32F2F !important;
        font-style: italic;
    }
    
    /* Action buttons container */
    .action-buttons {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    </style>
    """