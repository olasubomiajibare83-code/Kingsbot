import streamlit as st
import json
import time
from datetime import datetime
import requests
import re
import os

# Try to import Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    st.warning("⚠️ Groq package not installed. Run: pip install groq")

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="KingsBot AI - Groq Edition",
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
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'groq_api_key' not in st.session_state:
    st.session_state.groq_api_key = os.environ.get("GROQ_API_KEY", "")
if 'groq_model' not in st.session_state:
    st.session_state.groq_model = "llama-3.3-70b-versatile"

# ============================================
# GROQ AI FUNCTION
# ============================================

def call_groq_ai(user_message):
    """Call Groq API with memory and context"""
    
    if not st.session_state.groq_api_key:
        return "⚠️ Please enter your Groq API key in the sidebar.\n\nGet one for FREE at: https://console.groq.com/keys"
    
    if not GROQ_AVAILABLE:
        return "⚠️ Groq package not installed. Run: pip install groq"
    
    # Build context from conversation
    history = st.session_state.conversation[-6:] if st.session_state.conversation else []
    
    messages = []
    
    # System prompt with personalization
    system_prompt = "You are KingsBot, a helpful AI assistant with memory and personalization."
    if st.session_state.user_name:
        system_prompt += f"\nUser's name: {st.session_state.user_name}"
    if st.session_state.interests:
        system_prompt += f"\nUser's interests: {', '.join(st.session_state.interests)}"
    if st.session_state.facts:
        system_prompt += f"\nFacts about user: {'; '.join(st.session_state.facts)}"
    system_prompt += f"\nCurrent time: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    system_prompt += "\nBe concise, helpful, and remember what users tell you."
    system_prompt += "\nYou can code in any language, explain complex topics, and provide detailed answers."
    system_prompt += "\nIf you need to search the web, suggest the user uses /search."
    
    messages.append({"role": "system", "content": system_prompt})
    
    # Add conversation history
    for msg in history:
        messages.append({"role": msg['role'], "content": msg['content']})
    
    # Add current message
    messages.append({"role": "user", "content": user_message})
    
    try:
        client = Groq(api_key=st.session_state.groq_api_key)
        
        response = client.chat.completions.create(
            model=st.session_state.groq_model,
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=0.9,
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ Groq Error: {str(e)}\n\nTry:\n- Check your API key\n- Use a different model\n- Check rate limits (30/min free)"

def call_fallback_ai(user_message):
    """Fallback when Groq is unavailable"""
    msg = user_message.lower().strip()
    
    if msg in ["hello", "hi", "hey", "howdy"]:
        name = f" {st.session_state.user_name}" if st.session_state.user_name else ""
        return f"Hello{name}! 👋 Groq is currently unavailable, but I'm here to help!"
    
    if "how are you" in msg:
        return "I'm doing great! Thanks for asking. 😊"
    
    if "my name is" in msg:
        match = re.search(r"my name is ([a-z]+)", msg, re.IGNORECASE)
        if match:
            name = match.group(1).capitalize()
            st.session_state.user_name = name
            return f"Nice to meet you, {name}! 👍 I'll remember that."
    
    if "code" in msg or "python" in msg:
        return """Here's a Python example:

```python
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
```"""
    
    if "help" in msg:
        return """📖 **KingsBot Help**

**Commands:**
/help - Show this
/clear - Clear chat
/stats - Your stats
/name Name - Set your name
/interest Hobby - Add interest
/facts - What I know about you
/search query - Web search

**Features:**
🧠 Groq AI brain (Llama 3.3 70B)
💬 Memory & personalization
🔍 Web search
📜 History
🎤 Voice (HTML version)"""
    
    return f"That's interesting! 🤔 Tell me more about \"{user_message[:50]}...\""

# ============================================
# WEB SEARCH
# ============================================

def web_search(query):
    """Free web search using DuckDuckGo"""
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return f"🔍 Search results for: {query}\n\nTry: https://www.google.com/search?q={query.replace(' ', '+')}"
        
        data = response.json()
        results = f"🔍 **Search Results: {query}**\n\n"
        
        if data.get('Abstract'):
            results += f"📝 **Summary:** {data['Abstract']}\n\n"
            if data.get('AbstractURL'):
                results += f"🔗 Source: {data['AbstractURL']}\n\n"
        
        if data.get('RelatedTopics'):
            results += "📚 **Related Topics:**\n"
            count = 0
            for topic in data['RelatedTopics']:
                if count >= 5:
                    break
                if 'Text' in topic:
                    text = topic['Text'][:300]
                    results += f"• {text}\n"
                    if 'FirstURL' in topic:
                        results += f"  🔗 {topic['FirstURL']}\n"
                    results += "\n"
                    count += 1
        
        if not data.get('Abstract') and not data.get('RelatedTopics'):
            results += f"No summary available.\n\n🔗 Try Google: https://www.google.com/search?q={query.replace(' ', '+')}"
        
        return results
    except Exception as e:
        return f"🔍 Search error. Try: https://www.google.com/search?q={query.replace(' ', '+')}"

# ============================================
# HELPERS
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
• Facts: {len(st.session_state.facts)}
• Interests: {', '.join(st.session_state.interests) or 'None'}
• Name: {st.session_state.user_name or 'Not set'}
• Saved chats: {len(st.session_state.conversations)}
• Brain: Groq {st.session_state.groq_model}"""
    
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
/help - Show this help

🧠 Powered by **Groq AI** (Llama 3.3 70B)
⚡ Lightning fast! Up to 1000 tokens/sec
🆓 Free tier: 30 requests/min, 14,400/day"""
    
    return None

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/robot-2.png", width=64)
    st.title("⚙️ KingsBot")
    
    # Groq API Key
    groq_key = st.text_input(
        "🔑 Groq API Key",
        value=st.session_state.groq_api_key,
        type="password",
        help="Get FREE key at: https://console.groq.com/keys"
    )
    if groq_key != st.session_state.groq_api_key:
        st.session_state.groq_api_key = groq_key
    
    # Model Selection
    model = st.selectbox(
        "🧠 Model",
        options=[
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "llama-4-scout",
            "qwen-3-32b"
        ],
        index=0
    )
    if model != st.session_state.groq_model:
        st.session_state.groq_model = model
    
    if st.session_state.groq_api_key:
        st.success("✅ Groq Connected")
        st.caption(f"⚡ Model: {model}")
    else:
        st.warning("⚠️ No API Key")
        st.caption("Get FREE key at console.groq.com/keys")
    
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
st.title("🤖 KingsBot AI")
st.caption("⚡ Powered by **Groq** · Lightning Fast · 100% FREE")

tab1, tab2, tab3 = st.tabs(["💬 Chat", "📜 History", "🔍 Search"])

# ============================================
# CHAT TAB
# ============================================
with tab1:
    chat_container = st.container(height=400)
    
    with chat_container:
        if not st.session_state.conversation:
            st.info("👋 Welcome! Powered by Groq AI - Lightning Fast!")
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
            with st.spinner("⚡ Thinking..."):
                st.session_state.conversation.append({
                    'role': 'user',
                    'content': user_input,
                    'timestamp': datetime.now().strftime('%I:%M %p')
                })
                st.session_state.message_count += 1
                
                # Try Groq first, fallback if needed
                if st.session_state.groq_api_key and GROQ_AVAILABLE:
                    response = call_groq_ai(user_input)
                else:
                    response = call_fallback_ai(user_input)
                
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
st.caption("🤖 KingsBot | Powered by Groq AI | 100% FREE | Built with Streamlit")
