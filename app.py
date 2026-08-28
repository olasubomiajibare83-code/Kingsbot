import streamlit as st
import openai
import json
import time
from datetime import datetime
import requests
import re

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
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    .main {
        padding: 0px;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .chat-container {
        height: 500px;
        overflow-y: auto;
        padding: 20px;
        background: #0d1117;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 20px;
    }
    
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
    
    .stat-box {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}
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
# YOUR API KEY (HARDCODED)
# ============================================
YOUR_API_KEY = "sk-your-actual-api-key-here"  # <-- PUT YOUR REAL API KEY HERE

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
    st.session_state.api_key = YOUR_API_KEY
if 'model' not in st.session_state:
    st.session_state.model = "gpt-3.5-turbo"
if 'voice_enabled' not in st.session_state:
    st.session_state.voice_enabled = True
if 'current_conv_id' not in st.session_state:
    st.session_state.current_conv_id = str(int(time.time()))
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False
if 'web_search_key' not in st.session_state:
    st.session_state.web_search_key = ""
if 'search_engine_id' not in st.session_state:
    st.session_state.search_engine_id = ""

# ============================================
# HELPER FUNCTIONS
# ============================================

def save_conversation():
    if len(st.session_state.conversation) > 0:
        conv_data = {
            'id': st.session_state.current_conv_id,
            'date': datetime.now().isoformat(),
            'messages': st.session_state.conversation.copy(),
            'message_count': len(st.session_state.conversation),
            'preview': st.session_state.conversation[0]['content'][:60] if st.session_state.conversation else 'Empty'
        }
        existing = [c for c in st.session_state.conversations if c['id'] == st.session_state.current_conv_id]
        if existing:
            idx = st.session_state.conversations.index(existing[0])
            st.session_state.conversations[idx] = conv_data
        else:
            st.session_state.conversations.insert(0, conv_data)
        if len(st.session_state.conversations) > 50:
            st.session_state.conversations = st.session_state.conversations[:50]

def load_conversation(conv_id):
    conv = next((c for c in st.session_state.conversations if c['id'] == conv_id), None)
    if conv:
        st.session_state.conversation = conv['messages'].copy()
        st.session_state.current_conv_id = conv_id
        st.session_state.message_count = len(conv['messages'])
        st.rerun()

def call_openai(user_message):
    if not st.session_state.api_key:
        return "⚠️ No API key found. Please check the code."
    
    history = st.session_state.conversation[-12:] if st.session_state.conversation else []
    messages = []
    
    system_prompt = "You are KingsBot, a helpful AI assistant with memory and personalization."
    if st.session_state.user_name:
        system_prompt += f"\nUser's name: {st.session_state.user_name}"
    if st.session_state.interests:
        system_prompt += f"\nUser's interests: {', '.join(st.session_state.interests)}"
    if st.session_state.facts:
        system_prompt += f"\nFacts you know about user: {'; '.join(st.session_state.facts)}"
    system_prompt += f"\nCurrent time: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    system_prompt += "\nBe concise, helpful, and remember what users tell you."
    system_prompt += "\nYou can code in any language, explain complex topics, and provide detailed answers."
    
    messages.append({"role": "system", "content": system_prompt})
    
    for msg in history:
        messages.append({"role": msg['role'], "content": msg['content']})
    
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
    """Perform web search using DuckDuckGo (no API key required!)"""
    try:
        # Using DuckDuckGo API (free, no key needed)
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        response = requests.get(url)
        if response.status_code != 200:
            return f"❌ Search error: {response.status_code}"
        
        data = response.json()
        results = "🔍 **Web Search Results:**\n\n"
        
        # Get abstract if available
        if data.get('Abstract'):
            results += f"**Summary:** {data['Abstract']}\n\n"
            if data.get('AbstractURL'):
                results += f"Source: {data['AbstractURL']}\n\n"
        
        # Get related topics
        if data.get('RelatedTopics'):
            results += "**Related Topics:**\n"
            count = 0
            for topic in data['RelatedTopics']:
                if count >= 5:
                    break
                if 'Text' in topic:
                    results += f"- {topic['Text'][:300]}\n"
                    if 'FirstURL' in topic:
                        results += f"  Link: {topic['FirstURL']}\n"
                    results += "\n"
                    count += 1
        
        if not data.get('Abstract') and not data.get('RelatedTopics'):
            # Fallback to a free search API
            results += "No summary found. Here are some search suggestions:\n"
            results += f"- Search Google for: {query}\n"
            results += f"- Check Wikipedia: https://en.wikipedia.org/wiki/{query.replace(' ', '_')}\n"
        
        return results
    except Exception as e:
        return f"❌ Search error: {str(e)}\n\n💡 Try searching Google directly for: {query}"

def extract_facts(user_msg, ai_response):
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
        return "📦 Export function available in sidebar."
    
    elif cmd.startswith('/search '):
        query = cmd[8:].strip()
        if query:
            with st.spinner(f"🔍 Searching for '{query}'..."):
                return web_search(query)
    
    elif cmd == '/help':
        return """📖 **Commands:**
/clear - Clear chat
/stats - Show stats
/name YourName - Set your name
/interest Hobby - Add interest
/facts - Show learned facts
/export - Download chat JSON
/search query - Web search (FREE, no API key needed!)
/voice - Toggle voice output
/help - Show this help"""
    
    elif cmd == '/voice':
        st.session_state.voice_enabled = not st.session_state.voice_enabled
        return f"🎤 Voice output {'enabled' if st.session_state.voice_enabled else 'disabled'}"
    
    return None

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/robot-2.png", width=64)
    st.title("⚙️ KingsBot Settings")
    
    # API Status
    st.success("✅ API Key: Loaded")
    
    # Model Selection
    model = st.selectbox(
        "🧠 Model",
        options=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"],
        index=0
    )
    if model != st.session_state.model:
        st.session_state.model = model
    
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
st.caption("Your advanced AI assistant with memory, voice, and FREE web search")

# Create tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📜 History", "🔍 Search"])

# ============================================
# TAB 1: CHAT
# ============================================
with tab1:
    chat_container = st.container(height=400)
    
    with chat_container:
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
            "🎤" if not st.session_state.is_listening else "⏹️",
            use_container_width=True,
            help="Click to speak (voice input)"
        )
    
    if voice_button:
        st.session_state.is_listening = not st.session_state.is_listening
        if st.session_state.is_listening:
            st.info("🎤 Listening... Speak your message.")
        else:
            st.info("🎤 Voice input stopped.")
    
    if send_button and user_input:
        command_result = handle_command(user_input)
        if command_result:
            st.session_state.conversation.append({
                'role': 'assistant',
                'content': command_result,
                'timestamp': datetime.now().strftime('%I:%M %p')
            })
            st.session_state.message_count += 1
            save_conversation()
            st.rerun()
        else:
            with st.spinner("🤔 Thinking..."):
                st.session_state.conversation.append({
                    'role': 'user',
                    'content': user_input,
                    'timestamp': datetime.now().strftime('%I:%M %p')
                })
                st.session_state.message_count += 1
                
                response = call_openai(user_input)
                extract_facts(user_input, response)
                
                st.session_state.conversation.append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now().strftime('%I:%M %p')
                })
                st.session_state.message_count += 1
                
                save_conversation()
                
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
        
        search_hist = st.text_input("🔍 Search history", placeholder="Search by keyword...", key="history_search")
        
        filtered = st.session_state.conversations
        if search_hist:
            filtered = [
                c for c in st.session_state.conversations
                if any(search_hist.lower() in msg['content'].lower() for msg in c['messages'])
            ]
        
        for conv in filtered:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    <div class="history-item">
                        <div class="history-date">📅 {datetime.fromisoformat(conv['date']).strftime('%B %d, %Y at %I:%M %p')}</div>
                        <div class="history-preview">{conv['preview']}</div>
                        <div style="font-size:11px;color:#8b949e;">💬 {conv['message_count']} messages</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("📂 Load", key=f"load_{conv['id']}"):
                        load_conversation(conv['id'])

