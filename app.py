import streamlit as st
import sqlite3
import hashlib
import secrets
import json
import os
import time
from datetime import datetime
import requests

st.set_page_config(
    page_title="VoiceAI Builder",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DATABASE
# ============================================================

DB_FILE = "voiceai_killer.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            plan TEXT DEFAULT 'free',
            minutes_used REAL DEFAULT 0,
            minutes_limit REAL DEFAULT 60,
            concurrent_limit INTEGER DEFAULT 50,
            created_at TEXT NOT NULL
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            system_prompt TEXT NOT NULL,
            voice_id TEXT DEFAULT 'default',
            llm_model TEXT DEFAULT 'gpt-4o-mini',
            language TEXT DEFAULT 'en-US',
            max_duration_min INTEGER DEFAULT 15,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS phone_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            agent_id INTEGER,
            number TEXT UNIQUE NOT NULL,
            provider TEXT DEFAULT 'internal',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (agent_id) REFERENCES agents (id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            caller_number TEXT,
            duration_seconds INTEGER DEFAULT 0,
            transcript TEXT,
            summary TEXT,
            sentiment TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (agent_id) REFERENCES agents (id)
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_bases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            content TEXT,
            source_url TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # NEW: QA Table
    c.execute("""
        CREATE TABLE IF NOT EXISTS qa_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id INTEGER NOT NULL,
            score INTEGER,
            feedback TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (call_id) REFERENCES calls (id)
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
    return "va-" + secrets.token_urlsafe(32)

def generate_phone_number():
    return f"+1{secrets.randbelow(9000000000) + 1000000000}"

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
    st.session_state.page = "landing"

# ============================================================
# LANDING PAGE
# ============================================================

def landing_page():
    st.markdown("""
    <style>
        .hero {
            text-align: center;
            padding: 60px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            color: white;
            margin-bottom: 30px;
        }
        .hero h1 { font-size: 48px; margin-bottom: 20px; }
        .hero p { font-size: 20px; opacity: 0.9; }
        .feature-card {
            background: rgba(255,255,255,0.05);
            padding: 25px;
            border-radius: 15px;
            border: 1px solid rgba(255,255,255,0.1);
            text-align: center;
        }
        .price-card {
            background: rgba(255,255,255,0.05);
            padding: 30px;
            border-radius: 15px;
            border: 2px solid rgba(102,126,234,0.5);
            text-align: center;
        }
        .price-card.featured {
            border-color: #667eea;
            box-shadow: 0 0 30px rgba(102,126,234,0.3);
        }
        .killer-badge {
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="hero">
        <span class="killer-badge">🔥 RETELL KILLER</span>
        <h1>🎙️ VoiceAI Builder</h1>
        <p>Open-source voice AI platform. Self-hosted. No vendor lock-in.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col2:
        if st.button("🚀 Get Started Free", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()
    
    st.divider()
    
    st.subheader("🔥 What Makes Us Different")
    cols = st.columns(4)
    features = [
        ("🔓", "Open Source", "Every line is yours to modify [citation:7]"),
        ("🏠", "Self-Hosted", "Your infra, your rules [citation:7]"),
        ("💰", "$0.05/min", "All-in pricing — no stacking [citation:2]"),
        ("🧪", "Built-in QA", "QA node for prompt analysis [citation:7]")
    ]
    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(f"""
            <div class="feature-card">
                <div style="font-size: 40px;">{icon}</div>
                <h3>{title}</h3>
                <p style="opacity: 0.7;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    st.subheader("💎 Simple Pricing")
    cols = st.columns(3)
    plans = [
        ("Free", "$0", "60 minutes", ["50 Concurrent Calls", "Unlimited KBs", "Web Widget", "Built-in QA"]),
        ("Pro", "$29/mo", "500 minutes", ["Unlimited Agents", "Unlimited Numbers", "CRM + Calendar", "API + Webhooks"]),
        ("Business", "$99/mo", "2000 minutes", ["Everything in Pro", "Dedicated Server", "HIPAA/BAA", "24/7 Support"])
    ]
    for col, (name, price, minutes, features_list) in zip(cols, plans):
        with col:
            featured = "featured" if name == "Pro" else ""
            st.markdown(f"""
            <div class="price-card {featured}">
                <h3>{name}</h3>
                <div style="font-size: 36px; font-weight: bold; color: #667eea;">{price}</div>
                <p style="opacity: 0.7;">{minutes}/month</p>
                <ul style="text-align: left; margin-top: 20px;">
                    {''.join([f'<li>✅ {f}</li>' for f in features_list])}
                </ul>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# AUTH
# ============================================================

def signup_page():
    st.title("🚀 Create Your Account")
    st.caption("Start building AI voice agents in minutes")
    
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
        
        if st.button("Already have an account? Log in", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()

def login_page():
    st.title("🔐 Welcome Back")
    
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
        
        if st.button("Don't have an account? Sign up", use_container_width=True):
            st.session_state.page = "signup"
            st.rerun()

# ============================================================
# DASHBOARD
# ============================================================

def dashboard_page():
    st.title(f"👋 Welcome, {st.session_state.username}")
    st.caption("Your Voice AI Control Center")
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as count FROM agents WHERE user_id = ?", (st.session_state.user_id,))
    agent_count = c.fetchone()["count"]
    c.execute("SELECT COUNT(*) as count FROM phone_numbers WHERE user_id = ?", (st.session_state.user_id,))
    number_count = c.fetchone()["count"]
    c.execute("SELECT COUNT(*) as count FROM calls WHERE user_id = ?", (st.session_state.user_id,))
    call_count = c.fetchone()["count"]
    c.execute("SELECT minutes_used, minutes_limit, concurrent_limit FROM users WHERE id = ?", (st.session_state.user_id,))
    user = c.fetchone()
    conn.close()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🤖 Agents", agent_count)
    col2.metric("📞 Numbers", number_count)
    col3.metric("📊 Calls", call_count)
    col4.metric("⚡ Concurrent", user["concurrent_limit"])
    
    st.divider()
    
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("➕ Create Agent", use_container_width=True):
            st.session_state.page = "create_agent"
            st.rerun()
    with col2:
        if st.button("📞 Get Number", use_container_width=True):
            st.session_state.page = "phone_numbers"
            st.rerun()
    with col3:
        if st.button("📚 Knowledge Base", use_container_width=True):
            st.session_state.page = "knowledge"
            st.rerun()
    with col4:
        if st.button("🧪 QA Dashboard", use_container_width=True):
            st.session_state.page = "qa"
            st.rerun()
    
    st.divider()
    
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
            with st.expander(f"🎙️ {agent['name']}"):
                st.write(f"**Model:** {agent['llm_model']}")
                st.write(f"**Language:** {agent['language']}")
                st.write(f"**Description:** {agent['description'] or 'No description'}")
                st.caption(f"Created: {agent['created_at'][:19]}")

# ============================================================
# CREATE AGENT
# ============================================================

def create_agent_page():
    st.title("🎙️ Create Voice Agent")
    st.caption("Configure your AI voice agent's behavior")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("create_agent_form"):
            name = st.text_input("Agent Name", placeholder="e.g., Customer Support")
            description = st.text_area("Description (optional)")
            
            system_prompt = st.text_area(
                "System Prompt",
                value="""You are a helpful AI voice assistant.

Your job:
- Answer questions clearly and concisely
- Be friendly and professional
- If you don't know something, say so
- End the call politely when the user is done

Rules:
- Keep responses short (2-3 sentences max)
- Ask clarifying questions when needed
- Never make up information""",
                height=200
            )
            
            col_a, col_b = st.columns(2)
            with col_a:
                voice = st.selectbox(
                    "Voice",
                    ["Default", "Professional Male", "Professional Female", "Casual Male", "Casual Female", "Custom Clone"]
                )
                language = st.selectbox(
                    "Language",
                    ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "pt-BR", "hi-IN", "ar-SA", "zh-CN", "ja-JP"]
                )
            with col_b:
                model = st.selectbox(
                    "LLM Model",
                    ["gpt-4o-mini", "gpt-4o", "claude-4.5-haiku", "claude-4.5-sonnet", "gemini-3-flash"]
                )
                max_duration = st.slider("Max Call Duration (min)", 5, 60, 15)
            
            if st.form_submit_button("🚀 Create Agent", use_container_width=True):
                if not name:
                    st.error("Please enter an agent name")
                else:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO agents 
                        (user_id, name, description, system_prompt, voice_id, llm_model, language, max_duration_min, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        st.session_state.user_id,
                        name, description, system_prompt,
                        voice, model, language, max_duration,
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Agent '{name}' created!")
                    time.sleep(1)
                    st.session_state.page = "dashboard"
                    st.rerun()
    
    with col2:
        st.subheader("💡 Retell vs Us")
        st.info("""
        **Retell:**
        - ❌ Proprietary
        - ❌ SaaS only
        - ❌ 10 KB limit
        - ❌ $8/extra KB
        
        **Us:**
        - ✅ Open Source
        - ✅ Self-Hosted
        - ✅ Unlimited KBs
        - ✅ Free QA node
        """)

# ============================================================
# PHONE NUMBERS
# ============================================================

def phone_numbers_page():
    st.title("📞 Phone Numbers")
    st.caption("Get a phone number for your voice agent")
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name FROM agents WHERE user_id = ?", (st.session_state.user_id,))
    agents = c.fetchall()
    conn.close()
    
    if not agents:
        st.warning("Create an agent first!")
        if st.button("➕ Create Agent"):
            st.session_state.page = "create_agent"
            st.rerun()
        return
    
    with st.expander("➕ Get New Number", expanded=True):
        with st.form("buy_number_form"):
            agent_options = {f"{a['name']}": a["id"] for a in agents}
            selected_agent = st.selectbox("Link to Agent", list(agent_options.keys()))
            
            if st.form_submit_button("📞 Get Number ($2/month)", use_container_width=True):
                new_number = generate_phone_number()
                conn = get_db()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO phone_numbers (user_id, agent_id, number, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    st.session_state.user_id,
                    agent_options[selected_agent],
                    new_number,
                    datetime.now().isoformat()
                ))
                conn.commit()
                conn.close()
                st.success(f"✅ Number created: {new_number}")
                time.sleep(1)
                st.rerun()
    
    st.divider()
    st.subheader("Your Numbers")
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT p.*, a.name as agent_name 
        FROM phone_numbers p 
        LEFT JOIN agents a ON p.agent_id = a.id 
        WHERE p.user_id = ?
    """, (st.session_state.user_id,))
    numbers = c.fetchall()
    conn.close()
    
    if not numbers:
        st.info("No phone numbers yet")
    else:
        for num in numbers:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{num['number']}**")
                st.caption(f"Agent: {num['agent_name'] or 'Unlinked'} • Created: {num['created_at'][:19]}")
            with col2:
                st.write("🟢 Active")
            with col3:
                if st.button("🗑️", key=f"del_num_{num['id']}"):
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("DELETE FROM phone_numbers WHERE id = ?", (num["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()

# ============================================================
# KNOWLEDGE BASE
# ============================================================

def knowledge_page():
    st.title("📚 Knowledge Base")
    st.caption("Add documents and URLs your agent can reference")
    
    with st.expander("➕ Add Knowledge", expanded=True):
        with st.form("knowledge_form"):
            kb_name = st.text_input("Knowledge Base Name")
            source_type = st.selectbox("Source", ["Text", "URL", "Document"])
            
            content = ""
            url = ""
            if source_type == "Text":
                content = st.text_area("Content", height=150)
            elif source_type == "URL":
                url = st.text_input("URL")
            else:
                uploaded = st.file_uploader("Upload", type=["txt", "pdf", "docx"])
            
            if st.form_submit_button("📚 Add Knowledge", use_container_width=True):
                if not kb_name:
                    st.error("Please enter a name")
                else:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO knowledge_bases (user_id, name, content, source_url, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        st.session_state.user_id,
                        kb_name,
                        content,
                        url,
                        datetime.now().isoformat()
                    ))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Knowledge base '{kb_name}' created!")
                    time.sleep(1)
                    st.rerun()
    
    st.divider()
    st.subheader("Your Knowledge Bases")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM knowledge_bases WHERE user_id = ? ORDER BY created_at DESC", (st.session_state.user_id,))
    kbs = c.fetchall()
    conn.close()
    
    if not kbs:
        st.info("No knowledge bases yet")
    else:
        for kb in kbs:
            with st.expander(f"📚 {kb['name']}"):
                if kb["content"]:
                    st.write(f"**Content:** {kb['content'][:200]}...")
                if kb["source_url"]:
                    st.write(f"**URL:** {kb['source_url']}")
                st.caption(f"Created: {kb['created_at'][:19]}")

# ============================================================
# QA DASHBOARD (UNIQUE FEATURE)
# ============================================================

def qa_page():
    st.title("🧪 QA Dashboard")
    st.caption("Built-in quality analysis — Retell doesn't have this")
    
    st.info("""
    **QA Node** analyzes your prompt quality across all nodes in your workflow.
    This is a feature Retell AI does not offer natively.
    """)
    
    # Prompt quality analysis
    st.subheader("📊 Prompt Quality Analysis")
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM agents WHERE user_id = ?", (st.session_state.user_id,))
    agents = c.fetchall()
    conn.close()
    
    if not agents:
        st.warning("Create an agent first to analyze prompts")
        return
    
    selected = st.selectbox("Select Agent", [a["name"] for a in agents])
    agent = next(a for a in agents if a["name"] == selected)
    
    # Analyze prompt
    prompt = agent["system_prompt"]
    score = 0
    feedback = []
    
    # Check for key elements
    if len(prompt) > 100:
        score += 20
        feedback.append("✅ Good prompt length")
    else:
        feedback.append("⚠️ Prompt is very short")
    
    if "job" in prompt.lower() or "role" in prompt.lower() or "you are" in prompt.lower():
        score += 20
        feedback.append("✅ Role defined")
    else:
        feedback.append("❌ Missing role definition")
    
    if "rule" in prompt.lower() or "must" in prompt.lower() or "never" in prompt.lower():
        score += 20
        feedback.append("✅ Rules defined")
    else:
        feedback.append("❌ Missing rules")
    
    if "keep" in prompt.lower() or "short" in prompt.lower() or "concise" in prompt.lower():
        score += 20
        feedback.append("✅ Length guidance")
    else:
        feedback.append("⚠️ No length guidance")
    
    if "example" in prompt.lower() or "greet" in prompt.lower():
        score += 20
        feedback.append("✅ Examples provided")
    else:
        feedback.append("⚠️ No examples")
    
    # Display
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("QA Score", f"{score}/100")
        if score >= 80:
            st.success("Excellent prompt!")
        elif score >= 60:
            st.warning("Good prompt, can improve")
        else:
            st.error("Needs improvement")
    
    with col2:
        for f in feedback:
            st.write(f)
    
    st.divider()
    
    # Recent calls QA
    st.subheader("📞 Recent Call Analysis")
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT c.*, a.name as agent_name 
        FROM calls c 
        LEFT JOIN agents a ON c.agent_id = a.id 
        WHERE c.user_id = ?
        ORDER BY c.created_at DESC LIMIT 10
    """, (st.session_state.user_id,))
    calls = c.fetchall()
    conn.close()
    
    if not calls:
        st.info("No calls to analyze yet")
    else:
        for call in calls:
            with st.expander(f"📞 {call['created_at'][:19]}"):
                st.write(f"**Agent:** {call['agent_name']}")
                st.write(f"**Duration:** {call['duration_seconds']}s")
                if call["summary"]:
                    st.write(f"**Summary:** {call['summary']}")
                st.write(f"**Sentiment:** {call['sentiment'] or 'Not analyzed'}")

# ============================================================
# SIDEBAR
# ============================================================

def sidebar():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712031.png", width=60)
        st.title("🎙️ VoiceAI Builder")
        st.caption("🔥 Retell Killer")
        st.caption(f"👤 {st.session_state.username}")
        st.divider()
        
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
        if st.button("🎙️ Create Agent", use_container_width=True):
            st.session_state.page = "create_agent"
            st.rerun()
        if st.button("📞 Phone Numbers", use_container_width=True):
            st.session_state.page = "phone_numbers"
            st.rerun()
        if st.button("📚 Knowledge Base", use_container_width=True):
            st.session_state.page = "knowledge"
            st.rerun()
        if st.button("🧪 QA Dashboard", use_container_width=True):
            st.session_state.page = "qa"
            st.rerun()
        
        st.divider()
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT minutes_used, minutes_limit FROM users WHERE id = ?", (st.session_state.user_id,))
        user = c.fetchone()
        conn.close()
        
        if user:
            used = user["minutes_used"] or 0
            limit = user["minutes_limit"] or 60
            st.progress(min(used/limit, 1.0))
            st.caption(f"⏱️ {used:.0f}/{limit:.0f} min")
        
        st.divider()
        
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.page = "landing"
            st.rerun()

# ============================================================
# ROUTER
# ============================================================

if st.session_state.user_id is None:
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "signup":
        signup_page()
    else:
        landing_page()
else:
    sidebar()
    
    if st.session_state.page == "dashboard":
        dashboard_page()
    elif st.session_state.page == "create_agent":
        create_agent_page()
    elif st.session_state.page == "phone_numbers":
        phone_numbers_page()
    elif st.session_state.page == "knowledge":
        knowledge_page()
    elif st.session_state.page == "qa":
        qa_page()
    else:
        dashboard_page()
