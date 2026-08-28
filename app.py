import streamlit as st
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
    
    .free-badge {
        background: #238636;
        color: white;
        padding: 2px 12px;
        border-radius: 20px;
        font-size: 12px;
        display: inline-block;
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
if 'voice_enabled' not in st.session_state:
    st.session_state.voice_enabled = True
if 'current_conv_id' not in st.session_state:
    st.session_state.current_conv_id = str(int(time.time()))
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False
if 'model' not in st.session_state:
    st.session_state.model = "Hugging Face (FREE)"

# ============================================
# FREE AI FUNCTION (No API Key!)
# ============================================

def call_free_ai(user_message):
    """Use Hugging Face's FREE API - No key required!"""
    
    # Build context from conversation
    history = st.session_state.conversation[-6:] if st.session_state.conversation else []
    
    # Build conversation context
    context = ""
    for msg in history:
        if msg['role'] == 'user':
            context += f"User: {msg['content']}\n"
        else:
            context += f"Assistant: {msg['content']}\n"
    
    # Add user info
    user_info = ""
    if st.session_state.user_name:
        user_info += f"User's name is {st.session_state.user_name}. "
    if st.session_state.interests:
        user_info += f"User's interests: {', '.join(st.session_state.interests)}. "
    if st.session_state.facts:
        user_info += f"Facts about user: {'; '.join(st.session_state.facts)}. "
    
    # Create the prompt
    prompt = f"""You are KingsBot, a helpful AI assistant with memory and personalization.

{user_info}

Previous conversation:
{context}

User: {user_message}
Assistant:"""
    
    try:
        # Use Hugging Face's FREE inference API (no key needed!)
        response = requests.post(
            "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
            json={"inputs": prompt, "parameters": {"max_length": 500, "temperature": 0.7}},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0].get('generated_text', '').replace(prompt, '').strip()
            elif isinstance(data, dict) and 'generated_text' in data:
                return data['generated_text'].replace(prompt, '').strip()
            else:
                return "I'm here to help! What would you like to know?"
        else:
            # Fallback: Use a simple rule-based response
            return generate_fallback_response(user_message)
            
    except Exception as e:
        # If API fails, use fallback
        return generate_fallback_response(user_message)

def generate_fallback_response(user_message):
    """Simple fallback responses when API is unavailable"""
    msg = user_message.lower()
    
    if "hello" in msg or "hi" in msg:
        return "Hello! How can I help you today?"
    elif "how are you" in msg:
        return "I'm doing great! Thanks for asking. How can I assist you?"
    elif "name" in msg:
        name = st.session_state.user_name or "you"
        return f"Your name is {name}! I'll remember that."
    elif "help" in msg:
        return """I can help you with:
- General questions and answers
- Coding and programming
- Writing and editing
- Learning new topics
- Remembering your preferences
- Web search using /search command

Try typing /help for all commands!"""
    elif "code" in msg or "programming" in msg:
        return """I can help you code in Python, JavaScript, HTML, CSS, and more!
Just ask me to write or explain code. For example:
"Write a Python function to reverse a string"
"Explain this JavaScript code" """
    elif "search" in msg:
        return "Use /search followed by your query to search the web! Example: /search latest AI news"
    elif "bye" in msg or "goodbye" in msg:
        return "Goodbye! Come back anytime you need help. Have a great day!"
    else:
        return f"""That's a great question! Let me think about it...

Here's what I can tell you about "{user_message[:50]}...":

I'm KingsBot, your AI assistant. I have:
- Memory of our conversations
- Ability to learn facts about you
- Web search capability (/search)
- Conversation history

If you want a more detailed answer, try:
1. Breaking down your question
2. Using /search to find information
3. Asking for code examples
4. Explaining what you need help with

What specific aspect would you like me to elaborate on?"""

# ============================================
# WEB SEARCH (FREE - No API Key!)
# ============================================

def web_search(query):
    """Perform web search using DuckDuckGo (FREE!)"""
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return f"🔍 Here's what I found about '{query}':\n\nTry searching Google directly for more results."
        
        data = response.json()
        results = "🔍 **Web Search Results:**\n\n"
        
        if data.get('Abstract'):
            results += f"**Summary:** {data['Abstract']}\n\n"
            if data.get('AbstractURL'):
                results += f"Source: {data['AbstractURL']}\n\n"
        
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
            results += f"No summary found. Here are some search suggestions:\n"
            results += f"- Search Google for: {query}\n"
            results += f"- Check Wikipedia: https://en.wikipedia.org/wiki/{query.replace(' ', '_')}\n"
            results += f"- Try DuckDuckGo: https://duckduckgo.com/?q={query}\n"
        
        return results
    except Exception as e:
        return f"🔍 Search error. Try Google directly: https://www.google.com/search?q={query.replace(' ', '+')}"

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

def extract_facts(user_msg, ai_response):
    combined = user_msg + " " + ai_response
    patterns = [
        r"my name is ([^\.]+)",
        r"i (?:am|'m) ([^\.]+)",
        r"i like ([^\.]+)",
        r"i work as ([^\.]+)",
        r"i live in ([^\.]+)",
        r"i have ([^\.]+)",
        r"i (?:love|enjoy) ([^\.]+)",
        r"my favorite ([^\.]+)"
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
• Name: {st.session_state.user_name or 'Not set'}
• Saved conversations: {len(st.session_state.conversations)}
• Model: FREE Hugging Face AI"""
    
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
            return web_search(query)
    
    elif cmd == '/help':
        return """📖 **Commands:**
/clear - Clear chat
/stats - Show stats
/name YourName - Set your name
/interest Hobby - Add interest
/facts - Show learned facts
/export - Download chat JSON
/search query - Web search (FREE!)
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
    
    st.success("✅ FREE AI: Active")
    st.info("🎯 No API Key Required!")
    st.caption("Powered by Hugging Face")
    
    st.divider()
    
    st.subheader("📊 Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💬 Messages", st.session_state.message_count)
    with col2:
        st.metric("📚 Facts", len(st.session_state.facts))
    
    st.metric("💾 Saved Chats", len(st.session_state.conversations))
    
    st.divider()
    
    if st.button("📦 Export All Data", use_container_width=True):
        export_data = {
            "export_date": datetime.now().isoformat(),
            "user_name": st.session_state.user_name,
            "interests": st.session_state.interests,
            "facts": st.session_state.facts,
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
st.markdown("#### Your FREE AI assistant with memory, voice, and web search")
st.caption("🎯 **100% FREE** · No API Key Required · Powered by Hugging Face")

tab1, tab2, tab3 = st.tabs(["💬 Chat", "📜 History", "🔍 Search"])

# ============================================
# TAB 1: CHAT
# ============================================
with tab1:
    chat_container = st.container(height=400)
    
    with chat_container:
        if not st.session_state.conversation:
            st.info("👋 Welcome to KingsBot! I'm 100% FREE - no API key needed! Start a conversation below.")
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
                
                response = call_free_ai(user_input)
                extract_facts(user_input, response)
                
                st.session_state.conversation.append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now().strftime('%I:%M %p')
                })
                st.session_state.message_count += 1
                
                save_conversation()
                
                if s
