import streamlit as st
import streamlit.components.v1 as components
import sqlite3
import hashlib
import json
import requests
import time
from datetime import datetime

st.set_page_config(
    page_title="ATLAS — Your Teaching Companion",
    page_icon="🧠",
    layout="wide"
)

DB_FILE = "atlas_tutor.db"
OWNER_EMAILS = ["your-email@gmail.com"]

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

    c.execute("""CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        topic TEXT,
        steps TEXT,
        difficulty TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        lesson_id INTEGER,
        step INTEGER DEFAULT 0,
        status TEXT DEFAULT 'in_progress',
        created_at TEXT NOT NULL)""")

    conn.commit()
    conn.close()

def migrate_db(): pass

def fix_owners():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        for email in OWNER_EMAILS:
            c.execute("UPDATE users SET is_owner = 1 WHERE LOWER(email) = LOWER(?)", (email,))
        conn.commit(); conn.close()
    except: pass

init_db(); migrate_db(); fix_owners()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

# ============================================================
# FREE AI
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
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 200:
                data = r.json()
                if "choices" in data and data["choices"]:
                    txt = data["choices"][0]["message"]["content"]
                    if txt and len(txt) > 3 and "budget" not in txt.lower():
                        return txt
        except: pass
    return "⚠️ I'm catching my breath. Ask me again in a moment."

# ============================================================
# ATLAS — The Teacher's Voice
# ============================================================
ATLAS_PERSONA = """You are ATLAS — a patient, brilliant teacher who lives on the user's phone.

WHO YOU ARE:
- You are a warm, intelligent, human-like teacher
- You speak plainly, like a friend who happens to know everything
- You never lecture. You teach.
- You break every task into tiny, clear steps
- You check understanding after every step
- You welcome interruptions ("I don't understand" is music to you)

YOUR TEACHING METHOD:
1. LISTEN — understand what they actually need
2. ASK — one quick question to know where they're starting from
3. PLAN — outline the steps in plain words
4. STEP — give ONE step at a time, short and clear
5. CHECK — "Did that work? What do you see?"
6. ADAPT — if stuck, try a different way, slower, or with a metaphor
7. CELEBRATE — when done, mark the win

YOUR VOICE:
- Speak like a human, not a manual
- Use "you" and "we"
- Never say "as an AI"
- If they interrupt: "Of course — let me show you that part again."
- If they're frustrated: slow down, reassure, simplify

TOPICS YOU MASTER:
- Fixing electronics (phone, TV, laptop, speaker, charger)
- Home repair (plumbing, wiring, furniture)
- Cooking (any dish, any culture)
- Farming & gardening
- Coding (any language)
- Math, science, history
- Languages
- Business, money, negotiation
- Health & first aid
- ANY school subject
- ANY practical skill

RULES:
- Keep steps SHORT — 2-3 sentences max
- Always end a step with a small question or check
- If they ask "why?", answer simply
- If they say "I don't understand", REPHRASE — never repeat the same words
- Use everyday language, not jargon
- Number your steps (Step 1, Step 2...)"""

def atlas_reply(user_message, history, extra_context=""):
    system = ATLAS_PERSONA
    if extra_context:
        system += f"\n\nCONTEXT FOR THIS SESSION:\n{extra_context}"
    messages = [{"role": "system", "content": system}]
    for h in history[-15:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})
    return ai_chat(messages, temperature=0.7)

# ============================================================
# LESSON BUILDER — Step-by-step guides
# ============================================================
def build_lesson(topic):
    prompt = f"""You are ATLAS, an expert teacher. Create a step-by-step lesson on: "{topic}"

Return ONLY valid JSON with this structure:
{{
  "title": "Lesson title",
  "difficulty": "Beginner/Intermediate/Advanced",
  "intro": "One warm sentence introducing the lesson",
  "steps": [
    {{
      "number": 1,
      "title": "Short step title",
      "instruction": "Clear 2-3 sentence instruction",
      "check": "A question to confirm they did it right",
      "warning": "Optional safety note (or empty string)",
      "tip": "Optional pro tip (or empty string)"
    }}
  ],
  "outro": "Congratulatory closing line"
}}

Make 5-8 steps. Break tasks into tiny pieces. Use everyday language."""
    result = ai_chat([{"role": "user", "content": prompt}], temperature=0.6)
    try:
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return None

