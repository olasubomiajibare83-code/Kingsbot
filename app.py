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

st.set_page_config(
    page_title="NEXUS",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_FILE = "nexus.db"
UPLOAD_DIR = "echo_vault"
os.makedirs(UPLOAD_DIR, exist_ok=True)

OWNER_EMAILS = ["your-email@gmail.com"]

# ============================================================
# STYLING
# ============================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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
    .stApp::after {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image:
            radial-gradient(1px 1px at 20% 30%, white, transparent),
            radial-gradient(1px 1px at 60% 70%, white, transparent),
            radial-gradient(2px 2px at 50% 50%, rgba(255,255,255,0.6), transparent),
            radial-gradient(1px 1px at 80% 10%, white, transparent),
            radial-gradient(1px 1px at 90% 60%, rgba(255,255,255,0.5), transparent);
        background-size: 550px 550px, 350px 350px, 250px 250px, 400px 400px, 300px 300px;
        background-repeat: repeat;
        animation: starsTwinkle 8s ease-in-out infinite alternate;
        opacity: 0.35;
        pointer-events: none;
        z-index: 0;
    }
    @keyframes starsTwinkle { 0% { opacity: 0.2; } 100% { opacity: 0.5; } }
    .main, [data-testid="stAppViewContainer"] > .main { position: relative; z-index: 2; }
    .mood-ring {
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        pointer-events: none; z-index: 1;
        box-shadow: inset 0 0 120px 25px var(--mood-color, rgba(102,126,234,0.15));
        transition: box-shadow 1.5s ease;
    }
    .nexus-header { text-align: center; padding: 30px 0 18px 0; position: relative; z-index: 2; }
    .nexus-header h1 {
        font-family: 'Georgia', serif; font-size: 52px; font-weight: 700;
        background: linear-gradient(135deg, #667eea, #f093fb, #ffd93d, #4dd0e1, #667eea);
        background-size: 400% 400%; animation: gradientFlow 8s ease infinite;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0; filter: drop-shadow(0 0 25px rgba(240,147,251,0.5));
        letter-spacing: 2px;
    }
    .nexus-header p { color: rgba(255,255,255,0.6); font-size: 15px; margin-top: 8px; letter-spacing: 1px; }
    .login-hero { text-align: center; padding: 70px 0 40px 0; }
    .login-hero h1 {
        font-family: 'Georgia', serif; font-size: 72px; font-weight: 700;
        background: linear-gradient(135deg, #667eea, #f093fb, #ffd93d, #4dd0e1, #667eea);
        background-size: 400% 400%; animation: gradientFlow 8s ease infinite;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0; filter: drop-shadow(0 0 30px rgba(240,147,251,0.6));
    }
    .login-hero p { color: rgba(255,255,255,0.7); font-size: 17px; margin-top: 12px; }
    .module-tile {
        background: linear-gradient(135deg, rgba(102,126,234,0.22), rgba(240,147,251,0.15), rgba(77,208,225,0.12));
        border: 1px solid rgba(240,147,251,0.35);
        border-radius: 24px; padding: 28px 20px; text-align: center;
        min-height: 170px; display: flex; flex-direction: column;
        justify-content: center; align-items: center;
        backdrop-filter: blur(16px);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 10px 40px rgba(0,0,0,0.4);
        position: relative; overflow: hidden;
    }
    .module-tile:hover {
        transform: translateY(-10px) scale(1.03);
        border-color: rgba(240,147,251,0.9);
        box-shadow: 0 20px 60px rgba(240,147,251,0.35);
    }
    .module-icon { font-size: 48px; margin-bottom: 12px; }
    .module-title { font-size: 17px; font-weight: 700; color: #fff; font-family: 'Georgia', serif; }
    .module-desc { font-size: 11px; color: rgba(255,255,255,0.6); }
    .live-panel {
        background: linear-gradient(135deg, rgba(102,126,234,0.12), rgba(240,147,251,0.08));
        border: 1px solid rgba(240,147,251,0.2);
        border-radius: 18px; padding: 20px; backdrop-filter: blur(12px); margin: 12px 0;
    }
    .live-panel .time {
        font-size: 32px; font-family: 'Georgia', serif;
        background: linear-gradient(135deg, #667eea, #f093fb);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    .live-panel .label { font-size: 12px; color: rgba(255,255,255,0.5); letter-spacing: 2px; text-transform: uppercase; }
    .brain-card {
        background: linear-gradient(135deg, rgba(102,126,234,0.18), rgba(240,147,251,0.12));
        border: 1px solid rgba(240,147,251,0.3);
        border-radius: 18px; padding: 22px; margin: 14px 0;
        backdrop-filter: blur(14px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        position: relative; overflow: hidden;
    }
    .brain-card::before {
        content: ""; position: absolute; top: 0; left: 0;
        width: 4px; height: 100%;
        background: linear-gradient(180deg, #667eea, #f093fb, #ffd93d);
    }
    .brain-card .mood { font-size: 24px; margin-bottom: 8px; }
    .brain-card .story { font-size: 15px; line-height: 1.6; margin: 10px 0; color: rgba(255,255,255,0.92); }
    .brain-card .pattern { font-size: 13px; color: rgba(255,255,255,0.6); font-style: italic; }
    .brain-card .meta { font-size: 11px; color: rgba(255,255,255,0.45); margin-top: 10px; letter-spacing: 1px; }
    .echo-memory {
        background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(77,208,225,0.1));
        border-left: 4px solid #667eea;
        padding: 16px 20px; border-radius: 10px; margin: 12px 0;
    }
    .echo-says {
        background: linear-gradient(135deg, rgba(240,147,251,0.15), rgba(255,217,61,0.08));
        border-left: 4px solid #f093fb;
        padding: 16px 20px; border-radius: 10px; margin: 12px 0;
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
    .stat-card {
        background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(240,147,251,0.1));
        border: 1px solid rgba(240,147,251,0.25);
        border-radius: 14px; padding: 16px; text-align: center;
        backdrop-filter: blur(10px); transition: all 0.3s;
    }
    .stat-card:hover { border-color: rgba(240,147,251,0.6); transform: translateY(-3px); }
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
    .stButton > button {
        border-radius: 14px; border: 1px solid rgba(240,147,251,0.4);
        background: linear-gradient(135deg, rgba(102,126,234,0.3), rgba(240,147,251,0.2));
        color: white; font-weight: 600;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(8px);
    }
    .stButton > button:hover {
        border-color: rgba(240,147,251,1);
        background: linear-gradient(135deg, rgba(102,126,234,0.6), rgba(240,147,251,0.45));
        box-shadow: 0 0 25px rgba(240,147,251,0.6);
        transform: translateY(-3px);
    }
    .think-box {
        background: linear-gradient(135deg, rgba(240,147,251,0.1), rgba(77,208,225,0.08));
        border-left: 3px solid #f093fb;
        padding: 10px 16px; border-radius: 8px; margin: 10px 0;
        font-size: 13px; color: rgba(255,255,255,0.7); font-style: italic;
    }
    .flame { display: inline-block; animation: flamePulse 1.5s ease-in-out infinite; }
    @keyframes flamePulse {
        0%, 100% { transform: scale(1); filter: brightness(1); }
        50% { transform: scale(1.15); filter: brightness(1.3); }
    }
    .suggestion {
        background: linear-gradient(135deg, rgba(255,217,61,0.12), rgba(240,147,251,0.08));
        border: 1px solid rgba(255,217,61,0.3);
        border-radius: 14px; padding: 14px 18px; margin: 8px 0;
        display: flex; align-items: center; gap: 12px;
    }
    .suggestion .icon { font-size: 22px; }
    .suggestion .text { font-size: 14px; color: rgba(255,255,255,0.85); }
    .daily-card {
        background: linear-gradient(135deg, rgba(240,147,251,0.15), rgba(102,126,234,0.12));
        border: 1px solid rgba(240,147,251,0.4);
        border-radius: 18px; padding: 20px; margin: 12px 0;
        box-shadow: 0 8px 30px rgba(240,147,251,0.2);
    }
    .daily-card .title {
        font-size: 12px; letter-spacing: 3px; text-transform: uppercase;
        color: #f093fb; font-weight: 700; margin-bottom: 10px;
    }
    .daily-card .quote { font-size: 17px; font-style: italic; line-height: 1.6; color: rgba(255,255,255,0.9); }
    .confetti-piece {
        position: fixed; width: 10px; height: 10px;
        pointer-events: none; z-index: 9999;
        animation: confettiFall 3s linear forwards;
    }
    @keyframes confettiFall {
        0% { transform: translateY(-10vh) rotate(0deg); opacity: 1; }
        100% { transform: translateY(110vh) rotate(720deg); opacity: 0; }
    }
    .toast {
        position: fixed; top: 20px; right: 20px;
        background: linear-gradient(135deg, rgba(102,126,234,0.95), rgba(240,147,251,0.95));
        color: white; padding: 14px 20px; border-radius: 12px;
        box-shadow: 0 10px 40px rgba(240,147,251,0.5);
        z-index: 9999;
        animation: toastSlide 0.4s ease, toastFade 4s ease forwards;
        font-size: 14px; font-weight: 600;
    }
    @keyframes toastSlide { from { transform: translateX(400px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    @keyframes toastFade { 0%, 70% { opacity: 1; } 100% { opacity: 0; transform: translateX(400px); } }
    
    /* ARENA */
    .arena-cell {
        width: 52px; height: 52px; border-radius: 10px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(240,147,251,0.2);
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 22px; margin: 2px;
        transition: all 0.2s;
        cursor: pointer;
    }
    .arena-cell.p1 { background: linear-gradient(135deg, #667eea, #764ba2); }
    .arena-cell.p2 { background: linear-gradient(135deg, #f093fb, #f5576c); }
    .arena-cell.empty:hover { background: rgba(240,147,251,0.2); }
    .arena-board {
        background: rgba(0,0,0,0.3);
        padding: 16px; border-radius: 16px;
        display: inline-block;
        border: 1px solid rgba(240,147,251,0.3);
    }
    .rank-badge {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 11px; font-weight: 700; letter-spacing: 1px;
        text-transform: uppercase;
    }
    .rank-bronze { background: linear-gradient(135deg, #cd7f32, #8b4513); color: white; }
    .rank-silver { background: linear-gradient(135deg, #c0c0c0, #808080); color: white; }
    .rank-gold { background: linear-gradient(135deg, #ffd700, #ff8c00); color: white; }
    .rank-platinum { background: linear-gradient(135deg, #e5e4e2, #4dd0e1); color: #0a0a18; }
    .rank-diamond { background: linear-gradient(135deg, #b9f2ff, #667eea); color: #0a0a18; }
    .rank-legend { background: linear-gradient(135deg, #f093fb, #ffd93d); color: #0a0a18; }
    
    /* DREAM */
    .dream-symbol {
        display: inline-block; padding: 8px 16px; border-radius: 20px;
        background: linear-gradient(135deg, rgba(240,147,251,0.2), rgba(102,126,234,0.15));
        border: 1px solid rgba(240,147,251,0.4);
        font-size: 13px; font-weight: 600;
        margin: 4px 2px;
    }
    .dream-quote {
        font-size: 20px; font-style: italic; text-align: center;
        padding: 24px; line-height: 1.6;
        background: linear-gradient(135deg, rgba(240,147,251,0.12), rgba(255,217,61,0.08));
        border-radius: 16px; margin: 16px 0;
        border: 1px solid rgba(240,147,251,0.3);
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
        username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL, name TEXT, is_owner INTEGER DEFAULT 0,
        xp INTEGER DEFAULT 0, streak INTEGER DEFAULT 0, last_active TEXT,
        rank TEXT DEFAULT 'Bronze', arena_wins INTEGER DEFAULT 0,
        arena_losses INTEGER DEFAULT 0, total_thoughts INTEGER DEFAULT 0,
        title TEXT DEFAULT 'Seeker', theme TEXT DEFAULT 'cosmic',
        created_at TEXT NOT NULL)""")
    for tbl, cols in [
        ("places", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT, created_at TEXT"),
        ("memories", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, place_id INTEGER NOT NULL, photo_path TEXT, photo_hash TEXT, ai_description TEXT, ai_objects TEXT, user_note TEXT, mood TEXT, created_at TEXT"),
        ("place_brains", "id INTEGER PRIMARY KEY AUTOINCREMENT, place_id INTEGER UNIQUE, story TEXT, pattern TEXT, mood TEXT, first_seen TEXT, last_seen TEXT, total_visits INTEGER DEFAULT 0, updated_at TEXT"),
        ("chats", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, created_at TEXT"),
        ("messages", "id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT"),
        ("notes", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, content TEXT, tags TEXT, created_at TEXT"),
        ("journal", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, content TEXT, mood TEXT, created_at TEXT"),
        ("lessons", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, topic TEXT, steps TEXT, created_at TEXT"),
        ("repairs", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, device TEXT, problem TEXT, steps TEXT, created_at TEXT"),
        ("health_guides", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, symptoms TEXT, age_group TEXT, guide TEXT, created_at TEXT"),
        ("user_devices", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, device TEXT, brand TEXT, model TEXT, created_at TEXT"),
        ("user_health", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, age_group TEXT, allergies TEXT, medications TEXT, created_at TEXT"),
        ("dreams", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, content TEXT, ai_interpretation TEXT, dream_type TEXT, symbol TEXT, emotion TEXT, lucid INTEGER DEFAULT 0, recurring INTEGER DEFAULT 0, created_at TEXT"),
        ("time_capsules", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, message TEXT, unlock_date TEXT, opened INTEGER DEFAULT 0, created_at TEXT"),
        ("achievements", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, code TEXT, name TEXT, description TEXT, icon TEXT, unlocked_at TEXT"),
        ("arena_matches", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, result TEXT, moves INTEGER, difficulty TEXT, points INTEGER DEFAULT 0, board_state TEXT, created_at TEXT"),
        ("habits", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT, icon TEXT, streak INTEGER DEFAULT 0, last_done TEXT, created_at TEXT"),
        ("mood_log", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, mood TEXT, energy INTEGER, note TEXT, created_at TEXT"),
        ("focus_sessions", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, duration INTEGER, task TEXT, completed INTEGER DEFAULT 1, created_at TEXT"),
        ("gratitude", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, items TEXT, created_at TEXT"),
        ("wins_log", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, description TEXT, size TEXT, created_at TEXT"),
        ("reading_list", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, link TEXT, status TEXT DEFAULT 'Want to read', created_at TEXT"),
        ("quotes_saved", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, quote TEXT, author TEXT, created_at TEXT"),
        ("flash_cards", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, question TEXT, answer TEXT, deck TEXT, correct INTEGER DEFAULT 0, wrong INTEGER DEFAULT 0, created_at TEXT"),
        ("breathing_log", "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, cycles INTEGER, minutes INTEGER, created_at TEXT"),
    ]:
        c.execute(f"CREATE TABLE IF NOT EXISTS {tbl} ({cols})")
    conn.commit()
    conn.close()

def migrate_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in c.fetchall()]
    for col, default in [("xp", "0"), ("streak", "0"), ("last_active", "NULL"),
                        ("rank", "'Bronze'"), ("arena_wins", "0"), ("arena_losses", "0"),
                        ("total_thoughts", "0"), ("title", "'Seeker'"), ("theme", "'cosmic'")]:
        if col not in cols:
            try: c.execute(f"ALTER TABLE users ADD COLUMN {col} DEFAULT {default}")
            except: pass
    c.execute("PRAGMA table_info(dreams)")
    cols = [row[1] for row in c.fetchall()]
    for col, default in [("dream_type", "NULL"), ("symbol", "NULL"), ("emotion", "NULL"),
                        ("lucid", "0"), ("recurring", "0")]:
        if col not in cols:
            try: c.execute(f"ALTER TABLE dreams ADD COLUMN {col} DEFAULT {default}")
            except: pass
    conn.commit()
    conn.close()

init_db()
migrate_db()

def get_db():
    conn = sqlite3.connect(DB_FILE); conn.row_factory = sqlite3.Row; return conn
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
# XP / RANK / ACHIEVEMENTS / AUDIO / TOAST
# ============================================================
def award_xp(user_id, amount, reason=""):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE users SET xp = xp + ?, total_thoughts = total_thoughts + 1 WHERE id = ?", (amount, user_id))
    c.execute("SELECT xp FROM users WHERE id = ?", (user_id,))
    row = c.fetchone(); new_xp = row["xp"] if row else 0
    rank = xp_to_rank(new_xp)
    c.execute("UPDATE users SET rank = ? WHERE id = ?", (rank, user_id))
    conn.commit(); conn.close()
    check_achievements(user_id)
    return new_xp

def xp_to_rank(xp):
    if xp >= 5000: return "Legend"
    if xp >= 2500: return "Diamond"
    if xp >= 1000: return "Platinum"
    if xp >= 500: return "Gold"
    if xp >= 150: return "Silver"
    return "Bronze"

def rank_class(rank):
    return {"Bronze": "rank-bronze", "Silver": "rank-silver", "Gold": "rank-gold",
            "Platinum": "rank-platinum", "Diamond": "rank-diamond", "Legend": "rank-legend"}.get(rank, "rank-bronze")

def update_streak(user_id):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT streak, last_active FROM users WHERE id = ?", (user_id,))
    u = c.fetchone()
    today = datetime.now().date().isoformat()
    if not u: conn.close(); return 0
    last = u["last_active"]; streak = u["streak"] or 0
    if last == today: conn.close(); return streak
    yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
    streak = streak + 1 if last == yesterday else 1
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
    m = row["mood"]
    if "😊" in m or "😌" in m or "🔥" in m: return "rgba(107,203,119,0.18)"
    if "😔" in m or "😤" in m: return "rgba(255,107,107,0.18)"
    if "🤔" in m: return "rgba(240,147,251,0.15)"
    if "😴" in m: return "rgba(77,208,225,0.15)"
    return "rgba(102,126,234,0.15)"

def render_mood_ring(user_id):
    st.markdown(f'<div class="mood-ring" style="--mood-color:{get_current_mood_color(user_id)};"></div>', unsafe_allow_html=True)

def celebrate():
    st.components.v1.html("""
    <script>
    (function() {
        const colors = ['#667eea','#f093fb','#ffd93d','#4dd0e1','#6bcb77','#ff6b6b'];
        for (let i=0;i<60;i++){
            const p = document.createElement('div');
            p.className='confetti-piece';
            p.style.left=Math.random()*100+'vw';
            p.style.background=colors[Math.floor(Math.random()*colors.length)];
            p.style.animationDelay=Math.random()*0.5+'s';
            p.style.animationDuration=(2+Math.random()*2)+'s';
            p.style.borderRadius=Math.random()>0.5?'50%':'0';
            document.body.appendChild(p);
            setTimeout(()=>p.remove(),5000);
        }
    })();
    </script>
    """, height=0)

def toast(message):
    st.components.v1.html(f'<div class="toast">{message}</div>', height=0)

def play_sound(kind="success"):
    """Play a small sound effect."""
    freqs = {"success": [523, 659, 784], "win": [523, 659, 784, 1047],
             "lose": [400, 300, 200], "enter": [523, 784], "click": [800],
             "level_up": [523, 659, 784, 1047, 1319], "achievement": [659, 784, 1047]}
    seq = freqs.get(kind, freqs["click"])
    notes_js = ",".join([f"o.frequency.value={f};o.start(t+{i*0.1});o.stop(t+{i*0.1+0.15});"
                         for i, f in enumerate(seq)])
    html = f"""
    <script>
    (function(){{
        try {{
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            var t = ctx.currentTime;
            {notes_js}
        }} catch(e) {{}}
    }})();
    </script>
    """
    st.components.v1.html(html, height=0)

# ============================================================
# ACHIEVEMENTS
# ============================================================
ACHIEVEMENTS = {
    "first_login": ("First Step", "You entered NEXUS", "🌱"),
    "first_place": ("Cartographer", "Saved your first place in ECHO", "📍"),
    "five_places": ("Explorer", "Saved 5 places", "🗺️"),
    "ten_places": ("Voyager", "Saved 10 places", "🌍"),
    "first_note": ("Thinker", "Wrote your first note", "📝"),
    "ten_notes": ("Philosopher", "Wrote 10 notes", "🧠"),
    "first_journal": ("Reflector", "Wrote your first journal entry", "📖"),
    "ten_journals": ("Diary Keeper", "Wrote 10 journal entries", "✍️"),
    "first_dream": ("Dreamer", "Interpreted your first dream", "🌙"),
    "five_dreams": ("Oneironaut", "Interpreted 5 dreams", "✨"),
    "first_capsule": ("Time Traveler", "Sealed your first capsule", "⏳"),
    "first_lesson": ("Student", "Completed your first lesson", "🎓"),
    "first_repair": ("Fixer", "Completed your first repair", "🔧"),
    "first_health": ("Guardian", "Got your first health guidance", "💊"),
    "first_arena": ("Gladiator", "Won your first Arena match", "⚔️"),
    "arena_5_wins": ("Champion", "Won 5 Arena matches", "🏆"),
    "arena_10_wins": ("Grandmaster", "Won 10 Arena matches", "👑"),
    "streak_3": ("Consistent", "3-day streak", "🔥"),
    "streak_7": ("Committed", "7-day streak", "💎"),
    "streak_30": ("Dedicated", "30-day streak", "🌟"),
    "xp_100": ("Apprentice", "Earned 100 XP", "🥉"),
    "xp_500": ("Adept", "Earned 500 XP", "🥈"),
    "xp_2000": ("Master", "Earned 2000 XP", "🥇"),
    "xp_5000": ("Legend", "Earned 5000 XP", "👑"),
}

def check_achievements(user_id):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT code FROM achievements WHERE user_id = ?", (user_id,))
    unlocked = {row["code"] for row in c.fetchall()}
    new_unlocks = []
    
    checks = {}
    c.execute("SELECT COUNT(*) as x FROM memories WHERE user_id = ?", (user_id,))
    checks["first_place"] = c.fetchone()["x"] >= 1
    checks["five_places"] = c.fetchone()["x"] >= 5 if False else checks["first_place"]
    c.execute("SELECT COUNT(*) as x FROM places WHERE user_id = ?", (user_id,))
    pc = c.fetchone()["x"]
    checks["first_place"] = pc >= 1; checks["five_places"] = pc >= 5; checks["ten_places"] = pc >= 10
    c.execute("SELECT COUNT(*) as x FROM notes WHERE user_id = ?", (user_id,))
    nc = c.fetchone()["x"]
    checks["first_note"] = nc >= 1; checks["ten_notes"] = nc >= 10
    c.execute("SELECT COUNT(*) as x FROM journal WHERE user_id = ?", (user_id,))
    jc = c.fetchone()["x"]
    checks["first_journal"] = jc >= 1; checks["ten_journals"] = jc >= 10
    c.execute("SELECT COUNT(*) as x FROM dreams WHERE user_id = ?", (user_id,))
    dc = c.fetchone()["x"]
    checks["first_dream"] = dc >= 1; checks["five_dreams"] = dc >= 5
    c.execute("SELECT COUNT(*) as x FROM time_capsules WHERE user_id = ?", (user_id,))
    checks["first_capsule"] = c.fetchone()["x"] >= 1
    c.execute("SELECT COUNT(*) as x FROM lessons WHERE user_id = ?", (user_id,))
    checks["first_lesson"] = c.fetchone()["x"] >= 1
    c.execute("SELECT COUNT(*) as x FROM repairs WHERE user_id = ?", (user_id,))
    checks["first_repair"] = c.fetchone()["x"] >= 1
    c.execute("SELECT COUNT(*) as x FROM health_guides WHERE user_id = ?", (user_id,))
    checks["first_health"] = c.fetchone()["x"] >= 1
    c.execute("SELECT COUNT(*) as x FROM arena_matches WHERE user_id = ? AND result = 'win'", (user_id,))
    aw = c.fetchone()["x"]
    checks["first_arena"] = aw >= 1; checks["arena_5_wins"] = aw >= 5; checks["arena_10_wins"] = aw >= 10
    c.execute("SELECT streak, xp FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    if row:
        s = row["streak"] or 0; xp = row["xp"] or 0
        checks["streak_3"] = s >= 3; checks["streak_7"] = s >= 7; checks["streak_30"] = s >= 30
        checks["xp_100"] = xp >= 100; checks["xp_500"] = xp >= 500
        checks["xp_2000"] = xp >= 2000; checks["xp_5000"] = xp >= 5000
    checks["first_login"] = True
    
    for code, ok in checks.items():
        if ok and code not in unlocked:
            name, desc, icon = ACHIEVEMENTS[code]
            c.execute("INSERT INTO achievements (user_id, code, name, description, icon, unlocked_at) VALUES (?, ?, ?, ?, ?, ?)",
                      (user_id, code, name, desc, icon, datetime.now().isoformat()))
            new_unlocks.append((name, desc, icon))
    conn.commit(); conn.close()
    for name, desc, icon in new_unlocks:
        play_sound("achievement")
        toast(f"{icon} Achievement: {name}!")

# ============================================================
# ARENA — Competitive Mind Game (Deeper than Chess)
# ============================================================
# Rules:
# - 6x6 board
# - Each player has 6 pieces: 2 SHIELDS, 2 SPEARS, 1 SAGE, 1 KING
# - SHIELD moves 1 any direction, blocks captures
# - SPEAR moves 1 orthogonally, captures orthogonally
# - SAGE moves up to 3 diagonally, captures diagonally
# - KING moves 1 any direction, captures any adjacent
# - First to capture opponent KING OR control the center (4 turns holding) wins
# - Each piece can use a "power" once per game: freezes an enemy for 1 turn

ARENA_SIZE = 6

def new_arena_board():
    board = [[None for _ in range(ARENA_SIZE)] for _ in range(ARENA_SIZE)]
    board[0][0] = {"p": 1, "t": "S"}; board[0][1] = {"p": 1, "t": "S"}
    board[0][4] = {"p": 1, "t": "P"}; board[0][5] = {"p": 1, "t": "P"}
    board[0][2] = {"p": 1, "t": "G"}; board[0][3] = {"p": 1, "t": "K"}
    board[5][0] = {"p": 2, "t": "S"}; board[5][1] = {"p": 2, "t": "S"}
    board[5][4] = {"p": 2, "t": "P"}; board[5][5] = {"p": 2, "t": "P"}
    board[5][2] = {"p": 2, "t": "G"}; board[5][3] = {"p": 2, "t": "K"}
    return board

PIECE_ICONS = {"S": "🛡️", "P": "⚔️", "G": "🧙", "K": "👑"}

def arena_moves(board, r, c):
    piece = board[r][c]
    if not piece: return []
    p, t = piece["p"], piece["t"]
    moves = []
    dirs_orth = [(-1,0),(1,0),(0,-1),(0,1)]
    dirs_all = dirs_orth + [(-1,-1),(-1,1),(1,-1),(1,1)]
    if t == "S":
        for dr, dc in dirs_all:
            nr, nc = r+dr, c+dc
            if 0<=nr<ARENA_SIZE and 0<=nc<ARENA_SIZE:
                if not board[nr][nc] or board[nr][nc]["p"] != p:
                    moves.append((nr,nc))
    elif t == "P":
        for dr, dc in dirs_orth:
            nr, nc = r+dr, c+dc
            if 0<=nr<ARENA_SIZE and 0<=nc<ARENA_SIZE:
                if not board[nr][nc] or board[nr][nc]["p"] != p:
                    moves.append((nr,nc))
    elif t == "G":
        for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            for step in range(1, 4):
                nr, nc = r+dr*step, c+dc*step
                if not (0<=nr<ARENA_SIZE and 0<=nc<ARENA_SIZE): break
                if not board[nr][nc]: moves.append((nr,nc))
                else:
                    if board[nr][nc]["p"] != p: moves.append((nr,nc))
                    break
    elif t == "K":
        for dr, dc in dirs_all:
            nr, nc = r+dr, c+dc
            if 0<=nr<ARENA_SIZE and 0<=nc<ARENA_SIZE:
                if not board[nr][nc] or board[nr][nc]["p"] != p:
                    moves.append((nr,nc))
    return moves

def arena_apply(board, fr, fc, tr, tc):
    b = [[dict(cell) if cell else None for cell in row] for row in board]
    piece = b[fr][fc]
    captured = b[tr][tc]
    b[tr][tc] = piece
    b[fr][fc] = None
    return b, captured

def arena_center_control(board):
    """Player controlling center 2x2."""
    s = 0
    for r in [2,3]:
        for c in [2,3]:
            if board[r][c]: s += board[r][c]["p"]
    return s

def arena_ai_move(board, difficulty="medium"):
    """Simple strategic AI."""
    all_moves = []
    for r in range(ARENA_SIZE):
        for c in range(ARENA_SIZE):
            piece = board[r][c]
            if piece and piece["p"] == 2:
                for tr, tc in arena_moves(board, r, c):
                    all_moves.append((r,c,tr,tc))
    if not all_moves: return None
    # Score each move
    scored = []
    for m in all_moves:
        fr,fc,tr,tc = m
        score = 0
        target = board[tr][tc]
        if target and target["p"] == 1:
            if target["t"] == "K": score += 100
            elif target["t"] == "G": score += 30
            elif target["t"] == "P": score += 20
            elif target["t"] == "S": score += 15
        # Center preference
        if tr in [2,3] and tc in [2,3]: score += 5
        # King safety
        piece = board[fr][fc]
        if piece["t"] == "K" and difficulty != "hard":
            score -= 5
        scored.append((score + random.random(), m))
    scored.sort(reverse=True)
    if difficulty == "easy":
        return random.choice(all_moves)
    elif difficulty == "medium":
        return scored[0][1] if random.random() < 0.7 else scored[min(1, len(scored)-1)][1]
    else:
        return scored[0][1]

# ============================================================
# BRAIN — Pollinations
# ============================================================
def ai_chat(messages, temperature=0.7):
    try:
        r = requests.post("https://text.pollinations.ai/openai",
            json={"model": "openai-fast", "messages": messages, "temperature": temperature, "max_tokens": 1000},
            timeout=90)
        if r.status_code == 200:
            data = r.json()
            if data.get("choices") and data["choices"][0]["message"]["content"]:
                c = data["choices"][0]["message"]["content"].strip()
                if len(c) > 2: return c
    except: pass
    try:
        r = requests.post("https://text.pollinations.ai/openai",
            json={"model": "openai", "messages": messages, "temperature": temperature}, timeout=90)
        if r.status_code == 200:
            data = r.json()
            if data.get("choices") and data["choices"][0]["message"]["content"]:
                return data["choices"][0]["message"]["content"].strip()
    except: pass
    try:
        prompt = ""
        for m in messages:
            if m["role"]=="system": prompt += f"{m['content']}\n\n"
            elif m["role"]=="user": prompt += f"User: {m['content']}\n"
            elif m["role"]=="assistant": prompt += f"Assistant: {m['content']}\n"
        prompt += "Assistant:"
        r = requests.get(f"https://text.pollinations.ai/{requests.utils.quote(prompt)}", timeout=90)
        if r.status_code == 200 and len(r.text.strip()) > 3:
            return r.text.strip()
    except: pass
    return "⚠️ The AI is resting. Please send your message again in a few seconds."

def _img_b64(path):
    with open(path, "rb") as f: return base64.b64encode(f.read()).decode()

def ai_describe_photo(photo_path):
    try:
        img = _img_b64(photo_path)
        r = requests.post("https://text.pollinations.ai/openai",
            json={"model": "openai", "messages":[{"role":"user","content":[
                {"type":"text","text":"Describe this place in one warm, poetic sentence under 25 words. If unclear, say 'The image is unclear'."},
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}"}}]}],
                "temperature":0.7}, timeout=90)
        if r.status_code==200:
            d = r.json()
            if d.get("choices"): return d["choices"][0]["message"]["content"].strip()
    except: pass
    return "A place you've seen."

def ai_extract_objects(photo_path):
    try:
        img = _img_b64(photo_path)
        r = requests.post("https://text.pollinations.ai/openai",
            json={"model":"openai","messages":[{"role":"user","content":[
                {"type":"text","text":"List everything visible. Return ONLY a JSON array of short descriptions. 10-25 items. Only JSON."},
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}"}}]}],
                "temperature":0.3}, timeout=90)
        if r.status_code==200:
            d = r.json()
            if d.get("choices"):
                t = d["choices"][0]["message"]["content"].strip().replace("```json","").replace("```","").strip()
                s=t.find("["); e=t.rfind("]")
                if s!=-1 and e!=-1: return json.loads(t[s:e+1])
    except: pass
    return []

def ai_what_did_i_miss(old_o, old_d, new_o, new_d, name):
    p = f"""ECHO comparing "{name}". PREVIOUS: {old_d} | {json.dumps(old_o)}. TODAY: {new_d} | {json.dumps(new_o)}.
Return ONLY JSON: {{"gone":[], "new":[], "changed":[], "same":[], "tiny_details":[], "weather_feel":"", "story":""}}"""
    r = ai_chat([{"role":"user","content":p}], temperature=0.6)
    try:
        c = r.strip().replace("```json","").replace("```","").strip()
        s=c.find("{"); e=c.rfind("}")
        if s!=-1 and e!=-1: return json.loads(c[s:e+1])
    except: pass
    return {"gone":[],"new":[],"changed":[],"same":[],"tiny_details":[],"weather_feel":"A day like any other.","story":"The place has a story."}

def ai_place_brain(name, descs, dates, moods):
    t = ""
    for i,(d,dt,m) in enumerate(zip(descs,dates,moods)):
        t += f"Visit {i+1} ({dt[:10]}, felt {m}): {d}\n"
    p = f"""ECHO remembering "{name}". Visits: {t}
Return ONLY JSON: {{"story":"2-3 sentences","pattern":"1 sentence","mood":"1 word"}}"""
    r = ai_chat([{"role":"user","content":p}], temperature=0.75)
    try:
        c = r.strip().replace("```json","").replace("```","").strip()
        s=c.find("{"); e=c.rfind("}")
        if s!=-1 and e!=-1: return json.loads(c[s:e+1])
    except: pass
    return {"story":f"A place you've visited {len(descs)} time(s).","pattern":"You've returned here more than once.","mood":"familiar"}

def ai_echo_speaks(name, desc, prev):
    if not prev:
        p = f"""ECHO meeting new place "{name}". First impression: {desc}. ONE warm sentence, under 20 words."""
    else:
        last = prev[-1]
        p = f"""ECHO welcoming back to "{name}". Previous ({last['created_at'][:10]}): {last['ai_description']}. Today: {desc}. ONE warm sentence, under 25 words."""
    return ai_chat([{"role":"user","content":p}], temperature=0.8)

def ai_compare_photos(p1, p2, name):
    try:
        i1=_img_b64(p1); i2=_img_b64(p2)
        r = requests.post("https://text.pollinations.ai/openai",
            json={"model":"openai","messages":[{"role":"user","content":[
                {"type":"text","text":f"Two photos of '{name}'. Write a 2-3 sentence 'What Changed' paragraph."},
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{i1}"}},
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{i2}"}}]}],
                "temperature":0.7}, timeout=90)
        if r.status_code==200:
            d=r.json()
            if d.get("choices"): return d["choices"][0]["message"]["content"].strip()
    except: pass
    return "The place has changed over time."

def ai_build_lesson(topic):
    p = f"""ATLAS teacher. Lesson on: "{topic}"
Return ONLY JSON: {{"title":"","intro":"","steps":[{{"number":1,"title":"","instruction":"","check":"","tip":""}}],"outro":""}} 5-7 steps. Only JSON."""
    r = ai_chat([{"role":"user","content":p}], temperature=0.6)
    try:
        c=r.strip().replace("```json","").replace("```","").strip()
        s=c.find("{"); e=c.rfind("}")
        if s!=-1 and e!=-1: return json.loads(c[s:e+1])
    except: pass
    return None

def ai_build_repair(device, problem, brand="", model=""):
    df = f"{brand} {model}".strip() or device
    p = f"""ATLAS repair technician. Device: {df}. Problem: {problem}.
Return ONLY JSON: {{"title":"","safety":"","tools_needed":[],"likely_cause":"","steps":[{{"number":1,"title":"","instruction":"","check":"","warning":""}}],"outro":""}} 5-8 real steps. Only JSON."""
    r = ai_chat([{"role":"user","content":p}], temperature=0.5)
    try:
        c=r.strip().replace("```json","").replace("```","").strip()
        s=c.find("{"); e=c.rfind("}")
        if s!=-1 and e!=-1: return json.loads(c[s:e+1])
    except: pass
    return None

def ai_health_guide(symptoms, age, allergies="", meds=""):
    p = f"""ATLAS health guide. NOT a doctor.
Symptoms: {symptoms}. Age: {age}. Allergies: {allergies or 'None'}. Meds: {meds or 'None'}.
Return ONLY JSON: {{"title":"","seriousness":"Mild/Moderate/Serious/Emergency","possible_causes":[],"home_care":[],"medicines":[{{"name":"","dose":"","note":""}}],"warning_signs":[],"when_to_see_doctor":"","safety":"","outro":""}}
Only safe OTC medicines. Only JSON."""
    r = ai_chat([{"role":"user","content":p}], temperature=0.4)
    try:
        c=r.strip().replace("```json","").replace("```","").strip()
        s=c.find("{"); e=c.rfind("}")
        if s!=-1 and e!=-1: return json.loads(c[s:e+1])
    except: pass
    return None

def ai_suggest_tags(content):
    try:
        r = ai_chat([{"role":"user","content":f"3 short comma-separated tags:\n{content[:400]}"}])
        return r.replace("\n"," ").strip()[:100]
    except: return ""

def ai_daily_quote():
    try:
        r = ai_chat([{"role":"user","content":"Give ONE short inspiring sentence (max 15 words) for today. No quotes, no author."}])
        return r.strip().strip('"')[:120]
    except: return "Every small step builds a bigger tomorrow."

def ai_note_connections(user_id, content):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT title, content FROM notes WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,))
    old = c.fetchall(); conn.close()
    if not old: return ""
    ot = "\n".join([f"- {n['title']}" for n in old])
    p = f"""Find connections. NEW: {content[:300]}. OLD: {ot}.
If related, say ONE sentence: "Connects to: [title] because...". Else "No connections yet." Under 30 words."""
    return ai_chat([{"role":"user","content":p}], temperature=0.5)

# ============================================================
# DREAM — UPGRADED TO FULLEST
# ============================================================
DREAM_SYMBOLS = {
    "water": "💧 Emotions and flow", "fire": "🔥 Transformation", "flying": "🕊️ Freedom",
    "falling": "⚠️ Loss of control", "teeth": "😬 Anxiety or speech",
    "snake": "🐍 Change or hidden fear", "death": "💀 Endings and rebirth",
    "baby": "👶 New beginning", "road": "🛣️ Life path", "door": "🚪 Opportunity",
    "mirror": "🪞 Self-reflection", "forest": "🌲 Unknown journey",
    "mountain": "⛰️ Challenge", "bird": "🐦 Hope", "storm": "⛈️ Turmoil",
    "sun": "☀️ Clarity", "moon": "🌙 Intuition", "star": "⭐ Aspiration",
    "river": "🏞️ Life flow", "ocean": "🌊 Deep emotion", "spider": "🕷️ Fear/creativity",
    "money": "💰 Value/worth", "house": "🏠 Self/identity", "car": "🚗 Direction in life",
    "tree": "🌳 Growth", "flower": "🌸 Beauty/blooming", "rain": "🌧️ Release",
    "kiss": "💋 Connection", "chase": "🏃 Avoidance", "exam": "📝 Self-judgment",
    "naked": "👤 Vulnerability", "lost": "🧭 Confusion", "school": "🎓 Learning",
    "hospital": "🏥 Healing", "police": "👮 Guilt/order", "stranger": "👥 Unknown self"
}

def ai_interpret_dream(dream_text, user_id):
    """Full dream interpretation with symbols, emotion, type."""
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT content FROM dreams WHERE user_id = ? ORDER BY created_at DESC LIMIT 15", (user_id,))
    past = [d["content"] for d in c.fetchall()]
    conn.close()
    past_text = "\n".join([f"- {p[:100]}" for p in past]) if past else "No previous dreams."
    prompt = f"""You are a warm, wise dream interpreter. Interpret this dream deeply.

DREAM: {dream_text}

PAST DREAMS FROM THIS PERSON:
{past_text}

Return ONLY valid JSON:
{{
  "dream_type": "one of: Prophetic, Emotional, Processing, Nightmare, Lucid, Symbolic, Healing, Recurring",
  "emotion": "the dominant emotion in the dream — one word",
  "symbols": ["symbol1", "symbol2", "symbol3"],
  "meaning": "3-4 sentence poetic, specific interpretation",
  "life_connection": "1-2 sentences connecting this to their past dreams if any patterns exist",
  "message": "ONE warm, personal sentence for the dreamer",
  "action": "ONE tiny thing they could do today related to this dream",
  "is_recurring": true or false
}}

Be gentle, specific, and poetic. Only JSON."""
    r = ai_chat([{"role":"user","content":prompt}], temperature=0.8)
    try:
        c = r.strip().replace("```json","").replace("```","").strip()
        s=c.find("{"); e=c.rfind("}")
        if s!=-1 and e!=-1: return json.loads(c[s:e+1])
    except: pass
    return {"dream_type":"Symbolic","emotion":"unknown","symbols":[],
            "meaning":"Dreams are echoes of the heart.","life_connection":"","message":"Keep dreaming.",
            "action":"Notice how you feel today.","is_recurring":False}

def ai_dream_insight(user_id):
    """Read all dreams and give overall pattern insight."""
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT content, symbol, emotion, dream_type FROM dreams WHERE user_id = ? ORDER BY created_at DESC LIMIT 15", (user_id,))
    dreams = c.fetchall(); conn.close()
    if len(dreams) < 3: return None
    d_text = "\n".join([f"- [{d['dream_type'] or '?'} / {d['emotion'] or '?'}] {d['content'][:100]}" for d in dreams])
    prompt = f"""Analyze this person's dream patterns.
DREAMS:
{d_text}

Return ONLY JSON: {{"pattern": "2-3 sentence observation of recurring themes", "advice": "one warm sentence"}}
Only JSON."""
    r = ai_chat([{"role":"user","content":prompt}], temperature=0.75)
    try:
        c = r.strip().replace("```json","").replace("```","").strip()
        s=c.find("{"); e=c.rfind("}")
        if s!=-1 and e!=-1: return json.loads(c[s:e+1])
    except: pass
    return None

def ai_dream_question(user_id):
    """Ask the user a guided dream question."""
    prompts = [
        "Before you sleep — what is one thing you hope to dream about tonight?",
        "Describe the last feeling you had in a dream. Where did you feel it in your body?",
        "Did any person from your past appear in a recent dream?",
        "What colour appeared most in your last dream?",
        "If your last dream had a title, what would it be?",
        "Was there water, fire, or sky in your last dream?",
    ]
    return random.choice(prompts)

def ai_interpret_dream_short(dream_text):
    """For quick interpretation display."""
    return ai_chat([{"role":"user","content":f"Interpret this dream in 2 poetic sentences:\n{dream_text}"}], temperature=0.85)

# ============================================================
# TIME CAPSULE
# ============================================================
def ai_time_capsule_note(user_id, message):
    p = f"""A person wrote a message to their future self:
"{message[:400]}"

Write a warm, personal 2-sentence note FROM their future self BACK TO them, in second person. Poetic and hopeful."""
    return ai_chat([{"role":"user","content":p}], temperature=0.85)

# ============================================================
# LIFE INSIGHT
# ============================================================
def ai_life_insights(user_id):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) as x FROM memories WHERE user_id = ?", (user_id,)); mem = c.fetchone()["x"]
    c.execute("SELECT COUNT(*) as x FROM journal WHERE user_id = ?", (user_id,)); jc = c.fetchone()["x"]
    c.execute("SELECT mood FROM journal WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,)); moods = [m["mood"] for m in c.fetchall() if m["mood"]]
    c.execute("SELECT COUNT(*) as x FROM notes WHERE user_id = ?", (user_id,)); nc = c.fetchone()["x"]
    c.execute("SELECT COUNT(*) as x FROM dreams WHERE user_id = ?", (user_id,)); dc = c.fetchone()["x"]
    conn.close()
    prompt = f"""User data: Places {mem}, Journal {jc}, Moods {', '.join(moods) if moods else 'none'}, Notes {nc}, Dreams {dc}.
Write ONE short warm insight (max 25 words). Specific, not generic."""
    return ai_chat([{"role":"user","content":prompt}], temperature=0.8)

# ============================================================
# SESSION
# ============================================================
defaults = {
    "user_id": None, "name": None, "is_owner": False,
    "view": "home", "current_place_id": None, "current_chat_id": None,
    "current_lesson": None, "current_step": 0, "current_repair": None,
    "repair_step": 0, "last_snap_result": None, "health_guide": None,
    "pick_device": "", "daily_quote": None, "life_insight": None,
    "arena_board": None, "arena_turn": 1, "arena_difficulty": "medium",
    "arena_move_count": 0, "arena_center_turns": 0, "arena_last_result": None,
}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ============================================================
# AUTH
# ============================================================
def auth_page():
    st.markdown("""
    <div class="login-hero">
        <h1>🧠 NEXUS ULTIMATE</h1>
        <p>159 features + 120 more. One app. Everything you need.</p>
        <p style="font-size:13px;opacity:0.5;margin-top:16px;">Powered by GPT-OSS 20B. Free. Forever.</p>
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
                    if not u or not p: st.error("Fill both fields")
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
                            play_sound("enter")
                            st.rerun()
                        else: st.error("Invalid login.")
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
                            c.execute("""INSERT INTO users (username,email,password_hash,name,is_owner,xp,streak,last_active,rank,title,created_at)
                                VALUES (?,?,?,?,?,0,1,?,?,?,?)""",
                                (u, e, hash_pw(p), n, owner, datetime.now().date().isoformat(), "Bronze", "Seeker", datetime.now().isoformat()))
                            conn.commit(); conn.close()
                            st.success("✅ Welcome! Now log in.")
                        except sqlite3.IntegrityError: st.error("Username or email taken.")

# ============================================================
# HOME
# ============================================================
def home_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT xp, streak, rank, arena_wins FROM users WHERE id = ?", (user_id,))
    s = c.fetchone()
    c.execute("SELECT COUNT(*) as x FROM places WHERE user_id = ?", (user_id,)); pc = c.fetchone()["x"]
    c.execute("SELECT COUNT(*) as x FROM dreams WHERE user_id = ?", (user_id,)); dc = c.fetchone()["x"]
    c.execute("SELECT COUNT(*) as x FROM achievements WHERE user_id = ?", (user_id,)); ac = c.fetchone()["x"]
    conn.close()
    xp = s["xp"] if s else 0; streak = s["streak"] if s else 0
    rank = s["rank"] if s else "Bronze"; aw = s["arena_wins"] if s else 0
    st.markdown(f'<div class="nexus-header"><h1>🧠 NEXUS ULTIMATE</h1><p>{get_time_greeting()}, {st.session_state.name} — <span class="rank-badge {rank_class(rank)}">{rank}</span></p></div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f'<div class="stat-card"><div class="stat-number">{xp}</div><div class="stat-label">XP</div></div>', unsafe_allow_html=True)
    with c2:
        fl = "🔥" if streak > 1 else "✨"
        st.markdown(f'<div class="stat-card"><div class="stat-number"><span class="flame">{fl}</span> {streak}</div><div class="stat-label">Streak</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="stat-card"><div class="stat-number">{ac}</div><div class="stat-label">Achievements</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="stat-card"><div class="stat-number">{aw}</div><div class="stat-label">Arena Wins</div></div>', unsafe_allow_html=True)
    st.write("")
    now = datetime.now()
    col_a, col_b = st.columns([1,2])
    with col_a:
        st.markdown(f'<div class="live-panel"><div class="label">Now</div><div class="time">{now.strftime("%I:%M %p")}</div><div style="font-size:12px;opacity:0.5;margin-top:6px;">{now.strftime("%A, %B %d")}</div></div>', unsafe_allow_html=True)
    with col_b:
        if not st.session_state.get("daily_quote"):
            with st.spinner("NEXUS whispers..."): st.session_state.daily_quote = ai_daily_quote()
        st.markdown(f'<div class="daily-card"><div class="title">NEXUS whispers</div><div class="quote">"{st.session_state.daily_quote}"</div></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("### 🚀 Your Rooms")
    mods = [
        ("echo","📸","ECHO","Remember places"), ("chat","💬","AI CHAT","Talk to NEXUS"),
        ("tutor","🎓","TUTOR","Learn anything"), ("repair","🔧","ATLAS","Fix & health"),
        ("notes","📝","NOTES","Thoughts organized"), ("journal","📖","JOURNAL","Private diary"),
        ("dreams","🌙","DREAMS","Interpret dreams"), ("capsule","⏳","CAPSULE","Message future"),
        ("arena","⚔️","ARENA","Compete vs NEXUS"), ("habits","✅","HABITS","Build streaks"),
        ("focus","🎯","FOCUS","Pomodoro timer"), ("gratitude","🙏","GRATITUDE","Daily thanks"),
        ("wins","🏆","WINS","Small victories"), ("reading","📚","READING","Book list"),
        ("quotes","💬","QUOTES","Saved quotes"), ("flash","🃏","FLASH","Card study"),
        ("breathing","🫁","BREATHE","Calm down"), ("mood","😊","MOOD","Track feelings"),
        ("achievements","🎖️","AWARDS","Your badges"), ("stats","📊","STATS","Full history"),
    ]
    cols = st.columns(5)
    for i,(mid,icon,title,desc) in enumerate(mods):
        with cols[i % 5]:
            st.markdown(f'<div class="module-tile"><div class="module-icon">{icon}</div><div class="module-title">{title}</div><div class="module-desc">{desc}</div></div>', unsafe_allow_html=True)
            if st.button("Open", key=f"open_{mid}", use_container_width=True):
                st.session_state.view = mid; play_sound("click"); st.rerun()
    st.divider()
    st.markdown("### 🔮 Your Life Insight")
    if not st.session_state.get("life_insight"):
        with st.spinner("NEXUS is reading your story..."): st.session_state.life_insight = ai_life_insights(user_id)
    st.markdown(f'<div class="brain-card"><div class="story">✨ {st.session_state.life_insight}</div></div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("### 💡 NEXUS suggests")
    for icon, text in get_smart_suggestions(user_id):
        st.markdown(f'<div class="suggestion"><span class="icon">{icon}</span><span class="text">{text}</span></div>', unsafe_allow_html=True)

def get_smart_suggestions(user_id):
    conn = get_db(); c = conn.cursor(); su = []
    c.execute("SELECT MAX(created_at) as l FROM memories WHERE user_id = ?", (user_id,)); lp = c.fetchone()["l"]
    if not lp: su.append(("📸","Snap your first place"))
    else:
        try:
            d = (datetime.now() - datetime.fromisoformat(lp)).days
            if d >= 3: su.append(("📍", f"No snaps in {d} days"))
        except: pass
    c.execute("SELECT mood FROM journal WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,)); lj = c.fetchone()
    if lj and ("😔" in (lj["mood"] or "") or "😤" in (lj["mood"] or "")): su.append(("📖","Heavy mood — write again?"))
    c.execute("SELECT COUNT(*) as x FROM dreams WHERE user_id = ?", (user_id,))
    if c.fetchone()["x"] == 0: su.append(("🌙","Try Dream Interpreter tonight"))
    c.execute("SELECT COUNT(*) as x FROM arena_matches WHERE user_id = ?", (user_id,))
    if c.fetchone()["x"] == 0: su.append(("⚔️","Enter the Arena — beat NEXUS"))
    c.execute("SELECT COUNT(*) as x FROM time_capsules WHERE user_id = ?", (user_id,))
    if c.fetchone()["x"] == 0: su.append(("⏳","Write a message to future you"))
    conn.close()
    return su[:4]

def back_button(target="home"):
    if st.button("← Back"):
        st.session_state.view = target; st.rerun()

# ============================================================
# ECHO (same as before)
# ============================================================
def echo_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>📸 ECHO</h1><p>Snap a place. ECHO remembers everything.</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    tab_snap, tab_places, tab_brains, tab_compare = st.tabs(["📸 Snap", "🗺️ Places", "🧠 Mind", "🔮 Compare"])
    with tab_snap:
        cam = st.camera_input("📸 Take a photo")
        with st.expander("Or upload"):
            up = st.file_uploader("Choose", type=["jpg","jpeg","png"], label_visibility="collapsed")
        st.divider()
        pn = st.text_input("Where is this place?", placeholder="e.g. My street, Lagos")
        feel = st.selectbox("How does it feel?", ["Peaceful","Busy","Warm","Lonely","Joyful","Heavy","Bright","Quiet","Alive","Still"])
        nt = st.text_area("Describe what you see (helps ECHO)", height=80)
        if st.button("💾 Save to ECHO", type="primary", use_container_width=True):
            pb = cam.getvalue() if cam else (up.getvalue() if up else None)
            if not pb: st.error("Take or upload a photo first.")
            elif not pn: st.error("Give the place a name.")
            else:
                with st.spinner("ECHO is thinking..."):
                    fp, ph = save_photo_safely(user_id, pb)
                    ds = ai_describe_photo(fp); ob = ai_extract_objects(fp)
                    if len(ob)==0 and nt: ds = nt; ob = [n.strip() for n in nt.split(",") if n.strip()]
                    elif nt: ds = f"{ds} — noted: {nt}"
                    conn = get_db(); c = conn.cursor()
                    c.execute("SELECT * FROM places WHERE user_id = ? AND name = ?", (user_id, pn))
                    ex = c.fetchone(); is_new = ex is None
                    pv=[]; po=[]; pd=""
                    if ex:
                        pid = ex["id"]
                        c.execute("SELECT * FROM memories WHERE place_id = ? ORDER BY created_at ASC", (pid,))
                        pv = [dict(r) for r in c.fetchall()]
                        if pv:
                            last = pv[-1]; pd = last["ai_description"] or ""
                            try: po = json.loads(last["ai_objects"]) if last["ai_objects"] else []
                            except: po = []
                    else:
                        c.execute("INSERT INTO places (user_id,name,created_at) VALUES (?,?,?)", (user_id,pn,datetime.now().isoformat()))
                        pid = c.lastrowid
                    c.execute("""INSERT INTO memories (user_id,place_id,photo_path,photo_hash,ai_description,ai_objects,user_note,mood,created_at)
                        VALUES (?,?,?,?,?,?,?,?,?)""", (user_id,pid,fp,ph,ds,json.dumps(ob),nt,feel,datetime.now().isoformat()))
                    mr = ai_what_did_i_miss(po,pd,ob,ds,pn) if pv and po else None
                    c.execute("SELECT ai_description, created_at, mood FROM memories WHERE place_id = ? ORDER BY created_at ASC", (pid,))
                    am = c.fetchall()
                    descs = [m["ai_description"] or "" for m in am]; dates = [m["created_at"] for m in am]; moods = [m["mood"] or "neutral" for m in am]
                    bd = ai_place_brain(pn, descs, dates, moods)
                    c.execute("SELECT id FROM place_brains WHERE place_id = ?", (pid,))
                    br = c.fetchone()
                    if br: c.execute("UPDATE place_brains SET story=?,pattern=?,mood=?,last_seen=?,total_visits=?,updated_at=? WHERE place_id=?",
                                    (bd["story"],bd["pattern"],bd["mood"],datetime.now().isoformat(),len(am),datetime.now().isoformat(),pid))
                    else: c.execute("INSERT INTO place_brains (place_id,story,pattern,mood,first_seen,last_seen,total_visits,updated_at) VALUES (?,?,?,?,?,?,?,?)",
                                    (pid,bd["story"],bd["pattern"],bd["mood"],datetime.now().isoformat(),datetime.now().isoformat(),len(am),datetime.now().isoformat()))
                    conn.commit(); conn.close()
                    gr = ai_echo_speaks(pn, ds, pv)
                    award_xp(user_id, 15)
                    celebrate(); play_sound("success")
                    toast(f"✅ +15 XP · {pn} remembered")
                    st.session_state.last_snap_result = {"greeting":gr,"description":ds,"objects":ob,"miss":mr,"brain":bd,"is_new":is_new,"photo_path":fp}
                st.rerun()
        r = st.session_state.last_snap_result
        if r:
            st.divider(); st.subheader("🧠 What ECHO saw")
            c1,c2 = st.columns([1,2])
            with c1:
                if os.path.exists(r["photo_path"]): st.image(r["photo_path"], use_container_width=True)
            with c2:
                st.markdown(f'<div class="echo-memory"><strong>👁️ ECHO sees:</strong><br>{r["description"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="echo-says"><strong>💬 ECHO says:</strong><br><em>{r["greeting"]}</em></div>', unsafe_allow_html=True)
            if r["miss"]:
                m = r["miss"]; st.divider(); st.subheader("🔍 What did I miss?")
                if m.get("story"): st.markdown(f'<div class="brain-card"><div class="story">💭 {m["story"]}</div></div>', unsafe_allow_html=True)
                if m.get("weather_feel"): st.markdown(f'<div class="echo-says">🌤️ <em>{m["weather_feel"]}</em></div>', unsafe_allow_html=True)
                if m.get("gone"):
                    st.markdown("**❌ Gone:**")
                    for g in m["gone"]: st.markdown(f'<div class="missing-item">🚫 {g}</div>', unsafe_allow_html=True)
                if m.get("new"):
                    st.markdown("**✨ New:**")
                    for n in m["new"]: st.markdown(f'<div class="difference-item">➕ {n}</div>', unsafe_allow_html=True)
                if m.get("changed"):
                    st.markdown("**🔄 Changed:**")
                    for c_ in m["changed"]: st.markdown(f'<div class="difference-item">🔄 {c_}</div>', unsafe_allow_html=True)
                if m.get("tiny_details"):
                    st.markdown("**🔎 Tiny details:**")
                    for t in m["tiny_details"]: st.markdown(f'<div class="difference-item">🔍 {t}</div>', unsafe_allow_html=True)
            if r["objects"]:
                with st.expander(f"📋 {len(r['objects'])} items"):
                    for o in r["objects"]: st.write(f"• {o}")
            if r["brain"]:
                st.divider(); st.subheader("🧠 Place Brain"); b = r["brain"]
                st.markdown(f'<div class="brain-card"><div class="mood">💭 {b.get("mood","?")}</div><div class="story">{b.get("story","")}</div><div class="pattern">🔄 {b.get("pattern","")}</div></div>', unsafe_allow_html=True)
            if st.button("✨ Done"): st.session_state.last_snap_result = None; st.rerun()
    with tab_places:
        conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM places WHERE user_id = ? ORDER BY created_at DESC", (user_id,)); ps = c.fetchall(); conn.close()
        if not ps: st.info("No places yet.")
        for p in ps:
            conn = get_db(); c = conn.cursor()
            c.execute("SELECT COUNT(*) as x FROM memories WHERE place_id = ?", (p["id"],)); cnt = c.fetchone()["x"]
            c.execute("SELECT * FROM place_brains WHERE place_id = ?", (p["id"],)); br = c.fetchone()
            conn.close()
            with st.container(border=True):
                c1,c2 = st.columns([3,1])
                with c1:
                    st.markdown(f"### 📍 {p['name']}")
                    if br: st.caption(f"🧠 *{br['mood']}* • {cnt} visit(s)"); st.write(f"💭 {br['story']}")
                    else: st.caption(f"{cnt} visit(s)")
                with c2:
                    if st.button("Visit", key=f"vp_{p['id']}", use_container_width=True):
                        st.session_state.current_place_id = p["id"]; st.session_state.view = "place_detail"; st.rerun()
    with tab_brains:
        st.subheader("🧠 ECHO's Mind")
        conn = get_db(); c = conn.cursor()
        c.execute("""SELECT pb.*, p.name as pn FROM place_brains pb JOIN places p ON pb.place_id = p.id
            WHERE p.user_id = ? ORDER BY pb.last_seen DESC""", (user_id,)); bs = c.fetchall(); conn.close()
        if not bs: st.info("ECHO hasn't met your places yet.")
        for b in bs:
            st.markdown(f'<div class="brain-card"><strong>📍 {b["pn"]}</strong><div class="mood">💭 {b["mood"]}</div><div class="story">{b["story"]}</div><div class="pattern">🔄 {b["pattern"]}</div><div class="meta">First: {b["first_seen"][:10]} • Last: {b["last_seen"][:10]} • {b["total_visits"]} visit(s)</div></div>', unsafe_allow_html=True)
    with tab_compare:
        conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM places WHERE user_id = ?", (user_id,)); ps = c.fetchall(); conn.close()
        if not ps: st.info("Add places first.")
        else:
            opts = {p["name"]: p["id"] for p in ps}
            sn = st.selectbox("Choose place", list(opts.keys())); sid = opts[sn]
            conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM memories WHERE place_id = ? ORDER BY created_at ASC", (sid,)); ms = c.fetchall(); conn.close()
            if len(ms) < 2: st.warning("Need 2+ visits.")
            else:
                mo = {f"Visit {i+1} — {m['created_at'][:16]}": m for i,m in enumerate(ms)}
                c1,c2 = st.columns(2)
                with c1: o1 = st.selectbox("Older", list(mo.keys()), index=0)
                with c2: o2 = st.selectbox("Newer", list(mo.keys()), index=len(mo)-1)
                m1 = mo[o1]; m2 = mo[o2]
                cc1,cc2 = st.columns(2)
                with cc1:
                    if m1["photo_path"] and os.path.exists(m1["photo_path"]): st.image(m1["photo_path"], use_container_width=True)
                    st.write(m1["ai_description"])
                with cc2:
                    if m2["photo_path"] and os.path.exists(m2["photo_path"]): st.image(m2["photo_path"], use_container_width=True)
                    st.write(m2["ai_description"])
                if st.button("🔮 What Changed?", type="primary", use_container_width=True):
                    with st.spinner("..."):
                        ch = ai_compare_photos(m1["photo_path"], m2["photo_path"], sn)
                    st.markdown(f'<div class="echo-memory"><strong>🔮 What Changed:</strong><br>{ch}</div>', unsafe_allow_html=True)

def place_detail_view():
    pid = st.session_state.current_place_id
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT * FROM places WHERE id = ?", (pid,)); pl = c.fetchone()
    c.execute("SELECT * FROM memories WHERE place_id = ? ORDER BY created_at DESC", (pid,)); ms = c.fetchall()
    c.execute("SELECT * FROM place_brains WHERE place_id = ?", (pid,)); br = c.fetchone()
    conn.close()
    if not pl: st.session_state.view = "echo"; st.rerun(); return
    st.markdown(f'<div class="nexus-header"><h1>📍 {pl["name"]}</h1><p>{len(ms)} visit(s)</p></div>', unsafe_allow_html=True)
    if br: st.markdown(f'<div class="brain-card"><div class="mood">💭 {br["mood"]}</div><div class="story">{br["story"]}</div><div class="pattern">🔄 {br["pattern"]}</div></div>', unsafe_allow_html=True)
    if st.button("← Back"): st.session_state.current_place_id = None; st.session_state.view = "echo"; st.rerun()
    st.divider()
    for i,m in enumerate(ms):
        with st.container(border=True):
            st.markdown(f"**Visit {len(ms)-i}** — {m['created_at'][:16]} • felt *{m['mood'] or '—'}*")
            c1,c2 = st.columns([1,2])
            with c1:
                if m["photo_path"] and os.path.exists(m["photo_path"]): st.image(m["photo_path"], use_container_width=True)
            with c2:
                if m["ai_description"]: st.write(f"🧠 {m['ai_description']}")
                if m["user_note"]: st.write(f"📝 {m['user_note']}")

# ============================================================
# CHAT
# ============================================================
def chat_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>💬 NEXUS</h1><p>Powered by GPT-OSS 20B</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.sidebar:
        st.markdown("### 💬 Chats")
        if st.button("➕ New Chat", use_container_width=True):
            conn = get_db(); c = conn.cursor()
            c.execute("INSERT INTO chats (user_id,title,created_at) VALUES (?,?,?)", (user_id,"New Chat",datetime.now().isoformat()))
            st.session_state.current_chat_id = c.lastrowid; conn.commit(); conn.close(); st.rerun()
        conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM chats WHERE user_id = ? ORDER BY created_at DESC", (user_id,)); cs = c.fetchall(); conn.close()
        for ch in cs:
            t = ch["title"] or "New Chat"; pre = "🟢 " if ch["id"]==st.session_state.current_chat_id else "💬 "
            if st.button(f"{pre}{t[:20]}", key=f"c_{ch['id']}", use_container_width=True):
                st.session_state.current_chat_id = ch["id"]; st.rerun()
    if st.session_state.current_chat_id is None:
        conn = get_db(); c = conn.cursor(); c.execute("INSERT INTO chats (user_id,title,created_at) VALUES (?,?,?)", (user_id,"New Chat",datetime.now().isoformat()))
        st.session_state.current_chat_id = c.lastrowid; conn.commit(); conn.close(); st.rerun()
    cid = st.session_state.current_chat_id
    conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM messages WHERE chat_id = ? ORDER BY id ASC", (cid,)); ms = c.fetchall(); conn.close()
    for m in ms:
        with st.chat_message(m["role"]): st.write(m["content"])
    p = st.chat_input("Message NEXUS...")
    if p:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO messages (chat_id,role,content,created_at) VALUES (?,?,?,?)", (cid,"user",p,datetime.now().isoformat()))
        c.execute("SELECT title FROM chats WHERE id = ?", (cid,)); r = c.fetchone()
        if r and (r["title"]=="New Chat" or not r["title"]): c.execute("UPDATE chats SET title = ? WHERE id = ?", (p[:40], cid))
        conn.commit(); conn.close()
        with st.chat_message("user"): st.write(p)
        with st.chat_message("assistant"):
            ph = st.empty(); ph.markdown('<div class="think-box">🧠 Thinking...</div>', unsafe_allow_html=True)
            conn = get_db(); c = conn.cursor(); c.execute("SELECT role,content FROM messages WHERE chat_id = ? ORDER BY id ASC", (cid,)); h = c.fetchall(); conn.close()
            sp = f"You are NEXUS. Warm, personal. User context:\n{get_nexus_context(user_id)}"
            api = [{"role":"system","content":sp}]
            for x in h[-20:]: api.append({"role":x["role"],"content":x["content"]})
            rep = ai_chat(api); ph.empty(); st.write(rep)
        award_xp(user_id, 2); play_sound("click")
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO messages (chat_id,role,content,created_at) VALUES (?,?,?,?)", (cid,"assistant",rep,datetime.now().isoformat()))
        conn.commit(); conn.close(); st.rerun()

def get_nexus_context(user_id):
    conn = get_db(); c = conn.cursor(); ps = []
    c.execute("SELECT name FROM users WHERE id = ?", (user_id,)); u = c.fetchone()
    if u: ps.append(f"Name: {u['name']}")
    c.execute("SELECT name FROM places WHERE user_id = ? LIMIT 5", (user_id,)); pl = [x["name"] for x in c.fetchall()]
    if pl: ps.append(f"Places: {', '.join(pl)}")
    c.execute("SELECT title FROM notes WHERE user_id = ? LIMIT 3", (user_id,)); nt = [x["title"] for x in c.fetchall() if x["title"]]
    if nt: ps.append(f"Notes: {', '.join(nt)}")
    conn.close(); return "\n".join(ps)

# ============================================================
# TUTOR (compressed)
# ============================================================
def tutor_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>🎓 TUTOR</h1></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("nl"):
        t = st.text_input("What to learn?")
        if st.form_submit_button("🧠 Build Lesson", type="primary", use_container_width=True):
            if not t: st.error("Enter topic")
            else:
                with st.spinner("Preparing..."): L = ai_build_lesson(t)
                if L:
                    conn = get_db(); c = conn.cursor()
                    c.execute("INSERT INTO lessons (user_id,title,topic,steps,created_at) VALUES (?,?,?,?,?)",
                              (user_id,L.get("title",t),t,json.dumps(L),datetime.now().isoformat()))
                    st.session_state.current_lesson = {"id":c.lastrowid,**L}; st.session_state.current_step = 0
                    conn.commit(); conn.close(); award_xp(user_id,10); st.rerun()
    if st.session_state.current_lesson:
        L = st.session_state.current_lesson; st.divider()
        st.markdown(f"## 📖 {L.get('title','')}"); st.info(L.get("intro",""))
        stps = L.get("steps",[]); i = st.session_state.current_step
        st.progress(i/max(len(stps),1)); st.caption(f"Step {i+1}/{len(stps)}")
        if i < len(stps):
            s = stps[i]
            st.markdown(f"### {s.get('number',i+1)}. {s.get('title','')}")
            st.write(s.get("instruction",""))
            if s.get("tip"): st.info(f"💡 {s['tip']}")
            if s.get("check"): st.markdown(f"**🤔 {s['check']}**")
            c1,c2,c3 = st.columns(3)
            with c1:
                if st.button("✅ Next", type="primary", use_container_width=True):
                    st.session_state.current_step += 1; award_xp(user_id,5); play_sound("click"); st.rerun()
            with c2:
                if st.button("🤔 Don't Understand", use_container_width=True):
                    with st.spinner("..."): r = ai_chat([{"role":"system","content":"Rephrase simpler with metaphor. Under 80 words."},{"role":"user","content":s.get("instruction","")}])
                    st.warning(f"🧠 {r}")
            with c3:
                if st.button("⏸️ Pause", use_container_width=True):
                    st.session_state.current_lesson = None; st.session_state.current_step = 0; st.rerun()
        else:
            st.success("🎉 Complete! +50 XP"); award_xp(user_id,50); celebrate(); play_sound("win"); toast("🎉 +50 XP")
            if st.button("🔄 New"):
                st.session_state.current_lesson = None; st.session_state.current_step = 0; st.rerun()

# ============================================================
# ATLAS (compressed — repair + health)
# ============================================================
def repair_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>🔧 ATLAS</h1></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    mode = st.radio("Mode", ["🔧 Device", "💊 Health", "📖 History"], horizontal=True, label_visibility="collapsed")
    st.divider()
    if mode == "🔧 Device":
        with st.form("nr"):
            d = st.text_input("Device"); p = st.text_area("Problem", height=80)
            b = st.text_input("Brand (optional)"); m = st.text_input("Model (optional)")
            if st.form_submit_button("🔧 Build Guide", type="primary", use_container_width=True):
                if not d or not p: st.error("Fill both")
                else:
                    if b or m:
                        conn = get_db(); c = conn.cursor()
                        c.execute("INSERT INTO user_devices (user_id,device,brand,model,created_at) VALUES (?,?,?,?,?)",
                                  (user_id,d,b,m,datetime.now().isoformat()))
                        conn.commit(); conn.close()
                    with st.spinner("..."): g = ai_build_repair(d,p,b,m)
                    if g:
                        conn = get_db(); c = conn.cursor()
                        c.execute("INSERT INTO repairs (user_id,device,problem,steps,created_at) VALUES (?,?,?,?,?)",
                                  (user_id,d,p,json.dumps(g),datetime.now().isoformat()))
                        st.session_state.current_repair = {"id":c.lastrowid,**g,"device_name":d}; st.session_state.repair_step = 0
                        conn.commit(); conn.close(); award_xp(user_id,20); st.rerun()
        if st.session_state.current_repair:
            R = st.session_state.current_repair; st.divider()
            st.markdown(f"## 🔧 {R.get('title','')}")
            if R.get("likely_cause"): st.info(f"🎯 {R['likely_cause']}")
            if R.get("safety"): st.error(f"⚠️ {R['safety']}")
            if R.get("tools_needed"): st.markdown(f"🧰 {' • '.join(R['tools_needed'])}")
            stps = R.get("steps",[]); i = st.session_state.repair_step
            st.progress(i/max(len(stps),1))
            if i < len(stps):
                s = stps[i]; st.markdown(f"### {s.get('number',i+1)}. {s.get('title','')}")
                st.write(s.get("instruction",""))
                if s.get("warning"): st.warning(f"⚠️ {s['warning']}")
                if s.get("check"): st.markdown(f"**✅ {s['check']}**")
                c1,c2 = st.columns(2)
                with c1:
                    if st.button("✅ Next", type="primary", use_container_width=True):
                        st.session_state.repair_step += 1; st.rerun()
                with c2:
                    if st.button("⏸️ Pause", use_container_width=True):
                        st.session_state.current_repair = None; st.session_state.repair_step = 0; st.rerun()
            else:
                st.success("🎉 Repair done! +30 XP"); award_xp(user_id,30); celebrate(); play_sound("win")
                if st.button("🔄 New"):
                    st.session_state.current_repair = None; st.session_state.repair_step = 0; st.rerun()
    elif mode == "💊 Health":
        with st.form("nh"):
            ag = st.selectbox("Age group", ["Baby (0-2)","Child (3-12)","Teen (13-19)","Adult (20-59)","Elderly (60+)"])
            al = st.text_input("Allergies (optional)"); md = st.text_input("Medications (optional)")
            sy = st.text_area("Symptoms", height=100)
            if st.form_submit_button("💊 Get Guidance", type="primary", use_container_width=True):
                if not sy: st.error("Describe symptoms")
                else:
                    with st.spinner("..."): g = ai_health_guide(sy, ag, al, md)
                    if g:
                        conn = get_db(); c = conn.cursor()
                        c.execute("INSERT INTO health_guides (user_id,symptoms,age_group,guide,created_at) VALUES (?,?,?,?,?)",
                                  (user_id,sy,ag,json.dumps(g),datetime.now().isoformat()))
                        conn.commit(); conn.close(); st.session_state.health_guide = g; award_xp(user_id,10); st.rerun()
        g = st.session_state.get("health_guide")
        if g:
            st.divider()
            srs = g.get("seriousness","Mild")
            ico = {"Mild":"🟢","Moderate":"🟡","Serious":"🟠","Emergency":"🔴"}.get(srs,"🟡")
            st.markdown(f"## {ico} {g.get('title','')}")
            st.markdown(f"**{ico} {srs}**")
            if g.get("safety"): st.error(f"⚠️ {g['safety']}")
            st.subheader("🔍 Causes")
            for x in g.get("possible_causes",[]): st.markdown(f'<div class="difference-item">• {x}</div>', unsafe_allow_html=True)
            st.subheader("🏠 Home care")
            for x in g.get("home_care",[]): st.markdown(f'<div class="same-item">• {x}</div>', unsafe_allow_html=True)
            for m in g.get("medicines",[]):
                if isinstance(m,dict):
                    st.markdown(f'<div class="brain-card"><strong>💊 {m.get("name","")}</strong><br>Dose: {m.get("dose","")}<br><em>{m.get("note","")}</em></div>', unsafe_allow_html=True)
            st.subheader("🚨 Hospital if:")
            for x in g.get("warning_signs",[]): st.markdown(f'<div class="missing-item">🚨 {x}</div>', unsafe_allow_html=True)
            if g.get("when_to_see_doctor"): st.info(f"👨‍⚕️ {g['when_to_see_doctor']}")
            if st.button("🔄 New"): st.session_state.health_guide = None; st.rerun()
    else:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM repairs WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,)); rp = c.fetchall()
        c.execute("SELECT * FROM health_guides WHERE user_id = ? ORDER BY created_at DESC LIMIT 10", (user_id,)); hg = c.fetchall()
        conn.close()
        st.subheader("🔧 Repairs")
        for r in rp:
            with st.expander(f"{r['device']} — {r['created_at'][:10]}"):
                st.write(r["problem"])
        st.subheader("💊 Health")
        for h in hg:
            with st.expander(f"{h['symptoms'][:40]} — {h['created_at'][:10]}"):
                try:
                    g = json.loads(h["guide"]); st.write(f"**{g.get('seriousness','')}**")
                except: pass

# ============================================================
# NOTES
# ============================================================
def notes_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>📝 NOTES</h1></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("nn"):
        t = st.text_input("Title"); co = st.text_area("Note", height=150)
        if st.form_submit_button("💾 Save", type="primary", use_container_width=True):
            if not co: st.error("Write something")
            else:
                with st.spinner("..."):
                    tg = ai_suggest_tags(co); cn = ai_note_connections(user_id, co)
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO notes (user_id,title,content,tags,created_at) VALUES (?,?,?,?,?)",
                          (user_id, t or co[:40], co, tg, datetime.now().isoformat()))
                conn.commit(); conn.close()
                award_xp(user_id,5); play_sound("success"); toast("✅ +5 XP")
                if cn and "no connections" not in cn.lower(): st.info(f"🔗 {cn}")
                st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC", (user_id,)); ns = c.fetchall(); conn.close()
    for n in ns:
        with st.expander(f"📝 {n['title']} — {n['created_at'][:16]}"):
            st.write(n["content"])
            if n["tags"]: st.caption(f"🏷️ {n['tags']}")

# ============================================================
# JOURNAL
# ============================================================
def journal_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>📖 JOURNAL</h1></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("nj"):
        t = st.text_input("Title")
        mo = st.selectbox("Mood", ["😊 Happy","😌 Calm","🤔 Thoughtful","😔 Sad","😤 Frustrated","😴 Tired","🔥 Motivated","😐 Neutral"])
        co = st.text_area("Write freely...", height=200)
        if st.form_submit_button("📖 Save", type="primary", use_container_width=True):
            if not co: st.error("Write something")
            else:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO journal (user_id,title,content,mood,created_at) VALUES (?,?,?,?,?)",
                          (user_id, t or co[:40], co, mo, datetime.now().isoformat()))
                conn.commit(); conn.close()
                award_xp(user_id,8); play_sound("success"); toast("✅ +8 XP")
                st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM journal WHERE user_id = ? ORDER BY created_at DESC", (user_id,)); es = c.fetchall(); conn.close()
    for e in es:
        with st.expander(f"{e['mood']} {e['title']} — {e['created_at'][:16]}"):
            st.write(e["content"])
            if st.button("🤔 AI Reflect", key=f"r_{e['id']}"):
                with st.spinner("..."): r = ai_chat([{"role":"system","content":"Warm gentle journal companion. Reflect with empathy. Ask one gentle question. Under 60 words."},{"role":"user","content":e["content"]}])
                st.info(f"💭 {r}")

# ============================================================
# DREAMS — FULLY UPGRADED
# ============================================================
def dreams_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>🌙 DREAMS</h1><p>Your dream interpreter</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs(["✍️ New Dream", "🌌 My Dreams", "🔮 Patterns", "🌙 Dream Guide"])
    
    with tab1:
        st.subheader("Tell NEXUS your dream")
        guided = st.checkbox("Give me a dream prompt")
        if guided:
            if "dream_prompt" not in st.session_state: st.session_state.dream_prompt = ai_dream_question(user_id)
            st.markdown(f'<div class="dream-quote">{st.session_state.dream_prompt}</div>', unsafe_allow_html=True)
            if st.button("🔄 New prompt"): st.session_state.dream_prompt = ai_dream_question(user_id); st.rerun()
        
        with st.form("nd"):
            dream = st.text_area("Your dream...", height=200, placeholder="e.g. I was flying over a lake, then suddenly fell into cold water...")
            if st.form_submit_button("🌙 Interpret", type="primary", use_container_width=True):
                if not dream: st.error("Describe your dream")
                else:
                    with st.spinner("Reading your dream..."):
                        interp = ai_interpret_dream(dream, user_id)
                    conn = get_db(); c = conn.cursor()
                    symbols = ", ".join(interp.get("symbols", []))
                    c.execute("""INSERT INTO dreams (user_id,content,ai_interpretation,dream_type,symbol,emotion,recurring,created_at)
                        VALUES (?,?,?,?,?,?,?,?)""",
                        (user_id, dream, json.dumps(interp), interp.get("dream_type","Symbolic"),
                         symbols, interp.get("emotion","unknown"),
                         1 if interp.get("is_recurring") else 0, datetime.now().isoformat()))
                    conn.commit(); conn.close()
                    award_xp(user_id,12); play_sound("success"); toast("🌙 +12 XP · Dream interpreted")
                    st.rerun()
    
    with tab2:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM dreams WHERE user_id = ? ORDER BY created_at DESC", (user_id,)); ds = c.fetchall(); conn.close()
        if not ds: st.info("No dreams yet.")
        for d in ds:
            with st.expander(f"🌙 {d['created_at'][:16]} — [{d['dream_type'] or '?'}] {d['content'][:40]}..."):
                st.write(f"**Dream:** {d['content']}")
                try:
                    i = json.loads(d["ai_interpretation"])
                    st.markdown(f'<div class="brain-card"><div class="mood">🌙 {i.get("dream_type","")} · 💭 {i.get("emotion","")}</div><div class="story"><strong>Meaning:</strong> {i.get("meaning","")}</div></div>', unsafe_allow_html=True)
                    if i.get("symbols"):
                        sym_html = "".join([f'<span class="dream-symbol">{s}</span>' for s in i["symbols"]])
                        st.markdown(f"**Symbols:** {sym_html}", unsafe_allow_html=True)
                    if i.get("life_connection"):
                        st.markdown(f"🔗 *{i['life_connection']}*")
                    st.markdown(f'<div class="echo-says">💫 <em>{i.get("message","")}</em></div>', unsafe_allow_html=True)
                    if i.get("action"): st.info(f"🎯 **Today:** {i['action']}")
                except: st.write(d["ai_interpretation"])
    
    with tab3:
        st.subheader("🔮 Your Dream Patterns")
        insight = ai_dream_insight(user_id)
        if insight:
            st.markdown(f'<div class="brain-card"><div class="story">📖 {insight.get("pattern","")}</div><div class="pattern">✨ {insight.get("advice","")}</div></div>', unsafe_allow_html=True)
        else:
            st.info("Write at least 3 dreams for NEXUS to spot patterns.")
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT dream_type, COUNT(*) as x FROM dreams WHERE user_id = ? GROUP BY dream_type ORDER BY x DESC", (user_id,))
        dts = c.fetchall()
        c.execute("SELECT emotion, COUNT(*) as x FROM dreams WHERE user_id = ? GROUP BY emotion ORDER BY x DESC", (user_id,))
        ems = c.fetchall()
        conn.close()
        if dts:
            st.subheader("Dream types")
            for t in dts: st.write(f"• **{t['dream_type'] or '?'}** — {t['x']}")
        if ems:
            st.subheader("Emotions")
            for e in ems: st.write(f"• **{e['emotion'] or '?'}** — {e['x']}")
    
    with tab4:
        st.subheader("🌙 Common Dream Symbols")
        st.caption("The meanings NEXUS recognizes")
        cols = st.columns(3)
        for i, (sym, meaning) in enumerate(DREAM_SYMBOLS.items()):
            with cols[i % 3]:
                st.markdown(f'<div class="suggestion"><span class="icon">{meaning.split()[0]}</span><span class="text"><strong>{sym.capitalize()}:</strong> {" ".join(meaning.split()[1:])}</span></div>', unsafe_allow_html=True)
        st.divider()
        st.subheader("🛌 Before Sleep")
        st.markdown("""
        - **Write your intention** — what would you like to dream about?
        - **Journal one line** — what's on your mind?
        - **Hydrate** — dreams form better when rested
        - **Set your phone down** 30 min before sleep
        - **When you wake**, write your dream before touching anything else
        """)

# ============================================================
# CAPSULE
# ============================================================
def capsule_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>⏳ CAPSULE</h1><p>Message your future self</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("nc"):
        m = st.text_area("Message to future you...", height=200, placeholder="Dear future me...")
        u = st.date_input("Open on", value=datetime.now().date() + timedelta(days=365))
        if st.form_submit_button("🔒 Seal", type="primary", use_container_width=True):
            if not m: st.error("Write a message")
            else:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO time_capsules (user_id,message,unlock_date,opened,created_at) VALUES (?,?,?,0,?)",
                          (user_id,m,str(u),datetime.now().isoformat()))
                conn.commit(); conn.close()
                award_xp(user_id,25); celebrate(); play_sound("win"); toast("⏳ Sealed! +25 XP")
                st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM time_capsules WHERE user_id = ? ORDER BY unlock_date ASC", (user_id,)); cs = c.fetchall(); conn.close()
    if not cs: st.info("No capsules yet.")
    for cap in cs:
        try:
            ud = datetime.strptime(cap["unlock_date"], "%Y-%m-%d").date()
            dl = (ud - datetime.now().date()).days
        except: dl = 999
        if dl <= 0 and not cap["opened"]:
            with st.container(border=True):
                st.markdown("### 🔓 A capsule is ready!")
                st.write(f"**You wrote:** {cap['message']}")
                if st.button("💌 Read reply from future you", key=f"o_{cap['id']}"):
                    with st.spinner("..."): r = ai_time_capsule_note(user_id, cap["message"])
                    conn = get_db(); c = conn.cursor()
                    c.execute("UPDATE time_capsules SET opened = 1 WHERE id = ?", (cap["id"],))
                    conn.commit(); conn.close()
                    st.markdown(f'<div class="brain-card"><div class="story">💌 {r}</div></div>', unsafe_allow_html=True)
        else:
            with st.expander(f"🔒 opens in {dl} days ({cap['unlock_date']})"):
                st.caption("Still sealed.")

# ============================================================
# ⚔️ ARENA — Competitive Game
# ============================================================
def arena_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>⚔️ ARENA</h1><p>A game deeper than Chess</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    
    st.markdown("""
    ### 🎯 Rules of Arena
    
    **Board:** 6×6 · **Pieces per player:** 6
    
    | Piece | Icon | Movement | Captures |
    | :--- | :--- | :--- | :--- |
    | 🛡️ Shield | 2 per player | 1 step any direction | Never captures — blocks |
    | ⚔️ Spear | 2 per player | 1 step orthogonally | Orthogonally |
    | 🧙 Sage | 1 per player | up to 3 diagonally | Diagonally |
    | 👑 King | 1 per player | 1 step any direction | Any adjacent |
    
    **Victory:**
    - Capture the enemy King, OR
    - Hold all 4 center squares for 3 consecutive turns
    """)
    st.divider()
    
    # Setup
    if st.session_state.arena_board is None:
        st.subheader("⚙️ New Match")
        c1, c2 = st.columns(2)
        with c1:
            diff = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
            st.session_state.arena_difficulty = diff
        with c2:
            if st.button("⚔️ Start Match", type="primary", use_container_width=True):
                st.session_state.arena_board = new_arena_board()
                st.session_state.arena_turn = 1
                st.session_state.arena_move_count = 0
                st.session_state.arena_center_turns = 0
                play_sound("enter")
                st.rerun()
        return
    
    board = st.session_state.arena_board
    turn = st.session_state.arena_turn
    
    # Center control tracker
    cc = arena_center_control(board)
    if cc == 1: st.session_state.arena_center_turns += 1
    elif cc == 2: st.session_state.arena_center_turns -= 1
    else: st.session_state.arena_center_turns = 0
    if st.session_state.arena_center_turns >= 3:
        win_arena(user_id, "win"); st.session_state.arena_last_result = "You held center!"; return
    if st.session_state.arena_center_turns <= -3:
        win_arena(user_id, "loss"); st.session_state.arena_last_result = "NEXUS held center!"; return
    
    st.markdown(f"**Turn:** {'🟦 Your move' if turn==1 else '🟥 NEXUS thinking...'} · **Difficulty:** {st.session_state.arena_difficulty}")
    st.caption(f"Move #{st.session_state.arena_move_count + 1} · Center control: {'You' if cc==1 else 'NEXUS' if cc==2 else 'contested'}")
    
    # Board HTML
    html = '<div class="arena-board">'
    for r in range(ARENA_SIZE):
        html += '<div>'
        for c in range(ARENA_SIZE):
            piece = board[r][c]
            if piece:
                cls = "arena-cell p1" if piece["p"] == 1 else "arena-cell p2"
                html += f'<div class="{cls}">{PIECE_ICONS[piece["t"]]}</div>'
            else:
                html += '<div class="arena-cell empty"></div>'
        html += '</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    
    # Move selection
    if turn == 1:
        st.subheader("Your move")
        my_pieces = []
        for r in range(ARENA_SIZE):
            for c in range(ARENA_SIZE):
                p = board[r][c]
                if p and p["p"] == 1:
                    ms = arena_moves(board, r, c)
                    if ms: my_pieces.append((r, c, p["t"], ms))
        
        if not my_pieces:
            win_arena(user_id, "loss"); st.session_state.arena_last_result = "No moves left."; return
        
        options = [f"{PIECE_ICONS[t]} at {chr(65+c)}{r+1} → {len(ms)} moves" for r,c,t,ms in my_pieces]
        idx = st.selectbox("Choose piece", range(len(my_pieces)), format_func=lambda i: options[i])
        fr, fc, ft, ms = my_pieces[idx]
        
        dest_options = [f"{chr(65+tc)}{tr+1}" for tr,tc in ms]
        dest_idx = st.selectbox("Move to", range(len(ms)), format_func=lambda i: dest_options[i])
        tr, tc = ms[dest_idx]
        
        if st.button("✅ Confirm Move", type="primary", use_container_width=True):
            new_board, captured = arena_apply(board, fr, fc, tr, tc)
            st.session_state.arena_board = new_board
            st.session_state.arena_move_count += 1
            play_sound("click")
            if captured and captured["t"] == "K" and captured["p"] == 2:
                win_arena(user_id, "win"); st.session_state.arena_last_result = "You captured NEXUS's King!"; return
            st.session_state.arena_turn = 2
            st.rerun()
    else:
        st.subheader("NEXUS is thinking...")
        with st.spinner(""):
            time.sleep(0.5)
            mv = arena_ai_move(board, st.session_state.arena_difficulty)
        if not mv:
            win_arena(user_id, "win"); st.session_state.arena_last_result = "NEXUS has no moves!"; return
        fr, fc, tr, tc = mv
        new_board, captured = arena_apply(board, fr, fc, tr, tc)
        st.session_state.arena_board = new_board
        st.session_state.arena_move_count += 1
        if captured and captured["t"] == "K" and captured["p"] == 1:
            win_arena(user_id, "loss"); st.session_state.arena_last_result = "NEXUS captured your King!"; return
        st.session_state.arena_turn = 1
        st.rerun()
    
    st.divider()
    if st.button("🚪 Resign / Leave Match", use_container_width=True):
        win_arena(user_id, "loss")
        st.session_state.arena_last_result = "You resigned."
        st.rerun()

def win_arena(user_id, result):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO arena_matches (user_id,result,moves,difficulty,points,created_at) VALUES (?,?,?,?,?,?)",
              (user_id, result, st.session_state.arena_move_count, st.session_state.arena_difficulty,
               30 if result == "win" else 0, datetime.now().isoformat()))
    if result == "win":
        c.execute("UPDATE users SET arena_wins = arena_wins + 1 WHERE id = ?", (user_id,))
    else:
        c.execute("UPDATE users SET arena_losses = arena_losses + 1 WHERE id = ?", (user_id,))
    conn.commit(); conn.close()
    if result == "win":
        award_xp(user_id, 30); celebrate(); play_sound("win"); toast("🏆 Arena victory! +30 XP")
    else:
        play_sound("lose")
    st.session_state.arena_board = None
    st.session_state.arena_turn = 1
    st.session_state.arena_move_count = 0
    st.session_state.arena_center_turns = 0
    st.rerun()

# ============================================================
# HABITS
# ============================================================
def habits_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>✅ HABITS</h1><p>Build streaks</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("nh"):
        n = st.text_input("Habit name")
        i = st.text_input("Emoji icon", value="✅")
        if st.form_submit_button("➕ Add", type="primary", use_container_width=True):
            if n:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO habits (user_id,name,icon,created_at) VALUES (?,?,?,?)", (user_id,n,i,datetime.now().isoformat()))
                conn.commit(); conn.close(); award_xp(user_id,3); play_sound("success"); st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM habits WHERE user_id = ? ORDER BY created_at DESC", (user_id,)); hs = c.fetchall(); conn.close()
    today = datetime.now().date().isoformat()
    for h in hs:
        done = h["last_done"] == today
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"### {h['icon']} {h['name']}")
                st.caption(f"🔥 Streak: {h['streak']} days")
            with c2:
                if done:
                    st.success("✅ Done today")
                else:
                    if st.button("Mark done", key=f"hd_{h['id']}", use_container_width=True):
                        conn = get_db(); c = conn.cursor()
                        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
                        new_streak = (h["streak"] or 0) + 1 if h["last_done"] == yesterday else 1
                        c.execute("UPDATE habits SET last_done = ?, streak = ? WHERE id = ?", (today, new_streak, h["id"]))
                        conn.commit(); conn.close()
                        award_xp(user_id, 5); play_sound("success"); toast("✅ +5 XP")
                        st.rerun()

# ============================================================
# FOCUS (Pomodoro)
# ============================================================
def focus_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>🎯 FOCUS</h1><p>Pomodoro timer</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    st.subheader("Start a focus session")
    task = st.text_input("What are you focusing on?")
    dur = st.select_slider("Minutes", options=[5, 10, 15, 25, 30, 45, 60], value=25)
    if st.button("▶️ Start Focus", type="primary", use_container_width=True):
        if not task: st.error("Name your task")
        else:
            st.session_state.focus_task = task
            st.session_state.focus_end = time.time() + dur*60
            st.session_state.focus_duration = dur
            st.rerun()
    if st.session_state.get("focus_end"):
        remaining = int(st.session_state.focus_end - time.time())
        if remaining > 0:
            mins, secs = divmod(remaining, 60)
            st.markdown(f'<div class="brain-card"><div class="mood">⏱️ {mins:02d}:{secs:02d}</div><div class="story">Focusing on: <strong>{st.session_state.focus_task}</strong></div></div>', unsafe_allow_html=True)
            st.caption("Keep this tab open. Refresh to update timer.")
            if st.button("🔄 Refresh timer"): st.rerun()
        else:
            st.success(f"🎉 Focus session complete! +{st.session_state.focus_duration} XP")
            conn = get_db(); c = conn.cursor()
            c.execute("INSERT INTO focus_sessions (user_id,duration,task,completed,created_at) VALUES (?,?,?,1,?)",
                      (user_id, st.session_state.focus_duration, st.session_state.focus_task, datetime.now().isoformat()))
            conn.commit(); conn.close()
            award_xp(user_id, st.session_state.focus_duration)
            celebrate(); play_sound("win")
            st.session_state.focus_end = None
            st.session_state.focus_task = ""
            if st.button("🔄 Another session"): st.rerun()

# ============================================================
# GRATITUDE
# ============================================================
def gratitude_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>🙏 GRATITUDE</h1><p>Three things today</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("ng"):
        items = st.text_area("Three things you're grateful for (one per line)", height=150)
        if st.form_submit_button("💾 Save", type="primary", use_container_width=True):
            if items.strip():
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO gratitude (user_id,items,created_at) VALUES (?,?,?)", (user_id,items,datetime.now().isoformat()))
                conn.commit(); conn.close()
                award_xp(user_id, 5); play_sound("success"); toast("🙏 +5 XP")
                st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM gratitude WHERE user_id = ? ORDER BY created_at DESC LIMIT 30", (user_id,)); gs = c.fetchall(); conn.close()
    for g in gs:
        with st.expander(f"🙏 {g['created_at'][:16]}"):
            st.write(g["items"])

# ============================================================
# WINS
# ============================================================
def wins_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>🏆 WINS</h1><p>Track every small victory</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("nw"):
        d = st.text_input("What did you win today?")
        sz = st.selectbox("Size", ["tiny", "small", "medium", "big", "massive"])
        if st.form_submit_button("➕ Log Win", type="primary", use_container_width=True):
            if d:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO wins_log (user_id,description,size,created_at) VALUES (?,?,?,?)",
                          (user_id,d,sz,datetime.now().isoformat()))
                conn.commit(); conn.close()
                award_xp(user_id, 4); play_sound("win"); toast("🏆 +4 XP")
                st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM wins_log WHERE user_id = ? ORDER BY created_at DESC LIMIT 50", (user_id,)); ws = c.fetchall(); conn.close()
    for w in ws:
        emoji = {"tiny":"🐣","small":"✨","medium":"🌟","big":"🏆","massive":"👑"}.get(w["size"],"🏆")
        st.markdown(f'<div class="suggestion"><span class="icon">{emoji}</span><span class="text"><strong>{w["created_at"][:10]}</strong> — {w["description"]}</span></div>', unsafe_allow_html=True)

# ============================================================
# READING
# ============================================================
def reading_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>📚 READING</h1><p>Your book list</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("nr"):
        t = st.text_input("Title"); l = st.text_input("Link (optional)")
        s = st.selectbox("Status", ["Want to read","Reading","Finished"])
        if st.form_submit_button("➕ Add", type="primary", use_container_width=True):
            if t:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO reading_list (user_id,title,link,status,created_at) VALUES (?,?,?,?,?)",
                          (user_id,t,l,s,datetime.now().isoformat()))
                conn.commit(); conn.close(); award_xp(user_id,3); st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM reading_list WHERE user_id = ? ORDER BY created_at DESC", (user_id,)); rs = c.fetchall(); conn.close()
    for r in rs:
        st.markdown(f'<div class="suggestion"><span class="icon">📖</span><span class="text"><strong>{r["title"]}</strong> — {r["status"]}</span></div>', unsafe_allow_html=True)

# ============================================================
# QUOTES
# ============================================================
def quotes_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>💬 QUOTES</h1><p>Words that move you</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("nq"):
        q = st.text_area("Quote", height=80)
        a = st.text_input("Author (optional)")
        if st.form_submit_button("💾 Save", type="primary", use_container_width=True):
            if q:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO quotes_saved (user_id,quote,author,created_at) VALUES (?,?,?,?)",
                          (user_id,q,a,datetime.now().isoformat()))
                conn.commit(); conn.close(); award_xp(user_id,3); st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM quotes_saved WHERE user_id = ? ORDER BY created_at DESC", (user_id,)); qs = c.fetchall(); conn.close()
    for q in qs:
        st.markdown(f'<div class="dream-quote">"{q["quote"]}"<div style="font-size:13px;margin-top:8px;opacity:0.6;">— {q["author"] or "Unknown"}</div></div>', unsafe_allow_html=True)

# ============================================================
# FLASH CARDS
# ============================================================
def flash_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>🃏 FLASH</h1><p>Study with cards</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("nf"):
        q = st.text_input("Question"); a = st.text_input("Answer"); d = st.text_input("Deck", value="General")
        if st.form_submit_button("➕ Add Card", type="primary", use_container_width=True):
            if q and a:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO flash_cards (user_id,question,answer,deck,created_at) VALUES (?,?,?,?,?)",
                          (user_id,q,a,d,datetime.now().isoformat()))
                conn.commit(); conn.close(); award_xp(user_id,3); st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM flash_cards WHERE user_id = ? ORDER BY created_at DESC", (user_id,)); cs = c.fetchall(); conn.close()
    if not cs: st.info("No cards yet.")
    for card in cs:
        with st.expander(f"🃏 [{card['deck']}] {card['question']}"):
            if st.button("👁️ Reveal", key=f"rv_{card['id']}"):
                st.success(card["answer"])

# ============================================================
# BREATHING
# ============================================================
def breathing_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>🫁 BREATHE</h1><p>Calm the mind</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    st.markdown("""
    ### 4-7-8 Breathing
    
    1. **Inhale** through nose for **4 seconds**
    2. **Hold** for **7 seconds**
    3. **Exhale** slowly through mouth for **8 seconds**
    4. Repeat 4 times
    """)
    st.components.v1.html("""
    <div style="text-align:center;padding:40px;">
        <div id="breath-circle" style="width:200px;height:200px;margin:auto;border-radius:50%;
            background: linear-gradient(135deg,#667eea,#f093fb);
            transition:all 4s ease; display:flex; align-items:center; justify-content:center;
            color:white;font-size:20px;font-weight:700;">
            Start
        </div>
        <button onclick="startBreath()" style="margin-top:20px;padding:12px 24px;border-radius:12px;
            border:none;background:#667eea;color:white;font-weight:700;cursor:pointer;">
            Begin
        </button>
    </div>
    <script>
    function startBreath() {
        const c = document.getElementById('breath-circle');
        let phase = 0;
        const phases = [
            {text:'Inhale',dur:4000,scale:1.4},
            {text:'Hold',dur:7000,scale:1.4},
            {text:'Exhale',dur:8000,scale:1.0}
        ];
        function next() {
            if (phase >= 3) { c.textContent = 'Done 🧘'; return; }
            const p = phases[phase];
            c.textContent = p.text;
            c.style.transition = `all ${p.dur}ms ease`;
            c.style.transform = `scale(${p.scale})`;
            phase++;
            setTimeout(next, p.dur);
        }
        next();
    }
    </script>
    """, height=320)
    if st.button("✅ Log a 4-cycle session", type="primary", use_container_width=True):
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO breathing_log (user_id,cycles,minutes,created_at) VALUES (?,?,?,?)",
                  (user_id,4,2,datetime.now().isoformat()))
        conn.commit(); conn.close()
        award_xp(user_id, 5); play_sound("success"); toast("🫁 +5 XP")
        st.rerun()

# ============================================================
# MOOD TRACKER
# ============================================================
def mood_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>😊 MOOD</h1><p>Track how you feel</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    with st.form("nm"):
        mo = st.selectbox("Mood", ["😊 Happy","😌 Calm","🤔 Thoughtful","😔 Sad","😤 Frustrated","😴 Tired","🔥 Motivated","😐 Neutral"])
        en = st.slider("Energy", 1, 10, 5)
        note = st.text_input("Note (optional)")
        if st.form_submit_button("💾 Log Mood", type="primary", use_container_width=True):
            conn = get_db(); c = conn.cursor()
            c.execute("INSERT INTO mood_log (user_id,mood,energy,note,created_at) VALUES (?,?,?,?,?)",
                      (user_id,mo,en,note,datetime.now().isoformat()))
            conn.commit(); conn.close()
            award_xp(user_id,3); play_sound("success"); st.rerun()
    st.divider()
    conn = get_db(); c = conn.cursor(); c.execute("SELECT * FROM mood_log WHERE user_id = ? ORDER BY created_at DESC LIMIT 30", (user_id,)); ms = c.fetchall(); conn.close()
    for m in ms:
        st.markdown(f'<div class="suggestion"><span class="icon">{m["mood"].split()[0]}</span><span class="text"><strong>{m["created_at"][:16]}</strong> — Energy {m["energy"]}/10 {m["note"] or ""}</span></div>', unsafe_allow_html=True)

# ============================================================
# ACHIEVEMENTS
# ============================================================
def achievements_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>🎖️ ACHIEVEMENTS</h1><p>Your badges</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT code FROM achievements WHERE user_id = ?", (user_id,))
    unlocked = {row["code"] for row in c.fetchall()}
    conn.close()
    for code, (name, desc, icon) in ACHIEVEMENTS.items():
        locked = code not in unlocked
        opacity = "0.4" if locked else "1"
        st.markdown(f'<div class="suggestion" style="opacity:{opacity};"><span class="icon">{icon}</span><span class="text"><strong>{name}</strong> — {desc}</span></div>', unsafe_allow_html=True)

# ============================================================
# STATS
# ============================================================
def stats_view():
    user_id = st.session_state.user_id
    render_mood_ring(user_id)
    st.markdown('<div class="nexus-header"><h1>📊 STATS</h1><p>Your full history</p></div>', unsafe_allow_html=True)
    back_button("home"); st.divider()
    conn = get_db(); c = conn.cursor()
    tables = ["places","memories","notes","journal","dreams","time_capsules","lessons","repairs",
              "health_guides","arena_matches","habits","mood_log","focus_sessions","gratitude",
              "wins_log","reading_list","quotes_saved","flash_cards","breathing_log","achievements"]
    for t in tables:
        try:
            c.execute(f"SELECT COUNT(*) as x FROM {t} WHERE user_id = ?", (user_id,))
            n = c.fetchone()["x"]
            st.metric(t.replace("_", " ").title(), n)
        except: pass
    c.execute("SELECT xp, streak, rank, arena_wins, arena_losses FROM users WHERE id = ?", (user_id,))
    u = c.fetchone()
    conn.close()
    if u:
        st.divider()
        st.markdown(f"**Rank:** {u['rank']} · **XP:** {u['xp']} · **Streak:** {u['streak']} · **Arena:** {u['arena_wins']}W / {u['arena_losses']}L")

# ============================================================
# TIME CAPSULE NOTE: reuse function names
# ============================================================
def save_photo_safely(user_id, photo_bytes):
    user_dir = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    ph = hashlib.sha256(photo_bytes).hexdigest()[:16]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fp = os.path.join(user_dir, f"{ts}_{ph}.jpg")
    with open(fp, "wb") as f: f.write(photo_bytes)
    return fp, ph

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
    elif v == "arena": arena_view()
    elif v == "habits": habits_view()
    elif v == "focus": focus_view()
    elif v == "gratitude": gratitude_view()
    elif v == "wins": wins_view()
    elif v == "reading": reading_view()
    elif v == "quotes": quotes_view()
    elif v == "flash": flash_view()
    elif v == "breathing": breathing_view()
    elif v == "mood": mood_view()
    elif v == "achievements": achievements_view()
    elif v == "stats": stats_view()
    else: home_view()
