def get_css_styles():
    return """
    <style>
    /* Font - warm, readable */
    @import url('https://fonts.googleapis.com/css2?family=Amiri:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');
    
    /* Palestinian-inspired palette */
    :root {
        /* Olive - symbol of Palestine, olive groves */
        --olive: #4A6B3D;
        --olive-dark: #3D5A32;
        --olive-light: #E8EDE0;
        
        /* Terra cotta - traditional tatriz embroidery */
        --terracotta: #A63D3D;
        --terracotta-dark: #8B3333;
        --terracotta-light: #F5E6E6;
        
        /* Gold - embroidery thread, traditional crafts */
        --gold: #C9A227;
        --gold-dark: #A67C00;
        
        /* Jerusalem stone - warm cream, regional architecture */
        --stone: #F5F0E8;
        --stone-light: #FDFBF7;
        --stone-warm: #EDE6DC;
        
        /* Earth tones */
        --earth: #3C2C1E;
        --earth-light: #5C4A3A;
        --earth-muted: #8B7355;
        
        /* Borders & shadows */
        --border: #D4C4B0;
        --shadow-warm: 0 2px 8px rgba(60, 44, 30, 0.08);
        --shadow-soft: 0 4px 12px rgba(60, 44, 30, 0.06);
        
        --radius-sm: 0.5rem;
        --radius-md: 0.75rem;
        --radius-lg: 1rem;
    }
    
    /* Base - warm stone background */
    .stApp {
        background: linear-gradient(180deg, var(--stone-light) 0%, var(--stone) 50%, var(--stone-warm) 100%) !important;
    }
    
    /* Main header - Jerusalem stone with olive accent */
    .main-header {
        background: linear-gradient(135deg, var(--stone-light) 0%, var(--stone-warm) 100%);
        padding: 1.5rem 2rem;
        border-radius: var(--radius-lg);
        margin-bottom: 2rem;
        box-shadow: var(--shadow-warm);
        border: 1px solid var(--border);
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 1rem;
    }
    
    .main-header-content h1 {
        font-family: 'Amiri', 'Traditional Arabic', serif !important;
        font-size: 2.25rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        color: var(--earth) !important;
        letter-spacing: 0.02em;
    }
    
    .main-header-content h1 .arabic {
        color: var(--olive) !important;
    }
    
    .main-header-content .subtitle {
        font-family: 'Source Sans 3', system-ui, sans-serif !important;
        font-size: 0.95rem !important;
        color: var(--earth-light) !important;
        margin: 0.35rem 0 0 0 !important;
        font-weight: 500;
    }
    
    /* Sidebar - light green */
    [data-testid="stSidebar"] {
        background: #d4edda !important;
        border-right: 1px solid var(--border) !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        font-family: 'Source Sans 3', system-ui, sans-serif !important;
    }
    
    .sidebar-section-title {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        color: var(--earth-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem !important;
    }
    
    /* Chat messages - stone cards with olive/terracotta accents */
    div[data-testid="stChatMessage"] {
        background: var(--stone-light) !important;
        border-radius: var(--radius-lg) !important;
        padding: 1rem 1.25rem !important;
        margin-bottom: 1rem !important;
        box-shadow: var(--shadow-soft) !important;
        border: 1px solid var(--border) !important;
        font-family: 'Source Sans 3', system-ui, sans-serif !important;
    }
    
    /* User messages - olive tint */
    div[data-testid="stChatMessage"]:nth-of-type(odd) {
        background: linear-gradient(135deg, var(--olive-light) 0%, var(--stone-light) 100%) !important;
        border-left: 4px solid var(--olive) !important;
    }
    
    /* Assistant messages - terracotta accent */
    div[data-testid="stChatMessage"]:nth-of-type(even) {
        border-left: 4px solid var(--terracotta) !important;
    }
    
    .stChatMessage p, .stChatMessage div, .stChatMessage li {
        color: var(--earth) !important;
        font-size: 0.95rem !important;
        line-height: 1.65 !important;
    }
    
    /* Buttons - olive primary */
    .stButton > button {
        font-family: 'Source Sans 3', system-ui, sans-serif !important;
        font-weight: 600 !important;
        border-radius: var(--radius-md) !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
        border: none !important;
    }
    
    .stButton > button[kind="primary"] {
        background: var(--olive) !important;
        color: white !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: var(--olive-dark) !important;
        box-shadow: var(--shadow-warm) !important;
    }
    
    /* Bottom bar - all black (chat box + surrounding area) */
    [data-testid="stVerticalBlock"]:has([data-testid="stChatInput"]),
    [data-testid="stVerticalBlock"]:has(.stChatInputContainer),
    [class*="ChatInput"],
    .stChatInputContainer,
    .stChatInputContainer > div,
    [data-testid="stChatInput"] {
        background-color: #000000 !important;
        background-image: none !important;
        border: 1px solid #000000 !important;
        padding: 1rem !important;
    }
    
    /* Text area - black to match, white text */
    [class*="ChatInput"] textarea,
    [data-testid="stChatInput"] textarea,
    .stChatInputContainer textarea {
        background-color: #000000 !important;
        color: #ffffff !important;
        caret-color: #ffffff !important;
        border: 1px solid #000000 !important;
    }
    
    /* Empty state - olive branch motif */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: var(--earth-light);
    }
    
    .empty-state-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        opacity: 0.7;
    }
    
    .empty-state-title {
        font-family: 'Amiri', serif !important;
        font-size: 1.75rem !important;
        color: var(--earth) !important;
        margin-bottom: 0.5rem !important;
    }
    
    .empty-state-subtitle {
        font-size: 0.95rem !important;
        color: var(--earth-muted) !important;
        max-width: 420px;
        margin: 0 auto;
        line-height: 1.6;
    }
    
    .stopped-message {
        color: var(--earth-muted) !important;
        font-style: italic;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .status-badge.connected {
        background: var(--olive-light);
        color: var(--olive-dark);
    }
    
    .status-badge.disconnected {
        background: var(--terracotta-light);
        color: var(--terracotta-dark);
    }
    
    /* Decorative divider - geometric pattern inspired by tatriz */
    .tatriz-divider {
        height: 4px;
        background: linear-gradient(90deg, var(--olive) 0%, var(--gold) 25%, var(--terracotta) 50%, var(--gold) 75%, var(--olive) 100%);
        border-radius: 2px;
        margin: 1rem 0;
        opacity: 0.6;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