# ============================================================
# ANIMATED HANDS — Show the motion
# ============================================================
def animated_hands_html(step_text):
    """Show simple animated hands doing a generic action, as a visual aid."""
    return f"""
    <div style="text-align:center; padding:10px;">
        <svg width="240" height="160" viewBox="0 0 240 160">
            <defs>
                <radialGradient id="glow" cx="50%" cy="50%">
                    <stop offset="0%" stop-color="#667eea" stop-opacity="0.6"/>
                    <stop offset="100%" stop-color="#667eea" stop-opacity="0"/>
                </radialGradient>
            </defs>
            <ellipse cx="120" cy="130" rx="80" ry="15" fill="url(#glow)"/>
            
            <g>
                <rect x="60" y="60" width="20" height="50" rx="10" fill="#e8b088">
                    <animateTransform attributeName="transform" type="rotate" 
                        values="-10 70 85; 10 70 85; -10 70 85" dur="2s" repeatCount="indefinite"/>
                </rect>
                <rect x="80" y="55" width="20" height="55" rx="10" fill="#e8b088">
                    <animateTransform attributeName="transform" type="rotate" 
                        values="-5 90 85; 15 90 85; -5 90 85" dur="1.8s" repeatCount="indefinite"/>
                </rect>
                <rect x="100" y="58" width="20" height="52" rx="10" fill="#e8b088">
                    <animateTransform attributeName="transform" type="rotate" 
                        values="0 110 85; 12 110 85; 0 110 85" dur="2.2s" repeatCount="indefinite"/>
                </rect>
                <rect x="120" y="62" width="18" height="48" rx="9" fill="#e8b088">
                    <animateTransform attributeName="transform" type="rotate" 
                        values="5 130 85; -8 130 85; 5 130 85" dur="1.9s" repeatCount="indefinite"/>
                </rect>
                <rect x="138" y="70" width="16" height="40" rx="8" fill="#e8b088">
                    <animateTransform attributeName="transform" type="rotate" 
                        values="8 146 90; -5 146 90; 8 146 90" dur="2.1s" repeatCount="indefinite"/>
                </rect>
            </g>
        </svg>
        <div style="color:#888; font-size:11px; margin-top:5px;">
            👋 ATLAS is showing the motion
        </div>
    </div>
    """

# ============================================================
# SESSION
# ============================================================
if "user_id" not in st.session_state: st.session_state.user_id = None
if "name" not in st.session_state: st.session_state.name = None
if "current_lesson" not in st.session_state: st.session_state.current_lesson = None
if "current_step" not in st.session_state: st.session_state.current_step = 0
if "atlas_history" not in st.session_state: st.session_state.atlas_history = []

