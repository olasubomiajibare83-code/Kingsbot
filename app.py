import streamlit as st
import sqlite3
import hashlib
import json
import os
import requests
import time
from datetime import datetime

st.set_page_config(
    page_title="VoiceAI Platform",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "voiceai.db"

# ⚠️ CHANGE THIS TO YOUR EMAIL
OWNER_EMAILS = ["your-email@gmail.com"]

COST_PER_MINUTE = 0.05
FREE_SIGNUP_CREDITS = 10.00

# ============================================================
# DATABASE
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            is_owner INTEGER DEFAULT 0,
            credit_balance REAL DEFAULT 0,
            total_spent REAL DEFAULT 0,
            total_minutes REAL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            llm_model TEXT DEFAULT 'llama-3.3-70b',
            voice_id TEXT DEFAULT 'Cartesia',
            language TEXT DEFAULT 'en-US',
            temperature REAL DEFAULT 0.7,
            first_message TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_bases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            content TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def migrate_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA table_info(agents)")
    cols = [row[1] for row in c.fetchall()]
    for col, default in [("temperature", "0.7"), ("voice_id", "'Cartesia'"), ("language", "'en-US'"), ("first_message", "''")]:
        if col not in cols:
            try:
                c.execute(f"ALTER TABLE agents ADD COLUMN {col} DEFAULT {default}")
            except:
                pass
    conn.commit()
    conn.close()

init_db()
migrate_db()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def is_owner_email(email):
    return email.lower() in [e.lower() for e in OWNER_EMAILS]

# ============================================================
# FREE AI — Pollinations (no key, no blocking)
# ============================================================
def pollinations_chat(messages, temperature=0.7):
    """Call Pollinations AI — completely free, no API key, no blocking."""
    try:
        # Build prompt from messages
        prompt = ""
        for m in messages:
            if m["role"] == "system":
                prompt += f"{m['content']}\n\n"
            elif m["role"] == "user":
                prompt += f"User: {m['content']}\n"
            elif m["role"] == "assistant":
                prompt += f"Assistant: {m['content']}\n"
        prompt += "Assistant:"
        
        url = "https://text.pollinations.ai/openai"
        payload = {
            "model": "openai",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1000
        }
        
        r = requests.post(url, json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
        
        # Fallback: try the simple endpoint
        url2 = f"https://text.pollinations.ai/{requests.utils.quote(prompt)}"
        r2 = requests.get(url2, timeout=60)
        if r2.status_code == 200:
            return r2.text
        
        return f"❌ AI service returned {r.status_code}. Try again."
    except Exception as e:
        return f"❌ Connection error: {str(e)}"

# ============================================================
# SESSION STATE
# ============================================================
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "name" not in st.session_state:
    st.session_state.name = None
if "is_owner" not in st.session_state:
    st.session_state.is_owner = False
if "page" not in st.session_state:
    st.session_state.page = "🏠 Dashboard"

# ============================================================
# AUTH PAGE
# ============================================================
def auth_page():
    st.markdown("""
    <div style="text-align:center; padding:40px 0;">
        <h1 style="font-size:48px; margin:0;">🎙️ VoiceAI Platform</h1>
        <p style="opacity:0.7; font-size:18px; margin-top:10px;">
            Build AI voice agents that sound human.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Log In", "✨ Sign Up"])
        
        with tab1:
            with st.form("login"):
                u = st.text_input("Username or Email")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Log In", use_container_width=True):
                    if not u or not p:
                        st.error("Please fill all fields")
                    else:
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""SELECT id, name, is_owner FROM users 
                            WHERE (username = ? OR email = ?) AND password_hash = ?""", (u, u, hash_pw(p)))
                        user = c.fetchone()
                        conn.close()
                        if user:
                            st.session_state.user_id = user["id"]
                            st.session_state.name = user["name"] or u
                            st.session_state.is_owner = bool(user["is_owner"])
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Try signing up first.")
            
            st.markdown("---")
            st.caption("🔵 Google Sign-In requires OAuth setup")
            st.button("Sign in with Google", disabled=True, use_container_width=True)
        
        with tab2:
            with st.form("signup"):
                n = st.text_input("Full Name")
                u = st.text_input("Username")
                e = st.text_input("Email")
                p = st.text_input("Password", type="password")
                p2 = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    if not u or not e or not p:
                        st.error("Please fill all fields")
                    elif p != p2:
                        st.error("Passwords don't match")
                    elif len(p) < 6:
                        st.error("Password must be 6+ characters")
                    else:
                        try:
                            owner = 1 if is_owner_email(e) else 0
                            credits = 999999.99 if owner else FREE_SIGNUP_CREDITS
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("""INSERT INTO users 
                                (username, email, password_hash, name, is_owner, credit_balance, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                (u, e, hash_pw(p), n, owner, credits, datetime.now().isoformat()))
                            conn.commit()
                            conn.close()
                            if owner:
                                st.success("👑 Owner account created with unlimited credits!")
                            else:
                                st.success(f"✅ Account created with ${FREE_SIGNUP_CREDITS:.2f} free credits!")
                        except sqlite3.IntegrityError:
                            st.error("Username or email already exists")

# ============================================================
# MAIN APP
# ============================================================
def main_app():
    user_id = st.session_state.user_id
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        st.session_state.user_id = None
        st.rerun()
        return
    
    is_owner = bool(user["is_owner"])
    
    with st.sidebar:
        st.markdown("### 🎙️ VoiceAI")
        st.caption(f"👤 {user['name']}")
        
        if is_owner:
            st.success("👑 OWNER")
            st.caption("♾️ Unlimited credits")
        else:
            st.metric("💰 Balance", f"${user['credit_balance']:.2f}")
        
        st.divider()
        pages = ["🏠 Dashboard", "🤖 Agents", "💬 Playground", "📚 Knowledge Base", "📊 Analytics", "💳 Billing", "⚙️ Settings"]
        current_idx = pages.index(st.session_state.page) if st.session_state.page in pages else 0
        selected_page = st.radio("Navigation", pages, index=current_idx, label_visibility="collapsed")
        st.session_state.page = selected_page
        st.divider()
        if st.button("🚪 Log Out", use_container_width=True):
            for k in ["user_id", "name", "is_owner", "playground_messages", "playground_agent", "page"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
    
    # ========================================================
    # DASHBOARD
    # ========================================================
    if st.session_state.page == "🏠 Dashboard":
        st.title(f"Welcome back, {user['name']} 👋")
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as x FROM agents WHERE user_id = ?", (user_id,))
        agent_count = c.fetchone()["x"]
        c.execute("SELECT COUNT(*) as x FROM knowledge_bases WHERE user_id = ?", (user_id,))
        kb_count = c.fetchone()["x"]
        c.execute("SELECT COUNT(*) as x FROM conversations WHERE user_id = ?", (user_id,))
        conv_count = c.fetchone()["x"]
        conn.close()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🤖 Agents", agent_count)
        c2.metric("📚 Knowledge Bases", kb_count)
        c3.metric("💬 Conversations", conv_count)
        c4.metric("💰 Credits", "♾️ Unlimited" if is_owner else f"${user['credit_balance']:.2f}")
        
        st.divider()
        st.subheader("🚀 Get Started")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info("**1. Create Agent**\n\nSet up your first voice agent")
        with c2:
            st.info("**2. Test Playground**\n\nChat with your agent")
        with c3:
            st.info("**3. Add Knowledge**\n\nGive your agent context")
    
    # ========================================================
    # AGENTS
    # ========================================================
    elif st.session_state.page == "🤖 Agents":
        st.title("Voice Agents")
        st.caption("Create and manage AI voice agents")
        
        with st.expander("➕ Create New Agent", expanded=False):
            with st.form("new_agent"):
                agent_name = st.text_input("Agent Name", placeholder="e.g. Customer Support")
                first_message = st.text_input("First Message", placeholder="Hello! How can I help you today?", value="Hello! How can I help you today?")
                prompt = st.text_area("System Prompt", height=180, value="""You are a helpful voice assistant.

Rules:
- Keep responses short (1-3 sentences)
- Be polite and professional
- Ask clarifying questions when needed
- Never make up information""")
                
                c1, c2 = st.columns(2)
                with c1:
                    model = st.selectbox("LLM Model", ["llama-3.3-70b", "gpt-4o-mini", "claude-4.5-sonnet", "gemini-3-flash"])
                    language = st.selectbox("Language", ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "pt-BR", "hi-IN"])
                with c2:
                    voice = st.selectbox("Voice Provider", ["Cartesia", "ElevenLabs", "Minimax", "OpenAI"])
                    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
                
                if st.form_submit_button("🚀 Create Agent", use_container_width=True):
                    if not agent_name:
                        st.error("Please enter a name")
                    else:
                        try:
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("""INSERT INTO agents 
                                (user_id, name, system_prompt, llm_model, voice_id, language, temperature, first_message, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (user_id, agent_name, prompt, model, voice, language, temperature, first_message, datetime.now().isoformat()))
                            conn.commit()
                            conn.close()
                            st.success(f"✅ Agent '{agent_name}' created!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        st.divider()
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM agents WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        agents = c.fetchall()
        conn.close()
        
        if not agents:
            st.info("No agents yet. Create your first one above!")
        else:
            for a in agents:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.subheader(f"🎙️ {a['name']}")
                        st.caption(f"`{a['llm_model']}` • `{a['voice_id']}` • `{a['language']}`")
                    with c2:
                        if st.button("💬 Test", key=f"test_{a['id']}", use_container_width=True):
                            st.session_state.playground_agent = a['id']
                            st.session_state.page = "💬 Playground"
                            st.rerun()
                    with c3:
                        if st.button("🗑️", key=f"del_{a['id']}", use_container_width=True):
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("DELETE FROM agents WHERE id = ?", (a['id'],))
                            conn.commit()
                            conn.close()
                            st.rerun()
                    with st.expander("View Prompt"):
                        st.text(a['system_prompt'])
    
    # ========================================================
    # PLAYGROUND
    # ========================================================
    elif st.session_state.page == "💬 Playground":
        st.title("💬 Agent Playground")
        st.caption("Test your agent in real-time")
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM agents WHERE user_id = ?", (user_id,))
        agents = c.fetchall()
        conn.close()
        
        if not agents:
            st.warning("Create an agent first to test it!")
            if st.button("➕ Create Agent"):
                st.session_state.page = "🤖 Agents"
                st.rerun()
            return
        
        agent_options = {f"{a['name']}": a for a in agents}
        default_idx = 0
        if "playground_agent" in st.session_state:
            for i, a in enumerate(agents):
                if a['id'] == st.session_state.playground_agent:
                    default_idx = i
                    break
        
        selected_name = st.selectbox("🤖 Select Agent to Test", list(agent_options.keys()), index=default_idx)
        selected_agent = agent_options[selected_name]
        
        with st.sidebar:
            st.divider()
            st.subheader("⚙️ Test Controls")
            if st.button("🗑️ Clear Conversation", use_container_width=True):
                st.session_state.playground_messages = []
                st.rerun()
            st.caption("**Agent Config**")
            st.write(f"Model: `{selected_agent['llm_model']}`")
            st.write(f"Voice: `{selected_agent['voice_id']}`")
            st.write(f"Language: `{selected_agent['language']}`")
            st.write(f"Temperature: `{selected_agent['temperature']}`")
        
        if "playground_messages" not in st.session_state:
            st.session_state.playground_messages = []
        if "playground_agent" not in st.session_state or st.session_state.playground_agent != selected_agent['id']:
            st.session_state.playground_messages = []
            st.session_state.playground_agent = selected_agent['id']
        
        for msg in st.session_state.playground_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        if prompt := st.chat_input(f"Message {selected_agent['name']}..."):
            st.session_state.playground_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("🧠 Agent is thinking..."):
                    messages = [{"role": "system", "content": selected_agent['system_prompt']}]
                    messages.extend(st.session_state.playground_messages[-10:])
                    
                    response = pollinations_chat(messages, selected_agent.get('temperature', 0.7))
                    st.write(response)
                    
                    st.session_state.playground_messages.append({"role": "assistant", "content": response})
                    
                    try:
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""INSERT INTO conversations (agent_id, user_id, title, created_at)
                            VALUES (?, ?, ?, ?)""", (selected_agent['id'], user_id, prompt[:50], datetime.now().isoformat()))
                        conv_id = c.lastrowid
                        for m in st.session_state.playground_messages[-2:]:
                            c.execute("""INSERT INTO messages (conversation_id, role, content, created_at)
                                VALUES (?, ?, ?, ?)""", (conv_id, m["role"], m["content"], datetime.now().isoformat()))
                        conn.commit()
                        conn.close()
                    except:
                        pass
    
    # ========================================================
    # KNOWLEDGE BASE
    # ========================================================
    elif st.session_state.page == "📚 Knowledge Base":
        st.title("Knowledge Base")
        st.caption("Add context for your agents")
        
        with st.form("new_kb"):
            kb_name = st.text_input("Name")
            kb_content = st.text_area("Content", height=200)
            if st.form_submit_button("💾 Save", use_container_width=True):
                if not kb_name:
                    st.error("Please enter a name")
                else:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""INSERT INTO knowledge_bases (user_id, name, content, created_at)
                        VALUES (?, ?, ?, ?)""", (user_id, kb_name, kb_content, datetime.now().isoformat()))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ '{kb_name}' saved!")
                    st.rerun()
        
        st.divider()
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM knowledge_bases WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        kbs = c.fetchall()
        conn.close()
        
        if not kbs:
            st.info("No knowledge bases yet.")
        else:
            for kb in kbs:
                with st.expander(f"📚 {kb['name']}"):
                    st.caption(f"Added: {kb['created_at'][:19]}")
                    st.text(kb['content'][:500] if kb['content'] else "")
                    if st.button("🗑️ Delete", key=f"dk_{kb['id']}"):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("DELETE FROM knowledge_bases WHERE id = ?", (kb['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()
    
    # ========================================================
    # ANALYTICS
    # ========================================================
    elif st.session_state.page == "📊 Analytics":
        st.title("Analytics")
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as x FROM conversations WHERE user_id = ?", (user_id,))
        total = c.fetchone()["x"]
        conn.close()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Conversations", total)
        c2.metric("Minutes Used", f"{user['total_minutes']:.1f}")
        c3.metric("Credits Spent", f"${user['total_spent']:.2f}")
        
        st.divider()
        st.subheader("Recent Conversations")
        
        conn = get_db()
        c = conn.cursor()
        c.execute("""SELECT conv.*, a.name as agent_name FROM conversations conv
            LEFT JOIN agents a ON conv.agent_id = a.id
            WHERE conv.user_id = ? ORDER BY conv.created_at DESC LIMIT 20""", (user_id,))
        convs = c.fetchall()
        conn.close()
        
        if not convs:
            st.info("No conversations yet.")
        else:
            for conv in convs:
                with st.expander(f"💬 {conv['agent_name']} — {conv['created_at'][:19]}"):
                    st.write(f"**Title:** {conv['title']}")
    
    # ========================================================
    # BILLING
    # ========================================================
    elif st.session_state.page == "💳 Billing":
        st.title("Billing & Credits")
        
        if is_owner:
            st.success("👑 Owner Account — Unlimited Free Credits")
            
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as x FROM users WHERE is_owner = 0")
            total_users = c.fetchone()["x"]
            c.execute("SELECT SUM(total_spent) as r FROM users WHERE is_owner = 0")
            revenue = c.fetchone()["r"] or 0
            conn.close()
            
            c1, c2 = st.columns(2)
            c1.metric("👥 Paying Users", total_users)
            c2.metric("💰 Total Revenue", f"${revenue:.2f}")
        else:
            st.metric("💰 Credit Balance", f"${user['credit_balance']:.2f}")
            st.caption(f"Rate: ${COST_PER_MINUTE:.2f} per minute")
            
            st.divider()
            st.subheader("Buy Credits")
            cols = st.columns(4)
            for col, (amount, label) in zip(cols, [(10, "Starter"), (25, "Popular"), (50, "Pro"), (100, "Business")]):
                with col:
                    st.markdown(f"### ${amount}")
                    st.caption(label)
                    st.caption(f"{amount/COST_PER_MINUTE:.0f} min")
                    if st.button(f"Buy ${amount}", key=f"buy_{amount}", use_container_width=True):
                        st.info("🔗 Payment gateway would open here")
            
            st.divider()
            st.subheader("Transaction History")
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50", (user_id,))
            txs = c.fetchall()
            conn.close()
            
            if not txs:
                st.info("No transactions yet.")
            else:
                for tx in txs:
                    emoji = "💚" if tx["amount"] > 0 else "💸"
                    st.write(f"{emoji} **${abs(tx['amount']):.2f}** — {tx['type'].title()} — {tx['description']}")
    
    # ========================================================
    # SETTINGS
    # ========================================================
    elif st.session_state.page == "⚙️ Settings":
        st.title("Settings")
        
        st.subheader("Account")
        st.write(f"**Name:** {user['name']}")
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Role:** {'👑 Owner' if is_owner else '👤 User'}")
        
        st.divider()
        st.subheader("🔑 Bring Your Own Keys (BYOK)")
        st.text_input("OpenAI API Key", type="password", key="k_openai")
        st.text_input("ElevenLabs API Key", type="password", key="k_11")
        st.text_input("Cartesia API Key", type="password", key="k_cart")
        st.text_input("Twilio Account SID", type="password", key="k_tw")
        
        if st.button("💾 Save Keys"):
            st.success("Keys saved to session.")

# ============================================================
# ROUTER
# ============================================================
if st.session_state.user_id is None:
    auth_page()
else:
    main_app()
