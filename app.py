"""
NEXUS ULTIMATE v6 — family-friendly life OS
Run: streamlit run nexus.py
"""
import base64, hashlib, json, math, os, random, sqlite3, time
from contextlib import contextmanager
from datetime import datetime, timedelta

import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="NEXUS ULTIMATE", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")
DB_FILE = "nexus.db"
UPLOAD_DIR = "echo_vault"
os.makedirs(UPLOAD_DIR, exist_ok=True)

THEMES = {
    "cosmic": {"bg": "#0b1020", "card": "#151b2e", "ink": "#eef2ff", "muted": "#9aa6c3", "accent": "#7c5cff", "accent2": "#f093fb"},
    "forest": {"bg": "#0e1712", "card": "#16241c", "ink": "#e8f6ee", "muted": "#9bb5a6", "accent": "#3dd68c", "accent2": "#b6f36b"},
    "ocean": {"bg": "#07141c", "card": "#102433", "ink": "#e7f4ff", "muted": "#8eb4cc", "accent": "#3aa0ff", "accent2": "#67e8f9"},
    "sunrise": {"bg": "#1a120c", "card": "#2a1c14", "ink": "#fff6ec", "muted": "#d2b59a", "accent": "#ff8a3d", "accent2": "#ffd166"},
}

def css(theme):
    t = THEMES.get(theme, THEMES["cosmic"])
    st.markdown(f"""
    <style>
    .stApp {{ background: radial-gradient(1200px 600px at 10% -10%, {t['accent']}22, transparent), {t['bg']}; color: {t['ink']}; }}
    .block-container {{ padding-top: 1.2rem; }}
    .nx-hero {{ background: linear-gradient(135deg, {t['accent']}, {t['accent2']}); border-radius: 18px; padding: 22px 24px; color: white; margin-bottom: 14px; }}
    .nx-hero h1 {{ margin: 0; font-size: 1.8rem; }}
    .nx-card {{ background: {t['card']}; border: 1px solid #ffffff14; border-radius: 16px; padding: 14px 16px; margin-bottom: 10px; }}
    .nx-stat {{ background: {t['card']}; border-radius: 16px; padding: 14px; text-align: center; border: 1px solid #ffffff14; }}
    .nx-stat b {{ display: block; font-size: 1.5rem; }}
    .nx-muted {{ color: {t['muted']}; font-size: 0.9rem; }}
    .rank-badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; background: {t['accent']}33; }}
    .sq {{ width: 58px; height: 58px; display: inline-flex; align-items: center; justify-content: center; font-size: 34px; }}
    </style>
    """, unsafe_allow_html=True)

@contextmanager
def db():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

