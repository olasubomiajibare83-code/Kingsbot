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

# ⚠️⚠️⚠️ CHANGE THIS TO YOUR EMAIL ⚠️⚠️⚠️
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

    c.execute("""CREATE TABLE IF NOT EXISTS agent_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id INTEGER NOT NULL,
        version INTEGER NOT NULL,
        system_prompt TEXT NOT NULL,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        agent_id INTEGER,
        title TEXT NOT NULL,
        content TEXT,
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

    c.execute("""CREATE TABLE IF NOT EXISTS test_cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        expected TEXT,
        last_result TEXT,
        last_pass INTEGER,
        created_at TEXT NOT NULL)""")

    conn.commit()
    conn.close()

def migrate_db():
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
# FREE AI — Multi-Provider Fallback
# ============================================================
def ai_chat(messages, temperature=0.7):
    """Get AI response — tries multiple free providers, no API key."""
    prompt = ""
    for m in messages:
        if m["role"] == "system":
            prompt += f"{m['content']}\n\n"
        elif m["role"] == "user":
            prompt += f"User: {m['content']}\n"
        elif m["role"] == "assistant":
            prompt += f"Assistant: {m['content']}\n"
    prompt += "Assistant:"

    # Provider 1: Pollinations GET (anonymous)
    try:
        url = f"https://text.pollinations.ai/{requests.utils.quote(prompt)}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=45)
        if r.status_code == 200 and r.text and len(r.text.strip()) > 3:
            return r.text.strip()
    except:
        pass

    # Provider 2: Pollinations POST
    try:
        url = "https://text.pollinations.ai/openai"
        payload = {"model": "openai", "messages": messages, "temperature": temperature, "max_tokens": 1000}
        r = requests.post(url, json=payload, headers={"User-Agent": "Mozilla/5.0"}, timeout=45)
        if r.status_code == 200:
            data = r.json()
            if "choices" in data and data["choices"]:
                return data["choices"][0]["message"]["content"]
    except:
        pass

    # Provider 3: Hugging Face free
    try:
        url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        r = requests.post(url, json={"inputs": prompt, "parameters": {"max_new_tokens": 500, "temperature": temperature}}, timeout=45)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and data:
                result = data[0].get("generated_text", "")
                return result.replace(prompt, "").strip()
    except:
        pass

    return "⚠️ AI is busy. Please try again in a moment."

# ============================================================
# HELPERS
# ============================================================
def build_system_prompt(agent, user_id):
    """Build system prompt with knowledge base attached."""
    base = agent["system_prompt"]
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT title, content FROM knowledge WHERE user_id = ? AND (agent_id = ? OR agent_id IS NULL)", (user_id, agent["id"]))
    kbs = c.fetchall()
    conn.close()

    if kbs:
        kb_text = "\n\n--- KNOWLEDGE BASE ---\n"
        for kb in kbs:
            kb_text += f"\n[{kb['title']}]\n{kb['content']}\n"
        base += kb_text
    return base

def save_agent_version(agent_id, system_prompt):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT MAX(version) as v FROM agent_versions WHERE agent_id = ?", (agent_id,))
    row = c.fetchone()
    next_v = (row["v"] or 0) + 1
    c.execute("INSERT INTO agent_versions (agent_id, version, system_prompt, created_at) VALUES (?, ?, ?, ?)",
              (agent_id, next_v, system_prompt, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def analyze_chat(messages):
    """Post-chat analysis — sentiment + summary."""
    convo = "\n".join([f"{m['role']}: {m['content']}" for m in messages if m["role"] != "system"])
    analysis_prompt = f"""Analyze this conversation and return JSON with:
- sentiment: positive/neutral/negative
- summary: one sentence summary
- topics: list of 2-3 main topics

Conversation:
{convo}