# ============================================
# TAB 3: SEARCH
# ============================================
with tab3:
    search_query = st.text_input("🔍 Search all conversations", placeholder="Enter keyword...", key="search_all")
    
    if search_query and len(search_query) > 1:
        results = []
        for conv in st.session_state.conversations:
            for msg in conv['messages']:
                if search_query.lower() in msg['content'].lower():
                    results.append({
                        'conv_id': conv['id'],
                        'date': conv['date'],
                        'content': msg['content'],
                        'role': msg['role'],
                        'preview': msg['content'][:200] + ('...' if len(msg['content']) > 200 else '')
                    })
        
        if not results:
            st.info("🔍 No results found.")
        else:
            st.success(f"✅ Found {len(results)} results")
            for result in results[:20]:
                st.markdown(f"""
                <div class="search-result">
                    <div><strong>{'👤 You' if result['role'] == 'user' else '🤖 KingsBot'}</strong></div>
                    <div class="search-snippet">{result['preview']}</div>
                    <div style="font-size:10px;color:#484f58;">{datetime.fromisoformat(result['date']).strftime('%B %d, %Y')}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("📂 Load", key=f"search_load_{result['conv_id']}"):
                    load_conversation(result['conv_id'])

# ============================================
# FOOTER
# ============================================
st.divider()
st.caption("🤖 KingsBot Assistant AI | Built with ❤️ using Streamlit | Web Search by DuckDuckGo (FREE)")
