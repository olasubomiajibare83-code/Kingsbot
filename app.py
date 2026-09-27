import streamlit as st
import sqlite3
import hashlib
import requests
import time
from datetime import datetime

# ============================================================
# PAGE SETTINGS
# ============================================================
st.set_page_config(
    page_title="NEXUS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "nexus.db"

# ⚠️ CHANGE THIS TO YOUR EMAIL
OWNER_EMAILS = ["your-email@gmail.com"]

# ============================================================
# DATABASE SETUP
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
    
    c.execute("""CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
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

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def is_owner_email(email):
    return email.lower() in [e.lower() for e in OWNER_EMAILS]

def fix_owners():
    try:
        conn = get_db()
        c = conn.cursor()
        for email in OWNER_EMAILS:
            c.execute("UPDATE users SET is_owner = 1 WHERE LOWER(email) = LOWER(?)", (email,))
        conn.commit()
        conn.close()
    except:
        pass

init_db()
fix_owners()

# ============================================================
# FREE AI — 3 PROVIDERS (no API key)
# ============================================================
def ai_reply(messages):
    """Try 3 free AI providers in order."""
    
    # Provider 1: KeylessAI
    try:
        r = requests.post(
            "https://keylessai.thryx.workers.dev/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer not-needed"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.7
            },
            timeout=45
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("choices") and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                if content and len(content.strip()) > 2:
                    return content.strip()
    except:
        pass
    
    # Provider 2: OpenZoo
    try:
        r = requests.post(
            "https://api.openzoo.fun/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer sk-openzoo"
            },
            json={
                "model": "z-ai/glm-5.3-flash",
                "messages": messages,
                "temperature": 0.7
            },
            timeout=45
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("choices") and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                if content and len(content.strip()) > 2:
                    return content.strip()
    except:
        pass
    
    # Provider 3: LLM7.io
    try:
        r = requests.post(
            "https://api.llm7.io/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer unused"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.7
            },
            timeout=45
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("choices") and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                if content and len(content.strip()) > 2:
                    return content.strip()
    except:
        pass
    
    return "⚠️ The AI is busy right now. Please send your message again."

# ============================================================
# SESSION STATE
# ============================================================
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "name" not in st.session_state:
    st.session_state.name = None
if "is_owner" not in st.session_state:
    st.session_state.is_owner = False
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

# ============================================================
# LOGIN PAGE
# ============================================================
def login_page():
    st.markdown("""
    <div style="text-align:center; padding:40px 0;">
        <h1 style="font-size:52px; margin:0;">🧠 NEXUS</h1>
        <p style="opacity:0.7; font-size:18px;">One being. One mind. Yours.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Log In", "✨ Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                u = st.text_input("Username or Email")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Log In", use_container_width=True):
                    if not u or not p:
                        st.error("Please fill both fields")
                    else:
                        conn = get_db()
                        c = conn.cursor()
                        c.execute(
                            "SELECT id, name, is_owner FROM users WHERE (username = ? OR email = ?) AND password_hash = ?",
                            (u, u, hash_pw(p))
                        )
                        user = c.fetchone()
                        conn.close()
                        if user:
                            st.session_state.user_id = user["id"]
                            st.session_state.name = user["name"] or u
                            st.session_state.is_owner = bool(user["is_owner"])
                            st.rerun()
                        else:
                            st.error("Invalid login. Try signing up first.")
        
        with tab2:
            with st.form("signup_form"):
                n = st.text_input("Your Name")
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
                        st.error("Password must be at least 6 characters")
                    else:
                        try:
                            owner = 1 if is_owner_email(e) else 0
                            conn = get_db()
                            c = conn.cursor()
                            c.execute(
                                "INSERT INTO users (username, email, password_hash, name, is_owner, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (u, e, hash_pw(p), n, owner, datetime.now().isoformat())
                            )
                            conn.commit()
                            conn.close()
                            if owner:
                                st.success("👑 Owner account created! Log in now.")
                            else:
                                st.success("✅ Account created! Log in now.")
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
    
    # ========== SIDEBAR ==========
    with st.sidebar:
        st.markdown(f"### 🧠 NEXUS")
        st.caption(f"👤 {user['name']}")
        if is_owner:
            st.success("👑 Owner")
        st.divider()
        
        if st.button("➕ New Chat", use_container_width=True):
            conn = get_db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO chats (user_id, title, created_at) VALUES (?, ?, ?)",
                (user_id, "New Chat", datetime.now().isoformat())
            )
            st.session_state.current_chat_id = c.lastrowid
            conn.commit()
            conn.close()
            st.rerun()
        
        st.divider()
        st.subheader("💬 Your Chats")
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM chats WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        chats = c.fetchall()
        conn.close()
        
        if not chats:
            st.caption("No chats yet")
        else:
            for chat in chats:
                title = chat["title"] or "New Chat"
                prefix = "🟢 " if chat["id"] == st.session_state.current_chat_id else "💬 "
                if st.button(f"{prefix}{title[:25]}", key=f"chat_{chat['id']}", use_container_width=True):
                    st.session_state.current_chat_id = chat["id"]
                    st.rerun()
        
        st.divider()
        if st.button("🚪 Log Out", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    
    # ========== MAIN AREA ==========
    st.title("🧠 NEXUS")
    st.caption("Ask me anything. I'm here.")
    
    # If no chat selected, create one
    if st.session_state.current_chat_id is None:
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO chats (user_id, title, created_at) VALUES (?, ?, ?)",
            (user_id, "New Chat", datetime.now().isoformat())
        )
        st.session_state.current_chat_id = c.lastrowid
        conn.commit()
        conn.close()
        st.rerun()
    
    chat_id = st.session_state.current_chat_id
    
    # Load messages
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
    messages = c.fetchall()
    conn.close()
    
    # Display messages
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Chat input
    prompt = st.chat_input("Message NEXUS...")
    
    if prompt:
        # Save user message
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, "user", prompt, datetime.now().isoformat())
        )
        conn.commit()
        
        # Update chat title if it's still "New Chat"
        c.execute("SELECT title FROM chats WHERE id = ?", (chat_id,))
        chat_row = c.fetchone()
        if chat_row and (chat_row["title"] == "New Chat" or not chat_row["title"]):
            new_title = prompt[:40] + ("..." if len(prompt) > 40 else "")
            c.execute("UPDATE chats SET title = ? WHERE id = ?", (new_title, chat_id))
        
        conn.commit()
        conn.close()
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get AI reply
        with st.chat_message("assistant"):
            with st.spinner("NEXUS is thinking..."):
                # Build message history for AI
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
                history = c.fetchall()
                conn.close()
                
                api_messages = [
                    {"role": "system", "content": "You are NEXUS — a warm, patient, intelligent AI companion. Speak naturally, clearly, and kindly. Keep responses helpful and human."}
                ]
                for h in history[-20:]:
                    api_messages.append({"role": h["role"], "content": h["content"]})
                
                reply = ai_reply(api_messages)
                st.write(reply)
        
        # Save AI reply
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, "assistant", reply, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        
        st.rerun()

# ============================================================
# ROUTER
# ============================================================
if st.session_state.user_id is None:
    login_page()
else:
    main_app()
