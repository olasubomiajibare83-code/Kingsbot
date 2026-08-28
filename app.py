import streamlit as st
import openai
import json
import time
from datetime import datetime
import requests

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="KingsBot Assistant AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS (Properly embedded)
# ============================================
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 0px;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Chat container */
    .chat-container {
        height: 500px;
        overflow-y: auto;
        padding: 20px;
        background: #0d1117;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 20px;
    }
    
    /* Message bubbles */
    .user-msg {
        background: #238636;
        color: white;
        padding: 12px 16px;
        border-radius: 12px;
        margin: 8px 0;
        max-width: 80%;
        align-self: flex-end;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    
    .assistant-msg {
        background: #21262d;
        color: #e6edf3;
        padding: 12px 16px;
        border-radius: 12px;
        margin: 8px 0;
        max-width: 80%;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
    }
    
    .timestamp {
        font-size: 10px;
        color: #8b949e;
        margin-top: 4px;
        display: block;
    }
    
    /* Sidebar styling */
    .sidebar-content {
        padding: 20px 10px;
    }
    
    .stat-box {
        background: #161b22;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border: 1px solid #30363d;
    }
    
    .stat-label {
        color: #8b949e;
        font-size: 12px;
    }
    
    .stat-value {
        color: #e6edf3;
        font-size: 18px;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton > button {
        background: #238636;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 600;
        transition: 0.2s;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: #2ea043;
    }
    
    /* Input field */
    .stTextInput > div > div > input {
        background: #0d1117;
        color: #e6edf3;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px 14px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #238636;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #21262d;
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
        color: #8b949e;
    }
    
    .stTabs [aria-selected="true"] {
        background: #30363d;
        color: #e6edf3;
    }
    
    /* History items */
    .history-item {
        background: #21262d;
        padding: 10px 14px;
        border-radius: 8px;
        margin: 6px 0;
        cursor: pointer;
        transition: 0.2s;
        border: 1px solid #30363d;
    }
    
    .history-item:hover {
        background: #30363d;
        border-color: #238636;
    }
    
    .history-date {
        font-size: 11px;
        color: #8b949e;
    }
    
    .history-preview {
        font-size: 13px;
        color: #e6edf3;
        margin-top: 4px;
    }
    
    /* Voice button */
    .voice-btn {
        background: #1f6feb;
        color: white;
        border: none;
        border-radius: 50%;
        width: 48px;
        height: 48px;
        font-size: 20px;
        cursor: pointer;
        transition: 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .voice-btn:hover {
        background: #388bfd;
    }
    
    .voice-btn.listening {
        background: #da3633;
        animation: pulse 0.8s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.6; transform: scale(0.95); }
    }
    
    /* Search results */
    .search-result {
        background: #21262d;
        padding: 10px 14px;
        border-radius: 8px;
        margin: 4px 0;
        cursor: pointer;
        border: 1px solid #30363d;
    }
    
    .search-result:hover {
        background: #30363d;
        border-color: #238636;
    }
    
    .search-snippet {
        color: #8b949e;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'message_count' not in st.session_state:
    st.session_state.message_count = 0
if 'facts' not in st.session_state:
    st.session_state.facts = []
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'interests' not in st.session_state:
    st.session_state.interests = []
if 'conversations' not in st.session_state:
    st.session_state.conversations = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'model' not in st.session_state:
    st.session_state.model = "gpt-5.5"
if 'web_search_key' not in st.session_state:
    st.session_state.web_search_key = ""
if 'voice_enabled' not in st.session_state:
    st.session_state.voice_enabled = True
if 'current_conv_id' not in st.session_state:
    st.session_state.current_conv_id = str(int(time.time()))
if 'processing' not in st.session_state:
    st.session_state.processing = False

# ============================================
# HELPER FUNCTIONS
# ============================================

def save_conversation():
    """Save current conversation to history"""
    if len(st.session_state.conversation) > 0:
        conv_data = {
            'id': st.session_state.current_conv_id,
            'date': datetime.now().isoformat(),
            'messages': st.session_state.conversation.copy(),
            'message_count': len(st.session_state.conversation),
            'preview': st.session_state.conversation[0]['content'][:60] if st.session_state.conversation else 'Empty'
        }
        # Check if already exists
        existing = [c for c in st.session_state.conversations if c['id'] == st.session_state.current_conv_id]
        if existing:
            idx = st.session_state.conversations.index(existing[0])
            st.session_state.conversations[idx] = conv_data
        else:
            st.session_state.conversations.insert(0, conv_data)
        # Keep last 50
        if len(st.session_state.conversations) > 50:
            st.session_state.conversations = st.session_state.conversations[:50]

def load_conversation(conv_id):
    """Load a saved conversation"""
    conv = next((c for c in st.session_state.conversations if c['id'] == conv_id), None)
    if conv:
        st.session_state.conversation = conv['messages'].copy()
        st.session_state.current_conv_id = conv_id
        st.session_state.message_count = len(conv['messages'])
        st.rerun()

def call_openai(user_message):
    """Call OpenAI API"""
    if not st.session_state.api_key:
        return "⚠️ Please enter your OpenAI API key in the sidebar."

    # Build conversation history
    history = st.session_state.conversation[-12:] if st.session_state.conversation else []
    messages = []

    # System prompt
    system_prompt = "You are KingsBot, a helpful AI assistant with memory and personalization."
    if st.session_state.user_name:
        system_prompt += f"\nUser's name: {st.session_state.user_name}"
    if st.session_state.interests:
        system_prompt += f"\nUser's interests: {', '.join(st.session_state.interests)}"
    if st.session_state.facts:
        system_prompt += f"\nFacts you know about user: {'; '.join(st.session_state.facts)}"
    system_prompt += f"\nCurrent time: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    system_prompt += "\nBe concise, helpful, and remember what users tell you."

    messages.append({"role": "system", "content": system_prompt})

    # Add history
    for msg in history:
        messages.append({"role": msg['role'], "content": msg['content']})

    # Add current message
    messages.append({"role": "user", "content": user_message})

    try:
        client = openai.OpenAI(api_key=st.session_state.api_key)
        response = client.chat.completions.create(
            model=st.session_state.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            top_p=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {str(e)}"

def web_search(query):
    """Perform web search using Google Custom Search API"""
    if not st.session_state.web_search_key:
        return "⚠️ Google Search API key not set. Add it in sidebar."
    try:
        url = f"https://www.googleapis.com/customsearch/v1?key={st.session_state.web_search_key}&q={query}&num=5"
        response = requests.get(url)
        if response.status_code != 200:
            return f"❌ Search error: {response.status_code}"
        data = response.json()
        if 'items' not in data:
            return "No search results found."
        results = "🔍 **Search Results:**\n\n"
        for i, item in enumerate(data['items'][:5], 1):
            results += f"{i}. **{item.get('title', 'No title')}**\n{item.get('snippet', 'No snippet')}\n{item.get('link', '')}\n\n"
        return results
    except Exception as e:
        return f"❌ Search error: {str(e)}"

def extract_facts(user_msg, ai_response):
    """Extract facts from conversation"""
    combined = user_msg + " " + ai_response
    patterns = [
        r"my name is ([^\.]+)",
        r"i (?:am|'m) ([^\.]+)",
        r"i like ([^\.]+)",
        r"i work as ([^\.]+)",
        r"i live in ([^\.]+)",
        r"i have ([^\.]+)",
        r"i (?:love|enjoy) ([^\.]+)"
    ]
    import re
    new_facts = []
    for pattern in patterns:
        matches = re.findall(pattern, combined, re.IGNORECASE)
        for match in matches:
            fact = match.strip()
            if len(fact) > 3 and fact not in st.session_state.facts:
                if not any(f in fact or fact in f for f in st.session_state.facts):
                    new_facts.append(fact)
    if new_facts:
        st.session_state.facts.extend(new_facts)

def handle_command(text):
    """Handle slash commands"""
    cmd = text.strip().lower()
    if cmd == '/clear':
        st.session_state.conversation = []
        st.session_state.message_count = 0
        return "🧹 Conversation cleared."
    elif cmd == '/stats':
        return f"""📊 **Stats:**
• Messages: {st.session_state.message_count}
• Facts learned: {len(st.session_state.facts)}
• Interests: {', '.join(st.session_state.interests) or 'None'}
• Model: {st.session_state.model}
• Name: {st.session_state.user_name or 'Not set'}
• Saved conversations: {len(st.session_state.conversations)}"""
    elif cmd.startswith('/name '):
        name = cmd[6:].strip()
        if name:
            st.session_state.user_name = name
            return f"✅ Name set to '{name}'!"
    elif cmd.startswith('/interest '):
        interest = cmd[10:].strip()
        if interest and interest not in st.session_state.interests:
            st.session_state.interests.append(interest)
            return f"✅ Added '{interest}' to your interests!"
    elif cmd == '/facts':
        if not st.session_state.facts:
            return "📚 No facts learned yet. Share things about yourself!"
        facts_list = "\n".join([f"{i+1}. {f}" for i, f in enumerate(st.session_state.facts)])
        return f"📚 **Facts I've learned about you:**\n{facts_list}"
    elif cmd == '/export':
        # Export functionality handled separately
        return "📦 Export function available in sidebar."
    elif cmd.startswith('/search '):
        query = cmd[8:].strip()
        if query:
            return web_search(query)
    elif cmd == '/help':
        return """📖 **Commands:**
/clear - Clear chat
/stats - Show stats
/name YourName - Set your name
/interest Hobby - Add interest
/facts - Show learned facts
/export - Download chat JSON
/search query - Web search
/help - Show this help"""
    return None

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/robot-2.png", width=64)
    st.title("⚙️ KingsBot Settings")
    
    # API Key
    api_key = st.text_input(
        "🔑 OpenAI API Key",
        value=st.session_state.api_key,
        type="password",
        help="Get your API key from platform.openai.com"
    )
    if api_key != st.session_state.api_key:
        st.session_state.api_key = api_key
        st.rerun()
    
    # Model Selection
    model = st.selectbox(
        "🧠 Model",
        options=["gpt-5.5", "gpt-5.4", "gpt-5.2"],
        index=["gpt-5.5", "gpt-5.4", "gpt-5.2"].index(st.session_state.model)
    )
    if model != st.session_state.model:
        st.session_state.model = model
    
    # Web Search API Key
    web_key = st.text_input(
        "🔍 Google Search API Key",
        value=st.session_state.web_search_key,
        type="password",
        help="Get from Google Cloud Console"
    )
    if web_key != st.session_state.web_search_key:
        st.session_state.web_search_key = web_key
    
    # Voice toggle
    voice_enabled = st.toggle("🎤 Voice Output", value=st.session_state.voice_enabled)
    if voice_enabled != st.session_state.voice_enabled:
        st.session_state.voice_enabled = voice_enabled
    
    st.divider()
    
    # Stats
    st.subheader("📊 Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💬 Messages", st.session_state.message_count)
    with col2:
        st.metric("📚 Facts", len(st.session_state.facts))
    
    st.metric("💾 Saved Chats", len(st.session_state.conversations))
    
    st.divider()
    
    # Export
    if st.button("📦 Export All Data", use_container_width=True):
        export_data = {
            "export_date": datetime.now().isoformat(),
            "user_name": st.session_state.user_name,
            "interests": st.session_state.interests,
            "facts": st.session_state.facts,
            "model": st.session_state.model,
            "conversations": st.session_state.conversations,
            "current_conversation": st.session_state.conversation
        }
        st.download_button(
            label="⬇️ Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"kingsbot_export_{int(time.time())}.json",
            mime="application/json",
            use_container_width=True
        )
    
    # Clear all data
    if st.button("🗑️ Clear All Data", use_container_width=True, type="secondary"):
        if st.session_state.conversations or st.session_state.conversation:
            st.session_state.conversation = []
            st.session_state.conversations = []
            st.session_state.facts = []
            st.session_state.message_count = 0
            st.session_state.interests = []
            st.rerun()

# ============================================
# MAIN CONTENT
# ============================================
st.title("🤖 KingsBot Assistant AI")
st.caption("Your advanced AI assistant with memory, search, and voice capabilities")

# Create tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📜 History", "🔍 Search"])

# ============================================
# TAB 1: CHAT
# ============================================
with tab1:
    # Chat container
    chat_container = st.container(height=400)
    
    with chat_container:
        # Display conversation
        if not st.session_state.conversation:
            st.info("👋 Welcome to KingsBot! Start a conversation below.")
        else:
            for msg in st.session_state.conversation:
                if msg['role'] == 'user':
                    st.markdown(f"""
                    <div class="user-msg">
                        {msg['content']}
                        <span class="timestamp">{msg.get('timestamp', 'Just now')}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="assistant-msg">
                        {msg['content']}
                        <span class="timestamp">{msg.get('timestamp', 'Just now')}</span>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Input area
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col1:
        user_input = st.text_input(
            "Message",
            placeholder="Type your message... Use /help for commands",
            label_visibility="collapsed",
            key="user_input"
        )
    
    with col2:
        send_button = st.button("📤 Send", use_container_width=True)
    
    with col3:
        voice_button = st.button(
            "🎤" if not st.session_state.get('is_listening', False) else "⏹️",
            use_container_width=True,
            help="Click to speak (voice input)"
        )
    
    # Handle voice button (simulate for now)
    if voice_button:
        st.session_state.is_listening = not st.session_state.get('is_listening', False)
        if st.session_state.is_listening:
            st.info("🎤 Listening... Speak your message (simulated).")
        else:
            st.info("🎤 Voice input stopped.")
    
    # Handle send
    if send_button and user_input:
        # Check if it's a command
        command_result = handle_command(user_input)
        if command_result:
            # Add as assistant message
            st.session_state.conversation.append({
                'role': 'assistant',
                'content': command_result,
                'timestamp': datetime.now().strftime('%I:%M %p')
            })
            st.session_state.message_count += 1
            save_conversation()
            st.rerun()
        else:
            # Process with AI
            with st.spinner("🤔 Thinking..."):
                # Add user message
                st.session_state.conversation.append({
                    'role': 'user',
                    'content': user_input,
                    'timestamp': datetime.now().strftime('%I:%M %p')
                })
                st.session_state.message_count += 1
                
                # Get AI response
                response = call_openai(user_input)
                
                # Extract facts
                extract_facts(user_input, response)
                
                # Add assistant response
                st.session_state.conversation.append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now().strftime('%I:%M %p')
                })
                st.session_state.message_count += 1
                
                # Save conversation
                save_conversation()
                
                # Voice output (simulated)
                if st.session_state.voice_enabled:
                    st.info(f"🔊 Speaking: {response[:200]}...")
            
            st.rerun()

# ============================================
# TAB 2: HISTORY
# ============================================
with tab2:
    if not st.session_state.conversations:
        st.info("📭 No conversations saved yet. Start chatting!")
    else:
        st.caption(f"📜 {len(st.session_state.conversations)} saved conversations")
        
        # Search within history
        search_hist = st.text_input("🔍 Search history", placeholder="Search by keyword...", key="history_search")
        
