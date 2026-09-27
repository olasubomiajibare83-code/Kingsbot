import streamlit as st
import sqlite3
import hashlib
import json
import requests
import base64
import math
import os
from datetime import datetime

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="NEXUS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_FILE = "nexus.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

OWNER_EMAILS = ["ajibaretemiloluwa@gmail.com"]

# ============================================================
# STYLING
# ============================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
    }
    
    .nexus-header {
        text-align: center;
        padding: 20px 0 10px 0;
    }
    .nexus-header h1 {
        font-family: Georgia, serif;
        font-size: 42px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .nexus-header p {
        color: rgba(255,255,255,0.5);
        font-size: 14px;
        margin-top: 4px;
    }
    
    .module-tile {
        background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(240,147,251,0.10));
        border: 1px solid rgba(240,147,251,0.25);
        border-radius: 20px;
        padding: 24px 16px;
        text-align: center;
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .module-icon { font-size: 42px; margin-bottom: 10px; }
    .module-title {
        font-size: 17px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 4px;
        font-family: Georgia, serif;
    }
    .module-desc { font-size: 11px; color: rgba(255,255,255,0.5); }
    
    .login-hero { text-align: center; padding: 60px 0 30px 0; }
    .login-hero h1 {
        font-family: Georgia, serif;
        font-size: 56px;
        background: linear-gradient(135deg, #667eea, #f093fb, #ffd93d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .login-hero p { color: rgba(255,255,255,0.6); font-size: 16px; margin-top: 8px; }
    
    .echo-memory {
        background: rgba(102,126,234,0.1);
        border-left: 3px solid #667eea;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .stButton > button {
        border-radius: 12px;
        border: 1px solid rgba(240,147,251,0.3);
        background: rgba(102,126,234,0.15);
        color: white;
        font-weight: 600;
    }
    .stButton > button:hover {
        border-color: rgba(240,147,251,0.7);
        background: rgba(102,126,234,0.3);
    }
    
    .note-card {
        background: rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 14px;
        margin: 6px 0;
        border-left: 3px solid #ffd93d;
    }
</style>
""", unsafe_allow_html=True)

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

    c.execute("""CREATE TABLE IF NOT EXISTS places (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        place_id INTEGER NOT NULL,
        photo_path TEXT,
        ai_description TEXT,
        user_note TEXT,
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

    c.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        content TEXT,
        tags TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        content TEXT,
        mood TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        topic TEXT,
        steps TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS repairs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        device TEXT,
        problem TEXT,
        steps TEXT,
        created_at TEXT NOT NULL)""")

    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def is_owner_email(e): return e.lower() in [x.lower() for x in OWNER_EMAILS]

def fix_owners():
    try:
        conn = get_db()
        c = conn.cursor()
        for email in OWNER_EMAILS:
            c.execute("UPDATE users SET is_owner = 1 WHERE LOWER(email) = LOWER(?)", (email,))
        conn.commit()
        conn.close()
    except: pass

fix_owners()

# ============================================================
# AI
# ============================================================
def ai_chat(messages, temperature=0.7):
    for url, headers, payload in [
        ("https://keylessai.thryx.workers.dev/v1/chat/completions",
         {"Content-Type": "application/json", "Authorization": "Bearer not-needed"},
         {"model": "gpt-4o-mini", "messages": messages, "temperature": temperature}),
        ("https://api.openzoo.fun/v1/chat/completions",
         {"Content-Type": "application/json", "Authorization": "Bearer sk-openzoo"},
         {"model": "z-ai/glm-5.3-flash", "messages": messages, "temperature": temperature}),
        ("https://api.llm7.io/v1/chat/completions",
         {"Content-Type": "application/json", "Authorization": "Bearer unused"},
         {"model": "gpt-4o-mini", "messages": messages, "temperature": temperature}),
    ]:
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=45)
            if r.status_code == 200:
                data = r.json()
                if data.get("choices") and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    if content and len(content.strip()) > 2:
                        return content.strip()
        except: pass
    return "⚠️ AI is busy. Try again."

def ai_describe_photo(photo_path):
    try:
        with open(photo_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        r = requests.post(
            "https://keylessai.thryx.workers.dev/v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": "Bearer not-needed"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": "Describe this place in one warm, poetic sentence. Under 25 words."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}}
                ]}],
                "temperature": 0.7
            }, timeout=45
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("choices"):
                return data["choices"][0]["message"]["content"].strip()
    except: pass
    return "A place you've seen."

def ai_compare_photos(p1, p2, name):
    try:
        with open(p1, "rb") as f: img1 = base64.b64encode(f.read()).decode()
        with open(p2, "rb") as f: img2 = base64.b64encode(f.read()).decode()
        r = requests.post(
            "https://keylessai.thryx.workers.dev/v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": "Bearer not-needed"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": f"Two photos of '{name}'. Write a 2-3 sentence 'What Changed' paragraph about differences."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img1}"}},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img2}"}}
                ]}],
                "temperature": 0.7
            }, timeout=45
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("choices"):
                return data["choices"][0]["message"]["content"].strip()
    except: pass
    return "The place has changed over time."

def ai_build_lesson(topic):
    prompt = f"""You are ATLAS, an expert teacher. Build a step-by-step lesson on: "{topic}"

Return ONLY valid JSON:
{{
  "title": "Lesson title",
  "intro": "One warm sentence",
  "steps": [
    {{"number": 1, "title": "Short title", "instruction": "Clear 2-3 sentence instruction", "check": "Question to confirm", "tip": "Pro tip"}}
  ],
  "outro": "Closing line"
}}

Make 5-7 steps. Break it into tiny pieces. Everyday language."""
    result = ai_chat([{"role": "user", "content": prompt}], temperature=0.6)
    try:
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except: return None

def ai_build_repair(device, problem):
    prompt = f"""You are ATLAS, an expert repair technician. Build a step-by-step repair guide.

Device: {device}
Problem: {problem}

Return ONLY valid JSON:
{{
  "title": "Repair title",
  "safety": "Safety warning if any",
  "steps": [
    {{"number": 1, "title": "Short title", "instruction": "Clear 2-3 sentence instruction", "check": "How to confirm it worked", "warning": "Warning if any"}}
  ],
  "outro": "Closing line"
}}

Make 5-8 steps. Real steps. Everyday language. If the repair needs a professional, say so clearly."""
    result = ai_chat([{"role": "user", "content": prompt}], temperature=0.5)
    try:
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except: return None

def ai_suggest_tags(content):
    try:
        r = ai_chat([{"role": "user", "content": f"Give 3 short tags (comma separated, single words) for this note:\n\n{content[:500]}"}])
        return r.replace("\n", " ").strip()[:100]
    except: return ""

# ============================================================
# SESSION
# ============================================================
for k, v in {
    "user_id": None, "name": None, "is_owner": False,
    "view": "home", "current_place_id": None,
    "current_chat_id": None, "current_lesson": None,
    "current_step": 0, "current_repair": None, "repair_step": 0,
    "atlas_history": []
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# AUTH
# ============================================================
def auth_page():
    st.markdown("""
    <div class="login-hero">
        <h1>🧠 NEXUS</h1>
        <p>One app. Many rooms. Everything you need.</p>
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
                        st.error("Fill both fields")
                    else:
                        conn = get_db(); c = conn.cursor()
                        c.execute("SELECT id, name, is_owner FROM users WHERE (username = ? OR email = ?) AND password_hash = ?", (u, u, hash_pw(p)))
                        user = c.fetchone(); conn.close()
                        if user:
                            st.session_state.user_id = user["id"]
                            st.session_state.name = user["name"] or u
                            st.session_state.is_owner = bool(user["is_owner"])
                            st.rerun()
                        else:
                            st.error("Invalid login.")
        with tab2:
            with st.form("signup_form"):
                n = st.text_input("Your Name")
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
                        st.error("Password must be 6+")
                    else:
                        try:
                            owner = 1 if is_owner_email(e) else 0
                            conn = get_db(); c = conn.cursor()
                            c.execute("INSERT INTO users (username, email, password_hash, name, is_owner, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (u, e, hash_pw(p), n, owner, datetime.now().isoformat()))
                            conn.commit(); conn.close()
                            st.success("✅ Account created!")
                        except sqlite3.IntegrityError:
                            st.error("Username or email taken.")

# ============================================================
# HOME — MODULE GRID
# ============================================================
def home_view():
    st.markdown(f"""
    <div class="nexus-header">
        <h1>🧠 NEXUS</h1>
        <p>Welcome back, {st.session_state.name}</p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    
    modules = [
        ("echo", "📸", "ECHO", "Remember places"),
        ("chat", "💬", "AI CHAT", "Talk to NEXUS"),
        ("tutor", "🎓", "TUTOR", "Learn anything"),
        ("repair", "🔧", "REPAIR", "Fix what's broken"),
        ("notes", "📝", "NOTES", "Thoughts organized"),
        ("journal", "📖", "JOURNAL", "Private diary"),
    ]
    
    cols = st.columns(3)
    for i, (mid, icon, title, desc) in enumerate(modules):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="module-tile">
                <div class="module-icon">{icon}</div>
                <div class="module-title">{title}</div>
                <div class="module-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Open {title}", key=f"open_{mid}", use_container_width=True):
                st.session_state.view = mid
                st.rerun()

def back_button(target="home"):
    if st.button("← Back"):
        st.session_state.view = target
        st.rerun()

# ============================================================
# ECHO
# ============================================================
def echo_view():
    user_id = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>📸 ECHO</h1><p>Remember places. Watch them change.</p></div>', unsafe_allow_html=True)
    back_button("home")
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Memory", "🗺️ My Places", "🔮 Compare"])
    
    with tab1:
        with st.form("add_memory"):
            photo = st.file_uploader("Photo", type=["jpg", "jpeg", "png"])
            location_name = st.text_input("Where is this?", placeholder="e.g. My street, Lagos")
            note = st.text_area("Note (optional)", height=80)
            if st.form_submit_button("💾 Save to ECHO", use_container_width=True, type="primary"):
                if not photo:
                    st.error("Upload a photo")
                else:
                    with st.spinner("ECHO is looking..."):
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filepath = os.path.join(UPLOAD_DIR, f"{user_id}_{ts}.jpg")
                        with open(filepath, "wb") as f:
                            f.write(photo.getbuffer())
                        description = ai_describe_photo(filepath)
                        conn = get_db(); c = conn.cursor()
                        c.execute("SELECT * FROM places WHERE user_id = ? AND name = ?", (user_id, location_name))
                        existing = c.fetchone()
                        if existing:
                            place_id = existing["id"]
                        else:
                            c.execute("INSERT INTO places (user_id, name, created_at) VALUES (?, ?, ?)",
                                (user_id, location_name or "Untitled", datetime.now().isoformat()))
                            place_id = c.lastrowid
                        c.execute("INSERT INTO memories (user_id, place_id, photo_path, ai_description, user_note, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                            (user_id, place_id, filepath, description, note, datetime.now().isoformat()))
                        conn.commit(); conn.close()
                    st.success("✅ Saved!")
                    st.markdown(f'<div class="echo-memory"><strong>🧠 ECHO sees:</strong><br>{description}</div>', unsafe_allow_html=True)
                    st.rerun()
    
    with tab2:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM places WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        places = c.fetchall(); conn.close()
        if not places:
            st.info("No places yet.")
        for p in places:
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT COUNT(*) as cnt FROM memories WHERE place_id = ?", (p["id"],))
            count = c.fetchone()["cnt"]; conn.close()
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"### 📍 {p['name']}")
                    st.caption(f"{count} visit(s)")
                with c2:
                    if st.button("View", key=f"view_place_{p['id']}", use_container_width=True):
                        st.session_state.current_place_id = p["id"]
                        st.session_state.view = "place_detail"
                        st.rerun()
    
    with tab3:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM places WHERE user_id = ?", (user_id,))
        places = c.fetchall(); conn.close()
        if not places:
            st.info("Add places first.")
        else:
            opts = {p["name"]: p["id"] for p in places}
            sel_name = st.selectbox("Choose a place", list(opts.keys()))
            sel_id = opts[sel_name]
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT * FROM memories WHERE place_id = ? ORDER BY created_at ASC", (sel_id,))
            mems = c.fetchall(); conn.close()
            if len(mems) < 2:
                st.warning("Need at least 2 visits to compare.")
            else:
                mem_opts = {f"Visit {i+1} — {m['created_at'][:16]}": m for i, m in enumerate(mems)}
                c1, c2 = st.columns(2)
                with c1: o1 = st.selectbox("Older", list(mem_opts.keys()), index=0)
                with c2: o2 = st.selectbox("Newer", list(mem_opts.keys()), index=len(mem_opts)-1)
                m1 = mem_opts[o1]; m2 = mem_opts[o2]
                cc1, cc2 = st.columns(2)
                with cc1:
                    st.caption(f"**{m1['created_at'][:16]}**")
                    if m1["photo_path"] and os.path.exists(m1["photo_path"]):
                        st.image(m1["photo_path"], use_container_width=True)
                    st.write(m1["ai_description"])
                with cc2:
                    st.caption(f"**{m2['created_at'][:16]}**")
                    if m2["photo_path"] and os.path.exists(m2["photo_path"]):
                        st.image(m2["photo_path"], use_container_width=True)
                    st.write(m2["ai_description"])
                if st.button("🔮 What Changed?", type="primary", use_container_width=True):
                    with st.spinner("..."):
                        changed = ai_compare_photos(m1["photo_path"], m2["photo_path"], sel_name)
                    st.markdown(f'<div class="echo-memory"><strong>🔮 What Changed:</strong><br>{changed}</div>', unsafe_allow_html=True)

def place_detail_view():
    pid = st.session_state.current_place_id
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM places WHERE id = ?", (pid,))
    place = c.fetchone()
    c.execute("SELECT * FROM memories WHERE place_id = ? ORDER BY created_at DESC", (pid,))
    mems = c.fetchall(); conn.close()
    if not place:
        st.session_state.view = "echo"; st.rerun(); return
    st.markdown(f'<div class="nexus-header"><h1>📍 {place["name"]}</h1><p>{len(mems)} visit(s)</p></div>', unsafe_allow_html=True)
    if st.button("← Back"):
        st.session_state.current_place_id = None
        st.session_state.view = "echo"
        st.rerun()
    st.divider()
    for i, m in enumerate(mems):
        with st.container(border=True):
            st.markdown(f"**Visit {len(mems) - i}** — {m['created_at'][:16]}")
            c1, c2 = st.columns([1, 2])
            with c1:
                if m["photo_path"] and os.path.exists(m["photo_path"]):
                    st.image(m["photo_path"], use_container_width=True)
            with c2:
                if m["ai_description"]: st.write(f"🧠 {m['ai_description']}")
                if m["user_note"]: st.write(f"📝 {m['user_note']}")

# ============================================================
# CHAT
# ============================================================
def chat_view():
    user_id = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>💬 NEXUS</h1><p>Talk to me. I remember.</p></div>', unsafe_allow_html=True)
    back_button("home")
    st.divider()
    
    with st.sidebar:
        st.markdown("### 💬 Chats")
        if st.button("➕ New Chat", use_container_width=True):
            conn = get_db(); c = conn.cursor()
            c.execute("INSERT INTO chats (user_id, title, created_at) VALUES (?, ?, ?)",
                (user_id, "New Chat", datetime.now().isoformat()))
            st.session_state.current_chat_id = c.lastrowid
            conn.commit(); conn.close(); st.rerun()
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM chats WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        chats = c.fetchall(); conn.close()
        for chat in chats:
            title = chat["title"] or "New Chat"
            prefix = "🟢 " if chat["id"] == st.session_state.current_chat_id else "💬 "
            if st.button(f"{prefix}{title[:20]}", key=f"chat_{chat['id']}", use_container_width=True):
                st.session_state.current_chat_id = chat["id"]; st.rerun()
    
    if st.session_state.current_chat_id is None:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO chats (user_id, title, created_at) VALUES (?, ?, ?)",
            (user_id, "New Chat", datetime.now().isoformat()))
        st.session_state.current_chat_id = c.lastrowid
        conn.commit(); conn.close(); st.rerun()
    
    chat_id = st.session_state.current_chat_id
    
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT name FROM places WHERE user_id = ? LIMIT 5", (user_id,))
    places = [p["name"] for p in c.fetchall()]
    conn.close()
    echo_ctx = f"\nUser has visited: {', '.join(places)}." if places else ""
    
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
    msgs = c.fetchall(); conn.close()
    for m in msgs:
        with st.chat_message(m["role"]):
            st.write(m["content"])
    
    prompt = st.chat_input("Message NEXUS...")
    if prompt:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, "user", prompt, datetime.now().isoformat()))
        c.execute("SELECT title FROM chats WHERE id = ?", (chat_id,))
        r = c.fetchone()
        if r and (r["title"] == "New Chat" or not r["title"]):
            c.execute("UPDATE chats SET title = ? WHERE id = ?", (prompt[:40], chat_id))
        conn.commit(); conn.close()
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("..."):
                conn = get_db(); c = conn.cursor()
                c.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
                hist = c.fetchall(); conn.close()
                api_msgs = [{"role": "system", "content": f"You are NEXUS — warm, patient, intelligent. Human-like.{echo_ctx}"}]
                for h in hist[-20:]:
                    api_msgs.append({"role": h["role"], "content": h["content"]})
                reply = ai_chat(api_msgs)
                st.write(reply)
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, "assistant", reply, datetime.now().isoformat()))
        conn.commit(); conn.close(); st.rerun()

# ============================================================
# TUTOR
# ============================================================
def tutor_view():
    user_id = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🎓 TUTOR</h1><p>Learn anything, step by step.</p></div>', unsafe_allow_html=True)
    back_button("home")
    st.divider()
    
    tab1, tab2 = st.tabs(["✨ New Lesson", "📖 My Lessons"])
    
    with tab1:
        with st.form("new_lesson"):
            topic = st.text_input("What do you want to learn?", placeholder="e.g. Python, photosynthesis, cooking jollof rice, fractions")
            if st.form_submit_button("🧠 Build My Lesson", type="primary", use_container_width=True):
                if not topic:
                    st.error("Enter a topic")
                else:
                    with st.spinner("ATLAS is preparing..."):
                        lesson = ai_build_lesson(topic)
                    if lesson:
                        conn = get_db(); c = conn.cursor()
                        c.execute("INSERT INTO lessons (user_id, title, topic, steps, created_at) VALUES (?, ?, ?, ?, ?)",
                            (user_id, lesson.get("title", topic), topic, json.dumps(lesson), datetime.now().isoformat()))
                        st.session_state.current_lesson = {"id": c.lastrowid, **lesson}
                        st.session_state.current_step = 0
                        conn.commit(); conn.close(); st.rerun()
                    else:
                        st.error("Couldn't build that lesson. Try again.")
        
        if st.session_state.current_lesson:
            L = st.session_state.current_lesson
            st.divider()
            st.markdown(f"## 📖 {L.get('title', 'Lesson')}")
            st.info(L.get("intro", ""))
            steps = L.get("steps", [])
            i = st.session_state.current_step
            st.progress(i / max(len(steps), 1))
            st.caption(f"Step {i+1} of {len(steps)}")
            
            if i < len(steps):
                s = steps[i]
                st.markdown(f"### Step {s.get('number', i+1)}: {s.get('title','')}")
                st.write(s.get("instruction", ""))
                if s.get("tip"): st.info(f"💡 {s['tip']}")
                if s.get("check"): st.markdown(f"**🤔 {s['check']}**")
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("✅ Next", type="primary", use_container_width=True):
                        st.session_state.current_step += 1; st.rerun()
                with c2:
                    if st.button("🤔 Don't Understand", use_container_width=True):
                        with st.spinner("..."):
                            reply = ai_chat([
                                {"role": "system", "content": "You are ATLAS, a patient teacher. Rephrase the step using simpler words, a metaphor, and a tiny example. Under 80 words."},
                                {"role": "user", "content": f"Step: {s.get('instruction')}"}
                            ])
                        st.warning(f"🧠 ATLAS: {reply}")
                with c3:
                    if st.button("⏸️ Pause", use_container_width=True):
                        st.session_state.current_lesson = None
                        st.session_state.current_step = 0
                        st.rerun()
            else:
                st.success("🎉 Lesson complete!")
                st.write(L.get("outro", "Well done."))
                if st.button("🔄 New Lesson"):
                    st.session_state.current_lesson = None
                    st.session_state.current_step = 0
                    st.rerun()
    
    with tab2:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM lessons WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        lessons = c.fetchall(); conn.close()
        if not lessons:
            st.info("No lessons yet.")
        for l in lessons:
            with st.expander(f"📖 {l['title']} — {l['created_at'][:10]}"):
                try:
                    data = json.loads(l["steps"])
                    st.write(data.get("intro", ""))
                    st.caption(f"{len(data.get('steps',[]))} steps")
                    if st.button("▶️ Open", key=f"reopen_{l['id']}"):
                        st.session_state.current_lesson = {"id": l["id"], **data}
                        st.session_state.current_step = 0
                        st.session_state.view = "tutor"
                        st.rerun()
                except: st.text("Lesson data unavailable")

# ============================================================
# REPAIR
# ============================================================
def repair_view():
    user_id = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🔧 REPAIR</h1><p>Tell me what\'s broken. I\'ll walk you through it.</p></div>', unsafe_allow_html=True)
    back_button("home")
    st.divider()
    
    tab1, tab2 = st.tabs(["🛠️ New Repair", "📖 My Repairs"])
    
    with tab1:
        with st.form("new_repair"):
            device = st.text_input("What device?", placeholder="e.g. iPhone 12, Samsung TV, ceiling fan")
            problem = st.text_area("What's wrong?", height=100, placeholder="e.g. My phone speaker stopped working")
            if st.form_submit_button("🔧 Build Repair Guide", type="primary", use_container_width=True):
                if not device or not problem:
                    st.error("Enter device and problem")
                else:
                    with st.spinner("ATLAS is analyzing..."):
                        guide = ai_build_repair(device, problem)
                    if guide:
                        conn = get_db(); c = conn.cursor()
                        c.execute("INSERT INTO repairs (user_id, device, problem, steps, created_at) VALUES (?, ?, ?, ?, ?)",
                            (user_id, device, problem, json.dumps(guide), datetime.now().isoformat()))
                        st.session_state.current_repair = {"id": c.lastrowid, **guide}
                        st.session_state.repair_step = 0
                        conn.commit(); conn.close(); st.rerun()
                    else:
                        st.error("Couldn't build the guide. Try again.")
        
        if st.session_state.current_repair:
            R = st.session_state.current_repair
            st.divider()
            st.markdown(f"## 🔧 {R.get('title', 'Repair')}")
            if R.get("safety"):
                st.error(f"⚠️ **Safety:** {R['safety']}")
            steps = R.get("steps", [])
            i = st.session_state.repair_step
            st.progress(i / max(len(steps), 1))
            st.caption(f"Step {i+1} of {len(steps)}")
            
            if i < len(steps):
                s = steps[i]
                st.markdown(f"### Step {s.get('number', i+1)}: {s.get('title','')}")
                st.write(s.get("instruction", ""))
                if s.get("warning"): st.warning(f"⚠️ {s['warning']}")
                if s.get("check"): st.markdown(f"**✅ {s['check']}**")
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("✅ Done — Next", type="primary", use_container_width=True):
                        st.session_state.repair_step += 1; st.rerun()
                with c2:
                    if st.button("🤔 Don't Understand", use_container_width=True):
                        with st.spinner("..."):
                            reply = ai_chat([
                                {"role": "system", "content": "You are ATLAS, a patient repair technician. Rephrase this step more simply with a metaphor. Under 80 words."},
                                {"role": "user", "content": f"Step: {s.get('instruction')}"}
                            ])
                        st.warning(f"🧠 ATLAS: {reply}")
                with c3:
                    if st.button("⏸️ Pause", use_container_width=True):
                        st.session_state.current_repair = None
                        st.session_state.repair_step = 0
                        st.rerun()
            else:
                st.success("🎉 Repair complete!")
                st.write(R.get("outro", "Good job."))
                if st.button("🔄 New Repair"):
                    st.session_state.current_repair = None
                    st.session_state.repair_step = 0
                    st.rerun()
    
    with tab2:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM repairs WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        repairs = c.fetchall(); conn.close()
        if not repairs:
            st.info("No repairs yet.")
        for r in repairs:
            with st.expander(f"🔧 {r['device']} — {r['created_at'][:10]}"):
                st.write(f"**Problem:** {r['problem']}")
                if st.button("▶️ Reopen", key=f"reopen_r_{r['id']}"):
                    try:
                        data = json.loads(r["steps"])
                        st.session_state.current_repair = {"id": r["id"], **data}
                        st.session_state.repair_step = 0
                        st.session_state.view = "repair"
                        st.rerun()
                    except: pass

# ============================================================
# NOTES
# ============================================================
def notes_view():
    user_id = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>📝 NOTES</h1><p>Thoughts that organize themselves.</p></div>', unsafe_allow_html=True)
    back_button("home")
    st.divider()
    
    with st.form("new_note"):
        title = st.text_input("Title")
        content = st.text_area("Note", height=150)
        if st.form_submit_button("💾 Save Note", type="primary", use_container_width=True):
            if not content:
                st.error("Write something")
            else:
                with st.spinner("Organizing..."):
                    tags = ai_suggest_tags(content)
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO notes (user_id, title, content, tags, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, title or content[:40], content, tags, datetime.now().isoformat()))
                conn.commit(); conn.close()
                st.success("✅ Saved!")
                st.rerun()
    
    st.divider()
    st.subheader("Your Notes")
    
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    notes = c.fetchall(); conn.close()
    
    if not notes:
        st.info("No notes yet.")
    else:
        search = st.text_input("🔍 Search notes", placeholder="Type to filter...")
        filtered = notes
        if search:
            s = search.lower()
            filtered = [n for n in notes if s in (n["content"] or "").lower() or s in (n["title"] or "").lower() or s in (n["tags"] or "").lower()]
        
        for n in filtered:
            with st.expander(f"📝 {n['title']} — {n['created_at'][:16]}"):
                st.write(n["content"])
                if n["tags"]:
                    st.caption(f"🏷️ {n['tags']}")
                if st.button("🗑️ Delete", key=f"del_note_{n['id']}"):
                    conn = get_db(); c = conn.cursor()
                    c.execute("DELETE FROM notes WHERE id = ?", (n["id"],))
                    conn.commit(); conn.close(); st.rerun()

# ============================================================
# JOURNAL
# ============================================================
def journal_view():
    user_id = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>📖 JOURNAL</h1><p>Your private diary. AI helps you reflect.</p></div>', unsafe_allow_html=True)
    back_button("home")
    st.divider()
    
    with st.form("new_entry"):
        title = st.text_input("Today's title", placeholder="e.g. A quiet Sunday")
        mood = st.selectbox("How do you feel?", ["😊 Happy", "😌 Calm", "🤔 Thoughtful", "😔 Sad", "😤 Frustrated", "😴 Tired", "🔥 Motivated", "😐 Neutral"])
        content = st.text_area("Write freely...", height=200)
        if st.form_submit_button("📖 Save Entry", type="primary", use_container_width=True):
            if not content:
                st.error("Write something")
            else:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO journal (user_id, title, content, mood, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, title or content[:40], content, mood, datetime.now().isoformat()))
                conn.commit(); conn.close()
                st.success("✅ Entry saved.")
                st.rerun()
    
    st.divider()
    st.subheader("Your Journal")
    
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM journal WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    entries = c.fetchall(); conn.close()
    
    if not entries:
        st.info("No entries yet.")
    else:
        for e in entries:
            with st.expander(f"{e['mood']} {e['title']} — {e['created_at'][:16]}"):
                st.write(e["content"])
                if st.button("🤔 AI Reflect", key=f"reflect_{e['id']}"):
                    with st.spinner("..."):
                        reflection = ai_chat([
                            {"role": "system", "content": "You are a warm, gentle journal companion. Reflect on this entry with empathy. Ask one gentle question. Under 60 words."},
                            {"role": "user", "content": e["content"]}
                        ])
                    st.info(f"💭 {reflection}")
                if st.button("🗑️ Delete", key=f"del_j_{e['id']}"):
                    conn = get_db(); c = conn.cursor()
                    c.execute("DELETE FROM journal WHERE id = ?", (e["id"],))
                    conn.commit(); conn.close(); st.rerun()

# ============================================================
# ROUTER
# ============================================================
if st.session_state.user_id is None:
    auth_page()
else:
    v = st.session_state.view
    if v == "home": home_view()
    elif v == "echo": echo_view()
    elif v == "place_detail": place_detail_view()
    elif v == "chat": chat_view()
    elif v == "tutor": tutor_view()
    elif v == "repair": repair_view()
    elif v == "notes": notes_view()
    elif v == "journal": journal_view()
    else: home_view()