TABLES = {
    "users": "id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, name TEXT, xp INTEGER DEFAULT 0, streak INTEGER DEFAULT 0, last_active TEXT, rank TEXT DEFAULT 'Bronze', arena_wins INTEGER DEFAULT 0, arena_losses INTEGER DEFAULT 0, theme TEXT DEFAULT 'cosmic', created_at TEXT NOT NULL",
    "places": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT, created_at TEXT",
    "memories": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, place_id INTEGER, photo_path TEXT, ai_description TEXT, user_note TEXT, mood TEXT, created_at TEXT",
    "chats": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, created_at TEXT",
    "messages": "id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, role TEXT NOT NULL, content TEXT, created_at TEXT",
    "notes": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, content TEXT, created_at TEXT",
    "journal": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, content TEXT, mood TEXT, created_at TEXT",
    "lessons": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, topic TEXT, steps TEXT, created_at TEXT",
    "repairs": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, device TEXT, problem TEXT, steps TEXT, created_at TEXT",
    "dreams": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, content TEXT, interpretation TEXT, type TEXT, emotion TEXT, created_at TEXT",
    "capsules": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, message TEXT, unlock_date TEXT, opened INTEGER DEFAULT 0, created_at TEXT",
    "ach": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, code TEXT, name TEXT, icon TEXT, at TEXT",
    "matches": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, result TEXT, moves INTEGER, diff TEXT, created_at TEXT",
    "habits": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT, icon TEXT, streak INTEGER DEFAULT 0, last_done TEXT, created_at TEXT",
    "moods": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, mood TEXT, energy INTEGER, note TEXT, created_at TEXT",
    "focus": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, duration INTEGER, task TEXT, created_at TEXT",
    "gratitude": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, items TEXT, created_at TEXT",
    "wins": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, description TEXT, size TEXT, created_at TEXT",
    "reading": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, status TEXT, created_at TEXT",
    "quotes": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, quote TEXT, author TEXT, created_at TEXT",
    "flash": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, question TEXT, answer TEXT, created_at TEXT",
    "meditation": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, minutes INTEGER, note TEXT, created_at TEXT",
    "goals": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, objective TEXT, progress INTEGER DEFAULT 0, due_date TEXT, created_at TEXT",
    "challenges": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, cd TEXT, ct TEXT, completed INTEGER DEFAULT 0, created_at TEXT",
    "coach": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, role TEXT, content TEXT, created_at TEXT",
    "projects": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT, description TEXT, stage TEXT, created_at TEXT",
    "water": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, glasses INTEGER, created_at TEXT",
    "sleep": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, hours REAL, quality INTEGER, created_at TEXT",
    "workout": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, type TEXT, duration INTEGER, notes TEXT, created_at TEXT",
    "ttt": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, result TEXT, created_at TEXT",
    "wordle": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, word TEXT, guesses TEXT, won INTEGER DEFAULT 0, day TEXT, created_at TEXT",
    "tasks": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, priority TEXT, due TEXT, done INTEGER DEFAULT 0, created_at TEXT",
    "homework": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, subject TEXT, title TEXT, due TEXT, done INTEGER DEFAULT 0, created_at TEXT",
    "exams": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, subject TEXT, title TEXT, exam_date TEXT, notes TEXT, created_at TEXT",
    "vocab": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, word TEXT, meaning TEXT, example TEXT, box INTEGER DEFAULT 1, created_at TEXT",
    "kindness": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, act TEXT, created_at TEXT",
    "money": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, kind TEXT, amount REAL, note TEXT, created_at TEXT",
    "events": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, event_date TEXT, note TEXT, created_at TEXT",
    "grades": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, subject TEXT, title TEXT, score REAL, out_of REAL, created_at TEXT",
    "bookmarks": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, url TEXT, tag TEXT, created_at TEXT",
    "checks": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT, items TEXT, created_at TEXT",
    "typing": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, wpm INTEGER, accuracy INTEGER, created_at TEXT",
    "riddles_log": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, riddle TEXT, solved INTEGER DEFAULT 0, created_at TEXT",
}

def init_db():
    with db() as conn:
        for name, cols in TABLES.items():
            conn.execute(f"CREATE TABLE IF NOT EXISTS {name}({cols})")
        cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "theme" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'cosmic'")

init_db()

def hash_pw(password, salt=None):
    salt = salt or os.urandom(16).hex()
    digest = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}${digest}"

def check_pw(password, stored):
    if not stored or "$" not in stored:
        return hashlib.sha256(password.encode()).hexdigest() == stored
    salt, digest = stored.split("$", 1)
    return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest() == digest

def rank_of(xp):
    if xp >= 5000: return "Legend"
    if xp >= 2500: return "Diamond"
    if xp >= 1000: return "Platinum"
    if xp >= 500: return "Gold"
    if xp >= 150: return "Silver"
    return "Bronze"

def now():
    return datetime.now().isoformat(timespec="seconds")

def today():
    return datetime.now().date().isoformat()

def greet():
    h = datetime.now().hour
    if h < 5: return "Still up? Rest soon."
    if h < 12: return "Good morning"
    if h < 17: return "Good afternoon"
    if h < 21: return "Good evening"
    return "Good night"

ACH = {
    "first_login": ("First Step", "🌱"), "first_place": ("Cartographer", "📍"),
    "first_note": ("Thinker", "📝"), "first_journal": ("Reflector", "📖"),
    "first_dream": ("Dreamer", "🌙"), "first_capsule": ("Time Traveler", "⏳"),
    "first_lesson": ("Student", "🎓"), "first_chess": ("Gladiator", "♟️"),
    "chess5": ("Champion", "🏆"), "streak3": ("Consistent", "🔥"),
    "streak7": ("Committed", "💎"), "xp100": ("Apprentice", "🥉"),
    "xp500": ("Adept", "🥈"), "xp2000": ("Master", "🥇"),
    "first_task": ("Planner", "✅"), "first_hw": ("Scholar", "📚"),
    "first_kind": ("Kind Heart", "💛"), "first_grade": ("Scorekeeper", "📈"),
    "wordle_win": ("Wordsmith", "🔤"), "type40": ("Swift Fingers", "⌨️"),
}