Respond with ONLY valid JSON, no markdown, no explanation."""

    result = ai_chat([{"role": "user", "content": analysis_prompt}])
    try:
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return {"sentiment": "unknown", "summary": result[:200], "topics": []}

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
# AUTH
# ============================================================
def auth_page():
    st.markdown("""
    <div style="text-align:center; padding:40px 0;">
        <h1 style="font-size:48px;">🤖 AI Agent Platform</h1>
        <p style="opacity:0.7; font-size:18px;">Build, test, and chat with your own AI agents.</p>
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
            st.success("👑 Owner")
        st.divider()
        page = st.radio("Navigation", [
            "🏠 Dashboard",
            "🤖 Agents",
            "💬 Chat",
            "📚 Knowledge",
            "🧪 Test Cases",
            "⚖️ Compare Agents",
            "📊 Analytics",
        ], label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Log Out", use_container_width=True):
            for k in list(st.session_state.keys()):
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
        ac = c.fetchone()["x"]
        c.execute("SELECT COUNT(*) as x FROM chats WHERE user_id = ?", (user_id,))
        cc = c.fetchone()["x"]
        c.execute("SELECT COUNT(*) as x FROM knowledge WHERE user_id = ?", (user_id,))
        kc = c.fetchone()["x"]
        c.execute("SELECT COUNT(*) as x FROM test_cases WHERE user_id = ?", (user_id,))
        tc = c.fetchone()["x"]
        conn.close()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🤖 Agents", ac)
        c2.metric("💬 Chats", cc)
        c3.metric("📚 Knowledge", kc)
        c4.metric("🧪 Test Cases", tc)

        st.divider()
        st.subheader("🚀 What You Can Do")
        c1, c2 = st.columns(2)
        with c1:
            st.info("**Create Agents** — Define personalities with system prompts")
            st.info("**Add Knowledge** — Attach facts your agents reference")
            st.info("**Test Cases** — Run graded simulations")
        with c2:
            st.info("**Compare Agents** — A/B test two agents on same prompt")
            st.info("**Analytics** — See sentiment + summaries")
            st.info("**Versioning** — Revert prompt changes")

    # ========================================================
    # AGENTS
    # ========================================================
    elif page == "🤖 Agents":
        st.title("Your Agents")

        with st.expander("➕ Create New Agent", expanded=False):
            with st.form("new_agent"):
                agent_name = st.text_input("Agent Name", placeholder="e.g. Coding Helper")
                description = st.text_input("Description (optional)")
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
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("INSERT INTO agents (user_id, name, description, system_prompt, created_at) VALUES (?, ?, ?, ?, ?)",
                            (user_id, agent_name, description, prompt, datetime.now().isoformat()))
                        agent_id = c.lastrowid
                        conn.commit()
                        conn.close()
                        save_agent_version(agent_id, prompt)
                        st.success(f"✅ Agent '{agent_name}' created!")
                        time.sleep(0.5)
                        st.rerun()

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
                        if a["description"]:
                            st.caption(a["description"])
                    with c2:
                        if st.button("💬 Chat", key=f"chat_{a['id']}", use_container_width=True):
                            st.session_state.chat_agent_id = a["id"]
                            st.session_state.chat_messages = []
                            st.session_state.chat_id = None
                            st.session_state.page = "💬 Chat"
                            st.rerun()
                    with c3:
                        if st.button("🗑️ Delete", key=f"del_{a['id']}", use_container_width=True):
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("DELETE FROM agents WHERE id = ?", (a["id"],))
                            c.execute("DELETE FROM agent_versions WHERE agent_id = ?", (a["id"],))
                            conn.commit()
                            conn.close()
                            st.rerun()

                    with st.expander("✏️ Edit Prompt / View Versions"):
                        new_prompt = st.text_area("Update System Prompt", value=a["system_prompt"], height=180, key=f"edit_{a['id']}")
                        if st.button("💾 Save New Version", key=f"save_{a['id']}"):
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("UPDATE agents SET system_prompt = ? WHERE id = ?", (new_prompt, a["id"]))
                            conn.commit()
                            conn.close()
                            save_agent_version(a["id"], new_prompt)
                            st.success("✅ Saved as new version!")
                            st.rerun()

                        conn = get_db()
                        c = conn.cursor()
                        c.execute("SELECT * FROM agent_versions WHERE agent_id = ? ORDER BY version DESC", (a["id"],))
                        versions = c.fetchall()
                        conn.close()
                        if versions:
                            st.caption("Version history:")
                            for v in versions:
                                st.write(f"**v{v['version']}** — {v['created_at'][:19]}")

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
            return

        agents = [dict(a) for a in agents]
        options = {a["name"]: a for a in agents}
        default = 0
        if "chat_agent_id" in st.session_state:
            for i, a in enumerate(agents):
                if a["id"] == st.session_state.chat_agent_id:
                    default = i
                    break

        selected_name = st.selectbox("Choose agent", list(options.keys()), index=default)
        selected_agent = options[selected_name]

        if "chat_agent_id" not in st.session_state or st.session_state.chat_agent_id != selected_agent["id"]:
            st.session_state.chat_messages = []
            st.session_state.chat_agent_id = selected_agent["id"]
            st.session_state.chat_id = None

        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []

        with st.sidebar:
            st.divider()
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_messages = []
                st.session_state.chat_id = None
                st.rerun()

        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input(f"Message {selected_agent['name']}..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    system = build_system_prompt(selected_agent, user_id)
                    messages = [{"role": "system", "content": system}]
                    messages.extend(st.session_state.chat_messages[-10:])
                    response = ai_chat(messages)
                    st.write(response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})

                    try:
                        conn = get_db()
                        c = conn.cursor()
                        if not st.session_state.get("chat_id"):
                            c.execute("INSERT INTO chats (user_id, agent_id, title, created_at) VALUES (?, ?, ?, ?)",
                                (user_id, selected_agent["id"], prompt[:40], datetime.now().isoformat()))
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
        st.caption("Facts your agents can reference. Attach to a specific agent or make global.")

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, name FROM agents WHERE user_id = ?", (user_id,))
        agents = c.fetchall()
        conn.close()

        with st.form("new_kb"):
            title = st.text_input("Title")
            content = st.text_area("Content", height=150)
            agent_choice = st.selectbox("Attach to agent (optional)", ["Global (all agents)"] + [a["name"] for a in agents])
            if st.form_submit_button("💾 Save", use_container_width=True):
                if not title:
                    st.error("Enter a title")
                else:
                    agent_id = None
                    if agent_choice != "Global (all agents)":
                        agent_id = next(a["id"] for a in agents if a["name"] == agent_choice)
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT INTO knowledge (user_id, agent_id, title, content, created_at) VALUES (?, ?, ?, ?, ?)",
                        (user_id, agent_id, title, content, datetime.now().isoformat()))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Saved '{title}'!")
                    st.rerun()

        st.divider()
        conn = get_db()
        c = conn.cursor()
        c.execute("""SELECT k.*, a.name as agent_name FROM knowledge k
            LEFT JOIN agents a ON k.agent_id = a.id
            WHERE k.user_id = ? ORDER BY k.created_at DESC""", (user_id,))
        kbs = c.fetchall()
        conn.close()

        for kb in kbs:
            tag = f"→ {kb['agent_name']}" if kb["agent_name"] else "🌍 Global"
            with st.expander(f"📚 {kb['title']}  {tag}"):
                st.text(kb["content"][:500] if kb["content"] else "")
                if st.button("🗑️ Delete", key=f"dkb_{kb['id']}"):
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("DELETE FROM knowledge WHERE id = ?", (kb["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()

    # ========================================================
    # TEST CASES
    # ========================================================
    elif page == "🧪 Test Cases":
        st.title("Simulation Testing")
        st.caption("Save questions and run them against your agent to catch regressions.")

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, name FROM agents WHERE user_id = ?", (user_id,))
        agents = c.fetchall()
        conn.close()

        if not agents:
            st.warning("Create an agent first!")
            return

        agent_map = {a["name"]: a["id"] for a in agents}
        selected_agent_name = st.selectbox("Agent to test", list(agent_map.keys()))
        agent_id = agent_map[selected_agent_name]

        with st.form("new_test"):
            question = st.text_input("Test question")
            expected = st.text_area("Expected answer (for grading)", height=80)
            if st.form_submit_button("➕ Add Test Case"):
                if question:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT INTO test_cases (agent_id, user_id, question, expected, created_at) VALUES (?, ?, ?, ?, ?)",
                        (agent_id, user_id, question, expected, datetime.now().isoformat()))
                    conn.commit()
                    conn.close()
                    st.success("✅ Test added!")
                    st.rerun()

        st.divider()
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM test_cases WHERE agent_id = ? AND user_id = ? ORDER BY created_at DESC", (agent_id, user_id))
        tests = c.fetchall()
        conn.close()

        if not tests:
            st.info("No test cases yet.")
        else:
            if st.button("▶️ Run All Tests", type="primary"):
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
                agent = dict(c.fetchone())
                conn.close()

                system = build_system_prompt(agent, user_id)
                progress = st.progress(0)
                results = []

                for i, t in enumerate(tests):
                    msgs = [{"role": "system", "content": system}, {"role": "user", "content": t["question"]}]
                    answer = ai_chat(msgs)
                    passed = 1 if (t["expected"] and t["expected"].lower()[:30] in answer.lower()) else 0

                    conn = get_db()
                    c = conn.cursor()
                    c.execute("UPDATE test_cases SET last_result = ?, last_pass = ? WHERE id = ?", (answer, passed, t["id"]))
                    conn.commit()
                    conn.close()

                    results.append((t["question"], answer, passed))
                    progress.progress((i + 1) / len(tests))

                st.success(f"✅ Ran {len(results)} tests")
                for q, a, p in results:
                    icon = "✅" if p else "❌"
                    st.write(f"{icon} **{q}**")
                    st.caption(f"→ {a[:200]}")

            for t in tests:
                icon = "✅" if t["last_pass"] == 1 else ("❌" if t["last_pass"] == 0 else "⏸️")
                with st.expander(f"{icon} {t['question']}"):
                    st.write(f"**Expected:** {t['expected'] or '—'}")
                    st.write(f"**Last result:** {t['last_result'] or 'Not run yet'}")
                    if st.button("🗑️ Delete", key=f"dt_{t['id']}"):
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("DELETE FROM test_cases WHERE id = ?", (t["id"],))
                        conn.commit()
                        conn.close()
                        st.rerun()

    # ========================================================
    # COMPARE AGENTS
    # ========================================================
    elif page == "⚖️ Compare Agents":
        st.title("A/B Comparison")
        st.caption("Send the same message to two agents and compare responses.")

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM agents WHERE user_id = ?", (user_id,))
        agents = [dict(a) for a in c.fetchall()]
        conn.close()

        if len(agents) < 2:
            st.warning("Create at least 2 agents to compare.")
            return

        names = [a["name"] for a in agents]
        c1, c2 = st.columns(2)
        with c1:
            a_name = st.selectbox("Agent A", names, index=0)
        with c2:
            b_name = st.selectbox("Agent B", names, index=1)

        agent_a = next(a for a in agents if a["name"] == a_name)
        agent_b = next(a for a in agents if a["name"] == b_name)

        test_prompt = st.text_area("Test message", height=100, placeholder="Ask both agents the same question...")

        if st.button("▶️ Run Comparison", type="primary"):
            if not test_prompt:
                st.warning("Enter a message")
            else:
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader(f"🤖 {agent_a['name']}")
                    with st.spinner("Thinking..."):
                        msgs = [{"role": "system", "content": build_system_prompt(agent_a, user_id)}, {"role": "user", "content": test_prompt}]
                        r_a = ai_chat(msgs)
                        st.write(r_a)
                with c2:
                    st.subheader(f"🤖 {agent_b['name']}")
                    with st.spinner("Thinking..."):
                        msgs = [{"role": "system", "content": build_system_prompt(agent_b, user_id)}, {"role": "user", "content": test_prompt}]
                        r_b = ai_chat(msgs)
                        st.write(r_b)

    # ========================================================
    # ANALYTICS
    # ========================================================
    elif page == "📊 Analytics":
        st.title("Analytics")

        conn = get_db()
        c = conn.cursor()
        c.execute("""SELECT ch.*, a.name as agent_name FROM chats ch
            LEFT JOIN agents a ON ch.agent_id = a.id
            WHERE ch.user_id = ? ORDER BY ch.created_at DESC LIMIT 20""", (user_id,))
        chats = c.fetchall()
        conn.close()

        if not chats:
            st.info("No chats yet.")
        else:
            for ch in chats:
                with st.expander(f"💬 {ch['agent_name']} — {ch['title']} — {ch['created_at'][:19]}"):
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id", (ch["id"],))
                    msgs = c.fetchall()
                    conn.close()

                    if st.button("📈 Analyze", key=f"an_{ch['id']}"):
                        with st.spinner("Analyzing..."):
                            analysis = analyze_chat([dict(m) for m in msgs])
                            st.json(analysis)

                    for m in msgs:
                        role = "👤" if m["role"] == "user" else "🤖"
                        st.write(f"{role} {m['content']}")

# ============================================================
# ROUTER
# ============================================================
if st.session_state.user_id is None:
    auth_page()
else:
    main_app()
