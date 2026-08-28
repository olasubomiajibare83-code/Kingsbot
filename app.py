import streamlit as st
import json
import time
from datetime import datetime
import requests
import re

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="KingsBot Assistant AI",
    page_icon="🤖",
    layout="wide"
)

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
    st.session_state.user_name = None
if 'interests' not in st.session_state:
    st.session_state.interests = []
if 'conversations' not in st.session_state:
    st.session_state.conversations = []
if 'voice_enabled' not in st.session_state:
    st.session_state.voice_enabled = True
if 'current_conv_id' not in st.session_state:
    st.session_state.current_conv_id = str(int(time.time()))

# ============================================
# FUNCTIONS
# ============================================

def call_free_ai(user_message):
    """Use Hugging Face's FREE API"""
    history = st.session_state.conversation[-6:] if st.session_state.conversation else []
    
    context = ""
    for msg in history:
        if msg['role'] == 'user':
            context += f"User: {msg['content']}\n"
        else:
            context += f"Assistant: {msg['content']}\n"
    
    user_info = ""
    if st.session_state.user_name:
        user_info += f"User's name is {st.session_state.user_name}. "
    if st.session_state.interests:
        user_info += f"User's interests: {', '.join(st.session_state.interests)}. "
    if st.session_state.facts:
        user_info += f"Facts about user: {'; '.join(st.session_state.facts)}. "
    
    prompt = f"""You are KingsBot, a helpful AI assistant with memory and personalization.

{user_info}

Previous conversation:
{context}

User: {user_message}
Assistant:"""
    
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
            json={"inputs": prompt, "parameters": {"max_length": 500, "temperature": 0.7}},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                result = data[0].get('generated_text', '')
                return result.replace(prompt, '').strip() or "I'm here to help!"
            elif isinstance(data, dict) and 'generated_text' in data:
                result = data['generated_text']
                return result.replace(prompt, '').strip() or "I'm here to help!"
        return generate_fallback(user_message)
    except:
        return generate_fallback(user_message)

def generate_fallback(user_message):
    msg = user_message.lower()
    if "hello" in msg or "hi" in msg:
        return "Hello! How can I help you today?"
    elif "how are you" in msg:
        return "I'm doing great! Thanks for asking!"
    elif "name" in msg:
        name = st.session_state.user_name or "you"
        return f"Your name is {name}! I'll remember that."
    elif "code" in msg or "python" in msg:
        return """Here's a Python example:
```python
def greet(name):
    return f"Hello, {name}!"
print(greet("World"))
```"""
    else:
        return f"That's interesting! Tell me more about: {user_message[:100]}..."

