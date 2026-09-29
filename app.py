import streamlit as st
import streamlit.components.v1
import sqlite3
import hashlib
import json
import requests
import base64
import os
import random
import time
from datetime import datetime, timedelta

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

# ⚠️ CHANGE THIS TO YOUR EMAIL
OWNER_EMAILS = ["your-email@gmail.com"]

# ============================================================
# MAD STYLING — Animated, glowing, alive
# ============================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Animated multi-layer background */
    .stApp {
        background: linear-gradient(-45deg, #0a0a18, #1a1a3e, #2a1a4e, #0f1a3e, #0a0a18);
        background-size: 400% 400%;
        animation: gradientFlow 25s ease infinite;
    }
    @keyframes gradientFlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Aurora orbs */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background:
            radial-gradient(circle at 15% 20%, rgba(102,126,234,0.18) 0%, transparent 35%),
            radial-gradient(circle at 85% 30%, rgba(240,147,251,0.15) 0%, transparent 35%),
            radial-gradient(circle at 50% 80%, rgba(255,217,61,0.10) 0%, transparent 40%),
            radial-gradient(circle at 70% 90%, rgba(77,208,225,0.12) 0%, transparent 35%);
        animation: orbFloat 35s ease-in-out infinite alternate;
        pointer-events: none;
        z-index: 0;
    }
    @keyframes orbFloat {
        0% { transform: scale(1) translate(0, 0); }
        100% { transform: scale(1.15) translate(-2%, 2%); }
    }
    
    /* Star field */
    .stApp::after {
        content: "";
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        background-image:
            radial-gradient(1px 1px at 20% 30%, white, transparent),
            radial-gradient(1px 1px at 60% 70%, white, transparent),
            radial-gradient(2px 2px at 50% 50%, rgba(255,255,255,0.6), transparent),
            radial-gradient(1px 1px at 80% 10%, white, transparent),
            radial-gradient(1px 1px at 90% 60%, rgba(255,255,255,0.5), transparent),
            radial-gradient(1px 1px at 33% 80%, white, transparent),
            radial-gradient(1px 1px at 10% 90%, rgba(255,255,255,0.4), transparent),
            radial-gradient(1px 1px at 70% 40%, white, transparent);
        background-size: 550px 550px, 350px 350px, 250px 250px, 400px 400px,
                         300px 300px, 450px 450px, 500px 500px, 380px 380px;
        background-repeat: repeat;
        animation: starsTwinkle 8s ease-in-out infinite alternate;
        opacity: 0.35;
        pointer-events: none;
        z-index: 0;
    }
    @keyframes starsTwinkle {
        0% { opacity: 0.2; }
        100% { opacity: 0.5; }
    }
    
    .main, [data-testid="stAppViewContainer"] > .main {
        position: relative;
        z-index: 2;
    }
    
    /* Mood ring — colors the whole app */
    .mood-ring {
        position: fixed;
        top: 0; left: 0;
        width: 100%; height: 100%;
        pointer-events: none;
        z-index: 1;
        box-shadow: inset 0 0 120px 25px var(--mood-color, rgba(102,126,234,0.15));
        transition: box-shadow 1.5s ease;
    }
    
    /* Headers */
    .nexus-header {
        text-align: center;
        padding: 30px 0 18px 0;
        position: relative;
        z-index: 2;
    }
    .nexus-header h1 {
        font-family: 'Georgia', serif;
        font-size: 52px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #f093fb, #ffd93d, #4dd0e1, #667eea);
        background-size: 400% 400%;
        animation: gradientFlow 8s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        filter: drop-shadow(0 0 25px rgba(240,147,251,0.5)) drop-shadow(0 0 50px rgba(102,126,234,0.3));
        letter-spacing: 2px;
    }
    .nexus-header p {
        color: rgba(255,255,255,0.6);
        font-size: 15px;
        margin-top: 8px;
        letter-spacing: 1px;
    }
    
    /* Login hero */
    .login-hero {
        text-align: center;
        padding: 70px 0 40px 0;
        position: relative;
        z-index: 2;
    }
    .login-hero h1 {
        font-family: 'Georgia', serif;
        font-size: 72px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #f093fb, #ffd93d, #4dd0e1, #667eea);
        background-size: 400% 400%;
        animation: gradientFlow 8s ease infinite;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        filter: drop-shadow(0 0 30px rgba(240,147,251,0.6));
    }
    .login-hero p { color: rgba(255,255,255,0.7); font-size: 17px; margin-top: 12px; }
    
    /* Module tiles — glass */
    .module-tile {
        background: linear-gradient(135deg, rgba(102,126,234,0.22), rgba(240,147,251,0.15), rgba(77,208,225,0.12));
        border: 1px solid rgba(240,147,251,0.35);
        border-radius: 24px;
        padding: 32px 22px;
        text-align: center;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 10px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08);
        position: relative;
        overflow: hidden;
    }
    .module-tile:hover {
        transform: translateY(-10px) scale(1.03);
        border-color: rgba(240,147,251,0.9);
        box-shadow: 0 20px 60px rgba(240,147,251,0.35), 0 0 40px rgba(102,126,234,0.4);
    }
    .module-icon { font-size: 52px; margin-bottom: 14px; filter: drop-shadow(0 0 15px rgba(240,147,251,0.4)); }
    .module-title {
        font-size: 19px; font-weight: 700; color: #fff; margin-bottom: 6px;
        font-family: 'Georgia', serif; letter-spacing: 1px;
    }
    .module-desc { font-size: 12px; color: rgba(255,255,255,0.6); }
    
    /* Panels */
    .live-panel {
        background: linear-gradient(135deg, rgba(102,126,234,0.12), rgba(240,147,251,0.08));
        border: 1px solid rgba(240,147,251,0.2);
        border-radius: 18px;
        padding: 20px;
        backdrop-filter: blur(12px);
        margin: 12px 0;
    }
    .live-panel .time {
        font-size: 32px;
        font-family: 'Georgia', serif;
        background: linear-gradient(135deg, #667eea, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    .live-panel .label {
        font-size: 12px; color: rgba(255,255,255,0.5);
        letter-spacing: 2px; text-transform: uppercase;
    }
    
    /* Brain cards */
    .brain-card {
        background: linear-gradient(135deg, rgba(102,126,234,0.18), rgba(240,147,251,0.12));
        border: 1px solid rgba(240,147,251,0.3);
        border-radius: 18px;
        padding: 22px;
        margin: 14px 0;
        backdrop-filter: blur(14px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.06);
        position: relative;
        overflow: hidden;
    }
    .brain-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0;
        width: 4px; height: 100%;
        background: linear-gradient(180deg, #667eea, #f093fb, #ffd93d);
        animation: gradientFlow 4s ease infinite;
    }
    .brain-card .mood { font-size: 24px; margin-bottom: 8px; filter: drop-shadow(0 0 10px rgba(240,147,251,0.5)); }
    .brain-card .story { font-size: 15px; line-height: 1.6; margin: 10px 0; color: rgba(255,255,255,0.92); }
    .brain-card .pattern { font-size: 13px; color: rgba(255,255,255,0.6); font-style: italic; }
    .brain-card .meta { font-size: 11px; color: rgba(255,255,255,0.45); margin-top: 10px; letter-spacing: 1px; }
    
    /* ECHO blocks */
    .echo-memory {
        background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(77,208,225,0.1));
        border-left: 4px solid #667eea;
        padding: 16px 20px; border-radius: 10px; margin: 12px 0;
        box-shadow: 0 4px 20px rgba(102,126,234,0.15);
    }
    .echo-says {
        background: linear-gradient(135deg, rgba(240,147,251,0.15), rgba(255,217,61,0.08));
        border-left: 4px solid #f093fb;
        padding: 16px 20px; border-radius: 10px; margin: 12px 0;
        box-shadow: 0 4px 20px rgba(240,147,251,0.15);
    }
    .difference-item {
        background: rgba(255,217,61,0.1); border-left: 3px solid #ffd93d;
        padding: 11px 15px; border-radius: 6px; margin: 7px 0; font-size: 14px;
    }
    .missing-item {
        background: rgba(255,107,107,0.1); border-left: 3px solid #ff6b6b;
        padding: 11px 15px; border-radius: 6px; margin: 7px 0; font-size: 14px;
    }
    .same-item {
        background: rgba(107,203,119,0.1); border-left: 3px solid #6bcb77;
        padding: 11px 15px; border-radius: 6px; margin: 7px 0; font-size: 14px;
    }
    
    /* Stat cards */
    .stat-card {
        background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(240,147,251,0.1));
        border: 1px solid rgba(240,147,251,0.25);
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: all 0.3s;
    }
    .stat-card:hover {
        border-color: rgba(240,147,251,0.6);
        transform: translateY(-3px);
    }
    .stat-number {
        font-size: 32px; font-weight: 700;
        background: linear-gradient(135deg, #667eea, #f093fb);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-family: 'Georgia', serif;
    }
    .stat-label {
        font-size: 11px; color: rgba(255,255,255,0.5);
        letter-spacing: 2px; text-transform: uppercase; margin-top: 4px;
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 14px;
        border: 1px solid rgba(240,147,251,0.4);
        background: linear-gradient(135deg, rgba(102,126,234,0.3), rgba(240,147,251,0.2));
        color: white; font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(8px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .stButton > button:hover {
        border-color: rgba(240,147,251,1);
        background: linear-gradient(135deg, rgba(102,126,234,0.6), rgba(240,147,251,0.45));
        box-shadow: 0 0 25px rgba(240,147,251,0.6), 0 0 50px rgba(102,126,234,0.3);
        transform: translateY(-3px);
    }
    
    /* Thinking */
    .think-box {
        background: linear-gradient(135deg, rgba(240,147,251,0.1), rgba(77,208,225,0.08));
        border-left: 3px solid #f093fb;
        padding: 10px 16px; border-radius: 8px; margin: 10px 0;
        font-size: 13px; color: rgba(255,255,255,0.7); font-style: italic;
    }
    
    /* Streak flame */
    .flame {
        display: inline-block;
        animation: flamePulse 1.5s ease-in-out infinite;
    }
    @keyframes flamePulse {
        0%, 100% { transform: scale(1); filter: brightness(1); }
        50% { transform: scale(1.15); filter: brightness(1.3); }
    }
    
    /* Suggestion cards */
    .suggestion {
        background: linear-gradient(135deg, rgba(255,217,61,0.12), rgba(240,147,251,0.08));
        border: 1px solid rgba(255,217,61,0.3);
        border-radius: 14px;
        padding: 14px 18px; margin: 8px 0;
        display: flex; align-items: center; gap: 12px;
    }
    .suggestion .icon { font-size: 22px; }
    .suggestion .text { font-size: 14px; color: rgba(255,255,255,0.85); }
    
    /* Daily card */
    .daily-card {
        background: linear-gradient(135deg, rgba(240,147,251,0.15), rgba(102,126,234,0.12));
        border: 1px solid rgba(240,147,251,0.4);
        border-radius: 18px;
        padding: 20px;
        margin: 12px 0;
        box-shadow: 0 8px 30px rgba(240,147,251,0.2);
    }
    .daily-card .title {
        font-size: 12px; letter-spacing: 3px; text-transform: uppercase;
        color: #f093fb; font-weight: 700; margin-bottom: 10px;
    }
    .daily-card .quote {
        font-size: 17px; font-style: italic; line-height: 1.6;
        color: rgba(255,255,255,0.9);
    }
    .daily-card .author {
        font-size: 12px; color: rgba(255,255,255,0.5);
        margin-top: 10px; text-align: right;
    }
    
    /* Confetti */
    .confetti-piece {
        position: fixed; width: 10px; height: 10px;
        pointer-events: none; z-index: 9999;
        animation: confettiFall 3s linear forwards;
    }
    @keyframes confettiFall {
        0% { transform: translateY(-10vh) rotate(0deg); opacity: 1; }
        100% { transform: translateY(110vh) rotate(720deg); opacity: 0; }
    }
    
    /* Toast notification */
    .toast {
        position: fixed;
        top: 20px; right: 20px;
        background: linear-gradient(135deg, rgba(102,126,234,0.95), rgba(240,147,251,0.95));
        color: white; padding: 14px 20px;
        border-radius: 12px;
        box-shadow: 0 10px 40px rgba(240,147,251,0.5);
        z-index: 9999;
        animation: toastSlide 0.4s ease, toastFade 4s ease forwards;
        font-size: 14px;
        font-weight: 600;
    }
    @keyframes toastSlide {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes toastFade {
        0%, 70% { opacity: 1; }
        100% { opacity: 0; transform: translateX(400px); }
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
        xp INTEGER DEFAULT 0,
        streak INTEGER DEFAULT 0,
        last_active TEXT,
        created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS places (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        name TEXT, created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        place_id INTEGER NOT NULL, photo_path TEXT, photo_hash TEXT,
        ai_description TEXT, ai_objects TEXT, user_note TEXT, mood TEXT,
        created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS place_brains (
        id INTEGER PRIMARY KEY AUTOINCREMENT, place_id INTEGER UNIQUE NOT NULL,
        story TEXT, pattern TEXT, mood TEXT, first_seen TEXT, last_seen TEXT,
        total_visits INTEGER DEFAULT 0, updated_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        title TEXT, created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL,
        role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        title TEXT, content TEXT, tags TEXT, created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        title TEXT, content TEXT, mood TEXT, created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        title TEXT, topic TEXT, steps TEXT, created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS repairs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        device TEXT, problem TEXT, steps TEXT, created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS health_guides (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        symptoms TEXT, age_group TEXT, guide TEXT, created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        device TEXT, brand TEXT, model TEXT, created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_health (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        age_group TEXT, allergies TEXT, medications TEXT, created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS dreams (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        content TEXT, ai_interpretation TEXT, created_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS time_capsules (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        message TEXT, unlock_date TEXT, opened INTEGER DEFAULT 0,
        created_at TEXT NOT NULL)""")
    conn.commit()
    conn.close()

def migrate_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in c.fetchall()]
    for col, default in [("xp", "0"), ("streak", "0"), ("last_active", "NULL")]:
        if col not in cols:
            try: c.execute(f"ALTER TABLE users ADD COLUMN {col} DEFAULT {default}")
            except: pass
    conn.commit()
    conn.close()

init_db()
migrate_db()

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
# XP + STREAK + MOOD + CELEBRATE + TOAST
# ============================================================
def award_xp(user_id, amount, reason=""):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (amount, user_id))
    c.execute("SELECT xp FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    new_xp = row["xp"] if row else 0
    conn.commit(); conn.close()
    return new_xp

def update_streak(user_id):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT streak, last_active FROM users WHERE id = ?", (user_id,))
    u = c.fetchone()
    today = datetime.now().date().isoformat()
    if not u:
        conn.close(); return 0
    last = u["last_active"]
    streak = u["streak"] or 0
    if last == today:
        conn.close(); return streak
    yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
    if last == yesterday:
        streak += 1
    else:
        streak = 1
    c.execute("UPDATE users SET streak = ?, last_active = ? WHERE id = ?", (streak, today, user_id))
    conn.commit(); conn.close()
    return streak

def get_time_greeting():
    h = datetime.now().hour
    if h < 5: return "Still awake? 🌙"
    if h < 12: return "Good morning ☀️"
    if h < 17: return "Good afternoon 🌤️"
    if h < 21: return "Good evening 🌆"
    return "Good night 🌙"

def get_current_mood_color(user_id):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT mood FROM journal WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
    row = c.fetchone(); conn.close()
    if not row or not row["mood"]: return "rgba(102,126,234,0.15)"
    mood = row["mood"]
    if "😊" in mood or "😌" in mood or "🔥" in mood: return "rgba(107,203,119,0.18)"
    if "😔" in mood or "😤" in mood: return "rgba(255,107,107,0.18)"
    if "🤔" in mood: return "rgba(240,147,251,0.15)"
    if "😴" in mood: return "rgba(77,208,225,0.15)"
    return "rgba(102,126,234,0.15)"

def render_mood_ring(user_id):
    color = get_current_mood_color(user_id)
    st.markdown(f'<div class="mood-ring" style="--mood-color:{color};"></div>', unsafe_allow_html=True)

def celebrate():
    html = """
    <script>
        (function() {
            const colors = ['#667eea', '#f093fb', '#ffd93d', '#4dd0e1', '#6bcb77', '#ff6b6b'];
            for (let i = 0; i < 60; i++) {
                const piece = document.createElement('div');
                piece.className = 'confetti-piece';
                piece.style.left = Math.random() * 100 + 'vw';
                piece.style.background = colors[Math.floor(Math.random() * colors.length)];
                piece.style.animationDelay = Math.random() * 0.5 + 's';
                piece.style.animationDuration = (2 + Math.random() * 2) + 's';
                piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
                document.body.appendChild(piece);
                setTimeout(() => piece.remove(), 5000);
            }
        })();
    </script>
    """
    st.components.v1.html(html, height=0)

def toast(message):
    st.components.v1.html(f'<div class="toast">{message}</div>', height=0)

# ============================================================
# 🎁 SURPRISE FEATURES
# ============================================================
def get_surprise_messages():
    return [
        "You opened NEXUS at exactly the right moment.",
        "Every day you use this, NEXUS learns you a little more.",
        "Places you visit are becoming a map of your life.",
        "The next big idea might come from your next note.",
        "You've made more progress than you realize.",
        "NEXUS remembers everything so you don't have to.",
        "Your future self will thank you for what you save today.",
    ]

def get_daily_dream_prompt():
    return "What did you dream about last night? Describe it — I'll try to understand it."

def get_daily_ritual(user_id):
    """Pick one tiny ritual based on time of day."""
    h = datetime.now().hour
    if h < 11:
        return "☀️ Morning ritual: Write one thing you're grateful for in Journal."
    if h < 15:
        return "🌤️ Midday ritual: Snap a place you pass by today with ECHO."
    if h < 19:
        return "🌆 Evening ritual: Ask NEXUS a question in Chat."
    return "🌙 Night ritual: Write your day in Journal — NEXUS will reflect."

# ============================================================
# 🧠 BRAIN — Pollinations GPT-OSS 20B (Reasoning)
# ============================================================
def ai_chat(messages, temperature=0.7):
    try:
        r = requests.post(
            "https://text.pollinations.ai/openai",
            json={"model": "openai-fast", "messages": messages,
                  "temperature": temperature, "max_tokens": 1000},
            timeout=90
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("choices") and data["choices"][0]["message"]["content"]:
                content = data["choices"][0]["message"]["content"].strip()
                if len(content) > 2: return content
    except: pass
    try:
        r = requests.post(
            "https://text.pollinations.ai/openai",
            json={"model": "openai", "messages": messages, "temperature": temperature},
            timeout=90
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("choices") and data["choices"][0]["message"]["content"]:
                return data["choices"][0]["message"]["content"].strip()
    except: pass
    try:
        prompt = ""
        for m in messages:
            if m["role"] == "system": prompt += f"{m['content']}\n\n"
            elif m["role"] == "user": prompt += f"User: {m['content']}\n"
            elif m["role"] == "assistant": prompt += f"Assistant: {m['content']}\n"
        prompt += "Assistant:"
        r = requests.get(f"https://text.pollinations.ai/{requests.utils.quote(prompt)}", timeout=90)
        if r.status_code == 200 and len(r.text.strip()) > 3:
            return r.text.strip()
    except: pass
    return "⚠️ The AI is resting. Please send your message again in a few seconds."

def _img_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def ai_describe_photo(photo_path):
    try:
        img = _img_b64(photo_path)
        r = requests.post(
            "https://text.pollinations.ai/openai",
            json={"model": "openai", "messages": [{"role": "user", "content": [
                {"type": "text", "text": "Describe this place in one warm, poetic sentence under 25 words. If unclear, say 'The image is unclear'."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
            ]}], "temperature": 0.7}, timeout=90)
        if r.status_code == 200:
            data = r.json()
            if data.get("choices"): return data["choices"][0]["message"]["content"].strip()
    except: pass
    return "A place you've seen."

def ai_extract_objects(photo_path):
    try:
        img = _img_b64(photo_path)
        r = requests.post(
            "https://text.pollinations.ai/openai",
            json={"model": "openai", "messages": [{"role": "user", "content": [
                {"type": "text", "text": """List everything visible. Return ONLY a JSON array of short descriptions. 10-25 items. Only JSON."""},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
            ]}], "temperature": 0.3}, timeout=90)
        if r.status_code == 200:
            data = r.json()
            if data.get("choices"):
                txt = data["choices"][0]["message"]["content"].strip().replace("```json", "").replace("```", "").strip()
                s = txt.find("["); e = txt.rfind("]")
                if s != -1 and e != -1: return json.loads(txt[s:e+1])
    except: pass
    return []

def ai_what_did_i_miss(old_objects, old_description, new_objects, new_description, place_name):
    prompt = f"""ECHO comparing "{place_name}".
PREVIOUS: {old_description} | {json.dumps(old_objects)}
TODAY: {new_description} | {json.dumps(new_objects)}
Return ONLY JSON: {{"gone":[], "new":[], "changed":[], "same":[], "tiny_details":[], "weather_feel":"", "story":""}}
Only JSON."""
    result = ai_chat([{"role": "user", "content": prompt}], temperature=0.6)
    try:
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        s = clean.find("{"); e = clean.rfind("}")
        if s != -1 and e != -1: return json.loads(clean[s:e+1])
    except: pass
    return {"gone": [], "new": [], "changed": [], "same": [], "tiny_details": [],
            "weather_feel": "A day like any other.", "story": "The place has a story."}

def ai_place_brain(place_name, all_descriptions, all_dates, all_moods):
    visits_text = ""
    for i, (d, dt, mood) in enumerate(zip(all_descriptions, all_dates, all_moods)):
        visits_text += f"Visit {i+1} ({dt[:10]}, felt {mood}): {d}\n"
    prompt = f"""ECHO remembering "{place_name}". Visits: {visits_text}
Return ONLY JSON: {{"story": "2-3 sentences", "pattern": "1 sentence", "mood": "1 word"}}"""
    result = ai_chat([{"role": "user", "content": prompt}], temperature=0.75)
    try:
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        s = clean.find("{"); e = clean.rfind("}")
        if s != -1 and e != -1: return json.loads(clean[s:e+1])
    except: pass
    return {"story": f"A place you've visited {len(all_descriptions)} time(s).",
            "pattern": "You've returned here more than once.", "mood": "familiar"}

def ai_echo_speaks(place_name, current_visit_desc, previous_visits):
    if not previous_visits:
        prompt = f"""ECHO meeting new place "{place_name}". First impression: {current_visit_desc}. ONE warm sentence, under 20 words."""
    else:
        last = previous_visits[-1]
        prompt = f"""ECHO welcoming back to "{place_name}". Previous ({last['created_at'][:10]}): {last['ai_description']}. Today: {current_visit_desc}. ONE warm sentence, under 25 words."""
    return ai_chat([{"role": "user", "content": prompt}], temperature=0.8)

def ai_compare_photos(p1, p2, name):
    try:
        img1 = _img_b64(p1); img2 = _img_b64(p2)
        r = requests.post(
            "https://text.pollinations.ai/openai",
            json={"model": "openai", "messages": [{"role": "user", "content": [
                {"type": "text", "text": f"Two photos of '{name}'. Write a 2-3 sentence 'What Changed' paragraph."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img1}"}},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img2}"}}
            ]}], "temperature": 0.7}, timeout=90)
        if r.status_code == 200:
            data = r.json()
            if data.get("choices"): return data["choices"][0]["message"]["content"].strip()
    except: pass
    return "The place has changed over time."

def ai_build_lesson(topic):
    prompt = f"""ATLAS teacher. Lesson on: "{topic}"
Return ONLY JSON: {{"title":"","intro":"","steps":[{{"number":1,"title":"","instruction":"","check":"","tip":""}}],"outro":""}}
5-7 steps. Only JSON."""
    r = ai_chat([{"role": "user", "content": prompt}], temperature=0.6)
    try:
        clean = r.strip().replace("```json", "").replace("```", "").strip()
        s = clean.find("{"); e = clean.rfind("}")
        if s != -1 and e != -1: return json.loads(clean[s:e+1])
    except: pass
    return None

def ai_build_repair(device, problem, known_brand="", known_model=""):
    device_full = f"{known_brand} {known_model}".strip() or device
    prompt = f"""ATLAS repair technician. Device: {device_full}. Problem: {problem}.
Return ONLY JSON: {{"title":"","safety":"","tools_needed":[],"likely_cause":"","steps":[{{"number":1,"title":"","instruction":"","check":"","warning":""}}],"outro":""}}
5-8 real steps. Only JSON."""
    r = ai_chat([{"role": "user", "content": prompt}], temperature=0.5)
    try:
        clean = r.strip().replace("```json", "").replace("```", "").strip()
        s = clean.find("{"); e = clean.rfind("}")
        if s != -1 and e != -1: return json.loads(clean[s:e+1])
    except: pass
    return None

def ai_health_guide(symptoms, age_group, allergies="", medications=""):
    prompt = f"""ATLAS health guide. NOT a doctor.
Symptoms: {symptoms}. Age: {age_group}. Allergies: {allergies or 'None'}. Meds: {medications or 'None'}.
Return ONLY JSON: {{"title":"","seriousness":"Mild/Moderate/Serious/Emergency","possible_causes":[],"home_care":[],"medicines":[{{"name":"","dose":"","note":""}}],"warning_signs":[],"when_to_see_doctor":"","safety":"","outro":""}}
Only safe OTC medicines. Check allergies. Only JSON."""
    result = ai_chat([{"role": "user", "content": prompt}], temperature=0.4)
    try:
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        s = clean.find("{"); e = clean.rfind("}")
        if s != -1 and e != -1: return json.loads(clean[s:e+1])
    except: pass
    return None

def ai_suggest_tags(content):
    try:
        r = ai_chat([{"role": "user", "content": f"3 short comma-separated tags:\n{content[:400]}"}])
        return r.replace("\n", " ").strip()[:100]
    except: return ""

def ai_daily_quote():
    try:
        r = ai_chat([{"role": "user", "content": "Give ONE short inspiring sentence (max 15 words) for today. No quotes, no author."}])
        return r.strip().strip('"')[:120]
    except: return "Every small step builds a bigger tomorrow."

def ai_note_connections(user_id, new_content):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT title, content FROM notes WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,))
    old = c.fetchall(); conn.close()
    if not old: return ""
    old_text = "\n".join([f"- {n['title']}" for n in old])
    prompt = f"""Find connections.
NEW: {new_content[:300]}
OLD: {old_text}
If related, say ONE sentence: "Connects to: [title] because...". Else "No connections yet." Under 30 words."""
    return ai_chat([{"role": "user", "content": prompt}], temperature=0.5)

# 🎁 Surprise function: Dream Interpreter
def ai_interpret_dream(dream_text):
    prompt = f"""You are a warm, wise dream interpreter. Interpret this dream gently and poetically.
DREAM: {dream_text}
Return ONLY JSON: {{"meaning": "2-3 sentence poetic interpretation", "symbol": "one key symbol", "message": "one warm sentence for the dreamer"}}
Only JSON."""
    result = ai_chat([{"role": "user", "content": prompt}], temperature=0.8)
    try:
        clean = result.strip().replace("```json", "").replace("```", "").strip()
        s = clean.find("{"); e = clean.rfind("}")
        if s != -1 and e != -1: return json.loads(clean[s:e+1])
    except: pass
    return {"meaning": "Dreams are echoes of the heart.", "symbol": "mystery", "message": "Keep dreaming."}

# 🎁 Surprise function: Time Capsule
def ai_time_capsule_note(user_id, message):
    prompt = f"""A person just wrote a message to their future self:
"{message[:400]}"

Write a warm, personal 2-sentence note FROM their future self BACK TO them, in second person. Poetic and hopeful."""
    return ai_chat([{"role": "user", "content": prompt}], temperature=0.85)

# 🎁 Surprise function: Life Insights
def ai_life_insights(user_id):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) as x FROM memories WHERE user_id = ?", (user_id,))
    mem = c.fetchone()["x"]
    c.execute("SELECT COUNT(*) as x FROM journal WHERE user_id = ?", (user_id,))
    journ = c.fetchone()["x"]
    c.execute("SELECT mood FROM journal WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,))
    moods = [m["mood"] for m in c.fetchall() if m["mood"]]
    c.execute("SELECT COUNT(*) as x FROM notes WHERE user_id = ?", (user_id,))
    notes = c.fetchone()["x"]
    conn.close()
    prompt = f"""A person's data:
- Places remembered: {mem}
- Journal entries: {journ}
- Recent moods: {', '.join(moods) if moods else 'none'}
- Notes written: {notes}

Write ONE short, warm, personal insight (max 25 words) about their life right now. Make it specific, not generic."""
    return ai_chat([{"role": "user", "content": prompt}], temperature=0.8)

# ============================================================
# SESSION
# ============================================================
defaults = {
    "user_id": None, "name": None, "is_owner": False,
    "view": "home", "current_place_id": None,
    "current_chat_id": None, "current_lesson": None,
    "current_step": 0, "current_repair": None, "repair_step": 0,
    "last_snap_result": None, "health_guide": None, "pick_device": "",
    "xp_earned": 0, "daily_quote": None,
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
        <p>One app. Many rooms. Powered by GPT-OSS 20B.</p>
        <p style="font-size:13px;opacity:0.5;margin-top:16px;">Where AI becomes a companion.</p>
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
                            update_streak(user["id"])
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
                    if not u or not e or not p: st.error("Fill all fields")
                    elif p != p2: st.error("Passwords don't match")
                    elif len(p) < 6: st.error("6+ characters")
                    else:
                        try:
                            owner = 1 if is_owner_email(e) else 0
                            conn = get_db(); c = conn.cursor()
                            c.execute("INSERT INTO users (username, email, password_hash, name, is_owner, xp, streak, last_active, created_at) VALUES (?, ?, ?, ?, ?, 0, 1, ?, ?)",
                                (u, e, hash_pw(p), n, owner, datetime.now().date().isoformat(), datetime.now().isoformat()))
                            conn.commit(); conn.close()
                            st.success("✅ Welcome to NEXUS! Now log in.")
                        except sqlite3.IntegrityError:
                            st.error("Username or email taken.")

# ============================================================
# HOME
# ============================================================
def home_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT xp, streak FROM users WHERE id = ?", (user_id,))
    stats = c.fetchone()
    c.execute("SELECT COUNT(*) as x FROM places WHERE user_id = ?", (user_id,))
    place_count = c.fetchone()["x"]
    c.execute("SELECT COUNT(*) as x FROM notes WHERE user_id = ?", (user_id,))
    note_count = c.fetchone()["x"]
    c.execute("SELECT COUNT(*) as x FROM journal WHERE user_id = ?", (user_id,))
    journal_count = c.fetchone()["x"]
    conn.close()
    
    xp = stats["xp"] if stats else 0
    streak = stats["streak"] if stats else 0
    
    st.markdown(f'<div class="nexus-header"><h1>🧠 NEXUS</h1><p>{get_time_greeting()}, {st.session_state.name}</p></div>', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{xp}</div><div class="stat-label">XP</div></div>', unsafe_allow_html=True)
    with c2:
        flame = "🔥" if streak > 1 else "✨"
        st.markdown(f'<div class="stat-card"><div class="stat-number"><span class="flame">{flame}</span> {streak}</div><div class="stat-label">Day Streak</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{place_count}</div><div class="stat-label">Places</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-card"><div class="stat-number">{note_count + journal_count}</div><div class="stat-label">Thoughts</div></div>', unsafe_allow_html=True)
    
    st.write("")
    
    now = datetime.now()
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.markdown(f"""
        <div class="live-panel">
            <div class="label">Now</div>
            <div class="time">{now.strftime('%I:%M %p')}</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.5);margin-top:6px;">{now.strftime('%A, %B %d')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        if not st.session_state.get("daily_quote"):
            with st.spinner("NEXUS whispers..."):
                st.session_state.daily_quote = ai_daily_quote()
        st.markdown(f"""
        <div class="daily-card">
            <div class="title">NEXUS whispers</div>
            <div class="quote">"{st.session_state.daily_quote}"</div>
            <div class="author">— from your companion</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 🎁 Surprise: Daily ritual
    st.markdown(f'<div class="suggestion"><span class="icon">🎯</span><span class="text">{get_daily_ritual(user_id)}</span></div>', unsafe_allow_html=True)
    
    st.write("")
    st.markdown("### 🚀 Your Rooms")
    
    modules = [
        ("echo", "📸", "ECHO", "Remember places"),
        ("chat", "💬", "AI CHAT", "Talk to NEXUS"),
        ("tutor", "🎓", "TUTOR", "Learn anything"),
        ("repair", "🔧", "ATLAS", "Fix devices & health"),
        ("notes", "📝", "NOTES", "Thoughts organized"),
        ("journal", "📖", "JOURNAL", "Private diary"),
        ("dreams", "🌙", "DREAMS", "Interpret your dreams"),
        ("capsule", "⏳", "TIME CAPSULE", "Message your future"),
    ]
    cols = st.columns(4)
    for i, (mid, icon, title, desc) in enumerate(modules):
        with cols[i % 4]:
            st.markdown(f'<div class="module-tile"><div class="module-icon">{icon}</div><div class="module-title">{title}</div><div class="module-desc">{desc}</div></div>', unsafe_allow_html=True)
            if st.button(f"Open {title}", key=f"open_{mid}", use_container_width=True):
                st.session_state.view = mid
                st.rerun()
    
    # 🎁 Surprise: Life insights
    st.divider()
    st.markdown("### 🔮 Your Life Insight")
    if "life_insight" not in st.session_state:
        with st.spinner("NEXUS is reading your story..."):
            st.session_state.life_insight = ai_life_insights(user_id)
    st.markdown(f'<div class="brain-card"><div class="story">✨ {st.session_state.life_insight}</div></div>', unsafe_allow_html=True)
    
    # Smart suggestions
    st.divider()
    st.markdown("### 💡 NEXUS suggests")
    suggestions = get_smart_suggestions(user_id)
    if suggestions:
        for icon, text in suggestions:
            st.markdown(f'<div class="suggestion"><span class="icon">{icon}</span><span class="text">{text}</span></div>', unsafe_allow_html=True)
    else:
        st.caption("You're on top of everything ✨")

def get_smart_suggestions(user_id):
    conn = get_db(); c = conn.cursor()
    suggestions = []
    c.execute("SELECT MAX(created_at) as last FROM memories WHERE user_id = ?", (user_id,))
    last_place = c.fetchone()["last"]
    if not last_place: suggestions.append(("📸", "Snap your first place with ECHO"))
    else:
        try:
            days = (datetime.now() - datetime.fromisoformat(last_place)).days
            if days >= 3: suggestions.append(("📍", f"You haven't snapped a place in {days} days"))
        except: pass
    c.execute("SELECT mood FROM journal WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
    lj = c.fetchone()
    if lj and ("😔" in (lj["mood"] or "") or "😤" in (lj["mood"] or "")):
        suggestions.append(("📖", "Your last mood was heavy — want to write again?"))
    c.execute("SELECT COUNT(*) as x FROM dreams WHERE user_id = ?", (user_id,))
    if c.fetchone()["x"] == 0: suggestions.append(("🌙", "Try Dream Interpreter tonight"))
    c.execute("SELECT COUNT(*) as x FROM time_capsules WHERE user_id = ?", (user_id,))
    if c.fetchone()["x"] == 0: suggestions.append(("⏳", "Write a message to your future self"))
    conn.close()
    return suggestions[:3]

def back_button(target="home"):
    if st.button("← Back"):
        st.session_state.view = target
        st.rerun()

# ============================================================
# ECHO
# ============================================================
def echo_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>📸 ECHO</h1><p>Snap a place. ECHO remembers everything.</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    tab_snap, tab_places, tab_brains, tab_compare = st.tabs(["📸 Snap a Place", "🗺️ My Places", "🧠 ECHO's Mind", "🔮 Compare"])
    
    with tab_snap:
        camera_photo = st.camera_input("📸 Take a photo")
        with st.expander("Or upload a photo"):
            uploaded = st.file_uploader("Choose", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        st.divider()
        place_name = st.text_input("Where is this place?", placeholder="e.g. My street, Lagos")
        feeling = st.selectbox("How does this place feel?",
            ["Peaceful", "Busy", "Warm", "Lonely", "Joyful", "Heavy", "Bright", "Quiet", "Alive", "Still"])
        note = st.text_area("Describe what you see (helps ECHO)", height=80)
        if st.button("💾 Save to ECHO", type="primary", use_container_width=True):
            photo_bytes = None
            if camera_photo is not None: photo_bytes = camera_photo.getvalue()
            elif uploaded is not None: photo_bytes = uploaded.getvalue()
            if not photo_bytes: st.error("Take or upload a photo first.")
            elif not place_name: st.error("Give the place a name.")
            else:
                with st.spinner("ECHO is thinking..."):
                    filepath, photo_hash = save_photo_safely(user_id, photo_bytes)
                    description = ai_describe_photo(filepath)
                    objects = ai_extract_objects(filepath)
                    if len(objects) == 0 and note:
                        description = note
                        objects = [n.strip() for n in note.split(",") if n.strip()]
                    elif note:
                        description = f"{description} — you noted: {note}"
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
                            try: previous_objects = json.loads(last["ai_objects"]) if last["ai_objects"] else []
                            except: previous_objects = []
                    else:
                        c.execute("INSERT INTO places (user_id, name, created_at) VALUES (?, ?, ?)",
                            (user_id, place_name, datetime.now().isoformat()))
                        place_id = c.lastrowid
                    c.execute("""INSERT INTO memories 
                        (user_id, place_id, photo_path, photo_hash, ai_description, ai_objects, user_note, mood, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (user_id, place_id, filepath, photo_hash, description,
                         json.dumps(objects), note, feeling, datetime.now().isoformat()))
                    miss_result = None
                    if previous_visits and previous_objects:
                        miss_result = ai_what_did_i_miss(previous_objects, previous_description, objects, description, place_name)
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
                        c.execute("""INSERT INTO place_brains (place_id, story, pattern, mood, first_seen, last_seen, total_visits, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (place_id, brain_data["story"], brain_data["pattern"], brain_data["mood"],
                             datetime.now().isoformat(), datetime.now().isoformat(), len(all_mems), datetime.now().isoformat()))
                    conn.commit(); conn.close()
                    greeting = ai_echo_speaks(place_name, description, previous_visits)
                    award_xp(user_id, 15, "place saved")
                    celebrate()
                    toast(f"✅ +15 XP · {place_name} remembered")
                    st.session_state.last_snap_result = {
                        "greeting": greeting, "description": description,
                        "objects": objects, "miss": miss_result, "brain": brain_data,
                        "is_new": is_new, "photo_path": filepath,
                    }
                st.rerun()
        
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
            if result["miss"]:
                miss = result["miss"]
                st.divider()
                st.subheader("🔍 What did I miss?")
                if miss.get("story"): st.markdown(f'<div class="brain-card"><div class="story">💭 {miss["story"]}</div></div>', unsafe_allow_html=True)
                if miss.get("weather_feel"): st.markdown(f'<div class="echo-says">🌤️ <em>{miss["weather_feel"]}</em></div>', unsafe_allow_html=True)
                if miss.get("gone"):
                    st.markdown("**❌ Gone:**")
                    for g in miss["gone"]: st.markdown(f'<div class="missing-item">🚫 {g}</div>', unsafe_allow_html=True)
                if miss.get("new"):
                    st.markdown("**✨ New:**")
                    for n in miss["new"]: st.markdown(f'<div class="difference-item">➕ {n}</div>', unsafe_allow_html=True)
                if miss.get("changed"):
                    st.markdown("**🔄 Changed:**")
                    for c_ in miss["changed"]: st.markdown(f'<div class="difference-item">🔄 {c_}</div>', unsafe_allow_html=True)
                if miss.get("tiny_details"):
                    st.markdown("**🔎 Tiny details:**")
                    for t in miss["tiny_details"]: st.markdown(f'<div class="difference-item">🔍 {t}</div>', unsafe_allow_html=True)
                if miss.get("same"):
                    with st.expander("✅ Unchanged"):
                        for s in miss["same"]: st.markdown(f'<div class="same-item">✓ {s}</div>', unsafe_allow_html=True)
            if result["objects"]:
                with st.expander(f"📋 Everything ECHO noted ({len(result['objects'])} items)"):
                    for obj in result["objects"]: st.write(f"• {obj}")
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
    
    with tab_places:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM places WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        places = c.fetchall(); conn.close()
        if not places: st.info("No places yet.")
        for p in places:
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT COUNT(*) as cnt FROM memories WHERE place_id = ?", (p["id"],))
            count = c.fetchone()["cnt"]
            c.execute("SELECT * FROM place_brains WHERE place_id = ?", (p["id"],))
            brain = c.fetchone(); conn.close()
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"### 📍 {p['name']}")
                    if brain:
                        st.caption(f"🧠 *{brain['mood']}* • {count} visit(s)")
                        st.write(f"💭 {brain['story']}")
                    else: st.caption(f"{count} visit(s)")
                with c2:
                    if st.button("Visit", key=f"view_place_{p['id']}", use_container_width=True):
                        st.session_state.current_place_id = p["id"]
                        st.session_state.view = "place_detail"
                        st.rerun()
    
    with tab_brains:
        st.subheader("🧠 ECHO's Mind")
        conn = get_db(); c = conn.cursor()
        c.execute("""SELECT pb.*, p.name as place_name FROM place_brains pb
            JOIN places p ON pb.place_id = p.id
            WHERE p.user_id = ? ORDER BY pb.last_seen DESC""", (user_id,))
        brains = c.fetchall(); conn.close()
        if not brains: st.info("ECHO hasn't met your places yet.")
        for b in brains:
            st.markdown(f"""
            <div class="brain-card">
                <strong>📍 {b['place_name']}</strong>
                <div class="mood">💭 {b['mood']}</div>
                <div class="story">{b['story']}</div>
                <div class="pattern">🔄 {b['pattern']}</div>
                <div class="meta">First: {b['first_seen'][:10]} • Last: {b['last_seen'][:10]} • {b['total_visits']} visit(s)</div>
            </div>
            """, unsafe_allow_html=True)
    
    with tab_compare:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM places WHERE user_id = ?", (user_id,))
        places = c.fetchall(); conn.close()
        if not places: st.info("Add places first.")
        else:
            opts = {p["name"]: p["id"] for p in places}
            sel_name = st.selectbox("Choose a place", list(opts.keys()))
            sel_id = opts[sel_name]
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT * FROM memories WHERE place_id = ? ORDER BY created_at ASC", (sel_id,))
            mems = c.fetchall(); conn.close()
            if len(mems) < 2: st.warning("Need at least 2 visits.")
            else:
                mem_opts = {f"Visit {i+1} — {m['created_at'][:16]}": m for i, m in enumerate(mems)}
                c1, c2 = st.columns(2)
                with c1: o1 = st.selectbox("Older", list(mem_opts.keys()), index=0)
                with c2: o2 = st.selectbox("Newer", list(mem_opts.keys()), index=len(mem_opts)-1)
                m1 = mem_opts[o1]; m2 = mem_opts[o2]
                cc1, cc2 = st.columns(2)
                with cc1:
                    st.caption(f"**{m1['created_at'][:16]}**")
                    if m1["photo_path"] and os.path.exists(m1["photo_path"]): st.image(m1["photo_path"], use_container_width=True)
                    st.write(m1["ai_description"])
                with cc2:
                    st.caption(f"**{m2['created_at'][:16]}**")
                    if m2["photo_path"] and os.path.exists(m2["photo_path"]): st.image(m2["photo_path"], use_container_width=True)
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
    brain = c.fetchone(); conn.close()
    if not place: st.session_state.view = "echo"; st.rerun(); return
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
        st.session_state.current_place_id = None; st.session_state.view = "echo"; st.rerun()
    st.divider()
    for i, m in enumerate(mems):
        with st.container(border=True):
            st.markdown(f"**Visit {len(mems) - i}** — {m['created_at'][:16]} • felt *{m['mood'] or '—'}*")
            c1, c2 = st.columns([1, 2])
            with c1:
                if m["photo_path"] and os.path.exists(m["photo_path"]): st.image(m["photo_path"], use_container_width=True)
            with c2:
                if m["ai_description"]: st.write(f"🧠 {m['ai_description']}")
                if m["user_note"]: st.write(f"📝 {m['user_note']}")
                try:
                    objs = json.loads(m["ai_objects"]) if m["ai_objects"] else []
                    if objs:
                        with st.expander(f"📋 {len(objs)} objects noted"):
                            for o in objs: st.write(f"• {o}")
                except: pass

# ============================================================
# CHAT
# ============================================================
def chat_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>💬 NEXUS</h1><p>Powered by GPT-OSS 20B — real reasoning.</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
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
    nexus_ctx = get_nexus_context(user_id)
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
            think_placeholder = st.empty()
            think_placeholder.markdown('<div class="think-box">🧠 NEXUS is thinking...</div>', unsafe_allow_html=True)
            with st.spinner(""):
                conn = get_db(); c = conn.cursor()
                c.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
                hist = c.fetchall(); conn.close()
                system_prompt = f"""You are NEXUS — warm, patient, intelligent.
YOUR MEMORY OF THIS PERSON:
{nexus_ctx}
Speak warmly, personally. Reference their places, notes, journals naturally. Never say "as an AI". Be kind."""
                api = [{"role": "system", "content": system_prompt}]
                for h in hist[-20:]: api.append({"role": h["role"], "content": h["content"]})
                reply = ai_chat(api)
                think_placeholder.empty()
                st.write(reply)
        award_xp(user_id, 2, "chat")
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, "assistant", reply, datetime.now().isoformat()))
        conn.commit(); conn.close(); st.rerun()

# ============================================================
# TUTOR
# ============================================================
def tutor_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
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
                        conn.commit(); conn.close()
                        award_xp(user_id, 10, "lesson")
                        st.rerun()
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
                        st.session_state.current_step += 1
                        award_xp(user_id, 5, "step")
                        st.rerun()
                with c2:
                    if st.button("🤔 Don't Understand", use_container_width=True):
                        with st.spinner("..."):
                            reply = ai_chat([{"role":"system","content":"You are ATLAS. Rephrase simpler with metaphor. Under 80 words."},{"role":"user","content":s.get("instruction","")}])
                        st.warning(f"🧠 {reply}")
                with c3:
                    if st.button("⏸️ Pause", use_container_width=True):
                        st.session_state.current_lesson = None; st.session_state.current_step = 0; st.rerun()
            else:
                st.success("🎉 Lesson complete! +50 XP")
                award_xp(user_id, 50, "completed")
                celebrate()
                toast("🎉 +50 XP · Lesson finished!")
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

# ============================================================
# ATLAS
# ============================================================
def repair_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>🔧 ATLAS</h1><p>Smart technician. Kind health guide.</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    mode = st.radio("What do you need?", ["🔧 Fix a Device", "💊 Health Guidance", "📖 My History"], horizontal=True, label_visibility="collapsed")
    st.divider()
    if mode == "🔧 Fix a Device":
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM user_devices WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        known_devices = c.fetchall(); conn.close()
        if known_devices:
            st.caption("📱 Your devices (tap to select):")
            dev_cols = st.columns(min(4, len(known_devices)))
            for i, d in enumerate(known_devices[:4]):
                with dev_cols[i]:
                    label = f"{d['brand']} {d['model']}".strip() or d["device"]
                    if st.button(label, key=f"pick_dev_{d['id']}", use_container_width=True):
                        st.session_state.pick_device = label
        device = st.text_input("Device", value=st.session_state.get("pick_device", ""), placeholder="e.g. Samsung TV, iPhone 12")
        problem = st.text_area("What exactly is wrong?", height=100)
        with st.expander("➕ Add details (makes ATLAS smarter)"):
            brand = st.text_input("Brand", placeholder="e.g. Samsung")
            model = st.text_input("Model", placeholder="e.g. UA43T5300")
        if st.button("🔧 Build Smart Repair Guide", type="primary", use_container_width=True):
            if not device or not problem: st.error("Fill device and problem")
            else:
                if brand or model:
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO user_devices (user_id, device, brand, model, created_at) VALUES (?, ?, ?, ?, ?)",
                        (user_id, device, brand, model, datetime.now().isoformat()))
                    conn.commit(); conn.close()
                with st.spinner("ATLAS is thinking about your device..."):
                    guide = ai_build_repair(device, problem, brand, model)
                if guide:
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO repairs (user_id, device, problem, steps, created_at) VALUES (?, ?, ?, ?, ?)",
                        (user_id, device, problem, json.dumps(guide), datetime.now().isoformat()))
                    st.session_state.current_repair = {"id": c.lastrowid, **guide, "device_name": device}
                    st.session_state.repair_step = 0
                    st.session_state.pick_device = ""
                    conn.commit(); conn.close()
                    award_xp(user_id, 20, "repair")
                    st.rerun()
                else: st.error("Try again.")
        if st.session_state.current_repair:
            R = st.session_state.current_repair
            st.divider()
            st.markdown(f"## 🔧 {R.get('title','Repair Guide')}")
            st.caption(f"For: **{R.get('device_name','your device')}** • +20 XP")
            if R.get("likely_cause"): st.info(f"🎯 **Most likely cause:** {R['likely_cause']}")
            if R.get("safety"): st.error(f"⚠️ **Safety:** {R['safety']}")
            if R.get("tools_needed"): st.markdown(f"🧰 **Tools you need:** {' • '.join(R['tools_needed'])}")
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
                    if st.button("🤔 Stuck", use_container_width=True):
                        with st.spinner("..."):
                            reply = ai_chat([{"role":"system","content":f"You are ATLAS. Rephrase for a {R.get('device_name','device')}. Under 70 words."},{"role":"user","content":s.get("instruction","")}])
                        st.warning(f"🧠 {reply}")
                with c3:
                    if st.button("⏸️ Pause", use_container_width=True):
                        st.session_state.current_repair = None; st.session_state.repair_step = 0; st.rerun()
            else:
                st.success("🎉 Repair complete! +30 XP")
                award_xp(user_id, 30, "completed")
                celebrate()
                toast("🎉 +30 XP · Repair finished!")
                st.write(R.get("outro","Great work."))
                if st.button("🔄 New Repair"):
                    st.session_state.current_repair = None; st.session_state.repair_step = 0; st.rerun()
    elif mode == "💊 Health Guidance":
        st.caption("⚠️ ATLAS gives guidance, not a diagnosis. Always see a doctor for serious concerns.")
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM user_health WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
        last_health = c.fetchone(); conn.close()
        c1, c2 = st.columns(2)
        with c1:
            age_options = ["Baby (0-2)", "Child (3-12)", "Teen (13-19)", "Adult (20-59)", "Elderly (60+)"]
            default_age = 3
            if last_health and last_health["age_group"] in age_options:
                default_age = age_options.index(last_health["age_group"])
            age_group = st.selectbox("Age group", age_options, index=default_age)
        with c2:
            allergies = st.text_input("Allergies (optional)", value=last_health["allergies"] if last_health and last_health["allergies"] else "", placeholder="e.g. penicillin")
        medications = st.text_input("Current medications (optional)", value=last_health["medications"] if last_health and last_health["medications"] else "")
        symptoms = st.text_area("What are the symptoms?", height=120)
        if st.button("💊 Get Smart Guidance", type="primary", use_container_width=True):
            if not symptoms: st.error("Describe the symptoms")
            else:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO user_health (user_id, age_group, allergies, medications, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, age_group, allergies, medications, datetime.now().isoformat()))
                conn.commit(); conn.close()
                with st.spinner("ATLAS is thinking carefully..."):
                    guide = ai_health_guide(symptoms, age_group, allergies, medications)
                if guide:
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO health_guides (user_id, symptoms, age_group, guide, created_at) VALUES (?, ?, ?, ?, ?)",
                        (user_id, symptoms, age_group, json.dumps(guide), datetime.now().isoformat()))
                    conn.commit(); conn.close()
                    st.session_state.health_guide = guide
                    award_xp(user_id, 10, "health")
                    st.rerun()
        guide = st.session_state.get("health_guide")
        if guide:
            st.divider()
            seriousness = guide.get("seriousness", "Mild")
            colors = {"Mild": "🟢", "Moderate": "🟡", "Serious": "🟠", "Emergency": "🔴"}
            icons = colors.get(seriousness, "🟡")
            st.markdown(f"## {icons} {guide.get('title','Health Guidance')}")
            st.markdown(f"**Seriousness:** {icons} **{seriousness}**")
            if guide.get("safety"): st.error(f"⚠️ {guide['safety']}")
            st.subheader("🔍 Possible causes")
            for cause in guide.get("possible_causes", []):
                st.markdown(f'<div class="difference-item">• {cause}</div>', unsafe_allow_html=True)
            st.subheader("🏠 Home care")
            for step in guide.get("home_care", []):
                st.markdown(f'<div class="same-item">• {step}</div>', unsafe_allow_html=True)
            if guide.get("medicines"):
                st.subheader("💊 Medicines (safe for you)")
                for med in guide.get("medicines", []):
                    if isinstance(med, dict):
                        st.markdown(f"""
                        <div class="brain-card">
                            <strong>💊 {med.get('name','')}</strong><br>
                            <span style="font-size:13px;">Dose: {med.get('dose','')}</span><br>
                            <span style="font-size:12px;opacity:0.7;">{med.get('note','')}</span>
                        </div>
                        """, unsafe_allow_html=True)
            if guide.get("warning_signs"):
                st.subheader("🚨 Go to hospital if:")
                for sign in guide.get("warning_signs", []):
                    st.markdown(f'<div class="missing-item">🚨 {sign}</div>', unsafe_allow_html=True)
            if guide.get("when_to_see_doctor"):
                st.info(f"👨‍⚕️ **When to see a doctor:** {guide['when_to_see_doctor']}")
            if guide.get("outro"):
                st.markdown(f'<div class="echo-says">💙 <em>{guide["outro"]}</em></div>', unsafe_allow_html=True)
            if st.button("🔄 New Guidance"):
                st.session_state.health_guide = None; st.rerun()
    else:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM repairs WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (user_id,))
        repairs = c.fetchall()
        c.execute("SELECT * FROM health_guides WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (user_id,))
        health = c.fetchall(); conn.close()
        st.subheader("🔧 Repair History")
        for r in repairs:
            with st.expander(f"🔧 {r['device']} — {r['created_at'][:10]}"):
                st.write(f"**Problem:** {r['problem']}")
                if st.button("▶️ Reopen", key=f"reopen_r_{r['id']}"):
                    try:
                        data = json.loads(r["steps"])
                        st.session_state.current_repair = {"id": r["id"], **data, "device_name": r["device"]}
                        st.session_state.repair_step = 0
                        st.session_state.view = "repair"; st.rerun()
                    except: pass
        if health:
            st.divider()
            st.subheader("💊 Health History")
            for h in health:
                with st.expander(f"💊 {h['symptoms'][:40]}... — {h['created_at'][:10]}"):
                    try:
                        g = json.loads(h["guide"])
                        st.write(f"**Seriousness:** {g.get('seriousness','')}")
                    except: pass

# ============================================================
# NOTES
# ============================================================
def notes_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
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
                    connections = ai_note_connections(user_id, content)
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO notes (user_id, title, content, tags, created_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, title or content[:40], content, tags, datetime.now().isoformat()))
                conn.commit(); conn.close()
                award_xp(user_id, 5, "note")
                toast("✅ +5 XP · Note saved")
                st.success("✅ Saved! +5 XP")
                if connections and "no connections" not in connections.lower():
                    st.info(f"🔗 {connections}")
                st.rerun()
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

# ============================================================
# JOURNAL
# ============================================================
def journal_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
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
                award_xp(user_id, 8, "journal")
                toast("✅ +8 XP · Journal entry saved")
                st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM journal WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    entries = c.fetchall(); conn.close()
    for e in entries:
        with st.expander(f"{e['mood']} {e['title']} — {e['created_at'][:16]}"):
            st.write(e["content"])
            if st.button("🤔 AI Reflect", key=f"reflect_{e['id']}"):
                with st.spinner("..."):
                    reflection = ai_chat([{"role":"system","content":"Warm gentle journal companion. Reflect with empathy. Ask one gentle question. Under 60 words."},{"role":"user","content":e["content"]}])
                st.info(f"💭 {reflection}")
            if st.button("🗑️ Delete", key=f"del_j_{e['id']}"):
                conn = get_db(); c = conn.cursor()
                c.execute("DELETE FROM journal WHERE id = ?", (e["id"],))
                conn.commit(); conn.close(); st.rerun()

# ============================================================
# 🎁 SURPRISE MODULE 1: DREAM INTERPRETER
# ============================================================
def dreams_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>🌙 DREAMS</h1><p>What did you dream last night?</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    
    st.caption("Describe your dream. NEXUS will try to understand its meaning — gently and poetically.")
    with st.form("new_dream"):
        dream = st.text_area("Your dream...", height=200, placeholder="e.g. I was flying over a lake, then suddenly I fell into water...")
        if st.form_submit_button("🌙 Interpret My Dream", type="primary", use_container_width=True):
            if not dream: st.error("Describe your dream")
            else:
                with st.spinner("Reading your dream..."):
                    interp = ai_interpret_dream(dream)
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO dreams (user_id, content, ai_interpretation, created_at) VALUES (?, ?, ?, ?)",
                    (user_id, dream, json.dumps(interp), datetime.now().isoformat()))
                conn.commit(); conn.close()
                award_xp(user_id, 12, "dream")
                toast("🌙 +12 XP · Dream interpreted")
                st.rerun()
    
    st.divider()
    st.subheader("🌌 Your Dream Journal")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM dreams WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (user_id,))
    dreams = c.fetchall(); conn.close()
    
    if not dreams:
        st.info("No dreams yet. Write your first one above.")
    for d in dreams:
        with st.expander(f"🌙 {d['created_at'][:16]} — {d['content'][:50]}..."):
            st.write(f"**Dream:** {d['content']}")
            try:
                interp = json.loads(d["ai_interpretation"])
                st.markdown(f'<div class="brain-card"><div class="story">💭 <strong>Meaning:</strong> {interp.get("meaning","")}</div><div class="pattern">🔮 Symbol: {interp.get("symbol","")}</div></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="echo-says">💫 <em>{interp.get("message","")}</em></div>', unsafe_allow_html=True)
            except:
                st.write(d["ai_interpretation"])

# ============================================================
# 🎁 SURPRISE MODULE 2: TIME CAPSULE
# ============================================================
def capsule_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>⏳ TIME CAPSULE</h1><p>Send a message to your future self.</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    
    st.caption("Write a message. Choose when you want it unlocked. NEXUS will send it back to you — and let your future self reply.")
    with st.form("new_capsule"):
        message = st.text_area("Your message to the future...", height=200, placeholder="Dear future me, I hope...")
        unlock_date = st.date_input("Open on this date", value=datetime.now().date() + timedelta(days=365))
        if st.form_submit_button("🔒 Seal this Capsule", type="primary", use_container_width=True):
            if not message: st.error("Write a message")
            else:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO time_capsules (user_id, message, unlock_date, opened, created_at) VALUES (?, ?, ?, 0, ?)",
                    (user_id, message, str(unlock_date), datetime.now().isoformat()))
                conn.commit(); conn.close()
                award_xp(user_id, 25, "capsule")
                celebrate()
                toast("⏳ Capsule sealed! +25 XP")
                st.success("🔒 Sealed. NEXUS will hold it safe.")
                st.rerun()
    
    st.divider()
    st.subheader("📮 Your Capsules")
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM time_capsules WHERE user_id = ? ORDER BY unlock_date ASC", (user_id,))
    capsules = c.fetchall(); conn.close()
    
    if not capsules:
        st.info("No capsules yet. Write one above — it's a gift to your future self.")
    
    for cap in capsules:
        unlock = cap["unlock_date"]
        try:
            unlock_dt = datetime.strptime(unlock, "%Y-%m-%d").date()
            days_left = (unlock_dt - datetime.now().date()).days
        except:
            days_left = 999
        
        if days_left <= 0 and not cap["opened"]:
            with st.container(border=True):
                st.markdown(f"### 🔓 A capsule is ready!")
                st.caption(f"Sealed on {cap['created_at'][:10]} — ready to open")
                st.write(f"**You wrote:** {cap['message']}")
                if st.button("💌 Read the reply from future you", key=f"open_{cap['id']}"):
                    with st.spinner("Your future self is writing back..."):
                        reply = ai_time_capsule_note(user_id, cap["message"])
                    conn = get_db(); c = conn.cursor()
                    c.execute("UPDATE time_capsules SET opened = 1 WHERE id = ?", (cap["id"],))
                    conn.commit(); conn.close()
                    st.markdown(f'<div class="brain-card"><div class="story">💌 {reply}</div></div>', unsafe_allow_html=True)
        else:
            with st.expander(f"🔒 Capsule — opens in {days_left} days ({unlock})"):
                st.caption("Still sealed. Come back later.")
                st.write(f"*You wrote on {cap['created_at'][:10]}*")

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
    elif v == "dreams": dreams_view()
    elif v == "capsule": capsule_view()
    else: home_view()
