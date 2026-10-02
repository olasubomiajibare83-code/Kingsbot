"""
NEXUS ULTIMATE v6.1
Run: streamlit run app.py
"""
import hashlib, json, math, os, random, sqlite3, time
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
    "cosmic": ("#0b1020", "#151b2e", "#eef2ff", "#9aa6c3", "#7c5cff", "#f093fb"),
    "forest": ("#0e1712", "#16241c", "#e8f6ee", "#9bb5a6", "#3dd68c", "#b6f36b"),
    "ocean": ("#07141c", "#102433", "#e7f4ff", "#8eb4cc", "#3aa0ff", "#67e8f9"),
    "sunrise": ("#1a120c", "#2a1c14", "#fff6ec", "#d2b59a", "#ff8a3d", "#ffd166"),
}

def apply_css(theme):
    bg, card, ink, muted, accent, accent2 = THEMES.get(theme, THEMES["cosmic"])
    st.markdown(
        "<style>"
        f".stApp {{background:radial-gradient(1000px 500px at 8% -10%, {accent}22, transparent), {bg}; color:{ink};}}"
        ".block-container {padding-top:1.1rem;}"
        f".nx-hero {{background:linear-gradient(135deg,{accent},{accent2}); border-radius:18px; padding:20px 22px; color:white; margin-bottom:12px;}}"
        ".nx-hero h1 {margin:0; font-size:1.7rem;}"
        f".nx-card {{background:{card}; border:1px solid #ffffff14; border-radius:16px; padding:14px 16px; margin-bottom:10px;}}"
        f".nx-stat {{background:{card}; border-radius:16px; padding:12px; text-align:center; border:1px solid #ffffff14;}}"
        ".nx-stat b {display:block; font-size:1.45rem;}"
        f".nx-muted {{color:{muted};}}"
        f".rank-badge {{display:inline-block; padding:2px 8px; border-radius:999px; background:{accent}33;}}"
        "</style>",
        unsafe_allow_html=True,
    )

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
    "health": "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, symptoms TEXT, guide TEXT, created_at TEXT",
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
            conn.execute("CREATE TABLE IF NOT EXISTS " + name + "(" + cols + ")")
        have = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
        if "theme" not in have:
            conn.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'cosmic'")

init_db()

def hash_pw(password, salt=None):
    salt = salt or os.urandom(16).hex()
    digest = hashlib.sha256((salt + ":" + password).encode()).hexdigest()
    return salt + "$" + digest

def check_pw(password, stored):
    if not stored:
        return False
    if "$" not in stored:
        return hashlib.sha256(password.encode()).hexdigest() == stored
    salt, digest = stored.split("$", 1)
    return hashlib.sha256((salt + ":" + password).encode()).hexdigest() == digest

def rank_of(xp):
    if xp >= 5000:
        return "Legend"
    if xp >= 2500:
        return "Diamond"
    if xp >= 1000:
        return "Platinum"
    if xp >= 500:
        return "Gold"
    if xp >= 150:
        return "Silver"
    return "Bronze"

def now():
    return datetime.now().isoformat(timespec="seconds")

def today():
    return datetime.now().date().isoformat()

def greet():
    hour = datetime.now().hour
    if hour < 5:
        return "Still up? Rest soon."
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    if hour < 21:
        return "Good evening"
    return "Good night"

ACH = {
    "first_login": ("First Step", "🌱"),
    "first_place": ("Cartographer", "📍"),
    "first_note": ("Thinker", "📝"),
    "first_journal": ("Reflector", "📖"),
    "first_dream": ("Dreamer", "🌙"),
    "first_capsule": ("Time Traveler", "⏳"),
    "first_lesson": ("Student", "🎓"),
    "first_repair": ("Fixer", "🔧"),
    "first_health": ("Guardian", "💚"),
    "first_chess": ("Gladiator", "♟️"),
    "chess5": ("Champion", "🏆"),
    "streak3": ("Consistent", "🔥"),
    "streak7": ("Committed", "💎"),
    "xp100": ("Apprentice", "🥉"),
    "xp500": ("Adept", "🥈"),
    "xp2000": ("Master", "🥇"),
    "first_grat": ("Grateful", "🙏"),
    "first_win": ("Winner", "🏆"),
    "first_card": ("Learner", "🃏"),
    "first_medit": ("Zen", "🧘"),
    "challenge1": ("Challenger", "📅"),
    "coach": ("Coached", "🤖"),
    "first_water": ("Hydrated", "💧"),
    "first_sleep": ("Rested", "😴"),
    "wordle_win": ("Wordsmith", "🔤"),
    "first_task": ("Planner", "✅"),
    "first_hw": ("Scholar", "📚"),
    "first_kind": ("Kind Heart", "💛"),
    "type40": ("Swift Fingers", "⌨️"),
}

def award_xp(uid, amt):
    with db() as conn:
        conn.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (amt, uid))
        xp = conn.execute("SELECT xp FROM users WHERE id = ?", (uid,)).fetchone()["xp"]
        conn.execute("UPDATE users SET rank = ? WHERE id = ?", (rank_of(xp), uid))
    check_ach(uid)

def upd_streak(uid):
    with db() as conn:
        user = conn.execute("SELECT streak, last_active FROM users WHERE id = ?", (uid,)).fetchone()
        if not user or user["last_active"] == today():
            return
        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
        streak = (user["streak"] or 0) + 1 if user["last_active"] == yesterday else 1
        conn.execute("UPDATE users SET streak = ?, last_active = ? WHERE id = ?", (streak, today(), uid))

def check_ach(uid):
    with db() as conn:
        have = {row["code"] for row in conn.execute("SELECT code FROM ach WHERE user_id = ?", (uid,))}
        checks = {"first_login": True}
        pairs = [
            ("first_place", "places"), ("first_note", "notes"), ("first_journal", "journal"),
            ("first_dream", "dreams"), ("first_capsule", "capsules"), ("first_lesson", "lessons"),
            ("first_repair", "repairs"), ("first_health", "health"), ("first_grat", "gratitude"),
            ("first_win", "wins"), ("first_card", "flash"), ("first_medit", "meditation"),
            ("first_water", "water"), ("first_sleep", "sleep"), ("first_task", "tasks"),
            ("first_hw", "homework"), ("first_kind", "kindness"),
        ]
        for code, table in pairs:
            checks[code] = conn.execute("SELECT COUNT(*) AS x FROM " + table + " WHERE user_id = ?", (uid,)).fetchone()["x"] >= 1
        wins = conn.execute("SELECT COUNT(*) AS x FROM matches WHERE user_id = ? AND result = 'win'", (uid,)).fetchone()["x"]
        checks["first_chess"] = wins >= 1
        checks["chess5"] = wins >= 5
        checks["challenge1"] = conn.execute("SELECT COUNT(*) AS x FROM challenges WHERE user_id = ? AND completed = 1", (uid,)).fetchone()["x"] >= 1
        checks["coach"] = conn.execute("SELECT COUNT(*) AS x FROM coach WHERE user_id = ?", (uid,)).fetchone()["x"] >= 1
        checks["wordle_win"] = conn.execute("SELECT COUNT(*) AS x FROM wordle WHERE user_id = ? AND won = 1", (uid,)).fetchone()["x"] >= 1
        checks["type40"] = conn.execute("SELECT COUNT(*) AS x FROM typing WHERE user_id = ? AND wpm >= 40", (uid,)).fetchone()["x"] >= 1
        row = conn.execute("SELECT streak, xp FROM users WHERE id = ?", (uid,)).fetchone()
        checks["streak3"] = row["streak"] >= 3
        checks["streak7"] = row["streak"] >= 7
        checks["xp100"] = row["xp"] >= 100
        checks["xp500"] = row["xp"] >= 500
        checks["xp2000"] = row["xp"] >= 2000
        for code, ok in checks.items():
            if ok and code not in have and code in ACH:
                name, icon = ACH[code]
                conn.execute("INSERT INTO ach(user_id, code, name, icon, at) VALUES(?,?,?,?,?)", (uid, code, name, icon, now()))
                st.toast(icon + " " + name)

FALLBACKS = [
    "Small steps still count. Pick one thing and finish it.",
    "Curiosity is a skill. Ask one better question today.",
    "Rest is part of the work, not a break from it.",
    "Kindness is a habit you can practice on purpose.",
]

def ai_chat(msgs, temp=0.7, timeout=25):
    try:
        response = requests.post(
            "https://text.pollinations.ai/openai",
            json={"model": "openai", "messages": msgs, "temperature": temp, "max_tokens": 700},
            timeout=timeout,
        )
        if response.status_code == 200:
            text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            if text and len(text.strip()) > 2:
                return text.strip()
    except Exception:
        pass
    last = ""
    for msg in msgs:
        if msg.get("role") == "user":
            last = msg.get("content", "")
    return local_reply(last)

def local_reply(prompt):
    text = (prompt or "").lower()
    if "lesson" in text:
        return json.dumps({
            "title": "A clear mini-lesson",
            "intro": "Break the topic into a few moves you can practice today.",
            "steps": [
                {"n": 1, "title": "Name it", "instruction": "Write the topic in one sentence."},
                {"n": 2, "title": "Example", "instruction": "Find one simple example."},
                {"n": 3, "title": "Try", "instruction": "Do one practice question without notes."},
                {"n": 4, "title": "Check", "instruction": "Compare with a trusted source or a teacher."},
                {"n": 5, "title": "Teach", "instruction": "Explain it out loud in under a minute."},
            ],
        })
    if "repair" in text or "fix" in text:
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
    if "symptom" in text or "feel unwell" in text or "wellness" in text:
        return json.dumps({
            "title": "Tell a parent",
            "seriousness": "This is not a diagnosis.",
            "causes": ["Many everyday things can cause this. Only a doctor can say why."],
            "home_care": ["Rest, drink water, and tell a parent or guardian how you feel."],
            "warning_signs": ["Pain that gets worse, trouble breathing, fainting, or a rash. Tell an adult now."],
            "see_doctor": "Ask a parent to contact a doctor if it lasts or worries you.",
            "safety": "Not a doctor. Do not take medicine unless a parent or doctor says so.",
        })
    if "dream" in text:
        return json.dumps({
            "type": "Reflection",
            "emotion": "mixed",
            "symbols": ["memory", "feeling"],
            "meaning": "Dreams can echo a busy day. They are not predictions.",
            "message": "You can write it down and let it go.",
            "action": "Notice one calm thing today.",
        })
    if "weekly" in text:
        return "You showed up this week. Keep one small log tomorrow, and pick a single study block instead of trying to do everything."
    if "decision" in text or "options" in text:
        return "List what matters most, cross out anything unsafe or rushed, then pick the option you can explain to a parent."
    if "email" in text or "note to" in text:
        return "Subject: A quick note\n\nHello,\n\nI wanted to share a clear update and ask for the next step. Thank you for your time.\n\nBest regards"
    if "bullet" in text or "resume" in text:
        return "- Organized a school project and finished each task on time.\n- Practiced a skill every week and tracked progress.\n- Helped teammates by explaining steps clearly."
    if "habit" in text:
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

