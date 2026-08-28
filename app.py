import streamlit as st
import openai
import json
import time
from datetime import datetime
import requests
import re

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="KingsBot",
    page_icon="🤖",
    layout="wide"
)

# ============================================
# SIMPLE CSS (No complex nested quotes)
# ============================================
st.markdown("""
<style>
    .chat-msg { margin: 10px 0; padding: 10px 15px; border-radius: 10px; }
    .user { background: #238636; color: white; text-align: right; }
    .bot { background: #2d333b; color: #e6edf3; }
    .time { font-size: 10px; color: #8b949e; }
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'message_count' not in st.session_state:
    st.session_state.message_count = 0
if 'facts' not in st.session_state:
    st.session_state.facts = []
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'interests' not in st.session_state:
    st.session_state.interests = []
if 'conversations' not in st.session_state:
    st.session_state.conversations = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'model' not in st.session_state:
    st.session_state.model = "gpt-3.5-turbo"
if 'web_search_key' not in st.session_state:
    st.session_state.web_search_key = ""
if 'search_engine_id' not in st.session_state:
    st.session_state.search_engine_id = ""

# ============================================
# FUNCTIONS
# ============================================

def save_conversation():
    if len(st.session_state.conversation) > 0:
        conv_data = {
            'id': st.session_state.current_conv_id,
            'date': datetime.now().isoformat(),
            'messages': st.session_state.conversation.copy(),
            'message_count': len(st.session_state.conversation),
            'preview': st.session_state.conversation[0]['content'][:60]
        }
        st.session_state.conversations.insert(0, conv_data)
        if len(st.session_state.conversations) > 50:
            st.session_state.conversations = st.session_state.conversations[:50]

def call_openai(user_message):
    if not st.session_state.api_key:
        return "⚠️ Please enter your OpenAI API key in the sidebar."
    
    messages = [{"role": "system", "content": "You are KingsBot, a helpful AI assistant."}]
    
    for msg in st.session_state.conversation[-10:]:
        messages.append({"role": msg['role'], "content": msg['content']})
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        client = openai.OpenAI(api_key=st.session_state.api_key)
        response = client.chat.completions.create(
            model=st.session_state.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {str(e)}"

def web_search(query):
    if not st.session_state.web_search_key:
        return "⚠️ Google Search API key not set."
    if not st.session_state.search_engine_id:
        return "⚠️ Search Engine ID not set."
    
    try:
        url = f"https://www.googleapis.com/customsearch/v1?key={st.session_state.web_search_key}&cx={st.session_state.search_engine_id}&q={query}&num=5"
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
    combined = user_msg + " " + ai_response
    patterns = [
        r"my name is ([^\.]+)",
        r"i (?:am|'m) ([^\.]+)",
        r"i like ([^\.]+)",
        r"i work as ([^\.]+)"
    ]
    new_facts = []
    for pattern in patterns:
        matches = re.findall(pattern, combined, re.IGNORECASE)
        for match in matches:
            fact = match.strip()
            if len(fact) > 3 and fact not in st.session_state.facts:
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
- Messages: {st.session_state.message_count}
- Facts: {len(st.session_state.facts)}
- Interests: {', '.join(st.session_state.interests) or 'None'}
- Name: {st.session_state.user_name or 'Not set'}"""
    
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
            return "📚 No facts learned yet."
        return "📚 **Facts I know:**\n" + "\n".join([f"{i+1}. {f}" for i, f in enumerate(st.session_state.facts)])
    
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
/search query - Web search
/help - Show this help"""
    
    return None

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.title("⚙️ Settings")
    
    st.text_input("🔑 OpenAI API Key", key="api_key", type="password")
    st.selectbox("🧠 Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"], key="model")
    
    st.divider()
    st.subheader("🔍 Web Search (Optional)")
    st.text_input("Google API Key", key="web_search_key", type="password")
    st.text_input("Search Engine ID", key="search_engine_id")
    
    st.divider()
    st.metric("💬 Messages", st.session_state.message_count)
    st.metric("📚 Facts", len(st.session_state.facts))
    
    if st.button("🗑️ Clear All Data"):
        st.session_state.conversation = []
        st.session_state.conversations = []
        st.session_state.facts = []
        st.session_state.message_count = 0
        st.rerun()

# ============================================
# MAIN
# ============================================
st.title("🤖 KingsBot Assistant")
st.caption("AI assistant with memory and web search")

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📜 History", "🔍 Search"])

# ============================================
# TAB 1: CHAT
# ============================================
with tab1:
    chat_container = st.container(height=400)
    
    with chat_container:
        if not st.session_state.conversation:
            st.info("👋 Start a conversation!")
        else:
            for msg in st.session_state.conversation:
                if msg['role'] == 'user':
                    st.markdown(f'<div class="chat-msg user">👤 {msg["content"]}<div class="time">{msg.get("timestamp", "")}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-msg bot">🤖 {msg["content"]}<div class="time">{msg.get("timestamp", "")}</div></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input("Message", placeholder="Type /help for commands", key="user_input", label_visibility="collapsed")
    
    with col2:
        send_button = st.button("Send", use_container_width=True)
    
    if send_button and user_input:
        command_result = handle_command(user_input)
        
        if command_result:
            st.session_state.conversation.append({
                'role': 'assistant',
                'content': command_result,
                'timestamp': datetime.now().strftime('%I:%M %p')
            })
            st.session_state.message_count += 1
            st.rerun()
        else:
            with st.spinner("Thinking..."):
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
            
            st.rerun()

# ============================================
# TAB 2: HISTORY
# ============================================
with tab2:
    if not st.session_state.conversations:
        st.info("📭 No saved conversations.")
    else:
        for i, conv in enumerate(st.session_state.conversations[:20]):
            with st.expander(f"📅 {conv['date'][:16]} - {conv['preview']}"):
                for msg in conv['messages'][-5:]:
                    st.write(f"**{msg['role']}:** {msg['content'][:200]}...")
                if st.button("Load", key=f"load_{i}"):
                    st.session_state.conversation = conv['messages'].copy()
                    st.rerun()

# ============================================
# TAB 3: SEARCH
# ============================================
with tab3:
    search_query = st.text_input("🔍 Search conversations", placeholder="Enter keyword...", key="search_all")
    
    if search_query and len(search_query) > 1:
        results = []
        for conv in st.session_state.conversations:
            for msg in conv['messages']:
                if search_query.lower() in msg['content'].lower():
                    results.append({
                        'date': conv['date'],
                        'content': msg['content'][:300],
                        'role': msg['role']
                    })
        
        if results:
            st.success(f"✅ Found {len(results)} results")
            for result in results[:10]:
                st.markdown(f"**{result['role']}** ({result['date'][:16]}): {result['content']}...")
        else:
            st.info("No results found.")

st.divider()
st.caption("🤖 KingsBot AI Assistant")
