import streamlit as st
import sqlite3
import hashlib
import secrets
import json
import os
import time
from datetime import datetime
import requests

# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="AI Agent Builder",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DATABASE
# ============================================================

DB_FILE = "ai_builder.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    # Agents table
    c.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            system_prompt TEXT NOT NULL,
            model TEXT NOT NULL,
            temperature REAL DEFAULT 0.7,
            max_tokens INTEGER DEFAULT 1000,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # API Keys table
    c.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            agent_id INTEGER,
            key_value TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_used TEXT,
            usage_count INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (agent_id) REFERENCES agents (id)
        )
    """)
    
    # Conversations table
    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (agent_id) REFERENCES agents (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Messages table
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# ============================================================
# HELPERS
# ============================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_api_key():
    return "sk-" + secrets.token_urlsafe(32)

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================
# SESSION STATE
# ============================================================

if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ============================================================
# AUTH PAGES
# ============================================================

def signup_page():
    st.title("🚀 Create Your Account")
    st.caption("Start building AI agents in seconds")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("signup_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Create Account", use_container_width=True):
                if not username or not email or not password:
                    st.error("Please fill all fields")
                elif password != confirm:
                    st.error("Passwords don't match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    try:
                        conn = get_db()
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                            (username, email, hash_password(password), datetime.now().isoformat())
                        )
                        conn.commit()
                        conn.close()
                        st.success("✅ Account created! Please log in.")
                        st.session_state.page = "login"
                        time.sleep(1)
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username or email already exists")
        
        st.write("---")
        if st.button("Already have an account? Log in", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

def login_page():
    st.title("🔐 Welcome Back")
    st.caption("Log in to manage your AI agents")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Log In", use_container_width=True):
                conn = get_db()
                c = conn.cursor()
                c.execute(
                    "SELECT id, username FROM users WHERE username = ? AND password_hash = ?",
                    (username, hash_password(password))
                )
                user = c.fetchone()
                conn.close()
                
                if user:
                    st.session_state.user_id = user["id"]
                    st.session_state.username = user["username"]
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.write("---")
        if st.button("Don't have an account? Sign up", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()

# ============================================================
# DASHBOARD
# ============================================================

def dashboard_page():
    st.title(f"👋 Welcome, {st.session_state.username}")
    st.caption("Your AI Agent Control Center")
    
    # Stats
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as count FROM agents WHERE user_id = ?", (st.session_state.user_id,))
    agent_count = c.fetchone()["count"]
    c.execute("SELECT COUNT(*) as count FROM api_keys WHERE user_id = ? AND active = 1", (st.session_state.user_id,))
    key_count = c.fetchone()["count"]
    conn.close()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🤖 Agents", agent_count)
    col2.metric("🔑 API Keys", key_count)
    col3.metric("💬 Conversations", "—")
    col4.metric("📊 Requests", "—")
    
    st.divider()
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Create Agent", use_container_width=True):
            st.session_state.page = "create_agent"
            st.rerun()
    with col2:
        if st.button("💬 Test Chatbot", use_container_width=True):
            st.session_state.page = "playground"
            st.rerun()
    with col3:
        if st.button("🔑 Manage API Keys", use_container_width=True):
            st.session_state.page = "api_keys"
            st.rerun()
    
    st.divider()
    
    # Recent agents
    st.subheader("🤖 Your Agents")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM agents WHERE user_id = ? ORDER BY created_at DESC LIMIT 5", (st.session_state.user_id,))
    agents = c.fetchall()
    conn.close()
    
    if not agents:
        st.info("No agents yet. Create your first one!")
    else:
        for agent in agents:
            with st.expander(f"🤖 {agent['name']}"):
                st.write(f"**Model:** {agent['model']}")
                st.write(f"**Description:** {agent['description'] or 'No description'}")
                st.write(f"**System Prompt:** {agent['system_prompt'][:200]}...")
                st.caption(f"Created: {agent['created_at'][:19]}")

# ============================================================
# CREATE AGENT
# ============================================================

def create_agent_page():
    st.title("🤖 Create New Agent")
    st.caption("Configure your AI agent's behavior")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("create_agent_form"):
            name = st.text_input("Agent Name", placeholder="e.g., Customer Support Bot")
            description = st.text_area("Description (optional)", placeholder="What does this agent do?")
            
            system_prompt = st.text_area(
                "System Prompt",
                value="You are a helpful AI assistant. Answer questions clearly and concisely.",
                height=150,
                help="This defines your agent's personality and behavior"
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                model = st.selectbox(
                    "Model",
                    [
                        "gpt-4o-mini",
                        "gpt-4o",
                        "gpt-3.5-turbo",
                        "claude-3-5-sonnet",
                        "llama-3.1-70b",
                        "custom"
                    ]
                )
            with col_b:
                temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
            
            max_tokens = st.slider("Max Tokens", 100, 4000, 1000, 100)
            
            if st.form_submit_button("🚀 Create Agent", use_container_width=True):
                if not name:
                    st.error("Please enter an agent name")
                else:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO agents 
                        (user_id, name, description, system_prompt, model, temperature, max_tokens, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        st.session_state.user_id,
                        name, description, system_prompt,
                        model, temperature, max_tokens,
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Agent '{name}' created!")
                    time.sleep(1)
                    st.session_state.page = "dashboard"
                    st.rerun()
    
    with col2:
        st.subheader("💡 Tips")
        st.info("""
        **Good system prompts include:**
        - Role definition
        - Tone and style
        - Rules and boundaries
        - Examples of desired output
        - What NOT to do
        """)
        
        st.subheader("📝 Example Prompts")
        st.code("You are a customer support agent for a tech company. Be friendly, helpful, and concise. Always ask for clarification if the question is unclear.", language="text")

# ============================================================
# PLAYGROUND (CHAT)
# ============================================================

def playground_page():
    st.title("💬 Chat Playground")
    st.caption("Test your agents in real-time")
    
    # Select agent
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name FROM agents WHERE user_id = ?", (st.session_state.user_id,))
    agents = c.fetchall()
    conn.close()
    
    if not agents:
        st.warning("No agents yet. Create one first!")
        if st.button("➕ Create Agent"):
            st.session_state.page = "create_agent"
            st.rerun()
        return
    
    agent_options = {f"{a['name']} (ID: {a['id']})": a["id"] for a in agents}
    selected = st.selectbox("Select Agent", list(agent_options.keys()))
    agent_id = agent_options[selected]
    
    # Get agent details
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
    agent = c.fetchone()
    conn.close()
    
    # API Key input
    with st.expander("⚙️ API Configuration"):
        api_provider = st.selectbox("Provider", ["OpenAI", "Groq", "OpenRouter", "Custom"])
        api_key = st.text_input("API Key", type="password", help="Your API key is never stored")
        custom_url = ""
        if api_provider == "Custom":
            custom_url = st.text_input("Base URL")
    
    st.divider()
    
    # Chat interface
    if "playground_messages" not in st.session_state:
        st.session_state.playground_messages = []
    
    # Display messages
    for msg in st.session_state.playground_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Input
    prompt = st.chat_input("Type your message...")
    
    if prompt:
        st.session_state.playground_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            if not api_key:
                st.error("Please enter your API key above")
            else:
                with st.spinner("Thinking..."):
                    try:
                        # Build request based on provider
                        base_urls = {
                            "OpenAI": "https://api.openai.com/v1",
                            "Groq": "https://api.groq.com/openai/v1",
                            "OpenRouter": "https://openrouter.ai/api/v1",
                            "Custom": custom_url
                        }
                        
                        headers = {
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        }
                        
                        messages = [{"role": "system", "content": agent["system_prompt"]}]
                        messages.extend(st.session_state.playground_messages[-10:])
                        
                        response = requests.post(
                            f"{base_urls[api_provider]}/chat/completions",
                            headers=headers,
                            json={
                                "model": agent["model"],
                                "messages": messages,
                                "temperature": agent["temperature"],
                                "max_tokens": agent["max_tokens"]
                            },
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            answer = result["choices"][0]["message"]["content"]
                            st.write(answer)
                            st.session_state.playground_messages.append({"role": "assistant", "content": answer})
                        else:
                            st.error(f"Error {response.status_code}: {response.text[:200]}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.playground_messages = []
        st.rerun()

# ============================================================
# API KEYS
# ============================================================

def api_keys_page():
    st.title("🔑 API Keys")
    st.caption("Manage your API keys for programmatic access")
    
    # Create new key
    with st.expander("➕ Create New API Key", expanded=True):
        with st.form("create_key_form"):
            key_name = st.text_input("Key Name", placeholder="e.g., Production Key")
            
            # Optional: link to agent
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT id, name FROM agents WHERE user_id = ?", (st.session_state.user_id,))
            agents = c.fetchall()
            conn.close()
            
            agent_options = {"None": None}
            agent_options.update({a["name"]: a["id"] for a in agents})
            
            linked_agent = st.selectbox("Link to Agent (optional)", list(agent_options.keys()))
            
            if st.form_submit_button("🔑 Generate Key", use_container_width=True):
                if not key_name:
                    st.error("Please enter a key name")
                else:
                    new_key = generate_api_key()
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO api_keys 
                        (user_id, agent_id, key_value, name, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        st.session_state.user_id,
                        agent_options[linked_agent],
                        new_key,
                        key_name,
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    conn.close()
                    
                    st.success("✅ API Key created!")
                    st.code(new_key, language="text")
                    st.warning("⚠️ Copy this key now — it won't be shown again!")
    
    st.divider()
    
    # List keys
    st.subheader("Your API Keys")
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT k.*, a.name as agent_name 
        FROM api_keys k 
        LEFT JOIN agents a ON k.agent_id = a.id 
        WHERE k.user_id = ? 
        ORDER BY k.created_at DESC
    """, (st.session_state.user_id,))
    keys = c.fetchall()
    conn.close()
    
    if not keys:
        st.info("No API keys yet")
    else:
        for key in keys:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{key['name']}**")
                    st.caption(f"`{key['key_value'][:20]}...` • Agent: {key['agent_name'] or 'None'}")
                    st.caption(f"Created: {key['created_at'][:19]} • Used: {key['usage_count']} times")
                with col2:
                    status = "🟢 Active" if key["active"] else "🔴 Inactive"
                    st.write(status)
                with col3:
                    if st.button("🗑️ Delete", key=f"del_{key['id']}"):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("DELETE FROM api_keys WHERE id = ?", (key["id"],))
                        conn.commit()
                        conn.close()
                        st.rerun()
                st.divider()

# ============================================================
# API DOCS
# ============================================================

def api_docs_page():
    st