def award_xp(uid, amt):
    with db() as conn:
        conn.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (amt, uid))
        xp = conn.execute("SELECT xp FROM users WHERE id = ?", (uid,)).fetchone()["xp"]
        conn.execute("UPDATE users SET rank = ? WHERE id = ?", (rank_of(xp), uid))
    check_ach(uid)

def upd_streak(uid):
    with db() as conn:
        u = conn.execute("SELECT streak, last_active FROM users WHERE id = ?", (uid,)).fetchone()
        if not u:
            return
        t = today()
        if u["last_active"] == t:
            return
        y = (datetime.now() - timedelta(days=1)).date().isoformat()
        streak = (u["streak"] or 0) + 1 if u["last_active"] == y else 1
        conn.execute("UPDATE users SET streak = ?, last_active = ? WHERE id = ?", (streak, t, uid))

def check_ach(uid):
    with db() as conn:
        have = {r["code"] for r in conn.execute("SELECT code FROM ach WHERE user_id = ?", (uid,))}
        checks = {"first_login": True}
        pairs = [
            ("first_place", "places"), ("first_note", "notes"), ("first_journal", "journal"),
            ("first_dream", "dreams"), ("first_capsule", "capsules"), ("first_lesson", "lessons"),
            ("first_task", "tasks"), ("first_hw", "homework"), ("first_kind", "kindness"),
            ("first_grade", "grades"),
        ]
        for code, table in pairs:
            checks[code] = conn.execute(f"SELECT COUNT(*) AS x FROM {table} WHERE user_id = ?", (uid,)).fetchone()["x"] >= 1
        wins = conn.execute("SELECT COUNT(*) AS x FROM matches WHERE user_id = ? AND result = 'win'", (uid,)).fetchone()["x"]
        checks["first_chess"] = wins >= 1
        checks["chess5"] = wins >= 5
        checks["wordle_win"] = conn.execute("SELECT COUNT(*) AS x FROM wordle WHERE user_id = ? AND won = 1", (uid,)).fetchone()["x"] >= 1
        checks["type40"] = conn.execute("SELECT COUNT(*) AS x FROM typing WHERE user_id = ? AND wpm >= 40", (uid,)).fetchone()["x"] >= 1
        row = conn.execute("SELECT streak, xp FROM users WHERE id = ?", (uid,)).fetchone()
        checks["streak3"] = row["streak"] >= 3
        checks["streak7"] = row["streak"] >= 7
        checks["xp100"] = row["xp"] >= 100
        checks["xp500"] = row["xp"] >= 500
        checks["xp2000"] = row["xp"] >= 2000
        for code, ok in checks.items():
            if ok and code not in have:
                name, icon = ACH[code]
                conn.execute("INSERT INTO ach(user_id, code, name, icon, at) VALUES(?,?,?,?,?)", (uid, code, name, icon, now()))
                st.toast(f"{icon} {name}")

FALLBACKS = [
    "Small steps still count. Pick one thing and finish it.",
    "Curiosity is a skill. Ask one better question today.",
    "Rest is part of the work, not a break from it.",
    "Kindness is a habit you can practice on purpose.",
    "Write it down so tomorrow-you does not have to remember.",
]

def ai_chat(msgs, temp=0.7, timeout=25):
    try:
        r = requests.post(
            "https://text.pollinations.ai/openai",
            json={"model": "openai", "messages": msgs, "temperature": temp, "max_tokens": 700},
            timeout=timeout,
        )
        if r.status_code == 200:
            data = r.json()
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if text and len(text.strip()) > 2:
                return text.strip()
    except Exception:
        pass
    last = ""
    for m in msgs:
        if m.get("role") == "user":
            last = m.get("content", "")
    return local_reply(last)