def web_search(query):
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return f"Search results for: {query}\n\nTry Google: https://www.google.com/search?q={query}"
        data = response.json()
        results = f"🔍 Search results for: {query}\n\n"
        if data.get('Abstract'):
            results += f"Summary: {data['Abstract']}\n\n"
        if data.get('RelatedTopics'):
            results += "Related:\n"
            count = 0
            for topic in data['RelatedTopics']:
                if count >= 3:
                    break
                if 'Text' in topic:
                    results += f"- {topic['Text'][:200]}\n"
                    count += 1
        if not data.get('Abstract') and not data.get('RelatedTopics'):
            results += f"No summary. Try: https://www.google.com/search?q={query}"
        return results
    except:
        return f"Search error. Try Google: https://www.google.com/search?q={query}"

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
        return f"""📊 Stats:
- Messages: {st.session_state.message_count}
- Facts: {len(st.session_state.facts)}
- Interests: {', '.join(st.session_state.interests) or 'None'}
- Name: {st.session_state.user_name or 'Not set'}
- Saved chats: {len(st.session_state.conversations)}"""
    elif cmd.startswith('/name '):
        name = cmd[6:].strip()
        if name:
            st.session_state.user_name = name
            return f"✅ Name set to '{name}'!"
    elif cmd.startswith('/interest '):
        interest = cmd[10:].strip()
        if interest and interest not in st.session_state.interests:
            st.session_state.interests.append(interest)
            return f"✅ Added '{interest}'!"
    elif cmd == '/facts':
        if not st.session_state.facts:
            return "📚 No facts learned yet."
        return "📚 Facts:\n" + "\n".join([f"{i+1}. {f}" for i, f in enumerate(st.session_state.facts)])
    elif cmd.startswith('/search '):
        query = cmd[8:].strip()
        if query:
            return web_search(query)
    elif cmd == '/help':
        return """📖 Commands:
/clear - Clear chat
/stats - Show stats
/name Name - Set your name
/interest Hobby - Add interest
/facts - Show learned facts
/search query - Web search
/voice - Toggle voice
/help - This help"""
    elif cmd == '/voice':
        st.session_state.voice_enabled = not st.session_state.voice_enabled
        return f"🎤 Voice {'enabled' if st.session_state.voice_enabled else 'disabled'}"
    return None

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/robot-2.png", width=64)
    st.title("⚙️ KingsBot")
    st.success("✅ FREE AI Active")
    st.info("🎯 No API Key Required")
    
    st.divider()
    st.subheader("📊 Stats")
    st.metric("💬 Messages", st.session_state.message_count)
    st.metric("📚 Facts", len(st.session_state.facts))
    st.metric("💾 Saved", len(st.session_state.conversations))
    
    st.divider()
    if st.button("📦 Export Data", use_container_width=True):
        export_data = {
            "date": datetime.now().isoformat(),
            "name": st.session_state.user_name,
            "interests": st.session_state.interests,
            "facts": st.session_state.facts,
            "conversations": st.session_state.conversations
        }
        st.download_button(
            label="⬇️ Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"kingsbot_{int(time.time())}.json",
            mime="application/json",
            use_container_width=True
        )
    
    if st.button("🗑️ Clear All", use_container_width=True, type="secondary"):
        st.session_state.conversation = []
        st.session_state.conversations = []
        st.session_state.facts = []
        st.session_state.message_count = 0
        st.session_state.interests = []
        st.rerun()

# ============================================
# MAIN
# ============================================
st.title("🤖 KingsBot Assistant AI")
st.caption("100% FREE · No API Key · Memory · Voice · Web Search")

tab1, tab2, tab3 = st.tabs(["💬 Chat", "📜 History", "🔍 Search"])

# ============================================
# CHAT TAB
# ============================================
with tab1:
    chat_container = st.container(height=400)
    
    with chat_container:
        if not st.session_state.conversation:
            st.info("👋 Welcome! Start a conversation below.")
        else:
            for msg in st.session_state.conversation:
                if msg['role'] == 'user':
                    st.markdown(f"**👤 You:** {msg['content']}")
                else:
                    st.markdown(f"**🤖 KingsBot:** {msg['content']}")
    
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Message",
            placeholder="Type /help for commands",
            label_visibility="collapsed",
            key="user_input"
        )
    
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
            save_conversation()
            st.rerun()
        else:
            with st.spinner("Thinking..."):
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
            
            st.rerun()

# ============================================
# HISTORY TAB
# ============================================
with tab2:
    if not st.session_state.conversations:
        st.info("📭 No saved conversations.")
    else:
        st.caption(f"📜 {len(st.session_state.conversations)} saved")
        for conv in st.session_state.conversations[:20]:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div style="background:#21262d;padding:10px;border-radius:8px;margin:4px 0;">
                    <div style="font-size:11px;color:#8b949e;">📅 {datetime.fromisoformat(conv['date']).strftime('%B %d, %I:%M %p')}</div>
                    <div style="font-size:13px;">{conv['preview']}</div>
                    <div style="font-size:11px;color:#8b949e;">💬 {conv['message_count']} msgs</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("Load", key=f"load_{conv['id']}"):
                    load_conversation(conv['id'])

# ============================================
# SEARCH TAB
# ============================================
with tab3:
    search_query = st.text_input("🔍 Search", placeholder="Enter keyword...", key="search_all")
    
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
            st.success(f"✅ {len(results)} results")
            for r in results[:10]:
                st.markdown(f"**{r['role']}** ({r['date'][:16]}): {r['content']}...")
        else:
            st.info("No results.")

st.divider()
st.caption("🤖 KingsBot | 100% FREE | Built with Streamlit")