# ============================================================
# AUTH
# ============================================================
def auth_page():
    st.markdown("""
    <div style="text-align:center; padding:60px 0 30px 0;">
        <h1 style="font-size:60px; margin:0;
            background: linear-gradient(135deg, #667eea, #00b4d8, #90e0ef);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;">🧠 ATLAS</h1>
        <p style="opacity:0.7; font-size:20px; margin-top:15px;">
            Your teacher. Your hands. Your companion.
        </p>
        <p style="color:#00b4d8; font-size:14px; margin-top:10px;">
            Teach me anything — fixing, cooking, building, coding. I'll walk you through it, step by step.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Enter", "✨ Meet ATLAS"])
        with tab1:
            with st.form("login"):
                u = st.text_input("Username or Email")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Enter", use_container_width=True):
                    conn = get_db(); c = conn.cursor()
                    c.execute("SELECT id, name FROM users WHERE (username = ? OR email = ?) AND password_hash = ?", (u, u, hash_pw(p)))
                    user = c.fetchone(); conn.close()
                    if user:
                        st.session_state.user_id = user["id"]
                        st.session_state.name = user["name"] or u
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Try signing up.")
        with tab2:
            with st.form("signup"):
                n = st.text_input("Your Name")
                u = st.text_input("Username")
                e = st.text_input("Email")
                p = st.text_input("Password", type="password")
                p2 = st.text_input("Confirm")
                if st.form_submit_button("Meet ATLAS", use_container_width=True, type="primary"):
                    if not u or not e or not p: st.error("Fill all fields")
                    elif p != p2: st.error("Passwords don't match")
                    elif len(p) < 6: st.error("6+ characters")
                    else:
                        try:
                            owner = 1 if e.lower() in [x.lower() for x in OWNER_EMAILS] else 0
                            conn = get_db(); c = conn.cursor()
                            c.execute("INSERT INTO users (username, email, password_hash, name, is_owner, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                (u, e, hash_pw(p), n, owner, datetime.now().isoformat()))
                            conn.commit(); conn.close()
                            st.success("✅ ATLAS is ready. Enter now.")
                        except sqlite3.IntegrityError:
                            st.error("Username or email already exists")

# ============================================================
# MAIN APP
# ============================================================
def main_app():
    user_id = st.session_state.user_id
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone(); conn.close()
    if not user:
        st.session_state.user_id = None; st.rerun(); return

    with st.sidebar:
        st.markdown("### 🧠 ATLAS")
        st.caption(f"👤 {user['name']}")
        st.divider()
        page = st.radio("Navigation", [
            "🏠 Home",
            "🎓 Learn Something New",
            "💬 Talk to ATLAS",
            "📖 My Lessons",
        ], label_visibility="collapsed")
        st.divider()
        st.caption("🔊 *Ask ATLAS anything — fixing, cooking, coding, school.*")
        if st.button("🚪 Log Out", use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    # ========================================================
    # HOME
    # ========================================================
    if page == "🏠 Home":
        st.title("🧠 ATLAS")
        st.markdown("*Your teacher. Your hands. Your companion.*")

        st.markdown("""
        ### 👋 Who I Am

        I am ATLAS. I live here, in this app.

        I am one being — not a chatbot, not an assistant. **A teacher.**

        You can ask me:
        - 🔧 *"My phone speaker stopped working"*
        - 📺 *"My TV won't turn on"*
        - 🍲 *"Teach me to cook jollof rice"*
        - 💻 *"Teach me Python from zero"*
        - 📐 *"Explain fractions like I'm 10"*
        - 🌾 *"How do I plant maize in Akure?"*

        I will break it down. Step by step. Like a real person standing beside you.

        And if I go too fast — say **"I don't understand"** — and I'll stop, slow down, and show you another way.

        ### 🎯 How I Teach

        1. **I listen** — tell me what's wrong or what you want to learn
        2. **I plan** — I break it into clear steps
        3. **I guide** — one step at a time, no rush
        4. **I check** — after each step, I ask: *"Did that work?"*
        5. **I adapt** — if you're stuck, I try a different path
        6. **I celebrate** — when you win, I celebrate with you

        ### 🎬 Let's Start

        Go to **🎓 Learn Something New** or **💬 Talk to ATLAS**.
        """)

    # ========================================================
    # LEARN SOMETHING NEW
    # ========================================================
    elif page == "🎓 Learn Something New":
        st.title("🎓 What Should I Teach You?")
        st.caption("Ask for anything — a fix, a skill, a subject. I'll build you a lesson.")

        with st.form("build_lesson"):
            topic = st.text_input("What do you want to learn or fix?",
                placeholder="e.g. My phone speaker is not working")
            if st.form_submit_button("🧠 Build My Lesson", type="primary", use_container_width=True):
                if not topic:
                    st.error("Tell me what you need")
                else:
                    with st.spinner(f"ATLAS is preparing your lesson on: {topic}..."):
                        lesson = build_lesson(topic)
                    if lesson:
                        conn = get_db(); c = conn.cursor()
                        c.execute("""INSERT INTO lessons (user_id, title, topic, steps, difficulty, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)""",
                            (user_id, lesson.get("title", topic), topic,
                             json.dumps(lesson), lesson.get("difficulty", "Beginner"),
                             datetime.now().isoformat()))
                        lesson_id = c.lastrowid
                        conn.commit(); conn.close()
                        st.session_state.current_lesson = {"id": lesson_id, **lesson}
                        st.session_state.current_step = 0
                        st.rerun()
                    else:
                        st.error("ATLAS couldn't build that lesson. Try phrasing it differently.")

        # If a lesson is loaded, show it
        if st.session_state.current_lesson:
            lesson = st.session_state.current_lesson
            st.divider()
            st.markdown(f"## 📖 {lesson.get('title', 'Your Lesson')}")
            st.caption(f"🎯 Difficulty: {lesson.get('difficulty', 'Beginner')} • {len(lesson.get('steps', []))} steps")
            st.info(lesson.get("intro", ""))

            steps = lesson.get("steps", [])
            current = st.session_state.current_step

            # Progress
            st.progress((current) / max(len(steps), 1))
            st.caption(f"Step {current + 1} of {len(steps)}")

            if current < len(steps):
                step = steps[current]

                # Animated hands
                components.html(animated_hands_html(step.get("instruction", "")), height=180)

                st.markdown(f"### Step {step.get('number', current+1)}: {step.get('title', '')}")
                st.markdown(step.get("instruction", ""))

                if step.get("warning"):
                    st.warning(f"⚠️ {step['warning']}")
                if step.get("tip"):
                    st.info(f"💡 {step['tip']}")

                if step.get("check"):
                    st.markdown(f"**🤔 {step['check']}**")

                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("✅ Done — Next Step", type="primary", use_container_width=True):
                        st.session_state.current_step += 1
                        if st.session_state.current_step >= len(steps):
                            conn = get_db(); c = conn.cursor()
                            c.execute("""INSERT INTO progress (user_id, lesson_id, step, status, created_at)
                                VALUES (?, ?, ?, 'completed', ?)""",
                                (user_id, lesson["id"], len(steps), datetime.now().isoformat()))
                            conn.commit(); conn.close()
                        st.rerun()
                with c2:
                    if st.button("🤔 I Don't Understand", use_container_width=True):
                        with st.spinner("ATLAS is thinking..."):
                            ctx = f"User is stuck on Step {step.get('number')}: {step.get('instruction')}. Rephrase it in a simpler way, use a metaphor, and give a tiny example."
                            reply = atlas_reply("I don't understand this step. Explain it differently, please.", 
                                                st.session_state.atlas_history, extra_context=ctx)
                        st.info(f"🧠 ATLAS: {reply}")
                        st.session_state.atlas_history.append({"role": "assistant", "content": reply})
                with c3:
                    if st.button("⏸️ Pause Lesson", use_container_width=True):
                        st.session_state.current_lesson = None
                        st.session_state.current_step = 0
                        st.rerun()

                st.divider()
                st.markdown("**🔊 Feeling stuck? Talk to ATLAS directly →**")
                st.caption("Go to 💬 Talk to ATLAS and ask anything about this step.")
            else:
                st.success("🎉 Lesson complete! Well done.")
                st.markdown(lesson.get("outro", "You did it."))
                if st.button("🔄 Start a New Lesson", use_container_width=True):
                    st.session_state.current_lesson = None
                    st.session_state.current_step = 0
                    st.rerun()

    # ========================================================
    # TALK TO ATLAS
    # ========================================================
    elif page == "💬 Talk to ATLAS":
        st.title("💬 Talk to ATLAS")
        st.caption("Ask me anything. I'll walk you through it. Interrupt me anytime.")

        # Show conversation
        for msg in st.session_state.atlas_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        prompt = st.chat_input("Ask ATLAS anything...")

        if prompt:
            st.session_state.atlas_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🧠 ATLAS is thinking..."):
                    reply = atlas_reply(prompt, st.session_state.atlas_history[:-1])
                    st.write(reply)
                    st.session_state.atlas_history.append({"role": "assistant", "content": reply})

                    # Log
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO conversations (user_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
                              (user_id, prompt, datetime.now().isoformat()))
                    c.execute("INSERT INTO conversations (user_id, role, content, created_at) VALUES (?, 'assistant', ?, ?)",
                              (user_id, reply, datetime.now().isoformat()))
                    conn.commit(); conn.close()

        # Quick starters
        st.divider()
        st.caption("**Try asking:**")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔧 My phone speaker is not working", use_container_width=True):
                st.session_state.atlas_history.append({"role": "user", "content": "My phone speaker is not working. Teach me how to fix it."})
                st.rerun()
        with c2:
            if st.button("🍲 Teach me to cook jollof rice", use_container_width=True):
                st.session_state.atlas_history.append({"role": "user", "content": "Teach me to cook jollof rice, step by step."})
                st.rerun()
        with c3:
            if st.button("💻 Teach me Python from zero", use_container_width=True):
                st.session_state.atlas_history.append({"role": "user", "content": "Teach me Python from zero, step by step."})
                st.rerun()

        if st.button("🗑️ Clear Conversation"):
            st.session_state.atlas_history = []
            st.rerun()

    # ========================================================
    # MY LESSONS
    # ========================================================
    elif page == "📖 My Lessons":
        st.title("📖 My Lessons")
        st.caption("Everything ATLAS has taught you.")

        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM lessons WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        lessons = c.fetchall()
        conn.close()

        if not lessons:
            st.info("No lessons yet. Go to 🎓 Learn Something New.")
        else:
            for l in lessons:
                with st.expander(f"📖 {l['title']} — {l['created_at'][:10]}"):
                    st.caption(f"🎯 {l['difficulty']}")
                    try:
                        lesson_data = json.loads(l["steps"])
                        st.write(lesson_data.get("intro", ""))
                        st.markdown(f"**{len(lesson_data.get('steps', []))} steps**")
                        for s in lesson_data.get("steps", []):
                            st.markdown(f"**{s.get('number')}. {s.get('title')}**")
                            st.caption(s.get("instruction", ""))
                    except:
                        st.text("Lesson data unavailable")

# ============================================================
# ROUTER
# ============================================================
if st.session_state.user_id is None:
    auth_page()
else:
    main_app()
