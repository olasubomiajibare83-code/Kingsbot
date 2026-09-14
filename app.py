import streamlit as st
import sqlite3
import hashlib
import json
import requests
import time
from datetime import datetime

st.set_page_config(
    page_title="AI Agent Platform",
    page_icon="🤖",
    layout="wide"
)

DB_FILE = "agents.db"

# ⚠️ CHANGE THIS TO YOUR EMAIL
OWNER_EMAILS = ["ajibaretemiloluwa@gmail.com"]

# ============================================================
# DATABASE
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT,
        is_owner INTEGER DEFAULT 0,
        created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        system_prompt TEXT NOT NULL,
        created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        agent_id INTEGER NOT NULL,
        title TEXT,
        created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL)""")
    conn.commit()
    conn.close()

def migrate_db():
    """Add missing columns to old database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA table_info(agents)")
    cols = [row[1] for row in c.fetchall()]
    if "description" not in cols:
        try:
            c.execute("ALTER TABLE agents ADD COLUMN description TEXT")
        except:
            pass
    conn.commit()
    conn.close()

def fix_owners():
    """Auto-promote owner emails."""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        for email in OWNER_EMAILS:
            c.execute("UPDATE users SET is_owner = 1 WHERE LOWER(email) = LOWER(?)", (email,))
        conn.commit()
        conn.close()
    except:
        pass

init_db()
migrate_db()
fix_owners()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def is_owner_email(email):
    return email.lower() in [e.lower() for e in OWNER_EMAILS]

# ============================================================
# FREE AI — Text Chat
# ============================================================
def ai_chat(messages):
    """Get AI response — free, no API key."""
    prompt = ""
    for m in messages:
        if m["role"] == "system":
            prompt += f"{m['content']}\n\n"
        elif m["role"] == "user":
            prompt += f"User: {m['content']}\n"
        elif m["role"] == "assistant":
            prompt += f"Assistant: {m['content']}\n"
    prompt += "Assistant:"
    
    # Try Pollinations first
    try:
        url = f"https://text.pollinations.ai/{requests.utils.quote(prompt)}"
        r = requests.get(url, timeout=45)
        if r.status_code == 200 and r.text and len(r.text.strip()) > 3:
            return r.text.strip()
    except:
        pass
    
    # Fallback: Hugging Face
    try:
        url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        r = requests.post(url, json={"inputs": prompt, "parameters": {"max_new_tokens": 500}}, timeout=45)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "").replace(prompt, "").strip()
    except:
        pass
    
    return "⚠️ AI is busy. Please try again in a moment."

# ============================================================
# SESSION STATE
# ============================================================
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "name" not in st.session_state:
    st.session_state.name = None
if "is_owner" not in st.session_state:
    st.session_state.is_owner = False

