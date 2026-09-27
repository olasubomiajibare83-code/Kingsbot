import streamlit as st
import sqlite3
import hashlib
import json
import requests
import base64
import math
import os
import secrets
from datetime import datetime
from pathlib import Path

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
UPLOAD_DIR = "echo_vault"
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
    .stApp { background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%); }
    
    .nexus-header { text-align: center; padding: 20px 0 10px 0; }
    .nexus-header h1 {
        font-family: Georgia, serif;
        font-size: 42px; font-weight: 700;
        background: linear-gradient(135deg, #667eea, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .nexus-header p { color: rgba(255,255,255,0.5); font-size: 14px; margin-top: 4px; }
    
    .module-tile {
        background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(240,147,251,0.10));
        border: 1px solid rgba(240,147,251,0.25);
        border-radius: 20px; padding: 24px 16px; text-align: center;
        min-height: 150px; display: flex; flex-direction: column;
        justify-content: center; align-items: center;
    }
    .module-icon { font-size: 42px; margin-bottom: 10px; }
    .module-title { font-size: 17px; font-weight: 700; color: #fff; margin-bottom: 4px; font-family: Georgia, serif; }
    .module-desc { font-size: 11px; color: rgba(255,255,255,0.5); }
    
    .login-hero { text-align: center; padding: 60px 0 30px 0; }
    .login-hero h1 {
        font-family: Georgia, serif; font-size: 56px;
        background: linear-gradient(135deg, #667eea, #f093fb, #ffd93d);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .login-hero p { color: rgba(255,255,255,0.6); font-size: 16px; margin-top: 8px; }
    
    .echo-memory {
        background: rgba(102,126,234,0.1); border-left: 3px solid #667eea;
        padding: 12px 16px; border-radius: 8px; margin: 8px 0;
    }
    .echo-says {
        background: rgba(240,147,251,0.1); border-left: 3px solid #f093fb;
        padding: 12px 16px; border-radius: 8px; margin: 8px 0;
    }
    .brain-card {
        background: linear-gradient(135deg, rgba(102,126,234,0.12), rgba(240,147,251,0.08));
        border: 1px solid rgba(240,147,251,0.2);
        border-radius: 14px; padding: 18px; margin: 10px 0;
    }
    .brain-card .mood { font-size: 24px; }
    .brain-card .story { font-size: 15px; line-height: 1.5; margin: 8px 0; color: rgba(255,255,255,0.9); }
    .brain-card .pattern { font-size: 13px; color: rgba(255,255,255,0.55); font-style: italic; }
    .brain-card .meta { font-size: 11px; color: rgba(255,255,255,0.4); margin-top: 8px; }
    
    .difference-item {
        background: rgba(255,217,61,0.08);
        border-left: 3px solid #ffd93d;
        padding: 10px 14px; border-radius: 6px;
        margin: 6px 0; font-size: 14px;
    }
    .missing-item {
        background: rgba(255,107,107,0.08);
        border-left: 3px solid #ff6b6b;
        padding: 10px 14px; border-radius: 6px;
        margin: 6px 0; font-size: 14px;
    }
    .same-item {
        background: rgba(107,203,119,0.08);
        border-left: 3px solid #6bcb77;
        padding: 10px 14px; border-radius: 6px;
        margin: 6px 0; font-size: 14px;
    }
    
    .stButton > button {
        border-radius: 12px;
        border: 1px solid rgba(240,147,251,0.3);
        background: rgba(102,126,234,0.15);
        color: white; font-weight: 600;
    }
    .stButton > button:hover {
        border-color: rgba(240,147,251,0.7);
        background: rgba(102,126,234,0.3);
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
        lat REAL,
        lng REAL,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        place_id INTEGER NOT NULL,
        photo_path TEXT,
        photo_hash TEXT,
        ai_description TEXT,
        ai_objects TEXT,
        ai_analysis TEXT,
        user_note TEXT,
        mood TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS place_brains (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        place_id INTEGER UNIQUE NOT NULL,
        story TEXT,
        pattern TEXT,
        mood TEXT,
        first_seen TEXT,
        last_seen TEXT,
        total_visits INTEGER DEFAULT 0,
        updated_at TEXT NOT NULL)""")

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
        conn = get_db(); c = conn.cursor()
        for email in OWNER_EMAILS:
            c.execute("UPDATE users SET is_owner = 1 WHERE LOWER(email) = LOWER(?)", (email,))
        conn.commit(); conn.close()
    except: pass

fix_owners()

# ============================================================
# SAFE PHOTO STORAGE
# ============================================================
def save_photo_safely(user_id, photo_bytes):
    """Store photo with hashed name in echo_vault/<user_id>/."""
    user_dir = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    
    # Hash the photo content for deduplication
    photo_hash = hashlib.sha256(photo_bytes).hexdigest()[:16]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_{photo_hash}.jpg"
    filepath = os.path.join(user_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(photo_bytes)
    
    return filepath, photo_hash

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

def _img_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def ai_describe_photo(photo_path):
    try:
        img = _img_b64(photo_path)
        r = requests.post(
            "https://keylessai.thryx.workers.dev/v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": "Bearer not-needed"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": "Describe this place in one warm, poetic sentence under 25 words. Focus on buildings, nature, light, atmosphere."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
                ]}],
                "temperature": 0.7
            }, timeout=60
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("choices"):
                return data["choices"][0]["message"]["content"].strip()
    except: pass
    return "A place you've seen."

def ai_extract_objects(photo_path):
    """Extract list of objects/details visible in the photo — for the 'what did I miss' feature."""
    try:
        img = _img_b64(photo_path)
        r = requests.post(
            "https://keylessai.thryx.workers.dev/v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": "Bearer not-needed"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": """List every visible object, structure, plant, person, sign, or notable detail in this photo. 
Return ONLY a JSON array of short strings. Example: ["blue door", "mango tree", "cracked wall", "3 birds"]
Be specific and thorough — list 8-20 items. Only JSON, nothing else."""},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
                ]}],
                "temperature": 0.4
            }, timeout=60
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("choices"):
                txt = data["choices"][0]["message"]["content"].strip()
                txt = txt.replace("```json", "").replace("```", "").strip()
                return json.loads(txt)
    except: pass
    return []

def ai_what_did_i_miss(old_objects, old_description, new_objects, new_description, place_name):
    """The magic — what changed between visits."""
    prompt = f"""You are ECHO, comparing two visits to "{place_name}".

PREVIOUS visit:
- Description: {old_description}
- Objects seen: {json.dumps(old_objects)}

TODAY'S visit:
- Description: {new_description}
- Objects seen: {json.dumps(new_objects)}

Return ONLY valid JSON with this structure:
{{
  "gone": ["things that were there before but are missing now"],
  "new": ["things that are new today"],
  "changed": ["things that changed (e.g. 'blue door became red', 'tree grew taller')"],
  "same": ["things that are still there, unchanged"],
  "story": "A 2-3 sentence warm narrative of what changed, like a friend remembering with them."
}}

Be specific and gentle. Reference real items. Only JSON."""
    
    result = ai_chat([{"role": "user", "content": prompt}], temperature=0.6)
    try:
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return {"gone": [], "new": [], "changed": [], "same": [], "story": "The place has a story."}

def ai_place_brain(place_name, all_descriptions, all_dates, all_moods):
    visits_text = ""
    for i, (d, dt, mood) in enumerate(zip(all_descriptions, all_dates, all_moods)):
        visits_text += f"Visit {i+1} ({dt[:10]}, felt {mood}): {d}\n"
    
    prompt = f"""You are ECHO — an AI that remembers places like a human.

Place: "{place_name}"

Visit history:
{visits_text}

Return ONLY valid JSON:
{{
  "story": "2-3 sentence living story of this place. Warm, personal, like a friend remembering.",
  "pattern": "One-sentence observation about the visiting pattern (frequency, time, changes over time).",
  "mood": "One word capturing the overall feeling of this place"
}}

Be specific to actual visits. Do not invent."""
    
    result = ai_chat([{"role": "user", "content": prompt}], temperature=0.75)
    try:
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return {"story": f"A place you've visited {len(all_descriptions)} time(s).",
                "pattern": "You've returned here more than once.", "mood": "familiar"}

def ai_echo_speaks(place_name, current_visit_desc, previous_visits):
    if not previous_visits:
        prompt = f"""You are ECHO, meeting a new place for the first time.
Place: {place_name}
First impression: {current_visit_desc}
Say ONE warm sentence like meeting a new friend. Under 20 words."""
    else:
        last = previous_visits[-1]
        prompt = f"""You are ECHO, welcoming the user back to a familiar place.
Place: {place_name}
Previous visit ({last['created_at'][:10]}): {last['ai_description']}
Today: {current_visit_desc}
Total visits: {len(previous_visits) + 1}
Say ONE warm sentence welcoming them back, referencing the past. Under 25 words."""
    return ai_chat([{"role": "user", "content": prompt}], temperature=0.8)

def ai_compare_photos(p1, p2, name):
    try:
        img1 = _img_b64(p1); img2 = _img_b64(p2)
        r = requests.post(
            "https://keylessai.thryx.workers.dev/v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": "Bearer not-needed"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": f"Two photos of '{name}'. Write a 2-3 sentence 'What Changed' paragraph."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img1}"}},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img2}"}}
                ]}],
                "temperature": 0.7
            }, timeout=60
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("choices"):
                return data["choices"][0]["message"]["content"].strip()
    except: pass
    return "The place has changed over time."

def ai_build_lesson(topic):
    prompt = f"""You are ATLAS, expert teacher. Build a step-by-step lesson on: "{topic}"
Return ONLY valid JSON:
{{"title":"","intro":"","steps":[{{"number":1,"title":"","instruction":"","check":"","tip":""}}],"outro":""}}
5-7 steps, tiny pieces, everyday language."""
    r = ai_chat([{"role": "user", "content": prompt}], temperature=0.6)
    try: return json.loads(r.strip().replace("```json", "").replace("```", "").strip())
    except: return None

def ai_build_repair(device, problem):
    prompt = f"""You are ATLAS, repair technician. Build a repair guide.
Device: {device}
Problem: {problem}
Return ONLY valid JSON:
{{"title":"","safety":"","steps":[{{"number":1,"title":"","instruction":"","check":"","warning":""}}],"outro":""}}
5-8 steps, real, everyday language."""
    r = ai_chat([{"role": "user", "content": prompt}], temperature=0.5)
    try: return json.loads(r.strip().replace("```json", "").replace("```", "").strip())
    except: return None

def ai_suggest_tags(content):
    try:
        r = ai_chat([{"role": "user", "content": f"3 short comma-separated tags for this note:\n{content[:400]}"}])
        return r.replace("\n", " ").strip()[:100]
    except: return ""

# ============================================================
# SESSION
# ============================================================
defaults = {
    "user_id": None, "name": None, "is_owner": False,
    "view": "home", "current_place_id": None,
    "current_chat_id": None, "current_lesson": None,
    "current_step": 0, "current_repair": None, "repair_step": 0,
    "last_snap_result": None,
}
for k, v in defaults.items():
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
                        c.execute("SELECT id, name, is_owner FROM users WHERE (username = ? OR email = ?) AND password_hash = ?",
                            (u, u, hash_pw(p)))
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
                        st.error("6+ characters")
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
# HOME
# ============================================================
def home_view():
    st.markdown(f'<div class="nexus-header"><h1>🧠 NEXUS</h1><p>Welcome back, {st.session_state.name}</p></div>', unsafe_allow_html=True)
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
            st.markdown(f'<div class="module-tile"><div class="module-icon">{icon}</div><div class="module-title">{title}</div><div class="module-desc">{desc}</div></div>', unsafe_allow_html=True)
            if st.button(f"Open {title}", key=f"open_{mid}", use_container_width=True):
                st.session_state.view = mid
                st.rerun()

def back_button(target="home"):
    if st.button("← Back"):
        st.session_state.view = target
        st.rerun()

# ============================================================
# ECHO — with in-app camera, safe vault, and full brain
# ============================================================
def echo_view():
    user_id = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>📸 ECHO</h1><p>Snap a place. ECHO remembers everything.</p></div>', unsafe_allow_html=True)
    back_button("home")
    st.divider()
    
    tab_snap, tab_places, tab_brains, tab_compare = st.tabs(
        ["📸 Snap a Place", "🗺️ My Places", "🧠 ECHO's Mind", "🔮 Compare"]
    )
    
    # ==================== SNAP ====================
    with tab_snap:
        st.subheader("Snap the place")
        st.caption("Use your phone's camera. ECHO keeps every photo safe in your vault.")
        
        # In-app camera (works on mobile browsers)
        camera_photo = st.camera_input("📸 Take a photo")
        
        # Fallback: upload
        with st.expander("Or upload a photo"):
            uploaded = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        
        st.divider()
        
        place_name = st.text_input("Where is this place?", placeholder="e.g. My street, Lagos")
        feeling = st.selectbox("How does this place feel today?",
            ["Peaceful", "Busy", "Warm", "Lonely", "Joyful", "Heavy", "Bright", "Quiet", "Alive", "Still"])
        note = st.text_area("Any note? (optional)", height=80)
        
        if st.button("💾 Save to ECHO", type="primary", use_container_width=True):
            photo_bytes = None
            if camera_photo is not None:
                photo_bytes = camera_photo.getvalue()
            elif uploaded is not None:
                photo_bytes = uploaded.getvalue()
            
            if not photo_bytes:
                st.error("Take or upload a photo first.")
            elif not place_name:
                st.error("Give the place a name.")
            else:
                with st.spinner("ECHO is looking carefully at this place..."):
                    # Save photo safely
                    filepath, photo_hash = save_photo_safely(user_id, photo_bytes)
                    
                    # Analyze
                    description = ai_describe_photo(filepath)
                    objects = ai_extract_objects(filepath)
                    
                    conn = get_db(); c = conn.cursor()
                    c.execute("SELECT * FROM places WHERE user_id = ? AND name = ?", (user_id, place_name))
                    existing = c.fetchone()
                    is_new = existing is None
                    
                    previous_visits = []
                    previous_objects = []
                    previous_description = ""
                    
                    if existing:
                        place_id = existing["id"]
                        c.execute("SELECT * FROM memories WHERE place_id = ? ORDER BY created_at ASC", (place_id,))
                        previous_visits = [dict(r) for r in c.fetchall()]
                        if previous_visits:
                            last = previous_visits[-1]
                            previous_description = last["ai_description"] or ""
                            try:
                                previous_objects = json.loads(last["ai_objects"]) if last["ai_objects"] else []
                            except: previous_objects = []
                    else:
                        c.execute("INSERT INTO places (user_id, name, created_at) VALUES (?, ?, ?)",
                            (user_id, place_name, datetime.now().isoformat()))
                        place_id = c.lastrowid
                    
                    # Save memory
                    c.execute("""INSERT INTO memories 
                        (user_id, place_id, photo_path, photo_hash, ai_description, ai_objects, user_note, mood, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (user_id, place_id, filepath, photo_hash, description,
                         json.dumps(objects), note, feeling, datetime.now().isoformat()))
                    
                    # If this is not the first visit — compute "what did I miss"
                    miss_result = None
                    if previous_visits and previous_objects:
                        miss_result = ai_what_did_i_miss(
                            previous_objects, previous_description,
                            objects, description, place_name
                        )
                    
                    # Update the brain
                    c.execute("SELECT ai_description, created_at, mood FROM memories WHERE place_id = ? ORDER BY created_at ASC", (place_id,))
                    all_mems = c.fetchall()
                    descs = [m["ai_description"] or "" for m in all_mems]
                    dates = [m["created_at"] for m in all_mems]
                    moods = [m["mood"] or "neutral" for m in all_mems]
                    brain_data = ai_place_brain(place_name, descs, dates, moods)
                    
                    c.execute("SELECT id FROM place_brains WHERE place_id = ?", (place_id,))
                    brow = c.fetchone()
                    if brow:
                        c.execute("""UPDATE place_brains SET story = ?, pattern = ?, mood = ?, 
                            last_seen = ?, total_visits = ?, updated_at = ? WHERE place_id = ?""",
                            (brain_data["story"], brain_data["pattern"], brain_data["mood"],
                             datetime.now().isoformat(), len(all_mems), datetime.now().isoformat(), place_id))
                    else:
                        c.execute("""INSERT INTO place_brains 
                            (place_id, story, pattern, mood, first_seen, last_seen, total_visits, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (place_id, brain_data["story"], brain_data["pattern"], brain_data["mood"],
                             datetime.now().isoformat(), datetime.now().isoformat(), len(all_mems), datetime.now().isoformat()))
                    
                    conn.commit(); conn.close()
                    
                    # ECHO speaks
                    greeting = ai_echo_speaks(place_name, description, previous_visits)
                    
                    # Store for display
                    st.session_state.last_snap_result = {
                        "greeting": greeting,
                        "description": description,
                        "objects": objects,
                        "miss": miss_result,
                        "brain": brain_data,
                        "is_new": is_new,
                        "photo_path": filepath,
                    }
                st.rerun()
        
        # Show last snap result
        result = st.session_state.last_snap_result
        if result:
            st.divider()
            st.subheader("🧠 What ECHO saw")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                if os.path.exists(result["photo_path"]):
                    st.image(result["photo_path"], use_container_width=True)
            with c2:
                st.markdown(f'<div class="echo-memory"><strong>👁️ ECHO sees:</strong><br>{result["description"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="echo-says"><strong>💬 ECHO says:</strong><br><em>{result["greeting"]}</em></div>', unsafe_allow_html=True)
            
            # Show missed items
            if result["miss"]:
                miss = result["miss"]
                st.divider()
                st.subheader("🔍 What did I miss?")
                
                if miss.get("story"):
                    st.markdown(f'<div class="brain-card"><div class="story">{miss["story"]}</div></div>', unsafe_allow_html=True)
                
                if miss.get("gone"):
                    st.markdown("**❌ Gone since last time:**")
                    for g in miss["gone"]:
                        st.markdown(f'<div class="missing-item">🚫 {g}</div>', unsafe_allow_html=True)
                
                if miss.get("new"):
                    st.markdown("**✨ New today:**")
                    for n in miss["new"]:
                        st.markdown(f'<div class="difference-item">➕ {n}</div>', unsafe_allow_html=True)
                
                if miss.get("changed"):
                    st.markdown("**🔄 Changed:**")
                    for c_ in miss["changed"]:
                        st.markdown(f'<div class="difference-item">🔄 {c_}</div>', unsafe_allow_html=True)
                
                if miss.get("same"):
                    with st.expander("✅ Unchanged"):
                        for s in miss["same"]:
                            st.markdown(f'<div class="same-item">✓ {s}</div>', unsafe_allow_html=True)
            
            # Show all extracted objects
            if result["objects"]:
                with st.expander(f"📋 Everything ECHO noted ({len(result['objects'])} items)"):
                    for obj in result["objects"]:
                        st.write(f"• {obj}")
            
            # Show brain
            if result["brain"]:
                st.divider()
                st.subheader("🧠 Place Brain")
                b = result["brain"]
                st.markdown(f"""
                <div class="brain-card">
                    <div class="mood">💭 mood: {b.get('mood','?')}</div>
                    <div class="story">{b.get('story','')}</div>
                    <div class="pattern">🔄 {b.get('pattern','')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("✨ Done"):
                st.session_state.last_snap_result = None
                st.rerun()
    
    # ==================== MY PLACES ====================
    with tab_places:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM places WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        places = c.fetchall(); conn.close()
        if not places:
            st.info("No places yet. Go snap one.")
        for p in places:
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT COUNT(*) as cnt FROM memories WHERE place_id = ?", (p["id"],))
            count = c.fetchone()["cnt"]
            c.execute("SELECT * FROM place_brains WHERE place_id = ?", (p["id"],))
            brain = c.fetchone()
            conn.close()
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"### 📍 {p['name']}")
                    if brain:
                        st.caption(f"🧠 *{brain['mood']}* • {count} visit(s)")
                        st.write(f"💭 {brain['story']}")
                    else:
                        st.caption(f"{count} visit(s)")
                with c2:
                    if st.button("Visit", key=f"view_place_{p['id']}", use_container_width=True):
                        st.session_state.current_place_id = p["id"]
                        st.session_state.view = "place_detail"
                        st.rerun()
    
    # ==================== BRAINS ====================
    with tab_brains:
        st.subheader("🧠 ECHO's Mind")
        st.caption("How ECHO understands your places.")
        conn = get_db(); c = conn.cursor()
        c.execute("""SELECT pb.*, p.name as place_name FROM place_brains pb
            JOIN places p ON pb.place_id = p.id
            WHERE p.user_id = ? ORDER BY pb.last_seen DESC""", (user_id,))
        brains = c.fetchall(); conn.close()
        if not brains:
            st.info("ECHO hasn't met your places yet.")
        else:
            for b in brains:
                st.markdown(f"""
                <div class="brain-card">
                    <strong>📍 {b['place_name']}</strong>
                    <div class="mood">💭 {b['mood']}</div>
                    <div class="story">{b['story']}</div>
                    <div class="pattern">🔄 {b['pattern']}</div>
                    <div class="meta">First seen: {b['first_seen'][:10]} • Last: {b['last_seen'][:10]} • {b['total_visits']} visit(s)</div>
                </div>
                """, unsafe_allow_html=True)
    
    # ==================== COMPARE ====================
    with tab_compare:
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
    mems = c.fetchall()
    c.execute("SELECT * FROM place_brains WHERE place_id = ?", (pid,))
    brain = c.fetchone()
    conn.close()
    if not place:
        st.session_state.view = "echo"; st.rerun(); return
    
    st.markdown(f'<div class="nexus-header"><h1>📍 {place["name"]}</h1><p>{len(mems)} visit(s)</p></div>', unsafe_allow_html=True)
    
    if brain:
        st.markdown(f"""
        <div class="brain-card">
            <div class="mood">💭 {brain['mood']}</div>
            <div class="story">{brain['story']}</div>
            <div class="pattern">🔄 {brain['pattern']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("← Back"):
        st.session_state.current_place_id = None
        st.session_state.view = "echo"
        st.rerun()
    
    st.divider()
    st.subheader("🕰️ Timeline")
    
    for i, m in enumerate(mems):
        with st.container(border=True):
            st.markdown(f"**Visit {len(mems) - i}** — {m['created_at'][:16]} • felt *{m['mood'] or '—'}*")
            c1, c2 = st.columns([1, 2])
            with c1:
                if m["photo_path"] and os.path.exists(m["photo_path"]):
                    st.image(m["photo_path"], use_container_width=True)
            with c2:
                if m["ai_description"]:
                    st.write(f"🧠 {m['ai_description']}")
                if m["user_note"]:
                    st.write(f"📝 {m['user_note']}")
                try:
                    objs = json.loads(m["ai_objects"]) if m["ai_objects"] else []
                    if objs:
                        with st.expander(f"📋 {len(objs)} objects noted"):
                            for o in objs:
                                st.write(f"• {o}")
                except: pass

# ============================================================
# CHAT / TUTOR / REPAIR / NOTES / JOURNAL
# (keep from previous version — same as before)
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
    places = [p["name"] for p in c.fetchall()]; conn.close()
    ctx = f"\nUser has visited: {', '.join(places)}." if places else ""
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
    msgs = c.fetchall(); conn.close()
    for m in msgs:
        with st.chat_message(m["role"]): st.write(m["content"])
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
                api = [{"role": "system", "content": f"You are NEXUS — warm, patient, intelligent.{ctx}"}]
                for h in hist[-20:]: api.append({"role": h["role"], "content": h["content"]})
                reply = ai_chat(api); st.write(reply)
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, "assistant", reply, datetime.now().isoformat()))
        conn.commit(); conn.close(); st.rerun()

def tutor_view():
    user_id = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🎓 TUTOR</h1><p>Learn anything, step by step.</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    tab1, tab2 = st.tabs(["✨ New Lesson", "📖 My Lessons"])
    with tab1:
        with st.form("new_lesson"):
            topic = st.text_input("What do you want to learn?")
            if st.form_submit_button("🧠 Build Lesson", type="primary", use_container_width=True):
                if not topic: st.error("Enter a topic")
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
                    else: st.error("Try again.")
        if st.session_state.current_lesson:
            L = st.session_state.current_lesson
            st.divider()
            st.markdown(f"## 📖 {L.get('title','')}")
            st.info(L.get("intro",""))
            steps = L.get("steps", []); i = st.session_state.current_step
            st.progress(i / max(len(steps), 1))
            st.caption(f"Step {i+1} of {len(steps)}")
            if i < len(steps):
                s = steps[i]
                st.markdown(f"### Step {s.get('number',i+1)}: {s.get('title','')}")
                st.write(s.get("instruction",""))
                if s.get("tip"): st.info(f"💡 {s['tip']}")
                if s.get("check"): st.markdown(f"**🤔 {s['check']}**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("✅ Next", type="primary", use_container_width=True):
                        st.session_state.current_step += 1; st.rerun()
                with c2:
                    if st.button("🤔 Don't Understand", use_container_width=True):
                        with st.spinner("..."):
                            reply = ai_chat([{"role":"system","content":"You are ATLAS. Rephrase simpler with metaphor. Under 80 words."},{"role":"user","content":s.get("instruction","")}])
                        st.warning(f"🧠 {reply}")
                with c3:
                    if st.button("⏸️ Pause", use_container_width=True):
                        st.session_state.current_lesson = None; st.session_state.current_step = 0; st.rerun()
            else:
                st.success("🎉 Complete!")
                st.write(L.get("outro","Well done."))
                if st.button("🔄 New Lesson"):
                    st.session_state.current_lesson = None; st.session_state.current_step = 0; st.rerun()
    with tab2:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM lessons WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        lessons = c.fetchall(); conn.close()
        for l in lessons:
            with st.expander(f"📖 {l['title']} — {l['created_at'][:10]}"):
                try:
                    data = json.loads(l["steps"])
                    st.write(data.get("intro",""))
                    if st.button("▶️ Open", key=f"reopen_{l['id']}"):
                        st.session_state.current_lesson = {"id": l["id"], **data}
                        st.session_state.current_step = 0
                        st.session_state.view = "tutor"; st.rerun()
                except: st.text("Unavailable")

def repair_view():
    user_id = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🔧 REPAIR</h1><p>Tell me what\'s broken.</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    tab1, tab2 = st.tabs(["🛠️ New Repair", "📖 My Repairs"])
    with tab1:
        with st.form("new_repair"):
            device = st.text_input("Device", placeholder="e.g. iPhone 12, Samsung TV")
            problem = st.text_area("What's wrong?", height=100)
            if st.form_submit_button("🔧 Build Guide", type="primary", use_container_width=True):
                if not device or not problem: st.error("Enter both")
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
                    else: st.error("Try again.")
        if st.session_state.current_repair:
            R = st.session_state.current_repair
            st.divider()
            st.markdown(f"## 🔧 {R.get('title','')}")
            if R.get("safety"): st.error(f"⚠️ **Safety:** {R['safety']}")
            steps = R.get("steps", []); i = st.session_state.repair_step
            st.progress(i / max(len(steps), 1))
            st.caption(f"Step {i+1} of {len(steps)}")
            if i < len(steps):
                s = steps[i]
                st.markdown(f"### Step {s.get('number',i+1)}: {s.get('title','')}")
                st.write(s.get("instruction",""))
                if s.get("warning"): st.warning(f"⚠️ {s['warning']}")
                if s.get("check"): st.markdown(f"**✅ {s['check']}**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("✅ Done — Next", type="primary", use_container_width=True):
                        st.session_state.repair_step += 1; st.rerun()
                with c2:
                    if st.button("🤔 Don't Understand", use_container_width=True):
                        with st.spinner("..."):
                            reply = ai_chat([{"role":"system","content":"You are ATLAS, patient repair tech. Rephrase simpler. Under 80 words."},{"role":"user","content":s.get("instruction","")}])
                        st.warning(f"🧠 {reply}")
                with c3:
                    if st.button("⏸️ Pause", use_container_width=True):
                        st.session_state.current_repair = None; st.session_state.repair_step = 0; st.rerun()
            else:
                st.success("🎉 Complete!")
                st.write(R.get("outro","Good job."))
                if st.button("🔄 New Repair"):
                    st.session_state.current_repair = None; st.session_state.repair_step = 0; st.rerun()
    with tab2:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM repairs WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        repairs = c.fetchall(); conn.close()
        for r in repairs:
            with st.expander(f"🔧 {r['device']} — {r['created_at'][:10]}"):
                st.write(f"**Problem:** {r['problem']}")
                if st.button("▶️ Reopen", key=f"reopen_r_{r['id']}"):
                    try:
                        data = json.loads(r["steps"])
                        st.session_state.current_repair = {"id": r["id"], **data}
                        st.session_state.repair_step = 0
                        st.session_state.view = "repair"; st.rerun()
                    except: pass

def notes_view():
    user_id = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>📝 NOTES</h1><p>Thoughts that organize themselves.</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("new_note"):
        title = st.text_input("Title")
        content = st.text_area("Note", height=150)
        if st.form_submit_button("💾 Save", type="primary", use_container_width=True):
            if not content: st.error("Write something")
            else:
                with st.spinner("Organizing..."):
                    tags = ai_suggest_tags(content)
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO notes (user_id, title, content, tags, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, title or content[:40], content, tags, datetime.now().isoformat()))
                conn.commit(); conn.close()
                st.success("✅ Saved!"); st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    notes = c.fetchall(); conn.close()
    for n in notes:
        with st.expander(f"📝 {n['title']} — {n['created_at'][:16]}"):
            st.write(n["content"])
            if n["tags"]: st.caption(f"🏷️ {n['tags']}")
            if st.button("🗑️ Delete", key=f"del_note_{n['id']}"):
                conn = get_db(); c = conn.cursor()
                c.execute("DELETE FROM notes WHERE id = ?", (n["id"],))
                conn.commit(); conn.close(); st.rerun()

def journal_view():
    user_id = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>📖 JOURNAL</h1><p>Your private diary.</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("new_entry"):
        title = st.text_input("Title")
        mood = st.selectbox("Mood", ["😊 Happy","😌 Calm","🤔 Thoughtful","😔 Sad","😤 Frustrated","😴 Tired","🔥 Motivated","😐 Neutral"])
        content = st.text_area("Write freely...", height=200)
        if st.form_submit_button("📖 Save", type="primary", use_container_width=True):
            if not content: st.error("Write something")
            else:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO journal (user_id, title, content, mood, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, title or content[:40], content, mood, datetime.now().isoformat()))
                conn.commit(); conn.close()
                st.success("✅ Saved."); st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM journal WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    entries = c.fetchall(); conn.close()
    for e in entries:
        with st.expander(f"{e['mood']} {e['title']} — {e['created_at'][:16]}"):
            st.write(e["content"])
            if st.button("🤔 AI Reflect", key=f"reflect_{e['id']}"):
                with st.spinner("..."):
                    reflection = ai_chat([{"role":"system","content":"Warm, gentle journal companion. Reflect with empathy. Ask one gentle question. Under 60 words."},{"role":"user","content":e["content"]}])
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
