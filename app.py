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

# ============================================
# 🔑 YOUR GROQ API KEY - PASTE IT HERE!
# ============================================
GROQ_API_KEY = "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"  # <--- REPLACE WITH YOUR ACTUAL KEY!
# Get FREE key at: https://console.groq.com/keys
# ============================================

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
if 'current_conv_id' not in st.session_state:
    st.session_state.current_conv_id = str(int(time.time()))
if 'groq_model' not in st.session_state:
    st.session_state.groq_model = "llama-3.3-70b-versatile"

# ============================================
# GROQ AI FUNCTION
# ============================================

def call_groq_ai(user_message):
    """Call Groq API with full memory and context"""
    
    if not GROQ_API_KEY or GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
        return """⚠️ **Groq API Key Required!**

Please open the `app.py` file and replace `YOUR_GROQ_API_KEY_HERE` with your actual Groq API key.

Get your FREE key at: https://console.groq.com/keys

1. Sign up with email (no credit card needed)
2. Copy your API key
3. Replace `YOUR_GROQ_API_KEY_HERE` with your key
4. Redeploy or restart the app

Free tier: 30 requests/min, 14,400 requests/day"""
    
    if not GROQ_AVAILABLE:
        return "⚠️ Groq package not available. Deploy with requirements.txt"
    
    # Build context from conversation
    history = st.session_state.conversation[-8:] if st.session_state.conversation else []
    
    messages = []
    
    # System prompt with personalization
    system_prompt = """You are KingsBot, a powerful AI assistant with advanced capabilities.

CAPABILITIES:
- Code in any language (Python, JavaScript, Java, C++, etc.)
- Explain complex topics in simple terms
- Creative writing and problem solving
- Mathematical calculations and reasoning
- Detailed analysis and explanations

PERSONALIZATION:"""
    
    if st.session_state.user_name:
        system_prompt += f"\n- User's name: {st.session_state.user_name}"
    if st.session_state.interests:
        system_prompt += f"\n- User's interests: {', '.join(st.session_state.interests)}"
    if st.session_state.facts:
        system_prompt += f"\n- Facts about user: {'; '.join(st.session_state.facts)}"
    
    system_prompt += f"\n\nCurrent time: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    system_prompt += "\n\nINSTRUCTIONS:"
    system_prompt += "\n- Be concise but thorough"
    system_prompt += "\n- Provide code with explanations"
    system_prompt += "\n- Ask clarifying questions when needed"
    system_prompt += "\n- Remember previous conversations"
    system_prompt += "\n- If user asks for web search, suggest /search command"
    
    messages.append({"role": "system", "content": system_prompt})
    
    # Add conversation history
    for msg in history:
        messages.append({"role": msg['role'], "content": msg['content']})
    
    # Add current message
    messages.append({"role": "user", "content": user_message})
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        response = client.chat.completions.create(
            model=st.session_state.groq_model,
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            top_p=0.9,
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        error_msg = str(e)
        if "rate_limit" in error_msg.lower():
            return """⚠️ **Rate Limit Reached**

Free tier: 30 requests per minute
Wait a moment and try again.

💡 Upgrade or wait for reset."""
        elif "invalid" in error_msg.lower():
            return """⚠️ **Invalid API Key**

Please check your Groq API key:
1. Go to https://console.groq.com/keys
2. Create a new key
3. Replace `YOUR_GROQ_API_KEY_HERE` with your new key"""
        else:
            return f"❌ **Error:** {error_msg[:200]}"

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
            results += f"No summary available.\n\n🔗 Try Google: https://www.google.com/search?q={query.replace(' ', '+')}\n"
            results += f"📖 Try Wikipedia: https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
        
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
        return f"""📊 **Your Stats:**
• Messages: {st.session_state.message_count}
• Facts: {len(st.session_state.facts)}
• Interests: {', '.join(st.session_state.interests) or 'None'}
• Name: {st.session_state.user_name or 'Not set'}
• Saved chats: {len(st.session_state.conversations)}
• Brain: Groq {st.session_state.groq_model}
• Speed: Up to 1000 tokens/second"""
    
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
🆓 Free tier: 30 requests/min, 14,400/day

**Tips:**
• Just type anything - I'll answer like ChatGPT!
• Ask me to write code in any language
• Tell me about yourself - I'll remember
• Use /search to find information"""
    
    return None

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/robot-2.png", width=64)
    st.title("⚙️ KingsBot")
    
    # API Key Status
    if GROQ_API_KEY and GROQ_API_KEY != "YOUR_GROQ_API_KEY_HERE":
        st.success("✅ Groq API Key: Connected")
        st.caption(f"⚡ Model: {st.session_state.groq_model}")
        st.caption("🚀 Speed: Up to 1000 tokens/sec")
    else:
        st.error("❌ Groq API Key: Not Set")
        st.warning("Please add your API key in app.py")
        st.caption("Get FREE key at console.groq.com/keys")
        st.caption("No credit card needed!")
    
    # Model Selection
    model = st.selectbox(
        "🧠 Model",
        options=[
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "qwen-3-32b"
        ],
        index=0
    )
    if model != st.session_state.groq_model:
        st.session_state.groq_model = model
    
    st.divider()
    st.subheader("📊 Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💬 Messages", st.session_state.message_count)
    with col2:
        st.metric("📚 Facts", len(st.session_state.facts))
    st.metric("💾 Saved Chats", len(st.session_state.conversations))
    
    st.divider()
    
    if st.button("📦 Export Data", use_container_width=True):
        export_data = {
            "date": datetime.now().isoformat(),
            "name": st.session_state.user_name,
            "interests": st.session_state.interests,
            "facts": st.session_state.facts,
            "conversations": st.session_state.conversations,
            "current_conversation": st.session_state.conversation
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
# MAIN CONTENT
# ============================================
st.title("🤖 KingsBot AI")
st.caption("⚡ Powered by **Groq** · Lightning Fast · Advanced AI · 100% FREE")

# Create tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "📜 History", "🔍 Search"])

# ============================================
# CHAT TAB
# ============================================
with tab1:
    chat_container = st.container(height=400)
    
    with chat_container:
        if not st.session_state.conversation:
            st.info("👋 Welcome! I'm KingsBot with Groq AI - Lightning Fast!")
            st.caption("💡 Just type anything like ChatGPT, but faster!")
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
            placeholder="Ask me anything... (like ChatGPT!)",
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
                
                response = call_groq_ai(user_input)
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
                    <div style="background:#21262d;padding:10px;border-radius:8px;margin:4px 0;">
                        <div style="font-size:11px;color:#8b949e;">📅 {datetime.fromisoformat(conv['date']).strftime('%B %d, %I:%M %p')}</div>
                        <div style="font-size:13px;">{conv['preview']}</div>
                        <div style="font-size:11px;color:#8b949e;">💬 {conv['message_count']} msgs</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("📂 Load", key=f"load_{conv['id']}"):
                        load_conversation(conv['id'])

# ============================================
# SEARCH TAB
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
                        'content': msg['content'][:300],
                        'role': msg['role'],
                        'preview': msg['content'][:200] + ('...' if len(msg['content']) > 200 else '')
                    })
        
        if not results:
            st.info("🔍 No results found.")
        else:
            st.success(f"✅ Found {len(results)} results")
            for result in results[:20]:
                st.markdown(f"**{result['role']}** ({result['date'][:16]}): {result['preview']}")
                if st.button("📂 Load", key=f"search_load_{result['conv_id']}"):
                    load_conversation(result['conv_id'])

# ============================================
# FOOTER
# ============================================
st.divider()
st.caption("🤖 KingsBot | Powered by Groq AI | 100% FREE | Built with Streamlit")