# ============================================================
# AUTH PAGE
# ============================================================
def auth_page():
    st.markdown("""
    <div style="text-align:center; padding:40px 0;">
        <h1 style="font-size:48px;">🤖 AI Agent Platform</h1>
        <p style="opacity:0.7; font-size:18px;">Build and chat with your own AI agents.</p>
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
                        st.error("Fill all fields")
                    else:
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("SELECT id, name, is_owner, email FROM users WHERE (username = ? OR email = ?) AND password_hash = ?", (u, u, hash_pw(p)))
                        user = c.fetchone()
                        
                        if user:
                            if is_owner_email(user["email"]):
                                c.execute("UPDATE users SET is_owner = 1 WHERE id = ?", (user["id"],))
                                conn.commit()
                                st.session_state.is_owner = True
                            else:
                                st.session_state.is_owner = bool(user["is_owner"])
                            conn.close()
                            st.session_state.user_id = user["id"]
                            st.session_state.name = user["name"] or u
                            st.rerun()
                        else:
                            conn.close()
                            st.error("Invalid credentials. Sign up first.")
        
        with tab2:
            with st.form("signup"):
                n = st.text_input("Full Name")
                u = st.text_input("Username")
                e = st.text_input("Email")
                p = st.text_input("Password", type="password")
                p2 = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    if not u or not e or not p:
                        st.error("Fill all fields")
                    elif p != p2:
                        st.error("Passwords don't match")
                    elif len(p) < 6:
                        st.error("Password must be 6+ characters")
                    else:
                        try:
                            owner = 1 if is_owner_email(e) else 0
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("INSERT INTO users (username, email, password_hash, name, is_owner, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (u, e, hash_pw(p), n, owner, datetime.now().isoformat()))
                            conn.commit()
                            conn.close()
                            st.success("👑 Owner account created!" if owner else "✅ Account created! Log in now.")
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
    
    if not user:
        conn.close()
        st.session_state.user_id = None
        st.rerun()
        return
    
    # Auto-promote owner
    if is_owner_email(user["email"]) and not user["is_owner"]:
        c.execute("UPDATE users SET is_owner = 1 WHERE id = ?", (user_id,))
        conn.commit()
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
    
    conn.close()
    is_owner = bool(user["is_owner"])
    
    with st.sidebar:
        st.markdown("### 🤖 AI Agent Platform")
        st.caption(f"👤 {user['name']}")
        if is_owner:
            st.success("👑 Owner — Unlimited")
        
        st.divider()
        page = st.radio("Navigation", ["🏠 Dashboard", "🤖 Agents", "💬 Chat", "📚 Knowledge"], label_visibility="collapsed")
        st.divider()
        
        if st.button("🚪 Log Out", use_container_width=True):
            for k in ["user_id", "name", "is_owner", "chat_messages", "chat_agent_id", "chat_id"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
    
    # ========================================================
    # DASHBOARD
    # ========================================================
    if page == "🏠 Dashboard":
        st.title(f"Welcome, {user['name']} 👋")
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as x FROM agents WHERE user_id = ?", (user_id,))
        agent_count = c.fetchone()["x"]
        c.execute("SELECT COUNT(*) as x FROM chats WHERE user_id = ?", (user_id,))
        chat_count = c.fetchone()["x"]
        conn.close()
        
        c1, c2 = st.columns(2)
        c1.metric("🤖 Agents", agent_count)
        c2.metric("💬 Chats", chat_count)
        
        st.divider()
        st.subheader("🚀 Quick Start")
        c1, c2 = st.columns(2)
        with c1:
            st.info("**1. Create an Agent**\n\nGo to 🤖 Agents to build your first agent")
        with c2:
            st.info("**2. Start Chatting**\n\nGo to 💬 Chat to talk to your agent")
    
    # ========================================================
    # AGENTS
    # ========================================================
    elif page == "🤖 Agents":
        st.title("Your Agents")
        
        with st.expander("➕ Create New Agent", expanded=False):
            with st.form("new_agent"):
                agent_name = st.text_input("Agent Name", placeholder="e.g. Coding Helper")
                description = st.text_input("Description (optional)", placeholder="What does this agent do?")
                prompt = st.text_area("System Prompt", height=180, value="""You are a helpful AI assistant.

Rules:
- Be clear and concise
- Ask clarifying questions when needed
- Never make up information
- Be friendly and professional""")
                
                if st.form_submit_button("🚀 Create Agent", use_container_width=True):
                    if not agent_name:
                        st.error("Please enter a name")
                    else:
                        try:
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("INSERT INTO agents (user_id, name, description, system_prompt, created_at) VALUES (?, ?, ?, ?, ?)",
                                (user_id, agent_name, description, prompt, datetime.now().isoformat()))
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
                        st.subheader(f"🤖 {a['name']}")
                        if a['description']:
                            st.caption(a['description'])
                    with c2:
                        if st.button("💬 Chat", key=f"chat_{a['id']}", use_container_width=True):
                            st.session_state.chat_agent_id = a['id']
                            st.session_state.page = "💬 Chat"
                            st.session_state.chat_messages = []
                            st.session_state.chat_id = None
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
    # CHAT
    # ========================================================
    elif page == "💬 Chat":
        st.title("Chat with Your Agent")
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM agents WHERE user_id = ?", (user_id,))
        agents = c.fetchall()
        conn.close()
        
        if not agents:
            st.warning("Create an agent first!")
            if st.button("➕ Create Agent"):
                st.rerun()
            return
        
        agents = [dict(a) for a in agents]
        options = {f"{a['name']}": a for a in agents}
        default = 0
        if "chat_agent_id" in st.session_state:
            for i, a in enumerate(agents):
                if a['id'] == st.session_state.chat_agent_id:
                    default = i
                    break
        
        selected_name = st.selectbox("Choose agent", list(options.keys()), index=default)
        selected_agent = options[selected_name]
        
        if "chat_agent_id" not in st.session_state or st.session_state.chat_agent_id != selected_agent['id']:
            st.session_state.chat_messages = []
            st.session_state.chat_agent_id = selected_agent['id']
            st.session_state.chat_id = None
        
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        
        with st.sidebar:
            st.divider()
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_messages = []
                st.rerun()
        
        # Display messages
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        # Chat input
        if prompt := st.chat_input(f"Message {selected_agent['name']}..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    messages = [{"role": "system", "content": selected_agent['system_prompt']}]
                    messages.extend(st.session_state.chat_messages[-10:])
                    
                    response = ai_chat(messages)
                    st.write(response)
                    
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    
                    # Save to DB
                    try:
                        conn = get_db()
                        c = conn.cursor()
                        if not st.session_state.get("chat_id"):
                            c.execute("INSERT INTO chats (user_id, agent_id, title, created_at) VALUES (?, ?, ?, ?)",
                                (user_id, selected_agent['id'], prompt[:40], datetime.now().isoformat()))
                            st.session_state.chat_id = c.lastrowid
                        c.execute("INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                            (st.session_state.chat_id, "user", prompt, datetime.now().isoformat()))
                        c.execute("INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                            (st.session_state.chat_id, "assistant", response, datetime.now().isoformat()))
                        conn.commit()
                        conn.close()
                    except:
                        pass
    
    # ========================================================
    # KNOWLEDGE
    # ========================================================
    elif page == "📚 Knowledge":
        st.title("Knowledge Base")
        st.caption("Add reference info for yourself")
        
        with st.form("new_kb"):
            kb_name = st.text_input("Title")
            kb_content = st.text_area("Content", height=200)
            if st.form_submit_button("💾 Save", use_container_width=True):
                if not kb_name:
                    st.error("Enter a title")
                else:
                    st.success(f"✅ Saved '{kb_name}'!")
        
        st.info("Knowledge base is a notepad for you. Coming soon: agents can reference it.")

# ============================================================
# ROUTER
# ============================================================
if st.session_state.user_id is None:
    auth_page()
else:
    main_app()