def local_reply(prompt):
    p = (prompt or "").lower()
    if "lesson" in p or "learn" in p:
        return json.dumps({
            "title": "A clear mini-lesson",
            "intro": "Break the topic into a few small moves you can practice today.",
            "steps": [
                {"n": 1, "title": "Name it", "instruction": "Write the topic in one sentence."},
                {"n": 2, "title": "Example", "instruction": "Find one simple example."},
                {"n": 3, "title": "Try", "instruction": "Do one practice question without notes."},
                {"n": 4, "title": "Check", "instruction": "Compare with a trusted source or a teacher."},
                {"n": 5, "title": "Teach", "instruction": "Explain it out loud in under a minute."},
            ],
        })
    if "repair" in p or "fix" in p:
        return json.dumps({
            "title": "Safe check first",
            "safety": "Unplug devices. Ask an adult before opening anything electrical.",
            "tools": ["flashlight", "soft cloth"],
            "steps": [
                {"n": 1, "title": "Stop and look", "instruction": "Note what changed right before the problem."},
                {"n": 2, "title": "Simple reset", "instruction": "Restart the device after it is safe to do so."},
                {"n": 3, "title": "Connections", "instruction": "Check cables, power, and obvious switches."},
                {"n": 4, "title": "Ask", "instruction": "Show an adult if it still fails."},
            ],
        })
    if "weekly" in p:
        return "You showed up this week. Keep the streak by doing one small log tomorrow, and pick a single study block instead of trying to do everything."
    if "decision" in p or "options" in p:
        return "List what matters most, cross out anything unsafe or rushed, then pick the option you can explain to a parent. Sleep on it if it is not urgent."
    if "email" in p:
        return "Subject: A quick note\n\nHello,\n\nI wanted to share a clear update and ask for the next step. Thank you for your time.\n\nBest regards"
    if "bullet" in p or "resume" in p:
        return "• Organized a school project and finished each task on time.\n• Practiced a skill every week and tracked progress.\n• Helped teammates by explaining steps clearly."
    if "habit" in p:
        return "1. Pack tomorrow's bag tonight.\n2. Read 10 minutes after homework.\n3. Drink a glass of water when you sit down to study."
    return random.choice(FALLBACKS)

def ai_json(prompt):
    raw = ai_chat([{"role": "user", "content": prompt + " Reply with JSON only."}])
    try:
        start, end = raw.find("{"), raw.rfind("}")
        if start != -1 and end != -1:
            return json.loads(raw[start:end + 1])
    except Exception:
        return None
    return None

# ----- chess -----
UNI = {"K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙", "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"}

def start_board():
    return [
        list("rnbqkbnr"),
        list("pppppppp"),
        list("........"),
        list("........"),
        list("........"),
        list("........"),
        list("PPPPPPPP"),
        list("RNBQKBNR"),
    ]

def on_board(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def same_side(a, b):
    return a != "." and b != "." and a.isupper() == b.isupper()

def clone(board):
    return [row[:] for row in board]

def find_king(board, white):
    target = "K" if white else "k"
    for r in range(8):
        for c in range(8):
            if board[r][c] == target:
                return r, c
    return None

def pseudo(board, r, c, state):
    piece = board[r][c]
    if piece == ".":
        return []
    white = piece.isupper()
    kind = piece.upper()
    moves = []
    if kind == "P":
        direction = -1 if white else 1
        start = 6 if white else 1
        promo = 0 if white else 7
        nr = r + direction
        if on_board(nr, c) and board[nr][c] == ".":
            moves.append((nr, c, "promo" if nr == promo else ""))
            if r == start and board[r + 2 * direction][c] == ".":
                moves.append((r + 2 * direction, c, "double"))
        for dc in (-1, 1):
            nr, nc = r + direction, c + dc
            if not on_board(nr, nc):
                continue
            if board[nr][nc] != "." and not same_side(piece, board[nr][nc]):
                moves.append((nr, nc, "promo_cap" if nr == promo else "cap"))
            if state.get("ep") == (nr, nc):
                moves.append((nr, nc, "ep"))
    elif kind == "N":
        for dr, dc in ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)):
            nr, nc = r + dr, c + dc
            if on_board(nr, nc) and not same_side(piece, board[nr][nc]):
                moves.append((nr, nc, "cap" if board[nr][nc] != "." else ""))
    elif kind in ("B", "R", "Q"):
        dirs = {"B": ((-1, -1), (-1, 1), (1, -1), (1, 1)), "R": ((-1, 0), (1, 0), (0, -1), (0, 1)),
                "Q": ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))}[kind]
        for dr, dc in dirs:
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if not on_board(nr, nc):
                    break
                if board[nr][nc] == ".":
                    moves.append((nr, nc, ""))
                else:
                    if not same_side(piece, board[nr][nc]):
                        moves.append((nr, nc, "cap"))
                    break
    elif kind == "K":
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if on_board(nr, nc) and not same_side(piece, board[nr][nc]):
                    moves.append((nr, nc, "cap" if board[nr][nc] != "." else ""))
        castle = state.get("castling", {}