def celebrate():
    components.html("<script>console.log('nexus-win')</script>", height=0)

UNI = {"K": "♔", "Q": "♕", "R": "♖", "B": "♗", "N": "♘", "P": "♙", "k": "♚", "q": "♛", "r": "♜", "b": "♝", "n": "♞", "p": "♟"}

def start_board():
    return [list("rnbqkbnr"), list("pppppppp"), list("........"), list("........"), list("........"), list("........"), list("PPPPPPPP"), list("RNBQKBNR")]

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
    castle = state.get("castling") or {}
    if kind == "P":
        direction = -1 if white else 1
        start_row = 6 if white else 1
        promo_row = 0 if white else 7
        nr = r + direction
        if on_board(nr, c) and board[nr][c] == ".":
            moves.append((nr, c, "promo" if nr == promo_row else ""))
            jump = r + 2 * direction
            if r == start_row and board[jump][c] == ".":
                moves.append((jump, c, "double"))
        for dc in (-1, 1):
            nr, nc = r + direction, c + dc
            if not on_board(nr, nc):
                continue
            if board[nr][nc] != "." and not same_side(piece, board[nr][nc]):
                moves.append((nr, nc, "promo_cap" if nr == promo_row else "cap"))
            if state.get("ep") == (nr, nc):
                moves.append((nr, nc, "ep"))
    elif kind == "N":
        for dr, dc in ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)):
            nr, nc = r + dr, c + dc
            if on_board(nr, nc) and not same_side(piece, board[nr][nc]):
                moves.append((nr, nc, "cap" if board[nr][nc] != "." else ""))
    elif kind in ("B", "R", "Q"):
        dirs = {
            "B": ((-1, -1), (-1, 1), (1, -1), (1, 1)),
            "R": ((-1, 0), (1, 0), (0, -1), (0, 1)),
            "Q": ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)),
        }[kind]
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
                    tag = "cap" if board[nr][nc] != "." else ""
                    moves.append((nr, nc, tag))
        if white and castle.get("K") and board[7][5] == "." and board[7][6] == "." and board[7][7] == "R":
            moves.append((7, 6, "ck"))
        if white and castle.get("Q") and board[7][1] == "." and board[7][2] == "." and board[7][3] == "." and board[7][0] == "R":
            moves.append((7, 2, "cq"))
        if (not white) and castle.get("k") and board[0][5] == "." and board[0][6] == "." and board[0][7] == "r":
            moves.append((0, 6, "ck"))
        if (not white) and castle.get("q") and board[0][1] == "." and board[0][2] == "." and board[0][3] == "." and board[0][0] == "r":
            moves.append((0, 2, "cq"))
    return moves

def apply_move(board, state, fr, fc, tr, tc, special):
    nb = clone(board)
    ns = {"castling": dict(state.get("castling") or {"K": True, "Q": True, "k": True, "q": True}), "ep": None}
    piece = nb[fr][fc]
    white = piece.isupper()
    if special == "ep":
        nb[fr][tc] = "."
    nb[tr][tc] = piece
    nb[fr][fc] = "."
    if special == "double":
        ns["ep"] = ((fr + tr) // 2, fc)
    if special in ("promo", "promo_cap"):
        nb[tr][tc] = "Q" if white else "q"
    if special == "ck":
        nb[tr][5] = nb[tr][7]
        nb[tr][7] = "."
    if special == "cq":
        nb[tr][3] = nb[tr][0]
        nb[tr][0] = "."
    if piece == "K":
        ns["castling"]["K"] = False
        ns["castling"]["Q"] = False
    if piece == "k":
        ns["castling"]["k"] = False
        ns["castling"]["q"] = False
    if piece == "R" and (fr, fc) == (7, 0):
        ns["castling"]["Q"] = False
    if piece == "R" and (fr, fc) == (7, 7):
        ns["castling"]["K"] = False
    if piece == "r" and (fr, fc) == (0, 0):
        ns["castling"]["q"] = False
    if piece == "r" and (fr, fc) == (0, 7):
        ns["castling"]["k"] = False
    return nb, ns

def attacked(board, r, c, by_white):
    pawn = "P" if by_white else "p"
    step = 1 if by_white else -1
    for dc in (-1, 1):
        if on_board(r + step, c + dc) and board[r + step][c + dc] == pawn:
            return True
    knight = "N" if by_white else "n"
    for dr, dc in ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)):
        if on_board(r + dr, c + dc) and board[r + dr][c + dc] == knight:
            return True
    king = "K" if by_white else "k"
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if (dr or dc) and on_board(r + dr, c + dc) and board[r + dr][c + dc] == king:
                return True
    rays = [((-1, 0), (1, 0), (0, -1), (0, 1)), ((-1, -1), (-1, 1), (1, -1), (1, 1))]
    sliding = [("RQ", "rq"), ("BQ", "bq")]
    for group, pair in zip(rays, sliding):
        white_set, black_set = pair
        for dr, dc in group:
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if not on_board(nr, nc):
                    break
                p = board[nr][nc]
                if p == ".":
                    continue
                if by_white and p in white_set:
                    return True
                if (not by_white) and p in black_set:
                    return True
                break
    return False

def in_check(board, white):
    king = find_king(board, white)
    return bool(king and attacked(board, king[0], king[1], not white))

def legal_moves(board, state, white):
    out = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == "." or piece.isupper() != white:
                continue
            for tr, tc, special in pseudo(board, r, c, state):
                if special in ("ck", "cq"):
                    if in_check(board, white):
                        continue
                    row = 7 if white else 0
                    mids = [(row, 5), (row, 6)] if special == "ck" else [(row, 3), (row, 2)]
                    if any(attacked(board, mr, mc, not white) for mr, mc in mids):
                        continue
                nb, ns = apply_move(board, state, r, c, tr, tc, special)
                if not in_check(nb, white):
                    out.append((r, c, tr, tc, special))
    return out

def sq_name(r, c):
    return chr(ord("a") + c) + str(8 - r)

def piece_value(p):
    return {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000, "p": -100, "n": -320, "b": -330, "r": -500, "q": -900, "k": -20000}.get(p, 0)

def evaluate(board):
    score = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p == ".":
                continue
            value = piece_value(p)
            if 2 <= r <= 5 and 2 <= c <= 5:
                value += 12 if p.isupper() else -12
            score += value
    return score

def minimax(board, state, depth, alpha, beta, white):
    if depth == 0:
        return evaluate(board), None
    moves = legal_moves(board, state, white)
    if not moves:
        if in_check(board, white):
            return (-100000 - depth if white else 100000 + depth), None
        return 0, None
    moves.sort(key=lambda m: abs(piece_value(board[m[2]][m[3]])), reverse=True)
    best = None
    if white:
        value = -math.inf
        for move in moves:
            nb, ns = apply_move(board, state, *move)
            score, _ = minimax(nb, ns, depth - 1, alpha, beta, False)
            if score > value:
                value, best = score, move
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value, best
    value = math.inf
    for move in moves:
        nb, ns = apply_move(board, state, *move)
        score, _ = minimax(nb, ns, depth - 1, alpha, beta, True)
        if score < value:
            value, best = score, move
        beta = min(beta, value)
        if beta <= alpha:
            break
    return value, best

def ai_move(board, state, diff):
    depth = {"easy": 1, "medium": 2, "hard": 3}.get(diff, 2)
    moves = legal_moves(board, state, False)
    if not moves:
        return None
    if diff == "easy" and random.random() < 0.45:
        return random.choice(moves)
    _, best = minimax(board, state, depth, -math.inf, math.inf, False)
    return best or random.choice(moves)

def san(board, move):
    fr, fc, tr, tc, special = move
    piece = board[fr][fc]
    if special == "ck":
        return "O-O"
    if special == "cq":
        return "O-O-O"
    text = "" if piece.upper() == "P" else piece.upper()
    if board[tr][tc] != "." or special == "ep":
        if piece.upper() == "P":
            text += chr(ord("a") + fc)
        text += "x"
    text += sq_name(tr, tc)
    if special in ("promo", "promo_cap"):
        text += "=Q"
    return text

def new_chess(diff="medium"):
    return {
        "board": start_board(),
        "state": {"castling": {"K": True, "Q": True, "k": True, "q": True}, "ep": None},
        "turn": "white", "history": [], "capw": [], "capb": [],
        "diff": diff, "last": None, "status": "playing", "msg": "",
    }

def board_html(game):
    board, last = game["board"], game["last"]
    check = find_king(board, True) if in_check(board, True) else None
    html = "<div style='line-height:0'>"
    for r in range(8):
        html += "<div>"
        for c in range(8):
            bg = "#f0d9b5" if (r + c) % 2 == 0 else "#b58863"
            border = ""
            if last and (r, c) in ((last[0], last[1]), (last[2], last[3])):
                border = "box-shadow:inset 0 0 0 3px #7c5cff;"
            if check == (r, c):
                border = "box-shadow:inset 0 0 0 4px #ff5a5a;"
            glyph = UNI.get(board[r][c], "")
            color = "#fff" if board[r][c].isupper() else "#111"
            html += "<span style='width:56px;height:56px;display:inline-flex;align-items:center;justify-content:center;font-size:32px;background:" + bg + ";" + border + "color:" + color + "'>" + glyph + "</span>"
        html += "</div>"
    return html + "</div>"

