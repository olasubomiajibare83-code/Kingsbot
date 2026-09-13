import streamlit as st
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import os
import requests

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="VoiceAI Platform",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "voiceai.db"

# ============================================================
# ⚠️ OWNER CONFIG — CHANGE THIS TO YOUR EMAIL
# ============================================================
OWNER_EMAILS = [
    "your-email@gmail.com",      # ← CHANGE THIS
    "owner@voiceai.com",         # ← Add more if needed
]

# ============================================================
# CREDIT COSTS (per minute)
# ============================================================
COST_PER_MINUTE = 0.05   # $0.05/min (cheaper than Retell)
FREE_SIGNUP_CREDITS = 10.00  # $10 free for new users

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
            plan TEXT DEFAULT 'free',
            created_at TEXT NOT NULL
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            system_prompt TEXT NOT NULL,
            llm_model TEXT DEFAULT 'gpt-4o-mini',
            voice_id TEXT DEFAULT 'Cartesia',
            language TEXT DEFAULT 'en-US',
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
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER,
            user_id INTEGER,
            transcript TEXT,
            duration_seconds INTEGER DEFAULT 0,
            credits_used REAL DEFAULT 0,
            sentiment TEXT,
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

init_db()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

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
# HELPERS
# ============================================================
def get_user(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    u = c.fetchone()
    conn.close()
    return u

def deduct_credits(user_id, minutes, description="Call usage"):
    """Deduct credits from user's balance. Owner is exempt."""
    user = get_user(user_id)
    if user["is_owner"]:
        return True  # Owner never charged
    
    cost = minutes * COST_PER_MINUTE
    if user["credit_balance"] < cost:
        return False  # Insufficient balance
    
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE users 
        SET credit_balance = credit_balance - ?,
            total_spent = total_spent + ?,
            total_minutes = total_minutes + ?
        WHERE id = ?
    """, (cost, cost, minutes, user_id))
    c.execute("""
        INSERT INTO transactions (user_id, amount, type, description, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, -cost, "usage", description, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True

def add_credits(user_id, amount, description="Credit purchase"):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        UPDATE users SET credit_balance = credit_balance + ? WHERE id = ?
    """, (amount, user_id))
    c.execute("""
        INSERT INTO transactions (user_id, amount, type, description, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, "purchase", description, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def is_owner_email(email):
    return email.lower() in [e.lower() for e in OWNER_EMAILS]

# ============================================================
# AUTH PAGE
# ============================================================
def auth_page():
    st.markdown("""
    <div style="text-align:center; padding:30px 0;">
        <h1 style="font-size:42px;">🎙️ VoiceAI Platform</h1>
        <p style="opacity:0.7; font-size:16px;">Build AI voice agents that sound human.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
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
                        c.execute("""
                            SELECT id, name, is_owner FROM users 
                            WHERE (username = ? OR email = ?) AND password_hash = ?
                        """, (u, u, hash_pw(p)))
                        user = c.fetchone()
                        conn.close()
                        if user:
                            st.session_state.user_id = user["id"]
                            st.session_state.name = user["name"] or u
                            st.session_state.is_owner = bool(user["is_owner"])
                            st.rerun()
                        else:
                            st.error("Invalid credentials")
            
            st.markdown("---")
            st.caption("🔵 Google Sign-In (requires OAuth setup)")
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
                            # Owner gets unlimited credits, others get free signup
                            credits = 999999.99 if owner else FREE_SIGNUP_CREDITS
                            
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("""
                                INSERT INTO users 
                                (username, email, password_hash, name, is_owner, credit_balance, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (u, e, hash_pw(p), n, owner, credits, datetime.now().isoformat()))
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
    user = get_user(user_id)
    is_owner = bool(user["is_owner"])
    
    with st.sidebar:
        st.markdown("### 🎙️ VoiceAI")
        st.caption(f"👤 {user['name']}")
        
        # Owner badge
        if is_owner:
            st.success("👑 **OWNER ACCOUNT**")
            st.caption("♾️ Unlimited credits")
        else:
            st.metric("💰 Credit Balance", f"${user['credit_balance']:.2f}")
        
        st.divider()
        page = st.radio("Navigation", [
            "🏠 Dashboard",
            "🤖 Agents",
            "📚 Knowledge Base",
            "📊 Analytics",
            "💳 Billing",
            "⚙️ Settings"
        ], label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Log Out", use_container_width=True):
            for k in ["user_id", "name", "is_owner"]:
                st.session_state[k] = None
            st.rerun()
    
    # ========================================================
    # DASHBOARD
    # ========================================================
    if page == "🏠 Dashboard":
        st.title(f"Welcome back, {user['name']} 👋")
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as x FROM agents WHERE user_id = ?", (user_id,))
        agent_count = c.fetchone()["x"]
        c.execute("SELECT COUNT(*) as x FROM knowledge_bases WHERE user_id = ?", (user_id,))
        kb_count = c.fetchone()["x"]
        c.execute("SELECT COUNT(*) as x FROM calls WHERE user_id = ?", (user_id,))
        call_count = c.fetchone()["x"]
        conn.close()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🤖 Agents", agent_count)
        c2.metric("📚 KBs", kb_count)
        c3.metric("📞 Calls", call_count)
        if is_owner:
            c4.metric("💰 Credits", "♾️ Unlimited")
        else:
            c4.metric("💰 Credits", f"${user['credit_balance']:.2f}")
        
        st.divider()
        st.subheader("⚡ Quick Actions")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("➕ Create Agent", use_container_width=True):
                st.info("Go to Agents tab in sidebar")
        with c2:
            if st.button("📚 Add Knowledge", use_container_width=True):
                st.info("Go to Knowledge Base tab in sidebar")
        with c3:
            if st.button("💳 Buy Credits", use_container_width=True):
                st.info("Go to Billing tab in sidebar")
    
    # ========================================================
    # AGENTS
    # ========================================================
    elif page == "🤖 Agents":
        st.title("Voice Agents")
        
        with st.expander("➕ Create New Agent", expanded=False):
            with st.form("new_agent"):
                agent_name = st.text_input("Agent Name")
                prompt = st.text_area("System Prompt", height=180, value="""You are a helpful voice assistant.

Rules:
- Keep responses short (1-3 sentences)
- Be polite and professional
- Ask clarifying questions when needed""")
                c1, c2 = st.columns(2)
                with c1:
                    model = st.selectbox("LLM Model", ["gpt-4o-mini", "gpt-4o", "claude-4.5-sonnet", "gemini-3-flash"])
                    language = st.selectbox("Language", ["en-US", "en-GB", "es-ES", "fr-FR", "de-DE", "pt-BR", "hi-IN"])
                with c2:
                    voice = st.selectbox("Voice Provider", ["Cartesia", "ElevenLabs", "Minimax", "OpenAI", "Custom"])
                    speed = st.slider("Voice Speed", 0.5, 2.0, 1.0, 0.1)
                
                if st.form_submit_button("🚀 Create Agent", use_container_width=True):
                    if not agent_name:
                        st.error("Please enter a name")
                    else:
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("""
                            INSERT INTO agents (user_id, name, system_prompt, llm_model, voice_id, language, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (user_id, agent_name, prompt, model, voice, language, datetime.now().isoformat()))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Agent '{agent_name}' created!")
                        st.rerun()
        
        st.divider()
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM agents WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        agents = c.fetchall()
        conn.close()
        
        if not agents:
            st.info("No agents yet.")
        else:
            for a in agents:
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.subheader(f"🎙️ {a['name']}")
                        st.caption(f"`{a['llm_model']}` • `{a['voice_id']}` • `{a['language']}`")
                        with st.expander("View Prompt"):
                            st.text(a['system_prompt'])
                    with c2:
                        if st.button("🗑️", key=f"da_{a['id']}"):
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("DELETE FROM agents WHERE id = ?", (a['id'],))
                            conn.commit()
                            conn.close()
                            st.rerun()
    
    # ========================================================
    # KNOWLEDGE BASE
    # ========================================================
    elif page == "📚 Knowledge Base":
        st.title("Knowledge Base")
        st.caption("Unlimited knowledge bases — no per-KB fee.")
        
        with st.form("new_kb"):
            kb_name = st.text_input("Name")
            kb_content = st.text_area("Content", height=200)
            if st.form_submit_button("💾 Save", use_container_width=True):
                if not kb_name:
                    st.error("Please enter a name")
                else:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO knowledge_bases (user_id, name, content, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, kb_name, kb_content, datetime.now().isoformat()))
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
        
        for kb in kbs:
            with st.expander(f"📚 {kb['name']}"):
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
    elif page == "📊 Analytics":
        st.title("Analytics")
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as x FROM calls WHERE user_id = ?", (user_id,))
        total = c.fetchone()["x"]
        c.execute("SELECT SUM(duration_seconds) as s FROM calls WHERE user_id = ?", (user_id,))
        secs = c.fetchone()["s"] or 0
        c.execute("SELECT SUM(credits_used) as c FROM calls WHERE user_id = ?", (user_id,))
        credits = c.fetchone()["c"] or 0
        conn.close()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Calls", total)
        c2.metric("Minutes", f"{secs/60:.1f}")
        c3.metric("Credits Used", f"${credits:.2f}")
        
        st.divider()
        st.subheader("Recent Calls")
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT ca.*, a.name as agent_name FROM calls ca
            LEFT JOIN agents a ON ca.agent_id = a.id
            WHERE ca.user_id = ? ORDER BY ca.created_at DESC LIMIT 20
        """, (user_id,))
        calls = c.fetchall()
        conn.close()
        
        if not calls:
            st.info("No calls yet.")
        else:
            for call in calls:
                with st.expander(f"📞 {call['agent_name'] or 'Agent'} — {call['created_at'][:19]}"):
                    st.write(f"**Duration:** {call['duration_seconds']}s")
                    st.write(f"**Credits:** ${call['credits_used']:.3f}")
                    st.write(f"**Sentiment:** {call['sentiment'] or 'N/A'}")
    
    # ========================================================
    # BILLING
    # ========================================================
    elif page == "💳 Billing":
        st.title("Billing & Credits")
        
        if is_owner:
            st.success("👑 **Owner Account — Unlimited Free Credits**")
            st.info("You are the platform owner. You are never charged for usage.")
            
            st.divider()
            st.subheader("Platform Revenue")
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as users FROM users WHERE is_owner = 0")
            total_users = c.fetchone()["users"]
            c.execute("SELECT SUM(total_spent) as revenue FROM users WHERE is_owner = 0")
            revenue = c.fetchone()["revenue"] or 0
            c.execute("SELECT SUM(total_minutes) as minutes FROM users WHERE is_owner = 0")
            total_minutes = c.fetchone()["minutes"] or 0
            conn.close()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("👥 Paying Users", total_users)
            c2.metric("💰 Total Revenue", f"${revenue:.2f}")
            c3.metric("⏱️ Minutes Served", f"{total_minutes:.1f}")
            
            st.divider()
            st.subheader("All Users")
            conn = get_db()
            c = conn.cursor()
            c.execute("""
                SELECT username, email, credit_balance, total_spent, total_minutes, plan
                FROM users WHERE is_owner = 0 ORDER BY total_spent DESC
            """)
            users = c.fetchall()
            conn.close()
            
            if users:
                for u in users:
                    st.write(f"**{u['username']}** ({u['email']}) — ${u['credit_balance']:.2f} balance • ${u['total_spent']:.2f} spent • {u['total_minutes']:.1f} min")
        else:
            st.metric("💰 Credit Balance", f"${user['credit_balance']:.2f}")
            st.caption(f"Rate: ${COST_PER_MINUTE:.2f} per minute")
            
            st.divider()
            st.subheader("💳 Buy Credits")
            cols = st.columns(4)
            packages = [
                (10, "Starter"),
                (25, "Popular"),
                (50, "Pro"),
                (100, "Business")
            ]
            for col, (amount, label) in zip(cols, packages):
                with col:
                    st.markdown(f"### ${amount}")
                    st.caption(label)
                    st.caption(f"{amount/COST_PER_MINUTE:.0f} minutes")
                    if st.button(f"Buy ${amount}", key=f"buy_{amount}", use_container_width=True):
                        st.info("🔗 Stripe checkout would open here")
                        st.caption("Add Stripe API key in Settings to enable")
            
            st.divider()
            st.subheader("📜 Transaction History")
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
                    st.caption(tx["created_at"][:19])
    
    # ========================================================
    # SETTINGS
    # ========================================================
    elif page == "⚙️ Settings":
        st.title("Settings")
        
        st.subheader("Account")
        st.write(f"**Name:** {user['name']}")
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Plan:** {user['plan'].title()}")
        st.write(f"**Role:** {'👑 Owner' if is_owner else '👤 User'}")
        
        st.divider()
        st.subheader("🔑 Bring Your Own Keys (BYOK)")
        st.caption("Plug in your own API keys — no markup.")
        st.text_input("OpenAI API Key", type="password", key="k_openai")
        st.text_input("ElevenLabs API Key", type="password", key="k_11")
        st.text_input("Cartesia API Key", type="password", key="k_cart")
        st.text_input("Twilio Account SID", type="password", key="k_tw")
        
        st.divider()
        st.subheader("💳 Payment Integration")
        st.caption("Add Stripe key to enable credit purchases.")
        st.text_input("Stripe Secret Key", type="password", key="k_stripe")
        
        if st.button("💾 Save All Keys"):
            st.success("Keys saved to session.")

# ============================================================
# ROUTER
# ============================================================
if st.session_state.user_id is None:
    auth_page()
else:
    main_app()