DEFAULTS = {
    "user_id": None, "name": None, "view": "home", "history": [], "theme": "cosmic",
    "place": None, "chat": None, "lesson": None, "repair": None, "health": None,
    "chess": None, "ttt": None, "mem": None, "focus_end": None, "focus_task": "",
    "focus_min": 25, "quote": None, "riddle": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

def go(view):
    if st.session_state.view != view:
        st.session_state.history.append(st.session_state.view)
        st.session_state.history = st.session_state.history[-30:]
    st.session_state.view = view
    st.rerun()

def back():
    if st.session_state.history:
        st.session_state.view = st.session_state.history.pop()
        st.rerun()

NAV = [
    ("home", "🏠", "Home"), ("chess", "♟️", "Chess"), ("chat", "💬", "Chat"),
    ("echo", "📸", "Echo"), ("tutor", "🎓", "Tutor"), ("atlas", "🔧", "ATLAS"),
    ("notes", "📝", "Notes"), ("journal", "📖", "Journal"), ("dreams", "🌙", "Dreams"),
    ("capsule", "⏳", "Capsule"), ("habits", "✅", "Habits"), ("focus", "🎯", "Focus"),
    ("mood", "😊", "Mood"), ("gratitude", "🙏", "Gratitude"), ("wins", "🏆", "Wins"),
    ("reading", "📚", "Reading"), ("quotes", "💬", "Quotes"), ("flash", "🃏", "Flash"),
    ("breathe", "🫁", "Breathe"), ("meditate", "🧘", "Meditate"), ("water", "💧", "Water"),
    ("sleep", "😴", "Sleep"), ("workout", "🏃", "Workout"), ("goals", "🎯", "Goals"),
    ("coach", "🤖", "AI Coach"), ("challenge", "📅", "Challenge"), ("studio", "🏗️", "Studio"),
    ("games", "🎮", "Games"), ("search", "🔍", "Search"), ("weekly", "📊", "Weekly"),
    ("decide", "🎲", "Decide"), ("email", "💌", "Email"), ("resume", "📄", "Resume"),
    ("habitsuggest", "🌱", "Habit Ideas"), ("leaderboard", "🏆", "Leaderboard"),
    ("achievements", "🎖️", "Awards"), ("stats", "📊", "Stats"), ("settings", "⚙️", "Settings"),
    ("tasks", "✅", "Tasks"), ("homework", "📚", "Homework"), ("exams", "🗓️", "Exams"),
    ("grades", "📈", "Grades"), ("vocab", "🔤", "Vocab"), ("kindness", "💛", "Kindness"),
    ("money", "🪙", "Allowance"), ("events", "📌", "Events"), ("bookmarks", "🔖", "Bookmarks"),
    ("checks", "☑️", "Checklists"), ("riddle", "❓", "Riddle"), ("typing", "⌨️", "Typing"),
    ("spark", "✨", "Spark"),
]

def page_head(icon, title, sub=""):
    st.markdown("<div class='nx-hero'><h1>" + icon + " " + title + "</h1><div>" + sub + "</div></div>", unsafe_allow_html=True)

def auth():
    page_head("🧠", "NEXUS ULTIMATE", "Study, habits, chess, and a private journal")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        login, signup = st.tabs(["Login", "Sign up"])
        with login:
            with st.form("login"):
                user = st.text_input("Username or email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login", use_container_width=True):
                    with db() as conn:
                        row = conn.execute("SELECT * FROM users WHERE username = ? OR email = ?", (user, user)).fetchone()
                    if row and check_pw(password, row["password_hash"]):
                        st.session_state.user_id = row["id"]
                        st.session_state.name = row["name"] or row["username"]
                        st.session_state.theme = row["theme"] or "cosmic"
                        upd_streak(row["id"])
                        check_ach(row["id"])
                        st.rerun()
                    st.error("Those details do not match.")
        with signup:
            with st.form("signup"):
                name = st.text_input("Name")
                user = st.text_input("Username")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                confirm = st.text_input("Confirm password", type="password")
                if st.form_submit_button("Create account", use_container_width=True):
                    if not user or not email or not password:
                        st.error("Fill in username, email, and password.")
                    elif password != confirm:
                        st.error("Passwords do not match.")
                    elif len(password) < 6:
                        st.error("Use at least 6 characters.")
                    else:
                        try:
                            with db() as conn:
                                conn.execute(
                                    "INSERT INTO users(username, email, password_hash, name, streak, last_active, created_at) VALUES(?,?,?,?,1,?,?)",
                                    (user, email, hash_pw(password), name, today(), now()),
                                )
                            st.success("Account created. Log in.")
                        except sqlite3.IntegrityError:
                            st.error("That username or email is taken.")

def sidebar():
    uid = st.session_state.user_id
    with st.sidebar:
        st.markdown("### " + st.session_state.name)
        with db() as conn:
            user = conn.execute("SELECT xp, rank, streak FROM users WHERE id = ?", (uid,)).fetchone()
        st.markdown("<span class='rank-badge'>" + user["rank"] + " · " + str(user["xp"]) + " XP · 🔥 " + str(user["streak"]) + "</span>", unsafe_allow_html=True)
        if st.session_state.history and st.button("Back", use_container_width=True):
            back()
        query = st.text_input("Find a room", key="navq")
        for vid, icon, label in NAV:
            if query and query.lower() not in label.lower():
                continue
            mark = "● " if st.session_state.view == vid else ""
            if st.button(mark + icon + " " + label, key="nav_" + vid, use_container_width=True):
                go(vid)
        if st.button("Log out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def home():
    uid = st.session_state.user_id
    with db() as conn:
        user = conn.execute("SELECT xp, streak, rank, arena_wins FROM users WHERE id = ?", (uid,)).fetchone()
        awards = conn.execute("SELECT COUNT(*) AS x FROM ach WHERE user_id = ?", (uid,)).fetchone()["x"]
        open_tasks = conn.execute("SELECT COUNT(*) AS x FROM tasks WHERE user_id = ? AND done = 0", (uid,)).fetchone()["x"]
    page_head("🧠", "NEXUS ULTIMATE", greet() + ", " + st.session_state.name)
    a, b, c, d = st.columns(4)
    a.markdown("<div class='nx-stat'><b>" + str(user["xp"]) + "</b>XP</div>", unsafe_allow_html=True)
    b.markdown("<div class='nx-stat'><b>🔥 " + str(user["streak"]) + "</b>Streak</div>", unsafe_allow_html=True)
    c.markdown("<div class='nx-stat'><b>" + str(awards) + "</b>Awards</div>", unsafe_allow_html=True)
    d.markdown("<div class='nx-stat'><b>" + str(user["arena_wins"]) + "</b>Chess wins</div>", unsafe_allow_html=True)
    if not st.session_state.quote:
        st.session_state.quote = random.choice(FALLBACKS)
    st.markdown("<div class='nx-card'><div class='nx-muted'>Today's whisper</div><b>" + st.session_state.quote + "</b></div>", unsafe_allow_html=True)
    st.caption(user["rank"] + " · " + str(open_tasks) + " open tasks")
    rooms = [("chess", "Chess"), ("echo", "Echo"), ("tasks", "Tasks"), ("homework", "Homework"), ("journal", "Journal"), ("games", "Games"), ("coach", "Coach"), ("challenge", "Challenge")]
    cols = st.columns(4)
    for i, (vid, label) in enumerate(rooms):
        if cols[i % 4].button(label, key="home_" + vid, use_container_width=True):
            go(vid)

def finish_chess(uid, result):
    game = st.session_state.chess
    with db() as conn:
        conn.execute("INSERT INTO matches(user_id, result, moves, diff, created_at) VALUES(?,?,?,?,?)", (uid, result, len(game["history"]), game["diff"], now()))
        if result == "win":
            conn.execute("UPDATE users SET arena_wins = arena_wins + 1 WHERE id = ?", (uid,))
        else:
            conn.execute("UPDATE users SET arena_losses = arena_losses + 1 WHERE id = ?", (uid,))
    if result == "win":
        award_xp(uid, 40)
        celebrate()
    else:
        award_xp(uid, 8)
    st.session_state.chess = None
    st.rerun()

def chess_view():
    uid = st.session_state.user_id
    page_head("♟️", "Chess arena", "Castling, en passant, promotion, check, and mate")
    if st.session_state.chess is None:
        diff = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
        if st.button("Start game", type="primary"):
            st.session_state.chess = new_chess(diff)
            st.rerun()
        st.info("Full rules: castling, en passant, promotion, checkmate, stalemate.")
        return
    game = st.session_state.chess
    board = game["board"]
    if game["status"] == "playing" and game["turn"] == "black":
        with st.spinner("NEXUS is thinking..."):
            move = ai_move(board, game["state"], game["diff"])
        if move is None:
            finish_chess(uid, "win" if in_check(board, False) else "draw")
            return
        fr, fc, tr, tc, special = move
        cap = board[tr][tc]
        game["history"].append(san(board, move))
        nb, ns = apply_move(board, game["state"], fr, fc, tr, tc, special)
        game["board"], game["state"], game["last"] = nb, ns, (fr, fc, tr, tc)
        if cap != ".":
            game["capw"].append(cap)
        if not legal_moves(nb, ns, True):
            finish_chess(uid, "loss" if in_check(nb, True) else "draw")
            return
        game["turn"] = "white"
        st.rerun()
    label = "Your move" if game["turn"] == "white" else "NEXUS"
    if in_check(board, True):
        label += " — check"
    st.write(label)
    if game.get("msg"):
        st.caption(game["msg"])
    left, right = st.columns([2, 1])
    with left:
        st.markdown(board_html(game), unsafe_allow_html=True)
        moves = legal_moves(board, game["state"], True)
        if not moves:
            finish_chess(uid, "loss" if in_check(board, True) else "draw")
            return
        labels = []
        for move in moves:
            labels.append(UNI[board[move[0]][move[1]]] + " " + sq_name(move[0], move[1]) + " to " + sq_name(move[2], move[3]) + " " + move[4])
        pick = st.selectbox("Legal move", range(len(moves)), format_func=lambda i: labels[i])
        if st.button("Play move", type="primary"):
            fr, fc, tr, tc, special = moves[pick]
            played = san(board, moves[pick])
            cap = board[tr][tc]
            game["history"].append(played)
            nb, ns = apply_move(board, game["state"], fr, fc, tr, tc, special)
            game["board"], game["state"], game["last"] = nb, ns, (fr, fc, tr, tc)
            if cap != ".":
                game["capb"].append(cap)
            game["msg"] = ai_chat([{"role": "user", "content": "You are a kind chess rival. Player played " + played + ". One short sentence, max 12 words."}], timeout=12)
            award_xp(uid, 2)
            if not legal_moves(nb, ns, False):
                finish_chess(uid, "win" if in_check(nb, False) else "draw")
                return
            game["turn"] = "black"
            st.rerun()
    with right:
        if st.button("New game"):
            st.session_state.chess = None
            st.rerun()
        if st.button("Hint"):
            hint = ai_move(board, game["state"], "medium")
            if hint:
                st.info("Try " + san(board, hint))
        st.write("You captured:", " ".join(UNI[p] for p in game["capb"]) or "—")
        st.write("NEXUS captured:", " ".join(UNI[p] for p in game["capw"]) or "—")
        st.text("\n".join(game["history"][-16:]))

def chat_view():
    uid = st.session_state.user_id
    page_head("💬", "Chat", "School, ideas, and planning. Keep it kind.")
    with db() as conn:
        if st.button("New chat"):
            cur = conn.execute("INSERT INTO chats(user_id, title, created_at) VALUES(?,?,?)", (uid, "New chat", now()))
            st.session_state.chat = cur.lastrowid
            st.rerun()
        chats = conn.execute("SELECT id, title FROM chats WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    if chats:
        pick = st.selectbox("Chat", chats, format_func=lambda r: r["title"] or "Chat")
        st.session_state.chat = pick["id"]
    cid = st.session_state.chat
    if not cid:
        st.info("Start a new chat.")
        return
    with db() as conn:
        msgs = conn.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id", (cid,)).fetchall()
    for msg in msgs:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    prompt = st.chat_input("Message NEXUS")
    if prompt:
        with db() as conn:
            conn.execute("INSERT INTO messages(chat_id, role, content, created_at) VALUES(?,?,?,?)", (cid, "user", prompt, now()))
            conn.execute("UPDATE chats SET title = ? WHERE id = ? AND title = 'New chat'", (prompt[:40], cid))
            hist = conn.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id", (cid,)).fetchall()
        api = [{"role": "system", "content": "You are NEXUS, a warm study coach for a teenager. Be kind, practical, and family-friendly."}]
        api += [{"role": m["role"], "content": m["content"]} for m in hist[-12:]]
        reply = ai_chat(api)
        with db() as conn:
            conn.execute("INSERT INTO messages(chat_id, role, content, created_at) VALUES(?,?,?,?)", (cid, "assistant", reply, now()))
        award_xp(uid, 2)
        st.rerun()

def echo_view():
    uid = st.session_state.user_id
    page_head("📸", "Echo", "Places you want to remember")
    photo = st.camera_input("Photo") or st.file_uploader("Upload", type=["jpg", "jpeg", "png"])
    name = st.text_input("Place name")
    mood = st.selectbox("Mood", ["Peaceful", "Busy", "Warm", "Quiet", "Joyful", "Bright", "Still"])
    note = st.text_area("Note")
    if st.button("Save place") and photo and name:
        folder = os.path.join(UPLOAD_DIR, str(uid))
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, datetime.now().strftime("%Y%m%d%H%M%S") + ".jpg")
        with open(path, "wb") as handle:
            handle.write(photo.getvalue())
        desc = ai_chat([{"role": "user", "content": "Describe a saved place called " + name + " in one warm sentence under 20 words. Mood: " + mood + "."}])
        with db() as conn:
            place = conn.execute("SELECT id FROM places WHERE user_id = ? AND name = ?", (uid, name)).fetchone()
            pid = place["id"] if place else conn.execute("INSERT INTO places(user_id, name, created_at) VALUES(?,?,?)", (uid, name, now())).lastrowid
            conn.execute(
                "INSERT INTO memories(user_id, place_id, photo_path, ai_description, user_note, mood, created_at) VALUES(?,?,?,?,?,?,?)",
                (uid, pid, path, desc, note, mood, now()),
            )
        award_xp(uid, 12)
        celebrate()
        st.rerun()
    with db() as conn:
        places = conn.execute("SELECT id, name FROM places WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for place in places:
        if st.button("Open " + place["name"], key="pl" + str(place["id"])):
            st.session_state.place = place["id"]
            go("place")

def place_view():
    pid = st.session_state.place
    with db() as conn:
        place = conn.execute("SELECT * FROM places WHERE id = ?", (pid,)).fetchone()
        rows = conn.execute("SELECT * FROM memories WHERE place_id = ? ORDER BY id DESC", (pid,)).fetchall()
    if not place:
        go("echo")
        return
    page_head("📍", place["name"], str(len(rows)) + " visit(s)")
    for row in rows:
        st.write(row["created_at"][:16] + " · " + (row["mood"] or ""))
        if row["photo_path"] and os.path.exists(row["photo_path"]):
            st.image(row["photo_path"], width=320)
        if row["ai_description"]:
            st.write(row["ai_description"])
        if row["user_note"]:
            st.caption(row["user_note"])

def tutor_view():
    uid = st.session_state.user_id
    page_head("🎓", "Tutor", "A five-step lesson sketch")
    topic = st.text_input("What do you want to learn?")
    if st.button("Build lesson", type="primary") and topic:
        lesson = ai_json("Lesson on " + topic + ". JSON with title, intro, and steps list of 5 objects with n, title, instruction. School-friendly.")
        if not lesson:
            lesson = json.loads(local_reply("lesson"))
        with db() as conn:
            conn.execute("INSERT INTO lessons(user_id, title, topic, steps, created_at) VALUES(?,?,?,?,?)", (uid, lesson.get("title", topic), topic, json.dumps(lesson), now()))
        st.session_state.lesson = lesson
        award_xp(uid, 8)
    lesson = st.session_state.lesson
    if lesson:
        st.subheader(lesson.get("title", "Lesson"))
        st.info(lesson.get("intro", ""))
        for step in lesson.get("steps", []):
            with st.expander(str(step.get("n")) + ". " + str(step.get("title"))):
                st.write(step.get("instruction", ""))

def atlas_view():
    uid = st.session_state.user_id
    page_head("🔧", "ATLAS", "Fix-it checklists and a wellness note for a parent")
    mode = st.radio("Mode", ["Repair", "Wellness"], horizontal=True)
    if mode == "Repair":
        device = st.text_input("Item")
        problem = st.text_area("What is wrong?")
        if st.button("Make a checklist") and device and problem:
            guide = ai_json("Safe beginner checklist for " + device + ": " + problem + ". JSON title, safety, tools, steps. No dangerous electrical or chemical steps.")
            if not guide:
                guide = json.loads(local_reply("repair"))
            with db() as conn:
                conn.execute("INSERT INTO repairs(user_id, device, problem, steps, created_at) VALUES(?,?,?,?,?)", (uid, device, problem, json.dumps(guide), now()))
            st.session_state.repair = guide
            award_xp(uid, 8)
        guide = st.session_state.repair
        if guide:
            st.subheader(guide.get("title", "Checklist"))
            st.error(guide.get("safety", "Ask an adult if you are unsure."))
            for step in guide.get("steps", []):
                st.write(str(step.get("n")) + ". " + str(step.get("title")) + ": " + str(step.get("instruction")))
    else:
        st.warning("Not a doctor. Tell a parent or guardian. Do not take medicine unless they or a doctor say so.")
        symptoms = st.text_area("How do you feel?")
        age = st.selectbox("Who is this about?", ["Me", "A younger sibling with a parent present"])
        if st.button("Wellness note") and symptoms:
            guide = ai_json("Wellness note, not a diagnosis, for a teenager. Feeling: " + symptoms + ". Who: " + age + ". JSON title, seriousness, causes, home_care, warning_signs, see_doctor, safety. Always say tell a parent.")
            if not guide:
                guide = json.loads(local_reply("wellness symptoms"))
            with db() as conn:
                conn.execute("INSERT INTO health(user_id, symptoms, guide, created_at) VALUES(?,?,?,?)", (uid, symptoms, json.dumps(guide), now()))
            st.session_state.health = guide
            award_xp(uid, 4)
        guide = st.session_state.health
        if guide:
            st.subheader(guide.get("title", "Wellness note"))
            st.error(guide.get("safety", "Tell a parent."))
            st.write(guide.get("seriousness", ""))
            st.write("Tell an adult if: " + "; ".join(guide.get("warning_signs", [])))
            st.write(guide.get("see_doctor", "Ask a parent to call a doctor if it worries you."))

def notes_view():
    uid = st.session_state.user_id
    page_head("📝", "Notes")
    with st.form("note"):
        title = st.text_input("Title")
        content = st.text_area("Note")
        if st.form_submit_button("Save"):
            if content:
                with db() as conn:
                    conn.execute("INSERT INTO notes(user_id, title, content, created_at) VALUES(?,?,?,?)", (uid, title or content[:40], content, now()))
                award_xp(uid, 4)
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM notes WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        with st.expander(row["title"] + " · " + row["created_at"][:16]):
            st.write(row["content"])

def journal_view():
    uid = st.session_state.user_id
    page_head("📖", "Journal")
    with st.form("journal"):
        title = st.text_input("Title")
        mood = st.selectbox("Mood", ["Happy", "Calm", "Thoughtful", "Sad", "Frustrated", "Tired", "Motivated", "Neutral"])
        content = st.text_area("Write")
        if st.form_submit_button("Save entry"):
            if content:
                with db() as conn:
                    conn.execute("INSERT INTO journal(user_id, title, content, mood, created_at) VALUES(?,?,?,?,?)", (uid, title or content[:40], content, mood, now()))
                award_xp(uid, 6)
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM journal WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        with st.expander(row["mood"] + " · " + row["title"]):
            st.write(row["content"])
            if st.button("AI reflect", key="jr" + str(row["id"])):
                reply = ai_chat([
                    {"role": "system", "content": "Warm journal companion for a teenager. Empathetic reflection and one gentle question. Under 60 words. Family-friendly."},
                    {"role": "user", "content": row["content"]},
                ])
                st.info(reply)

def dreams_view():
    uid = st.session_state.user_id
    page_head("🌙", "Dreams", "A gentle reading, not a prediction")
    text = st.text_area("What do you remember?")
    if st.button("Save dream") and text:
        reading = ai_json("Dream reflection for a teenager. No scary content. JSON type, emotion, symbols, meaning, message, action. Dream: " + text)
        if not reading:
            reading = json.loads(local_reply("dream"))
        with db() as conn:
            conn.execute(
                "INSERT INTO dreams(user_id, content, interpretation, type, emotion, created_at) VALUES(?,?,?,?,?,?)",
                (uid, text, json.dumps(reading), reading.get("type", "Reflection"), reading.get("emotion", "mixed"), now()),
            )
        award_xp(uid, 6)
        st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM dreams WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        with st.expander(row["created_at"][:16]):
            st.write(row["content"])
            try:
                data = json.loads(row["interpretation"])
                st.write(data.get("type", "") + " · " + data.get("emotion", ""))
                st.write(data.get("meaning", ""))
                st.write(data.get("message", ""))
                st.write(data.get("action", ""))
                if data.get("symbols"):
                    st.caption("Symbols: " + ", ".join(data["symbols"]))
            except Exception:
                st.write(row["interpretation"])

def capsule_view():
    uid = st.session_state.user_id
    page_head("⏳", "Time capsule")
    with st.form("cap"):
        message = st.text_area("Note to future you")
        unlock = st.date_input("Open on", value=datetime.now().date() + timedelta(days=30))
        if st.form_submit_button("Seal"):
            if message:
                with db() as conn:
                    conn.execute("INSERT INTO capsules(user_id, message, unlock_date, created_at) VALUES(?,?,?,?)", (uid, message, str(unlock), now()))
                award_xp(uid, 10)
                celebrate()
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM capsules WHERE user_id = ? ORDER BY unlock_date", (uid,)).fetchall()
    for row in rows:
        days = (datetime.strptime(row["unlock_date"], "%Y-%m-%d").date() - datetime.now().date()).days
        if days <= 0 and not row["opened"]:
            st.success(row["message"])
            if st.button("Mark opened", key="cap" + str(row["id"])):
                with db() as conn:
                    conn.execute("UPDATE capsules SET opened = 1 WHERE id = ?", (row["id"],))
                st.rerun()
        elif row["opened"]:
            st.caption("Opened · " + row["unlock_date"])
        else:
            st.caption("Sealed for " + str(days) + " more days (" + row["unlock_date"] + ")")

def habits_view():
    uid = st.session_state.user_id
    page_head("✅", "Habits")
    with st.form("habit"):
        name = st.text_input("Habit")
        icon = st.text_input("Emoji", value="✅")
        if st.form_submit_button("Add habit"):
            if name:
                with db() as conn:
                    conn.execute("INSERT INTO habits(user_id, name, icon, created_at) VALUES(?,?,?,?)", (uid, name, icon, now()))
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM habits WHERE user_id = ?", (uid,)).fetchall()
    for row in rows:
        c1, c2 = st.columns([4, 1])
        c1.write(row["icon"] + " " + row["name"] + " · " + str(row["streak"]) + " days")
        if row["last_done"] == today():
            c2.success("Done")
        elif c2.button("Mark", key="h" + str(row["id"])):
            yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            streak = (row["streak"] or 0) + 1 if row["last_done"] == yesterday else 1
            with db() as conn:
                conn.execute("UPDATE habits SET last_done = ?, streak = ? WHERE id = ?", (today(), streak, row["id"]))
            award_xp(uid, 5)
            st.rerun()

def focus_view():
    uid = st.session_state.user_id
    page_head("🎯", "Focus", "A simple study timer")
    task = st.text_input("Task", value=st.session_state.focus_task)
    minutes = st.select_slider("Minutes", [5, 10, 15, 25, 45], value=25)
    if st.button("Start"):
        if not task:
            st.error("Name the task.")
        else:
            st.session_state.focus_end = time.time() + minutes * 60
            st.session_state.focus_task = task
            st.session_state.focus_min = minutes
            st.rerun()
    if st.session_state.focus_end:
        left = int(st.session_state.focus_end - time.time())
        if left > 0:
            mins, secs = divmod(left, 60)
            st.markdown("<div class='nx-stat'><b>" + f"{mins:02d}:{secs:02d}" + "</b>" + st.session_state.focus_task + "</div>", unsafe_allow_html=True)
            if st.button("Refresh timer"):
                st.rerun()
        else:
            with db() as conn:
                conn.execute("INSERT INTO focus(user_id, duration, task, created_at) VALUES(?,?,?,?)", (uid, st.session_state.focus_min, st.session_state.focus_task, now()))
            award_xp(uid, st.session_state.focus_min)
            celebrate()
            st.session_state.focus_end = None
            st.rerun()

def mood_view():
    uid = st.session_state.user_id
    page_head("😊", "Mood")
    with st.form("mood"):
        mood = st.selectbox("Mood", ["Happy", "Calm", "Thoughtful", "Sad", "Frustrated", "Tired", "Motivated", "Neutral"])
        energy = st.slider("Energy", 1, 10, 5)
        note = st.text_input("Note")
        if st.form_submit_button("Log"):
            with db() as conn:
                conn.execute("INSERT INTO moods(user_id, mood, energy, note, created_at) VALUES(?,?,?,?,?)", (uid, mood, energy, note, now()))
            award_xp(uid, 2)
            st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM moods WHERE user_id = ? ORDER BY id DESC LIMIT 20", (uid,)).fetchall()
    for row in rows:
        st.write(row["created_at"][:16] + " · " + row["mood"] + " · energy " + str(row["energy"]) + " · " + (row["note"] or ""))

def gratitude_view():
    uid = st.session_state.user_id
    page_head("🙏", "Gratitude")
    text = st.text_area("Three good things")
    if st.button("Save gratitude") and text.strip():
        with db() as conn:
            conn.execute("INSERT INTO gratitude(user_id, items, created_at) VALUES(?,?,?)", (uid, text, now()))
        award_xp(uid, 4)
        st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM gratitude WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        st.markdown("<div class='nx-card'>" + row["created_at"][:10] + "<br>" + row["items"] + "</div>", unsafe_allow_html=True)

def wins_view():
    uid = st.session_state.user_id
    page_head("🏆", "Wins", "Small wins count")
    with st.form("win"):
        desc = st.text_input("What went well?")
        size = st.selectbox("Size", ["tiny", "small", "medium", "big"])
        if st.form_submit_button("Log win"):
            if desc:
                with db() as conn:
                    conn.execute("INSERT INTO wins(user_id, description, size, created_at) VALUES(?,?,?,?)", (uid, desc, size, now()))
                award_xp(uid, 4)
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM wins WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        st.write(row["size"] + " · " + row["description"])

def reading_view():
    uid = st.session_state.user_id
    page_head("📚", "Reading list")
    with st.form("read"):
        title = st.text_input("Title")
        status = st.selectbox("Status", ["Want to read", "Reading", "Finished"])
        if st.form_submit_button("Add"):
            if title:
                with db() as conn:
                    conn.execute("INSERT INTO reading(user_id, title, status, created_at) VALUES(?,?,?,?)", (uid, title, status, now()))
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM reading WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        st.write(row["title"] + " — " + row["status"])

def quotes_view():
    uid = st.session_state.user_id
    page_head("💬", "Quotes")
    with st.form("quote"):
        quote = st.text_area("Quote")
        author = st.text_input("Author")
        if st.form_submit_button("Save"):
            if quote:
                with db() as conn:
                    conn.execute("INSERT INTO quotes(user_id, quote, author, created_at) VALUES(?,?,?,?)", (uid, quote, author, now()))
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM quotes WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        st.markdown("<div class='nx-card'>" + row["quote"] + "<div class='nx-muted'>" + (row["author"] or "Unknown") + "</div></div>", unsafe_allow_html=True)

def flash_view():
    uid = st.session_state.user_id
    page_head("🃏", "Flashcards")
    with st.form("flash"):
        question = st.text_input("Question")
        answer = st.text_input("Answer")
        if st.form_submit_button("Add"):
            if question and answer:
                with db() as conn:
                    conn.execute("INSERT INTO flash(user_id, question, answer, created_at) VALUES(?,?,?,?)", (uid, question, answer, now()))
                award_xp(uid, 2)
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM flash WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        with st.expander(row["question"]):
            if st.button("Reveal", key="rv" + str(row["id"])):
                st.success(row["answer"])

def breathe_view():
    page_head("🫁", "Breathe", "In 4 · hold 4 · out 6")
    components.html(
        "<div style='text-align:center;font-family:sans-serif;color:#eef2ff'>"
        "<div id='c' style='width:140px;height:140px;margin:20px auto;border-radius:50%;background:#7c5cff;display:flex;align-items:center;justify-content:center'>Ready</div>"
        "<button onclick='go()' style='padding:8px 16px;border:0;border-radius:10px'>Begin</button></div>"
        "<script>async function go(){const c=document.getElementById('c');const steps=[['In',4],['Hold',4],['Out',6]];"
        "for(let n=0;n<3;n++){for(const [name,sec] of steps){c.textContent=name;await new Promise(r=>setTimeout(r,sec*1000));}}c.textContent='Done';}</script>",
        height=260,
    )

def meditate_view():
    uid = st.session_state.user_id
    page_head("🧘", "Meditate")
    with st.form("med"):
        mins = st.slider("Minutes", 1, 30, 5)
        note = st.text_input("Note")
        if st.form_submit_button("Log"):
            with db() as conn:
                conn.execute("INSERT INTO meditation(user_id, minutes, note, created_at) VALUES(?,?,?,?)", (uid, mins, note, now()))
            award_xp(uid, mins)
            celebrate()
            st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM meditation WHERE user_id = ? ORDER BY id DESC LIMIT 10", (uid,)).fetchall()
    for row in rows:
        st.write(str(row["minutes"]) + " min · " + row["created_at"][:10] + " · " + (row["note"] or ""))

def water_view():
    uid = st.session_state.user_id
    page_head("💧", "Water")
    with db() as conn:
        total = conn.execute("SELECT SUM(glasses) AS g FROM water WHERE user_id = ? AND created_at LIKE ?", (uid, today() + "%")).fetchone()["g"] or 0
    st.progress(min(total / 8, 1.0))
    st.write(str(total) + " / 8 glasses")
    c1, c2 = st.columns(2)
    if c1.button("+1 glass"):
        with db() as conn:
            conn.execute("INSERT INTO water(user_id, glasses, created_at) VALUES(?,1,?)", (uid, now()))
        award_xp(uid, 1)
        st.rerun()
    if c2.button("+2 glasses"):
        with db() as conn:
            conn.execute("INSERT INTO water(user_id, glasses, created_at) VALUES(?,2,?)", (uid, now()))
        award_xp(uid, 2)
        st.rerun()

def sleep_view():
    uid = st.session_state.user_id
    page_head("😴", "Sleep")
    with st.form("sleep"):
        hours = st.number_input("Hours", 0.0, 16.0, 8.0, 0.5)
        quality = st.slider("Quality", 1, 10, 7)
        if st.form_submit_button("Log sleep"):
            with db() as conn:
                conn.execute("INSERT INTO sleep(user_id, hours, quality, created_at) VALUES(?,?,?,?)", (uid, hours, quality, now()))
            award_xp(uid, 3)
            st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM sleep WHERE user_id = ? ORDER BY id DESC LIMIT 14", (uid,)).fetchall()
    for row in rows:
        st.write(row["created_at"][:10] + " · " + str(row["hours"]) + "h · quality " + str(row["quality"]))

def workout_view():
    uid = st.session_state.user_id
    page_head("🏃", "Workout")
    with st.form("move"):
        kind = st.selectbox("Type", ["Walk", "Run", "Sport", "Stretch", "Dance", "Other"])
        mins = st.number_input("Minutes", 1, 180, 20)
        notes = st.text_input("Notes")
        if st.form_submit_button("Log"):
            with db() as conn:
                conn.execute("INSERT INTO workout(user_id, type, duration, notes, created_at) VALUES(?,?,?,?,?)", (uid, kind, mins, notes, now()))
            award_xp(uid, max(1, mins // 5))
            st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM workout WHERE user_id = ? ORDER BY id DESC LIMIT 14", (uid,)).fetchall()
    for row in rows:
        st.write(row["created_at"][:10] + " · " + row["type"] + " · " + str(row["duration"]) + " min " + (row["notes"] or ""))

def goals_view():
    uid = st.session_state.user_id
    page_head("🎯", "Goals")
    with st.form("goal"):
        obj = st.text_input("Goal")
        due = st.date_input("Due")
        if st.form_submit_button("Add"):
            if obj:
                with db() as conn:
                    conn.execute("INSERT INTO goals(user_id, objective, due_date, created_at) VALUES(?,?,?,?)", (uid, obj, str(due), now()))
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM goals WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        st.write(row["objective"] + " · due " + (row["due_date"] or ""))
        val = st.slider("Progress", 0, 100, row["progress"] or 0, key="g" + str(row["id"]))
        if val != (row["progress"] or 0):
            with db() as conn:
                conn.execute("UPDATE goals SET progress = ? WHERE id = ?", (val, row["id"]))
            st.rerun()

def coach_view():
    uid = st.session_state.user_id
    page_head("🤖", "AI Coach", "Study and habit ideas")
    with db() as conn:
        logs = conn.execute("SELECT role, content FROM coach WHERE user_id = ? ORDER BY id", (uid,)).fetchall()
    for msg in logs:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    prompt = st.chat_input("Ask for a plan")
    if prompt:
        reply = ai_chat([
            {"role": "system", "content": "You are a kind study coach for a teenager. Practical steps only. Family-friendly. Ask one short follow-up."},
            {"role": "user", "content": prompt},
        ])
        with db() as conn:
            conn.execute("INSERT INTO coach(user_id, role, content, created_at) VALUES(?,?,?,?)", (uid, "user", prompt, now()))
            conn.execute("INSERT INTO coach(user_id, role, content, created_at) VALUES(?,?,?,?)", (uid, "assistant", reply, now()))
        award_xp(uid, 3)
        st.rerun()

POOL = [
    "Write three things you are grateful for",
    "Pack your bag for tomorrow",
    "Read for 15 minutes",
    "Drink a glass of water before homework",
    "Tell a family member one kind thing",
    "Review one flashcard set",
    "Tidy your desk for five minutes",
    "Write tomorrow's first task",
]

def challenge_view():
    uid = st.session_state.user_id
    page_head("📅", "Daily challenge")
    with db() as conn:
        row = conn.execute("SELECT * FROM challenges WHERE user_id = ? AND cd = ?", (uid, today())).fetchone()
        if not row:
            conn.execute("INSERT INTO challenges(user_id, cd, ct, created_at) VALUES(?,?,?,?)", (uid, today(), random.choice(POOL), now()))
            row = conn.execute("SELECT * FROM challenges WHERE user_id = ? AND cd = ?", (uid, today())).fetchone()
    st.markdown("<div class='nx-card'><b>" + row["ct"] + "</b></div>", unsafe_allow_html=True)
    if row["completed"]:
        st.success("Completed")
    elif st.button("Mark complete"):
        with db() as conn:
            conn.execute("UPDATE challenges SET completed = 1 WHERE id = ?", (row["id"],))
        award_xp(uid, 15)
        celebrate()
        st.rerun()

def studio_view():
    uid = st.session_state.user_id
    page_head("🏗️", "Studio", "Project ideas")
    with st.form("proj"):
        name = st.text_input("Project")
        desc = st.text_area("What is it?")
        stage = st.selectbox("Stage", ["idea", "building", "paused", "done"])
        if st.form_submit_button("Add"):
            if name:
                with db() as conn:
                    conn.execute("INSERT INTO projects(user_id, name, description, stage, created_at) VALUES(?,?,?,?,?)", (uid, name, desc, stage, now()))
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM projects WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        st.markdown("<div class='nx-card'><b>" + row["name"] + "</b><div class='nx-muted'>" + row["stage"] + "</div>" + (row["description"] or "") + "</div>", unsafe_allow_html=True)

def check_ttt(board):
    lines = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
    for a, b, c in lines:
        if board[a] == board[b] == board[c] and board[a] != " ":
            return board[a]
    return None

def ai_ttt(board):
    for mark in ("O", "X"):
        for i in range(9):
            if board[i] == " ":
                board[i] = mark
                if check_ttt(board) == mark:
                    board[i] = " "
                    return i
                board[i] = " "
    if board[4] == " ":
        return 4
    empty = [i for i, v in enumerate(board) if v == " "]
    return random.choice(empty) if empty else None

WORDS = ["apple", "beach", "chair", "dance", "eagle", "flame", "grape", "house", "light", "mango", "night", "ocean", "piano", "river", "stone", "tiger", "water", "youth", "zebra", "cloud"]
RIDDLES = [("What has hands but cannot clap?", "a clock"), ("What gets wetter as it dries?", "a towel"), ("What has keys but no locks?", "a piano")]
SPARKS = ["Octopuses have three hearts.", "Honey never spoils if it is sealed.", "Light from the Sun takes about 8 minutes to reach Earth."]
TYPING = ["small steps still move you forward", "pack the bag before you sleep", "read the question twice then answer"]

def games_view():
    uid = st.session_state.user_id
    page_head("🎮", "Games")
    tab1, tab2, tab3 = st.tabs(["Tic-tac-toe", "Memory", "Wordle"])
    with tab1:
        if st.session_state.ttt is None:
            st.session_state.ttt = {"board": [" "] * 9, "over": False, "msg": ""}
        board = st.session_state.ttt
        cols = st.columns(3)
        for i in range(9):
            label = board["board"][i] if board["board"][i] != " " else "·"
            if cols[i % 3].button(label, key="ttt" + str(i)):
                if not board["over"] and board["board"][i] == " ":
                    board["board"][i] = "X"
                    winner = check_ttt(board["board"])
                    if winner or " " not in board["board"]:
                        board["over"] = True
                        board["msg"] = (winner + " wins") if winner else "Draw"
                    else:
                        mv = ai_ttt(board["board"])
                        board["board"][mv] = "O"
                        winner = check_ttt(board["board"])
                        if winner or " " not in board["board"]:
                            board["over"] = True
                            board["msg"] = (winner + " wins") if winner else "Draw"
                    if board["over"]:
                        result = "win" if board["msg"] == "X wins" else "loss" if board["msg"] == "O wins" else "draw"
                        with db() as conn:
                            conn.execute("INSERT INTO ttt(user_id, result, created_at) VALUES(?,?,?)", (uid, result, now()))
                        if result == "win":
                            award_xp(uid, 12)
                            celebrate()
                    st.rerun()
        if board["msg"]:
            st.info(board["msg"])
        if st.button("Reset game"):
            st.session_state.ttt = None
            st.rerun()
    with tab2:
        if st.session_state.mem is None:
            cards = ["🌟", "🌙", "📚", "♟️", "💧", "🎯", "🌱", "🔥"] * 2
            random.shuffle(cards)
            st.session_state.mem = {"cards": cards, "up": [], "done": []}
        mem = st.session_state.mem
        cols = st.columns(4)
        for i, card in enumerate(mem["cards"]):
            shown = i in mem["done"] or i in mem["up"]
            if cols[i % 4].button(card if shown else "?", key="mem" + str(i)):
                if i not in mem["done"] and i not in mem["up"] and len(mem["up"]) < 2:
                    mem["up"].append(i)
                    if len(mem["up"]) == 2:
                        a, b = mem["up"]
                        if mem["cards"][a] == mem["cards"][b]:
                            mem["done"] += [a, b]
                            award_xp(uid, 2)
                        mem["up"] = []
                    st.rerun()
        st.caption("Matched " + str(len(mem["done"]) // 2) + "/8")
        if st.button("New memory game"):
            st.session_state.mem = None
            st.rerun()
    with tab3:
        with db() as conn:
            row = conn.execute("SELECT * FROM wordle WHERE user_id = ? AND day = ?", (uid, today())).fetchone()
            if not row:
                conn.execute("INSERT INTO wordle(user_id, word, guesses, day, created_at) VALUES(?,?,?,?,?)", (uid, random.choice(WORDS), "", today(), now()))
                row = conn.execute("SELECT * FROM wordle WHERE user_id = ? AND day = ?", (uid, today())).fetchone()
        guesses = [g for g in (row["guesses"] or "").split(",") if g]
        for guess in guesses:
            bits = []
            for i, ch in enumerate(guess):
                color = "#3dd68c" if row["word"][i] == ch else "#ffd166" if ch in row["word"] else "#666"
                bits.append("<span style='display:inline-block;width:32px;text-align:center;background:" + color + ";margin:2px;border-radius:6px'>" + ch.upper() + "</span>")
            st.markdown("".join(bits), unsafe_allow_html=True)
        if row["word"] in guesses:
            st.success("Solved")
        elif len(guesses) >= 6:
            st.error("Word was " + row["word"].upper())
        else:
            guess = st.text_input("5-letter guess", max_chars=5).lower()
            if st.button("Submit guess") and len(guess) == 5 and guess.isalpha():
                guesses.append(guess)
                won = 1 if guess == row["word"] else 0
                with db() as conn:
                    conn.execute("UPDATE wordle SET guesses = ?, won = ? WHERE id = ?", (",".join(guesses), won, row["id"]))
                if won:
                    award_xp(uid, 20)
                    celebrate()
                st.rerun()

def search_view():
    uid = st.session_state.user_id
    page_head("🔍", "Search")
    q = st.text_input("Search notes, journal, tasks, quotes")
    if not q or len(q) < 2:
        return
    like = "%" + q + "%"
    with db() as conn:
        for table, col in [("notes", "content"), ("journal", "content"), ("tasks", "title"), ("homework", "title"), ("quotes", "quote"), ("places", "name"), ("wins", "description")]:
            rows = conn.execute("SELECT " + col + " AS t FROM " + table + " WHERE user_id = ? AND " + col + " LIKE ? LIMIT 8", (uid, like)).fetchall()
            for row in rows:
                st.write(table + ": " + str(row["t"])[:140])

def weekly_view():
    uid = st.session_state.user_id
    page_head("📊", "Weekly report")
    if st.button("Build report"):
        since = (datetime.now() - timedelta(days=7)).isoformat()
        with db() as conn:
            stats = {}
            for table in ["journal", "notes", "tasks", "homework", "focus", "wins", "moods", "dreams"]:
                stats[table] = conn.execute("SELECT COUNT(*) AS x FROM " + table + " WHERE user_id = ? AND created_at >= ?", (uid, since)).fetchone()["x"]
        st.write(ai_chat([{"role": "user", "content": "Weekly report for a student. Counts: " + str(stats) + ". Two kind sentences, one win, one next step."}]))

def decide_view():
    page_head("🎲", "Decide", "Talk big choices over with a parent")
    question = st.text_area("What are you deciding?")
    options = st.text_area("Options, one per line")
    if st.button("Help me think") and question and options:
        st.write(ai_chat([{"role": "user", "content": "Help a teenager think through this decision safely. Question: " + question + ". Options: " + options + ". Pros, cons, and one careful suggestion. Under 160 words."}]))

def email_view():
    page_head("💌", "Email drafts", "School notes: thank-you, question, club, apology, follow-up")
    kind = st.selectbox("Type", ["Thank you", "Request", "Follow-up", "Apology", "Club intro", "Polite concern", "Leaving a club"])
    who = st.text_input("Who is it for?")
    what = st.text_area("What should it say?")
    tone = st.select_slider("Tone", ["Formal", "Professional", "Friendly", "Warm"], value="Professional")
    if st.button("Draft") and who and what:
        st.write(ai_chat([{"role": "user", "content": "Write a short polite " + kind + " note to " + who + ". Tone: " + tone + ". Content: " + what + ". School-appropriate. Under 140 words. Include a subject."}]))
        award_xp(st.session_state.user_id, 4)

def resume_view():
    page_head("📄", "Resume helper", "School and club bullets")
    role = st.text_input("Target role or club")
    exp = st.text_area("What you did")
    if st.button("Generate bullets") and role and exp:
        st.write(ai_chat([{"role": "user", "content": "5 school-friendly resume bullets for " + role + ". Experience: " + exp + ". Action verbs. No adult job claims."}]))
        award_xp(st.session_state.user_id, 4)

def habitsuggest_view():
    uid = st.session_state.user_id
    page_head("🌱", "Habit ideas")
    if st.button("Suggest"):
        with db() as conn:
            journals = [row["content"][:80] for row in conn.execute("SELECT content FROM journal WHERE user_id = ? ORDER BY id DESC LIMIT 3", (uid,))]
            moods = [row["mood"] for row in conn.execute("SELECT mood FROM moods WHERE user_id = ? ORDER BY id DESC LIMIT 3", (uid,))]
        st.write(ai_chat([{"role": "user", "content": "Suggest 3 small habits for a student. Journals: " + "; ".join(journals) + ". Moods: " + ", ".join(moods) + ". Under 120 words."}]))
        award_xp(uid, 3)

def leaderboard_view():
    page_head("🏆", "Leaderboard")
    with db() as conn:
        rows = conn.execute("SELECT name, username, xp, rank, streak, arena_wins FROM users ORDER BY xp DESC LIMIT 20").fetchall()
    for i, row in enumerate(rows, 1):
        st.write(str(i) + ". " + (row["name"] or row["username"]) + " — " + str(row["xp"]) + " XP · " + row["rank"] + " · 🔥 " + str(row["streak"]) + " · chess " + str(row["arena_wins"]))

def achievements_view():
    uid = st.session_state.user_id
    page_head("🎖️", "Awards")
    with db() as conn:
        have = {row["code"] for row in conn.execute("SELECT code FROM ach WHERE user_id = ?", (uid,))}
    for code, (name, icon) in ACH.items():
        st.write(icon + " " + name + (" ✅" if code in have else " 🔒"))

def stats_view():
    uid = st.session_state.user_id
    page_head("📊", "Stats")
    with db() as conn:
        user = conn.execute("SELECT xp, streak, rank, arena_wins, arena_losses FROM users WHERE id = ?", (uid,)).fetchone()
        st.write(user["rank"] + " · " + str(user["xp"]) + " XP · streak " + str(user["streak"]) + " · chess " + str(user["arena_wins"]) + "W/" + str(user["arena_losses"]) + "L")
        for table in ["places", "memories", "notes", "journal", "dreams", "capsules", "lessons", "repairs", "health", "matches", "habits", "tasks", "homework", "grades"]:
            n = conn.execute("SELECT COUNT(*) AS x FROM " + table + " WHERE user_id = ?", (uid,)).fetchone()["x"]
            st.metric(table, n)

def settings_view():
    uid = st.session_state.user_id
    page_head("⚙️", "Settings")
    profile, data, danger = st.tabs(["Profile", "Data", "Danger"])
    with profile:
        with db() as conn:
            user = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
        name = st.text_input("Display name", value=user["name"] or "")
        theme = st.selectbox("Theme", list(THEMES), index=list(THEMES).index(user["theme"] or "cosmic"))
        if st.button("Save profile"):
            with db() as conn:
                conn.execute("UPDATE users SET name = ?, theme = ? WHERE id = ?", (name, theme, uid))
            st.session_state.name = name
            st.session_state.theme = theme
            st.rerun()
        old = st.text_input("Current password", type="password")
        new = st.text_input("New password", type="password")
        if st.button("Update password"):
            with db() as conn:
                row = conn.execute("SELECT password_hash FROM users WHERE id = ?", (uid,)).fetchone()
                if not check_pw(old, row["password_hash"]):
                    st.error("Current password is wrong.")
                elif len(new) < 6:
                    st.error("Use at least 6 characters.")
                else:
                    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_pw(new), uid))
                    st.success("Password updated.")
    with data:
        if st.button("Prepare export"):
            with db() as conn:
                export = {"users": [dict(conn.execute("SELECT id, username, name, xp, rank, streak FROM users WHERE id = ?", (uid,)).fetchone())]}
                for table in TABLES:
                    if table == "users":
                        continue
                    try:
                        rows = conn.execute("SELECT * FROM " + table + " WHERE user_id = ?", (uid,)).fetchall()
                    except sqlite3.OperationalError:
                        rows = []
                    export[table] = [dict(row) for row in rows]
            st.session_state["export_json"] = json.dumps(export, indent=2, default=str)
        if st.session_state.get("export_json"):
            st.download_button("Download JSON", st.session_state["export_json"], file_name="nexus_" + str(uid) + ".json")
    with danger:
        st.warning("This cannot be undone.")
        confirm = st.text_input("Type DELETE to confirm")
        if st.button("Delete account"):
            if confirm != "DELETE":
                st.error("Type DELETE")
            else:
                with db() as conn:
                    for table in TABLES:
                        try:
                            conn.execute("DELETE FROM " + table + " WHERE user_id = ?", (uid,))
                        except sqlite3.OperationalError:
                            pass
                    conn.execute("DELETE FROM users WHERE id = ?", (uid,))
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

def tasks_view():
    uid = st.session_state.user_id
    page_head("✅", "Tasks")
    with st.form("task"):
        title = st.text_input("Task")
        priority = st.selectbox("Priority", ["low", "medium", "high"])
        due = st.date_input("Due")
        if st.form_submit_button("Add"):
            if title:
                with db() as conn:
                    conn.execute("INSERT INTO tasks(user_id, title, priority, due, created_at) VALUES(?,?,?,?,?)", (uid, title, priority, str(due), now()))
                award_xp(uid, 3)
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM tasks WHERE user_id = ? ORDER BY done, due", (uid,)).fetchall()
    for row in rows:
        c1, c2 = st.columns([5, 1])
        c1.write(("✅ " if row["done"] else "⬜ ") + "[" + row["priority"] + "] " + row["title"] + " · " + row["due"])
        if not row["done"] and c2.button("Done", key="td" + str(row["id"])):
            with db() as conn:
                conn.execute("UPDATE tasks SET done = 1 WHERE id = ?", (row["id"],))
            award_xp(uid, 6)
            st.rerun()

def homework_view():
    uid = st.session_state.user_id
    page_head("📚", "Homework")
    with st.form("hw"):
        subject = st.text_input("Subject")
        title = st.text_input("Assignment")
        due = st.date_input("Due date")
        if st.form_submit_button("Add homework"):
            if subject and title:
                with db() as conn:
                    conn.execute("INSERT INTO homework(user_id, subject, title, due, created_at) VALUES(?,?,?,?,?)", (uid, subject, title, str(due), now()))
                award_xp(uid, 4)
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM homework WHERE user_id = ? ORDER BY done, due", (uid,)).fetchall()
    for row in rows:
        c1, c2 = st.columns([5, 1])
        c1.write(("✅ " if row["done"] else "📘 ") + row["subject"] + ": " + row["title"] + " · due " + row["due"])
        if not row["done"] and c2.button("Done", key="hw" + str(row["id"])):
            with db() as conn:
                conn.execute("UPDATE homework SET done = 1 WHERE id = ?", (row["id"],))
            award_xp(uid, 10)
            st.rerun()

def exams_view():
    uid = st.session_state.user_id
    page_head("🗓️", "Exam countdown")
    with st.form("exam"):
        subject = st.text_input("Subject")
        title = st.text_input("Exam name")
        when = st.date_input("Date")
        notes = st.text_area("Study notes")
        if st.form_submit_button("Save exam"):
            if subject and title:
                with db() as conn:
                    conn.execute("INSERT INTO exams(user_id, subject, title, exam_date, notes, created_at) VALUES(?,?,?,?,?,?)", (uid, subject, title, str(when), notes, now()))
                award_xp(uid, 5)
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM exams WHERE user_id = ? ORDER BY exam_date", (uid,)).fetchall()
    for row in rows:
        days = (datetime.strptime(row["exam_date"], "%Y-%m-%d").date() - datetime.now().date()).days
        st.markdown("<div class='nx-card'><b>" + row["subject"] + "</b> — " + row["title"] + "<div class='nx-muted'>" + str(days) + " days · " + row["exam_date"] + "</div>" + (row["notes"] or "") + "</div>", unsafe_allow_html=True)

def grades_view():
    uid = st.session_state.user_id
    page_head("📈", "Grades")
    with st.form("grade"):
        subject = st.text_input("Subject")
        title = st.text_input("Test or project")
        score = st.number_input("Score", 0.0, 1000.0, 0.0)
        out_of = st.number_input("Out of", 1.0, 1000.0, 100.0)
        if st.form_submit_button("Log score"):
            if subject:
                with db() as conn:
                    conn.execute("INSERT INTO grades(user_id, subject, title, score, out_of, created_at) VALUES(?,?,?,?,?,?)", (uid, subject, title, score, out_of, now()))
                award_xp(uid, 3)
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM grades WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    buckets = {}
    for row in rows:
        buckets.setdefault(row["subject"], []).append(row["score"] / row["out_of"] * 100)
        st.write(row["subject"] + " · " + row["title"] + " · " + str(row["score"]) + "/" + str(row["out_of"]))
    for subject, vals in buckets.items():
        st.metric(subject + " average", f"{sum(vals) / len(vals):.1f}%")

def vocab_view():
    uid = st.session_state.user_id
    page_head("🔤", "Vocabulary")
    with st.form("vocab"):
        word = st.text_input("Word")
        meaning = st.text_input("Meaning")
        example = st.text_input("Example")
        if st.form_submit_button("Add card"):
            if word and meaning:
                with db() as conn:
                    conn.execute("INSERT INTO vocab(user_id, word, meaning, example, created_at) VALUES(?,?,?,?,?)", (uid, word, meaning, example, now()))
                award_xp(uid, 3)
                st.rerun()
    with db() as conn:
        cards = conn.execute("SELECT * FROM vocab WHERE user_id = ? ORDER BY box, id", (uid,)).fetchall()
    if not cards:
        st.info("Add a word to start.")
        return
    card = cards[0]
    st.markdown("<div class='nx-card'><b>" + card["word"] + "</b><div class='nx-muted'>Box " + str(card["box"]) + "</div></div>", unsafe_allow_html=True)
    if st.button("Show meaning"):
        st.success(card["meaning"] + " — " + (card["example"] or ""))
    c1, c2 = st.columns(2)
    if c1.button("I knew it"):
        with db() as conn:
            conn.execute("UPDATE vocab SET box = MIN(box + 1, 5) WHERE id = ?", (card["id"],))
        award_xp(uid, 2)
        st.rerun()
    if c2.button("Still learning"):
        with db() as conn:
            conn.execute("UPDATE vocab SET box = 1 WHERE id = ?", (card["id"],))
        st.rerun()

def kindness_view():
    uid = st.session_state.user_id
    page_head("💛", "Kindness log")
    act = st.text_input("A kind thing you did or noticed")
    if st.button("Save act") and act:
        with db() as conn:
            conn.execute("INSERT INTO kindness(user_id, act, created_at) VALUES(?,?,?)", (uid, act, now()))
        award_xp(uid, 5)
        st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM kindness WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        st.write(row["created_at"][:10] + " · " + row["act"])

def money_view():
    uid = st.session_state.user_id
    page_head("🪙", "Allowance")
    with st.form("money"):
        kind = st.selectbox("Type", ["in", "out"])
        amount = st.number_input("Amount", 0.0, 100000.0, 1.0)
        note = st.text_input("Note")
        if st.form_submit_button("Add"):
            with db() as conn:
                conn.execute("INSERT INTO money(user_id, kind, amount, note, created_at) VALUES(?,?,?,?,?)", (uid, kind, amount, note, now()))
            st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM money WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    bal = sum(row["amount"] if row["kind"] == "in" else -row["amount"] for row in rows)
    st.metric("Balance", f"{bal:.2f}")
    for row in rows:
        sign = "+" if row["kind"] == "in" else "-"
        st.write(row["created_at"][:10] + " " + sign + f"{row['amount']:.2f} " + (row["note"] or ""))

def events_view():
    uid = st.session_state.user_id
    page_head("📌", "Events")
    with st.form("ev"):
        title = st.text_input("Event")
        when = st.date_input("Date")
        note = st.text_input("Note")
        if st.form_submit_button("Add"):
            if title:
                with db() as conn:
                    conn.execute("INSERT INTO events(user_id, title, event_date, note, created_at) VALUES(?,?,?,?,?)", (uid, title, str(when), note, now()))
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM events WHERE user_id = ? ORDER BY event_date", (uid,)).fetchall()
    for row in rows:
        days = (datetime.strptime(row["event_date"], "%Y-%m-%d").date() - datetime.now().date()).days
        st.write(row["event_date"] + " (" + str(days) + " days) · " + row["title"] + " · " + (row["note"] or ""))

def bookmarks_view():
    uid = st.session_state.user_id
    page_head("🔖", "Bookmarks")
    with st.form("bm"):
        title = st.text_input("Title")
        url = st.text_input("Link")
        tag = st.text_input("Tag", value="school")
        if st.form_submit_button("Save"):
            if title:
                with db() as conn:
                    conn.execute("INSERT INTO bookmarks(user_id, title, url, tag, created_at) VALUES(?,?,?,?,?)", (uid, title, url, tag, now()))
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM bookmarks WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        st.write("[" + (row["tag"] or "") + "] " + row["title"] + " — " + (row["url"] or ""))

def checks_view():
    uid = st.session_state.user_id
    page_head("☑️", "Checklists", "One item per line")
    with st.form("chk"):
        name = st.text_input("List name")
        items = st.text_area("Items")
        if st.form_submit_button("Save list"):
            if name and items:
                with db() as conn:
                    conn.execute("INSERT INTO checks(user_id, name, items, created_at) VALUES(?,?,?,?)", (uid, name, items, now()))
                st.rerun()
    with db() as conn:
        rows = conn.execute("SELECT * FROM checks WHERE user_id = ? ORDER BY id DESC", (uid,)).fetchall()
    for row in rows:
        with st.expander(row["name"]):
            for item in row["items"].splitlines():
                st.checkbox(item, key="ck" + str(row["id"]) + item)

def riddle_view():
    uid = st.session_state.user_id
    page_head("❓", "Riddle")
    if st.session_state.riddle is None:
        st.session_state.riddle = random.choice(RIDDLES)
    question, answer = st.session_state.riddle
    st.markdown("<div class='nx-card'><b>" + question + "</b></div>", unsafe_allow_html=True)
    guess = st.text_input("Your answer")
    if st.button("Check") and guess:
        if answer in guess.lower():
            st.success("Yes")
            with db() as conn:
                conn.execute("INSERT INTO riddles_log(user_id, riddle, solved, created_at) VALUES(?,?,1,?)", (uid, question, now()))
            award_xp(uid, 6)
        else:
            st.info("Try again. Hint: " + answer[0] + "...")
    if st.button("New riddle"):
        st.session_state.riddle = random.choice(RIDDLES)
        st.rerun()

def typing_view():
    uid = st.session_state.user_id
    page_head("⌨️", "Typing sprint")
    if "type_start" not in st.session_state:
        st.session_state.type_start = None
        st.session_state.type_text = random.choice(TYPING)
    st.code(st.session_state.type_text)
    if st.button("Start typing clock"):
        st.session_state.type_start = time.time()
    typed = st.text_input("Type the line")
    if st.button("Score") and st.session_state.type_start and typed:
        elapsed = max(time.time() - st.session_state.type_start, 1)
        target = st.session_state.type_text
        correct = sum(1 for a, b in zip(typed, target) if a == b)
        accuracy = int(100 * correct / max(len(target), 1))
        wpm = int((len(typed) / 5) / (elapsed / 60))
        st.metric("WPM", wpm)
        st.metric("Accuracy", str(accuracy) + "%")
        with db() as conn:
            conn.execute("INSERT INTO typing(user_id, wpm, accuracy, created_at) VALUES(?,?,?,?)", (uid, wpm, accuracy, now()))
        award_xp(uid, 4)
        st.session_state.type_start = None
        st.session_state.type_text = random.choice(TYPING)

def spark_view():
    page_head("✨", "Spark", "A small fact")
    st.markdown("<div class='nx-card'><b>" + random.choice(SPARKS) + "</b></div>", unsafe_allow_html=True)
    if st.button("Another fact"):
        st.rerun()

def main():
    theme = st.session_state.get("theme") or "cosmic"
    if st.session_state.user_id:
        with db() as conn:
            row = conn.execute("SELECT theme FROM users WHERE id = ?", (st.session_state.user_id,)).fetchone()
            if row and row["theme"]:
                theme = row["theme"]
                st.session_state.theme = theme
    apply_css(theme)
    if st.session_state.user_id is None:
        auth()
        return
    sidebar()
    pages = {
        "home": home, "chess": chess_view, "chat": chat_view, "echo": echo_view, "place": place_view,
        "tutor": tutor_view, "atlas": atlas_view, "notes": notes_view, "journal": journal_view,
        "dreams": dreams_view, "capsule": capsule_view, "habits": habits_view, "focus": focus_view,
        "mood": mood_view, "gratitude": gratitude_view, "wins": wins_view, "reading": reading_view,
        "quotes": quotes_view, "flash": flash_view, "breathe": breathe_view, "meditate": meditate_view,
        "water": water_view, "sleep": sleep_view, "workout": workout_view, "goals": goals_view,
        "coach": coach_view, "challenge": challenge_view, "studio": studio_view, "games": games_view,
        "search": search_view, "weekly": weekly_view, "decide": decide_view, "email": email_view,
        "resume": resume_view, "habitsuggest": habitsuggest_view, "leaderboard": leaderboard_view,
        "achievements": achievements_view, "stats": stats_view, "settings": settings_view,
        "tasks": tasks_view, "homework": homework_view, "exams": exams_view, "grades": grades_view,
        "vocab": vocab_view, "kindness": kindness_view, "money": money_view, "events": events_view,
        "bookmarks": bookmarks_view, "checks": checks_view, "riddle": riddle_view, "typing": typing_view,
        "spark": spark_view,
    }
    pages.get(st.session_state.view, home)()

main()
