"""
NEXUS ULTIMATE v3.0 — Complete Single-File App
Brain: Pollinations GPT-OSS 20B (free)
Run: streamlit run nexus.py
"""
import streamlit as st
import streamlit.components.v1
import sqlite3, hashlib, json, requests, base64, os, random, time, math
from datetime import datetime, timedelta, date
from contextlib import contextmanager

st.set_page_config(page_title="NEXUS ULTIMATE", page_icon="🧠",
                   layout="wide", initial_sidebar_state="expanded")

DB_FILE = "nexus.db"
UPLOAD_DIR = "echo_vault"
os.makedirs(UPLOAD_DIR, exist_ok=True)
OWNER_EMAILS = ["your-email@gmail.com"]

st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden;}
.stApp { background: linear-gradient(-45deg,#0a0a18,#1a1a3e,#2a1a4e,#0f1a3e,#0a0a18);
  background-size:400% 400%; animation: gradientFlow 25s ease infinite; }
@keyframes gradientFlow {0%{background-position:0% 50%;}50%{background-position:100% 50%;}100%{background-position:0% 50%;}}
.main {position:relative; z-index:2;}
.nexus-header {text-align:center; padding:14px 0 10px 0;}
.nexus-header h1 {font-family:'Georgia',serif; font-size:40px; font-weight:700;
  background: linear-gradient(135deg,#667eea,#f093fb,#ffd93d,#4dd0e1,#667eea);
  background-size:400% 400%; animation: gradientFlow 8s ease infinite;
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0;}
.nexus-header p {color:rgba(255,255,255,0.6); font-size:13px; margin-top:4px;}
.stat-card {background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(240,147,251,0.1));
  border:1px solid rgba(240,147,251,0.25); border-radius:14px; padding:14px; text-align:center;}
.stat-number {font-size:26px; font-weight:700;
  background: linear-gradient(135deg,#667eea,#f093fb);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-family:'Georgia',serif;}
.stat-label {font-size:11px; color:rgba(255,255,255,0.5); letter-spacing:2px; text-transform:uppercase; margin-top:4px;}
.module-tile {background: linear-gradient(135deg, rgba(102,126,234,0.22), rgba(240,147,251,0.15));
  border:1px solid rgba(240,147,251,0.35); border-radius:20px; padding:22px 16px; text-align:center;
  min-height:150px; display:flex; flex-direction:column; justify-content:center; align-items:center;
  transition:all 0.4s; box-shadow:0 10px 40px rgba(0,0,0,0.4);}
.module-tile:hover {transform: translateY(-8px) scale(1.03);}
.module-icon {font-size:40px; margin-bottom:8px;}
.module-title {font-size:15px; font-weight:700; color:#fff; font-family:'Georgia',serif;}
.module-desc {font-size:11px; color:rgba(255,255,255,0.6);}
.brain-card {background: linear-gradient(135deg, rgba(102,126,234,0.18), rgba(240,147,251,0.12));
  border:1px solid rgba(240,147,251,0.3); border-radius:16px; padding:18px; margin:10px 0;}
.brain-card .mood {font-size:20px; margin-bottom:6px;}
.brain-card .story {font-size:15px; line-height:1.6; margin:8px 0; color:rgba(255,255,255,0.92);}
.echo-memory {background: linear-gradient(135deg, rgba(102,126,234,0.15), rgba(77,208,225,0.1));
  border-left:4px solid #667eea; padding:14px 18px; border-radius:10px; margin:10px 0;}
.echo-says {background: linear-gradient(135deg, rgba(240,147,251,0.15), rgba(255,217,61,0.08));
  border-left:4px solid #f093fb; padding:14px 18px; border-radius:10px; margin:10px 0;}
.suggestion {background: linear-gradient(135deg, rgba(255,217,61,0.12), rgba(240,147,251,0.08));
  border:1px solid rgba(255,217,61,0.3); border-radius:12px; padding:12px 16px; margin:6px 0;
  display:flex; align-items:center; gap:12px;}
.rank-badge {display:inline-block; padding:4px 12px; border-radius:20px; font-size:11px;
  font-weight:700; letter-spacing:1px; text-transform:uppercase;}
.rank-bronze {background: linear-gradient(135deg,#cd7f32,#8b4513); color:white;}
.rank-silver {background: linear-gradient(135deg,#c0c0c0,#808080); color:white;}
.rank-gold {background: linear-gradient(135deg,#ffd700,#ff8c00); color:white;}
.rank-platinum {background: linear-gradient(135deg,#e5e4e2,#4dd0e1); color:#0a0a18;}
.rank-diamond {background: linear-gradient(135deg,#b9f2ff,#667eea); color:#0a0a18;}
.rank-legend {background: linear-gradient(135deg,#f093fb,#ffd93d); color:#0a0a18;}
.stButton > button {border-radius:12px; border:1px solid rgba(240,147,251,0.4);
  background: linear-gradient(135deg, rgba(102,126,234,0.3), rgba(240,147,251,0.2));
  color:white; font-weight:600; transition:all 0.3s;}
.stButton > button:hover {border-color:rgba(240,147,251,1); transform:translateY(-2px);}
</style>
""", unsafe_allow_html=True)

# ==================== DB ====================
@contextmanager
def db():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn; conn.commit()
    finally:
        conn.close()

def init_db():
    with db() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, name TEXT,
            is_owner INTEGER DEFAULT 0, xp INTEGER DEFAULT 0, streak INTEGER DEFAULT 0,
            last_active TEXT, rank TEXT DEFAULT 'Bronze', arena_wins INTEGER DEFAULT 0,
            arena_losses INTEGER DEFAULT 0, created_at TEXT NOT NULL)""")
        t = {
            "places":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT, created_at TEXT",
            "memories":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, place_id INTEGER NOT NULL, photo_path TEXT, ai_description TEXT, user_note TEXT, mood TEXT, created_at TEXT",
            "chats":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, created_at TEXT",
            "messages":"id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT",
            "notes":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, content TEXT, created_at TEXT",
            "journal":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, content TEXT, mood TEXT, created_at TEXT",
            "lessons":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, topic TEXT, steps TEXT, created_at TEXT",
            "repairs":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, device TEXT, problem TEXT, steps TEXT, created_at TEXT",
            "health_guides":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, symptoms TEXT, guide TEXT, created_at TEXT",
            "dreams":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, content TEXT, interpretation TEXT, dream_type TEXT, emotion TEXT, created_at TEXT",
            "capsules":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, message TEXT, unlock_date TEXT, opened INTEGER DEFAULT 0, created_at TEXT",
            "achievements":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, code TEXT, name TEXT, icon TEXT, unlocked_at TEXT",
            "matches":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, result TEXT, moves INTEGER, difficulty TEXT, created_at TEXT",
            "habits":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT, icon TEXT, streak INTEGER DEFAULT 0, last_done TEXT, created_at TEXT",
            "moods":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, mood TEXT, energy INTEGER, note TEXT, created_at TEXT",
            "focus":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, duration INTEGER, task TEXT, created_at TEXT",
            "gratitude":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, items TEXT, created_at TEXT",
            "wins":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, description TEXT, size TEXT, created_at TEXT",
            "reading":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, title TEXT, status TEXT DEFAULT 'Want to read', created_at TEXT",
            "quotes":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, quote TEXT, author TEXT, created_at TEXT",
            "flash":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, question TEXT, answer TEXT, created_at TEXT",
            "meditation":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, minutes INTEGER, note TEXT, created_at TEXT",
            "goals":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, objective TEXT, progress INTEGER DEFAULT 0, due_date TEXT, created_at TEXT",
            "challenges":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, challenge_date TEXT, challenge_text TEXT, completed INTEGER DEFAULT 0, created_at TEXT",
            "coach":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, role TEXT, content TEXT, created_at TEXT",
            "projects":"id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, name TEXT, description TEXT, stage TEXT DEFAULT 'idea', created_at TEXT",
        }
        for name, cols in t.items():
            c.execute(f"CREATE TABLE IF NOT EXISTS {name} ({cols})")

init_db()
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def is_owner(e): return e.lower() in [x.lower() for x in OWNER_EMAILS]

# ==================== XP ====================
def award_xp(uid, amount):
    with db() as conn:
        conn.execute("UPDATE users SET xp = xp + ? WHERE id = ?", (amount, uid))
        row = conn.execute("SELECT xp FROM users WHERE id=?", (uid,)).fetchone()
        conn.execute("UPDATE users SET rank=? WHERE id=?", (xp_to_rank(row["xp"]), uid))
    check_achievements(uid)

def xp_to_rank(xp):
    if xp>=5000: return "Legend"
    if xp>=2500: return "Diamond"
    if xp>=1000: return "Platinum"
    if xp>=500: return "Gold"
    if xp>=150: return "Silver"
    return "Bronze"

def rank_class(r):
    return {"Bronze":"rank-bronze","Silver":"rank-silver","Gold":"rank-gold",
            "Platinum":"rank-platinum","Diamond":"rank-diamond","Legend":"rank-legend"}.get(r,"rank-bronze")

def update_streak(uid):
    with db() as conn:
        u = conn.execute("SELECT streak, last_active FROM users WHERE id=?", (uid,)).fetchone()
        if not u: return
        today = datetime.now().date().isoformat()
        if u["last_active"] == today: return
        y = (datetime.now() - timedelta(days=1)).date().isoformat()
        s = (u["streak"] or 0) + 1 if u["last_active"] == y else 1
        conn.execute("UPDATE users SET streak=?, last_active=? WHERE id=?", (s, today, uid))

def greeting():
    h = datetime.now().hour
    if h<5: return "Still awake? 🌙"
    if h<12: return "Good morning ☀️"
    if h<17: return "Good afternoon 🌤️"
    if h<21: return "Good evening 🌆"
    return "Good night 🌙"

def celebrate():
    st.components.v1.html("""<script>(function(){const c=['#667eea','#f093fb','#ffd93d','#4dd0e1','#6bcb77','#ff6b6b'];
    for(let i=0;i<50;i++){const p=document.createElement('div');
    p.style.cssText='position:fixed;width:10px;height:10px;pointer-events:none;z-index:9999;top:-10vh;left:'+Math.random()*100+'vw;background:'+c[Math.floor(Math.random()*c.length)]+';border-radius:50%;animation:cf 2.5s linear forwards;';
    document.body.appendChild(p);setTimeout(()=>p.remove(),4000);}})();</script>
    <style>@keyframes cf{0%{transform:translateY(0) rotate(0);opacity:1;}100%{transform:translateY(120vh) rotate(720deg);opacity:0;}}</style>""", height=0)

def toast(msg):
    st.components.v1.html(f'<div style="position:fixed;top:20px;right:20px;background:linear-gradient(135deg,#667eea,#f093fb);color:white;padding:14px 20px;border-radius:12px;z-index:9999;font-weight:600;">{msg}</div>', height=0)

ACHIEVEMENTS = {
    "first_login":("First Step","You entered NEXUS","🌱"),
    "first_place":("Cartographer","Saved your first place","📍"),
    "first_note":("Thinker","Wrote your first note","📝"),
    "first_journal":("Reflector","Wrote first journal","📖"),
    "first_dream":("Dreamer","Interpreted first dream","🌙"),
    "first_capsule":("Time Traveler","Sealed first capsule","⏳"),
    "first_lesson":("Student","Completed a lesson","🎓"),
    "first_repair":("Fixer","Completed a repair","🔧"),
    "first_health":("Guardian","Got health guidance","💊"),
    "first_chess_win":("Gladiator","Won your first Chess match","♟️"),
    "chess_5_wins":("Champion","Won 5 Chess matches","🏆"),
    "streak_3":("Consistent","3-day streak","🔥"),
    "streak_7":("Committed","7-day streak","💎"),
    "xp_100":("Apprentice","100 XP","🥉"),
    "xp_500":("Adept","500 XP","🥈"),
    "xp_2000":("Master","2000 XP","🥇"),
    "first_gratitude":("Grateful","Logged gratitude","🙏"),
    "first_win":("Winner","Logged your first win","🏆"),
    "first_card":("Learner","Created flash card","🃏"),
    "first_meditation":("Zen","Completed meditation","🧘"),
    "challenge_1":("Challenger","Completed daily challenge","📅"),
    "coach_session":("Coached","Talked to your AI coach","🤖"),
}

def check_achievements(uid):
    with db() as conn:
        unlocked = {r["code"] for r in conn.execute("SELECT code FROM achievements WHERE user_id=?", (uid,)).fetchall()}
        checks = {"first_login": True}
        for code, tbl, n in [("first_place","places",1),("first_note","notes",1),
                              ("first_journal","journal",1),("first_dream","dreams",1),
                              ("first_capsule","capsules",1),("first_lesson","lessons",1),
                              ("first_repair","repairs",1),("first_health","health_guides",1),
                              ("first_gratitude","gratitude",1),("first_win","wins",1),
                              ("first_card","flash",1),("first_meditation","meditation",1)]:
            cnt = conn.execute(f"SELECT COUNT(*) as x FROM {tbl} WHERE user_id=?", (uid,)).fetchone()["x"]
            checks[code] = cnt >= n
        aw = conn.execute("SELECT COUNT(*) as x FROM matches WHERE user_id=? AND result='win'", (uid,)).fetchone()["x"]
        checks["first_chess_win"] = aw >= 1; checks["chess_5_wins"] = aw >= 5
        cc = conn.execute("SELECT COUNT(*) as x FROM challenges WHERE user_id=? AND completed=1", (uid,)).fetchone()["x"]
        checks["challenge_1"] = cc >= 1
        cl = conn.execute("SELECT COUNT(*) as x FROM coach WHERE user_id=?", (uid,)).fetchone()["x"]
        checks["coach_session"] = cl >= 1
        row = conn.execute("SELECT streak, xp FROM users WHERE id=?", (uid,)).fetchone()
        if row:
            checks["streak_3"]=row["streak"]>=3; checks["streak_7"]=row["streak"]>=7
            checks["xp_100"]=row["xp"]>=100; checks["xp_500"]=row["xp"]>=500; checks["xp_2000"]=row["xp"]>=2000
        new = []
        for code, ok in checks.items():
            if ok and code not in unlocked:
                name, desc, icon = ACHIEVEMENTS[code]
                conn.execute("INSERT INTO achievements (user_id,code,name,icon,unlocked_at) VALUES (?,?,?,?,?)",
                             (uid, code, name, icon, datetime.now().isoformat()))
                new.append((name, icon))
    for name, icon in new:
        toast(f"{icon} Achievement: {name}!")

# ==================== AI (POLLINATIONS BRAIN) ====================
def ai_chat(messages, temperature=0.7, timeout=45):
    try:
        r = requests.post("https://text.pollinations.ai/openai",
            json={"model":"openai","messages":messages,"temperature":temperature,"max_tokens":800},
            timeout=timeout)
        if r.status_code == 200:
            d = r.json()
            if d.get("choices") and d["choices"][0]["message"]["content"]:
                return d["choices"][0]["message"]["content"].strip()
    except: pass
    try:
        p = "".join(f"{m['role']}: {m['content']}\n" for m in messages) + "assistant:"
        r = requests.get(f"https://text.pollinations.ai/{requests.utils.quote(p[:1500])}", timeout=timeout)
        if r.status_code == 200 and len(r.text.strip()) > 3: return r.text.strip()
    except: pass
    return "⚠️ Brain is resting. Try again in a moment."

def ai_json(prompt, temp=0.6, timeout=45):
    r = ai_chat([{"role":"user","content":prompt}], temp, timeout)
    try:
        c = r.strip().replace("```json","").replace("```","").strip()
        s = c.find("{"); e = c.rfind("}")
        if s!=-1 and e!=-1: return json.loads(c[s:e+1])
    except: pass
    return None

def ai_quote():
    r = ai_chat([{"role":"user","content":"ONE short inspiring sentence (max 15 words). No quotes, no author."}])
    return r.strip().strip('"')[:120]

def ai_dream(text, uid):
    with db() as conn:
        past = [d["content"] for d in conn.execute("SELECT content FROM dreams WHERE user_id=? ORDER BY created_at DESC LIMIT 5",(uid,)).fetchall()]
    p = f"""Dream interpreter. DREAM: {text}
PAST: {'; '.join(past) or 'none'}
Return JSON: {{"dream_type":"","emotion":"","symbols":[],"meaning":"","message":"","action":""}}"""
    r = ai_json(p, 0.8)
    return r or {"dream_type":"Symbolic","emotion":"unknown","symbols":[],"meaning":"Dreams echo the heart.","message":"Keep dreaming.","action":"Notice today."}

def ai_photo(path):
    try:
        with open(path,"rb") as f: img = base64.b64encode(f.read()).decode()
        r = requests.post("https://text.pollinations.ai/openai",
            json={"model":"openai","messages":[{"role":"user","content":[
                {"type":"text","text":"Describe this place in one warm sentence under 25 words."},
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img}"}}]}],"temperature":0.7}, timeout=60)
        if r.status_code==200:
            d = r.json()
            if d.get("choices"): return d["choices"][0]["message"]["content"].strip()
    except: pass
    return "A place you've seen."

# ==================== CHESS ENGINE ====================
UNICODE = {'K':'♔','Q':'♕','R':'♖','B':'♗','N':'♘','P':'♙','k':'♚','q':'♛','r':'♜','b':'♝','n':'♞','p':'♟'}

def start_board():
    return [['r','n','b','q','k','b','n','r'],['p']*8,['.']*8,['.']*8,['.']*8,['.']*8,['P']*8,['R','N','B','Q','K','B','N','R']]

def is_white(p): return p != '.' and p.isupper()
def same_side(a,b): return (a.isupper() and b.isupper()) or (a.islower() and b.islower())
def on_board(r,c): return 0<=r<8 and 0<=c<8
def clone(b): return [row[:] for row in b]

def find_king(b, w):
    t = 'K' if w else 'k'
    for r in range(8):
        for c in range(8):
            if b[r][c]==t: return (r,c)
    return None

def pseudo(b, r, c, st):
    p = b[r][c]
    if p=='.': return []
    w = is_white(p); t = p.upper(); ms = []
    if t=='P':
        d = -1 if w else 1; sr = 6 if w else 1; pr = 0 if w else 7
        nr = r+d
        if on_board(nr,c) and b[nr][c]=='.':
            ms.append((nr,c,'promote' if nr==pr else ''))
            if r==sr and b[r+2*d][c]=='.': ms.append((r+2*d,c,'pawn_double'))
        for dc in (-1,1):
            nr,nc = r+d,c+dc
            if on_board(nr,nc) and b[nr][nc]!='.' and not same_side(p,b[nr][nc]):
                ms.append((nr,nc,'promote_capture' if nr==pr else 'capture'))
            ep = st.get('ep')
            if ep and (nr,nc)==ep: ms.append((nr,nc,'en_passant'))
    elif t=='N':
        for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr,nc = r+dr,c+dc
            if on_board(nr,nc) and (b[nr][nc]=='.' or not same_side(p,b[nr][nc])): ms.append((nr,nc,'capture' if b[nr][nc]!='.' else ''))
    elif t in ('B','R','Q'):
        dirs = {'B':[(-1,-1),(-1,1),(1,-1),(1,1)],'R':[(-1,0),(1,0),(0,-1),(0,1)],
                'Q':[(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]}[t]
        for dr,dc in dirs:
            for i in range(1,8):
                nr,nc = r+dr*i,c+dc*i
                if not on_board(nr,nc): break
                if b[nr][nc]=='.': ms.append((nr,nc,''))
                else:
                    if not same_side(p,b[nr][nc]): ms.append((nr,nc,'capture'))
                    break
    elif t=='K':
        for dr,dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            nr,nc = r+dr,c+dc
            if on_board(nr,nc) and (b[nr][nc]=='.' or not same_side(p,b[nr][nc])): ms.append((nr,nc,'capture' if b[nr][nc]!='.' else ''))
        cr = st.get('castling',{})
        if w:
            if cr.get('K') and b[7][5]=='.' and b[7][6]=='.' and b[7][7]=='R': ms.append((7,6,'castle_k'))
            if cr.get('Q') and b[7][3]=='.' and b[7][2]=='.' and b[7][1]=='.' and b[7][0]=='R': ms.append((7,2,'castle_q'))
        else:
            if cr.get('k') and b[0][5]=='.' and b[0][6]=='.' and b[0][7]=='r': ms.append((0,6,'castle_k'))
            if cr.get('q') and b[0][3]=='.' and b[0][2]=='.' and b[0][1]=='.' and b[0][0]=='r': ms.append((0,2,'castle_q'))
    return ms

def apply(b, st, fr, fc, tr, tc, sp):
    nb = clone(b); ns = dict(st); ns['castling'] = dict(st.get('castling',{'K':True,'Q':True,'k':True,'q':True})); ns['ep']=None
    p = nb[fr][fc]; w = is_white(p)
    if sp=='en_passant': nb[fr][tc]='.'
    nb[tr][tc]=p; nb[fr][fc]='.'
    if sp=='pawn_double': ns['ep']=((fr+tr)//2,fc)
    if sp in ('promote','promote_capture'): nb[tr][tc]='Q' if w else 'q'
    if sp=='castle_k': nb[tr][5]=nb[tr][7]; nb[tr][7]='.'
    if sp=='castle_q': nb[tr][3]=nb[tr][0]; nb[tr][0]='.'
    if p=='K': ns['castling']['K']=False; ns['castling']['Q']=False
    if p=='k': ns['castling']['k']=False; ns['castling']['q']=False
    if p=='R':
        if (fr,fc)==(7,0): ns['castling']['Q']=False
        if (fr,fc)==(7,7): ns['castling']['K']=False
    if p=='r':
        if (fr,fc)==(0,0): ns['castling']['q']=False
        if (fr,fc)==(0,7): ns['castling']['k']=False
    return nb, ns

def attacked(b, r, c, by_w):
    ap = 'P' if by_w else 'p'; pd = 1 if by_w else -1
    for dc in (-1,1):
        if on_board(r+pd,c+dc) and b[r+pd][c+dc]==ap: return True
    n = 'N' if by_w else 'n'
    for dr,dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        if on_board(r+dr,c+dc) and b[r+dr][c+dc]==n: return True
    k = 'K' if by_w else 'k'
    for dr,dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
        if on_board(r+dr,c+dc) and b[r+dr][c+dc]==k: return True
    for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        for i in range(1,8):
            nr,nc = r+dr*i,c+dc*i
            if not on_board(nr,nc): break
            p = b[nr][nc]
            if p=='.': continue
            if (by_w and p in 'RQ') or (not by_w and p in 'rq'): return True
            break
    for dr,dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        for i in range(1,8):
            nr,nc = r+dr*i,c+dc*i
            if not on_board(nr,nc): break
            p = b[nr][nc]
            if p=='.': continue
            if (by_w and p in 'BQ') or (not by_w and p in 'bq'): return True
            break
    return False

def in_check(b, w):
    kp = find_king(b, w)
    if not kp: return False
    return attacked(b, kp[0], kp[1], not w)

def legal(b, st, w):
    out = []
    for r in range(8):
        for c in range(8):
            p = b[r][c]
            if p=='.' or is_white(p)!=w: continue
            for tr,tc,sp in pseudo(b,r,c,st):
                nb, ns = apply(b,st,r,c,tr,tc,sp)
                if sp in ('castle_k','castle_q'):
                    row = 7 if w else 0
                    if in_check(b,w): continue
                    mids = [(row,5),(row,6)] if sp=='castle_k' else [(row,3),(row,2)]
                    if any(attacked(b,mr,mc,not w) for mr,mc in mids): continue
                if not in_check(nb,w): out.append((r,c,tr,tc,sp))
    return out

def has_legal(b, st, w): return len(legal(b,st,w)) > 0

def sq(r,c): return chr(ord('a')+c)+str(8-r)

def pval(p):
    return {'P':1,'N':3,'B':3,'R':5,'Q':9,'K':1000,'p':-1,'n':-3,'b':-3,'r':-5,'q':-9,'k':-1000}.get(p,0)

def evaluate(b):
    s = 0
    for r in range(8):
        for c in range(8):
            p = b[r][c]
            if p=='.': continue
            v = pval(p)
            if 2<=r<=5 and 2<=c<=5: v += 0.15 if p.isupper() else -0.15
            s += v
    return s

def minimax(b, st, d, a, beta, mx):
    if d==0: return evaluate(b), None
    ms = legal(b, st, mx)
    if not ms:
        if in_check(b,mx): return (10000 if not mx else -10000), None
        return 0, None
    ms.sort(key=lambda m: -abs(pval(b[m[2]][m[3]])) if b[m[2]][m[3]]!='.' else 0)
    best = None
    if mx:
        v = -math.inf
        for m in ms:
            nb, ns = apply(b,st,*m[:4],m[4])
            sc, _ = minimax(nb,ns,d-1,a,beta,False)
            if sc>v: v=sc; best=m
            a = max(a,v)
            if beta<=a: break
        return v, best
    else:
        v = math.inf
        for m in ms:
            nb, ns = apply(b,st,*m[:4],m[4])
            sc, _ = minimax(nb,ns,d-1,a,beta,True)
            if sc<v: v=sc; best=m
            beta = min(beta,v)
            if beta<=a: break
        return v, best

def ai_move(b, st, diff):
    d = {"easy":1,"medium":2,"hard":3}.get(diff,2)
    if diff=="easy" and random.random()<0.4:
        ms = legal(b,st,False)
        return random.choice(ms) if ms else None
    _, best = minimax(b, st, d, -math.inf, math.inf, False)
    return best

def san(b, st, mv):
    fr,fc,tr,tc,sp = mv
    p = b[fr][fc]
    if sp=='castle_k': return "O-O"
    if sp=='castle_q': return "O-O-O"
    s = "" if p.upper()=='P' else p.upper()
    if b[tr][tc]!='.':
        if p.upper()=='P': s += chr(ord('a')+fc)
        s += 'x'
    s += sq(tr,tc)
    if sp in ('promote','promote_capture'): s += "=Q"
    return s

# ==================== SESSION ====================
defaults = {"user_id":None,"name":None,"view":"home","current_place":None,
            "current_chat":None,"lesson":None,"repair":None,"health":None,
            "daily_quote":None,"chess":None,"focus_end":None,"focus_task":"","focus_min":25}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ==================== AUTH ====================
def auth_page():
    st.markdown("""
    <div style="text-align:center;padding:60px 0 30px 0;">
        <h1 style="font-family:'Georgia',serif;font-size:64px;
            background: linear-gradient(135deg,#667eea,#f093fb,#ffd93d,#4dd0e1,#667eea);
            background-size:400% 400%; animation: gradientFlow 8s ease infinite;
            -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0;">🧠 NEXUS ULTIMATE</h1>
        <p style="color:rgba(255,255,255,0.7);font-size:16px;margin-top:12px;">
            Powered by GPT-OSS 20B · Chess · Life OS</p>
    </div>
    """, unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1,1.2,1])
    with c2:
        t1, t2 = st.tabs(["🔐 Log In", "✨ Sign Up"])
        with t1:
            with st.form("login"):
                u = st.text_input("Username or Email"); p = st.text_input("Password", type="password")
                if st.form_submit_button("Log In", use_container_width=True):
                    with db() as conn:
                        row = conn.execute("SELECT id,name FROM users WHERE (username=? OR email=?) AND password_hash=?",
                                           (u,u,hash_pw(p))).fetchone()
                    if row:
                        st.session_state.user_id = row["id"]; st.session_state.name = row["name"] or u
                        update_streak(row["id"]); st.rerun()
                    else: st.error("Invalid login.")
        with t2:
            with st.form("signup"):
                n = st.text_input("Name"); u = st.text_input("Username"); e = st.text_input("Email")
                p = st.text_input("Password", type="password"); p2 = st.text_input("Confirm", type="password")
                if st.form_submit_button("Create", use_container_width=True):
                    if not u or not e or not p: st.error("Fill fields")
                    elif p != p2: st.error("Passwords don't match")
                    elif len(p) < 6: st.error("6+ chars")
                    else:
                        try:
                            with db() as conn:
                                conn.execute("""INSERT INTO users (username,email,password_hash,name,xp,streak,last_active,rank,created_at)
                                    VALUES (?,?,?,?,0,1,?,?,?)""",
                                    (u,e,hash_pw(p),n,datetime.now().date().isoformat(),"Bronze",datetime.now().isoformat()))
                            st.success("✅ Created! Log in.")
                        except sqlite3.IntegrityError: st.error("Taken.")

# ==================== SIDEBAR ====================
NAV = [("home","🏠","Home"),("chess","♟️","Chess"),("chat","💬","Chat"),
       ("echo","📸","ECHO"),("tutor","🎓","Tutor"),("atlas","🔧","ATLAS"),
       ("notes","📝","Notes"),("journal","📖","Journal"),("dreams","🌙","Dreams"),
       ("capsule","⏳","Capsule"),("habits","✅","Habits"),("focus","🎯","Focus"),
       ("mood","😊","Mood"),("gratitude","🙏","Gratitude"),("wins","🏆","Wins"),
       ("reading","📚","Reading"),("quotes","💬","Quotes"),("flash","🃏","Flash"),
       ("breathe","🫁","Breathe"),("meditate","🧘","Meditate"),("goals","🎯","Goals"),
       ("coach","🤖","AI Coach"),("challenge","📅","Challenge"),("studio","🏗️","Studio"),
       ("leaderboard","🏆","Leaderboard"),("achievements","🎖️","Awards"),("stats","📊","Stats")]

def sidebar():
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.name}")
        with db() as conn:
            u = conn.execute("SELECT xp,rank,streak FROM users WHERE id=?", (st.session_state.user_id,)).fetchone()
        st.markdown(f'<span class="rank-badge {rank_class(u["rank"])}">{u["rank"]}</span> {u["xp"]} XP · 🔥 {u["streak"]}',
                    unsafe_allow_html=True)
        st.divider()
        for vid, icon, label in NAV:
            active = "🟢 " if st.session_state.view == vid else ""
            if st.button(f"{active}{icon} {label}", key=f"n_{vid}", use_container_width=True):
                st.session_state.view = vid; st.rerun()
        st.divider()
        if st.button("🚪 Log out", use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

# ==================== HOME ====================
def home_view():
    uid = st.session_state.user_id
    with db() as conn:
        s = conn.execute("SELECT xp,streak,rank,arena_wins FROM users WHERE id=?", (uid,)).fetchone()
        ac = conn.execute("SELECT COUNT(*) as x FROM achievements WHERE user_id=?", (uid,)).fetchone()["x"]
    st.markdown(f'<div class="nexus-header"><h1>🧠 NEXUS ULTIMATE</h1>'
                f'<p>{greeting()}, {st.session_state.name} — '
                f'<span class="rank-badge {rank_class(s["rank"])}">{s["rank"]}</span></p></div>',
                unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f'<div class="stat-card"><div class="stat-number">{s["xp"]}</div><div class="stat-label">XP</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="stat-card"><div class="stat-number">🔥 {s["streak"]}</div><div class="stat-label">Streak</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="stat-card"><div class="stat-number">{ac}</div><div class="stat-label">Awards</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="stat-card"><div class="stat-number">{s["arena_wins"]}</div><div class="stat-label">Chess Wins</div></div>', unsafe_allow_html=True)
    if not st.session_state.daily_quote:
        with st.spinner("NEXUS whispers..."): st.session_state.daily_quote = ai_quote()
    st.markdown(f'<div class="brain-card"><div class="mood">✨ Today\'s whisper</div>'
                f'<div class="story"><em>{st.session_state.daily_quote}</em></div></div>', unsafe_allow_html=True)
    st.markdown("### 🚀 Rooms")
    mods = [("chess","♟️","Chess","Play NEXUS"),("echo","📸","ECHO","Remember places"),
            ("chat","💬","Chat","Talk freely"),("dreams","🌙","Dreams","Interpret"),
            ("journal","📖","Journal","Private diary"),("habits","✅","Habits","Build streaks"),
            ("mood","😊","Mood","Track feelings"),("focus","🎯","Focus","Pomodoro"),
            ("coach","🤖","Coach","AI guidance"),("studio","🏗️","Studio","Build products"),
            ("challenge","📅","Challenge","Today's task"),("goals","🎯","Goals","OKR tracker")]
    cols = st.columns(4)
    for i,(vid,icon,title,desc) in enumerate(mods):
        with cols[i%4]:
            st.markdown(f'<div class="module-tile"><div class="module-icon">{icon}</div>'
                        f'<div class="module-title">{title}</div><div class="module-desc">{desc}</div></div>',
                        unsafe_allow_html=True)
            if st.button("Open", key=f"o_{vid}", use_container_width=True):
                st.session_state.view = vid; st.rerun()

# ==================== CHESS ====================
def new_chess(diff="medium"):
    return {"board":start_board(),"state":{"castling":{"K":True,"Q":True,"k":True,"q":True},"ep":None},
            "turn":"white","history":[],"cap_w":[],"cap_b":[],"diff":diff,"last":None,
            "status":"playing","msg":None,"selected":None}

def board_html(g):
    b = g["board"]; sel = g.get("selected"); last = g.get("last")
    targets = []
    if sel:
        targets = [(m[2],m[3]) for m in legal(b,g["state"],True) if (m[0],m[1])==sel]
    chk = find_king(b, True) if in_check(b, True) else None
    h = '<div style="text-align:center;"><div style="display:inline-block;background:rgba(0,0,0,0.5);padding:10px;border-radius:14px;border:2px solid rgba(240,147,251,0.5);">'
    for r in range(8):
        h += '<div style="display:flex;">'
        for c in range(8):
            p = b[r][c]; light = (r+c)%2==0
            cls = "background:#ebd4b0;" if light else "background:#7a5230;"
            border = ""
            if sel==(r,c): border += "box-shadow:inset 0 0 0 4px #ffd93d;"
            if (r,c) in targets:
                if b[r][c]!='.': border += "box-shadow:inset 0 0 0 4px rgba(255,107,107,0.7);"
            if last and ((r,c)==(last[0],last[1]) or (r,c)==(last[2],last[3])):
                border += "box-shadow:inset 0 0 0 3px rgba(240,147,251,0.8);"
            if chk==(r,c): border += "box-shadow:inset 0 0 0 4px #ff4444;"
            glyph = ""
            if p!='.':
                color = "#fff" if p.isupper() else "#111"
                shadow = "0 1px 2px #000, 0 0 3px #000" if p.isupper() else "0 0 2px #fff"
                glyph = f'<span style="color:{color};text-shadow:{shadow};">{UNICODE[p]}</span>'
            h += f'<div style="width:54px;height:54px;display:flex;align-items:center;justify-content:center;font-size:34px;{cls}{border}">{glyph}</div>'
        h += '</div>'
    h += '</div></div>'
    return h

def chess_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>♟️ CHESS ARENA</h1><p>Real chess. Smart AI.</p></div>', unsafe_allow_html=True)
    if st.session_state.chess is None:
        c1, c2 = st.columns([2,1])
        with c1: diff = st.selectbox("Difficulty", ["easy","medium","hard"], index=1)
        with c2:
            if st.button("⚔️ Start Match", type="primary", use_container_width=True):
                st.session_state.chess = new_chess(diff); st.rerun()
        st.info("Click a white piece, then a destination. Full rules incl. castling, en passant, promotion.")
        return
    g = st.session_state.chess
    b = g["board"]
    c1, c2, c3 = st.columns([2,2,1])
    with c1:
        if g["status"]=="playing":
            lbl = "🟦 Your move" if g["turn"]=="white" else "🟥 NEXUS thinking…"
            if in_check(b, g["turn"]=="white"): lbl += " — CHECK!"
            st.markdown(f"**{lbl}**")
        elif g["status"]=="win": st.success("♔ Checkmate! You win!")
        elif g["status"]=="loss": st.error("♚ NEXUS wins.")
        elif g["status"]=="draw": st.info("½ Draw.")
    with c2: st.caption(f"Move {len(g['history'])//2+1} · {g['diff']}")
    with c3:
        if st.button("🔄 New", use_container_width=True): st.session_state.chess = None; st.rerun()
    if g["msg"]: st.markdown(f'<div class="echo-says">💬 <em>{g["msg"]}</em></div>', unsafe_allow_html=True)
    bc, pc = st.columns([2,1])
    with bc:
        st.markdown(board_html(g), unsafe_allow_html=True)
        if g["status"]=="playing" and g["turn"]=="white":
            st.markdown("##### Make your move")
            white = []
            for r in range(8):
                for c in range(8):
                    if is_white(b[r][c]):
                        ms = [m for m in legal(b,g["state"],True) if (m[0],m[1])==(r,c)]
                        if ms: white.append((r,c,b[r][c],ms))
            if not white: finish_chess(uid, "loss"); return
            opts = [f"{UNICODE[p]} {sq(r,c)}" for r,c,p,_ in white]
            i = st.selectbox("Piece", range(len(white)), format_func=lambda i: opts[i], key="cp")
            fr,fc,fp,moves = white[i]
            dests = [(m[2],m[3],m[4]) for m in moves]
            dl = []
            for tr,tc,sp in dests:
                tag = ""
                if b[tr][tc]!='.': tag = " ✕"
                if sp in ('promote','promote_capture'): tag += " ↑Q"
                if sp=='castle_k': tag = " O-O"
                if sp=='castle_q': tag = " O-O-O"
                if sp=='en_passant': tag = " e.p."
                dl.append(f"{sq(tr,tc)}{tag}")
            di = st.selectbox("To", range(len(dests)), format_func=lambda i: dl[i], key="cd")
            tr,tc,sp = dests[di]
            if st.button("✅ Play", type="primary", use_container_width=True):
                do_player(uid, fr, fc, tr, tc, sp); st.rerun()
    with pc:
        st.markdown("##### Captured")
        st.write("**You:**", " ".join(UNICODE[p] for p in g["cap_b"]) or "—")
        st.write("**NEXUS:**", " ".join(UNICODE[p] for p in g["cap_w"]) or "—")
        st.markdown("##### Moves")
        if g["history"]:
            rows = []; i = 0; num = 1
            while i < len(g["history"]):
                w = g["history"][i]; bk = g["history"][i+1] if i+1<len(g["history"]) else ""
                rows.append(f"{num:>2}. {w:<8} {bk}"); num += 1; i += 2
            st.markdown('<div style="max-height:240px;overflow-y:auto;background:rgba(0,0,0,0.35);border-radius:10px;padding:12px;font-family:monospace;font-size:13px;color:rgba(255,255,255,0.85);line-height:1.6;">' + "<br>".join(rows) + '</div>', unsafe_allow_html=True)
        if g["status"]=="playing" and g["turn"]=="white":
            if st.button("💡 Hint", use_container_width=True):
                with st.spinner("..."): best = ai_move(b, g["state"], g["diff"])
                if best: st.info(f"Try **{san(b,g['state'],best)}**")
    if g["status"]=="playing" and g["turn"]=="black":
        with st.spinner("NEXUS thinking…"):
            time.sleep(0.3)
            best = ai_move(b, g["state"], g["diff"])
        if best is None:
            finish_chess(uid, "loss" if in_check(b,False) else "draw"); return
        do_ai(uid, best); st.rerun()

def do_player(uid, fr, fc, tr, tc, sp):
    g = st.session_state.chess; b = g["board"]; stt = g["state"]
    cap = b[tr][tc]
    mv = (fr,fc,tr,tc,sp)
    s = san(b,stt,mv)
    nb, ns = apply(b,stt,fr,fc,tr,tc,sp)
    g["board"] = nb; g["state"] = ns; g["history"].append(s); g["last"] = (fr,fc,tr,tc); g["selected"] = None
    if cap!='.': g["cap_b"].append(cap)
    if not has_legal(nb,ns,False):
        finish_chess(uid, "win" if in_check(nb,False) else "draw"); return
    g["turn"] = "black"
    if cap!='.' or in_check(nb,False):
        try:
            g["msg"] = ai_chat([{"role":"user","content":f"You are NEXUS chess rival. Player played {s}. Capture:{cap!='.'} Check:{in_check(nb,False)}. Reply ONE short sentence (max 12 words)."}], 0.85, timeout=15)
        except: pass
    award_xp(uid, 2)

def do_ai(uid, mv):
    g = st.session_state.chess; b = g["board"]; stt = g["state"]
    fr,fc,tr,tc,sp = mv
    cap = b[tr][tc]
    s = san(b,stt,mv)
    nb, ns = apply(b,stt,fr,fc,tr,tc,sp)
    g["board"] = nb; g["state"] = ns; g["history"].append(s); g["last"] = (fr,fc,tr,tc)
    if cap!='.': g["cap_w"].append(cap)
    if not has_legal(nb,ns,True):
        finish_chess(uid, "loss" if in_check(nb,True) else "draw"); return
    g["turn"] = "white"

def finish_chess(uid, result):
    g = st.session_state.chess
    with db() as conn:
        conn.execute("INSERT INTO matches (user_id,result,moves,difficulty,created_at) VALUES (?,?,?,?,?)",
                     (uid, result, len(g["history"]), g["diff"], datetime.now().isoformat()))
        if result=="win": conn.execute("UPDATE users SET arena_wins=arena_wins+1 WHERE id=?", (uid,))
        else: conn.execute("UPDATE users SET arena_losses=arena_losses+1 WHERE id=?", (uid,))
    if result=="win": award_xp(uid, 40); celebrate(); toast("👑 +40 XP")
    else: award_xp(uid, 5)
    st.session_state.chess = None
    st.rerun()

# ==================== CHAT ====================
def chat_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>💬 AI CHAT</h1></div>', unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### Chats")
        if st.button("➕ New", use_container_width=True, key="new_chat"):
            with db() as conn:
                c = conn.execute("INSERT INTO chats (user_id,title,created_at) VALUES (?,?,?)", (uid,"New Chat",datetime.now().isoformat()))
                st.session_state.current_chat = c.lastrowid
            st.rerun()
    if st.session_state.current_chat is None:
        with db() as conn:
            row = conn.execute("SELECT id FROM chats WHERE user_id=? ORDER BY created_at DESC LIMIT 1", (uid,)).fetchone()
        if row: st.session_state.current_chat = row["id"]
        else:
            with db() as conn:
                c = conn.execute("INSERT INTO chats (user_id,title,created_at) VALUES (?,?,?)", (uid,"New Chat",datetime.now().isoformat()))
                st.session_state.current_chat = c.lastrowid
    cid = st.session_state.current_chat
    with db() as conn:
        msgs = conn.execute("SELECT * FROM messages WHERE chat_id=? ORDER BY id", (cid,)).fetchall()
    for m in msgs:
        with st.chat_message(m["role"]): st.write(m["content"])
    p = st.chat_input("Message NEXUS…")
    if p:
        with db() as conn:
            conn.execute("INSERT INTO messages (chat_id,role,content,created_at) VALUES (?,?,?,?)", (cid,"user",p,datetime.now().isoformat()))
            t = conn.execute("SELECT title FROM chats WHERE id=?", (cid,)).fetchone()
            if t and (t["title"]=="New Chat" or not t["title"]): conn.execute("UPDATE chats SET title=? WHERE id=?", (p[:40], cid))
        with st.chat_message("user"): st.write(p)
        with st.chat_message("assistant"):
            with st.spinner("NEXUS thinks…"):
                with db() as conn:
                    h = conn.execute("SELECT role,content FROM messages WHERE chat_id=? ORDER BY id", (cid,)).fetchall()
                api = [{"role":"system","content":"You are NEXUS. Warm, thoughtful, personal."}]
                for x in h[-20:]: api.append({"role":x["role"],"content":x["content"]})
                rep = ai_chat(api)
            st.write(rep)
        award_xp(uid, 2)
        with db() as conn:
            conn.execute("INSERT INTO messages (chat_id,role,content,created_at) VALUES (?,?,?,?)", (cid,"assistant",rep,datetime.now().isoformat()))
        st.rerun()

# ==================== ECHO ====================
def echo_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>📸 ECHO</h1><p>Snap. Remember. Watch change.</p></div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["📸 New", "🗺️ Timeline"])
    with t1:
        cam = st.camera_input("Take a photo")
        up = st.file_uploader("Or upload", type=["jpg","jpeg","png"])
        c1, c2 = st.columns(2)
        with c1:
            pn = st.text_input("Place name")
            feel = st.selectbox("Mood", ["Peaceful","Busy","Warm","Lonely","Joyful","Heavy","Bright","Quiet","Alive","Still"])
        with c2:
            note = st.text_area("Note (optional)", height=100)
        if st.button("💾 Save", type="primary", use_container_width=True):
            pb = cam.getvalue() if cam else (up.getvalue() if up else None)
            if not pb or not pn: st.error("Need photo + name")
            else:
                with st.spinner("ECHO seeing…"):
                    d = os.path.join(UPLOAD_DIR, str(uid)); os.makedirs(d, exist_ok=True)
                    fp = os.path.join(d, f"{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
                    with open(fp,"wb") as f: f.write(pb)
                    desc = ai_photo(fp)
                    if note: desc += f" — {note}"
                    with db() as conn:
                        pl = conn.execute("SELECT id FROM places WHERE user_id=? AND name=?", (uid,pn)).fetchone()
                        pid = pl["id"] if pl else conn.execute("INSERT INTO places (user_id,name,created_at) VALUES (?,?,?)",
                            (uid,pn,datetime.now().isoformat())).lastrowid
                        conn.execute("INSERT INTO memories (user_id,place_id,photo_path,ai_description,user_note,mood,created_at) VALUES (?,?,?,?,?,?,?)",
                                     (uid,pid,fp,desc,note,feel,datetime.now().isoformat()))
                    award_xp(uid, 15); celebrate(); toast("✅ +15 XP")
                st.rerun()
    with t2:
        with db() as conn:
            places = conn.execute("""SELECT p.id, p.name, COUNT(m.id) as visits FROM places p
                LEFT JOIN memories m ON m.place_id = p.id WHERE p.user_id=? GROUP BY p.id ORDER BY p.created_at DESC""", (uid,)).fetchall()
        if not places: st.info("No places yet.")
        for p in places:
            st.markdown(f'<div class="brain-card"><div class="mood">📍 {p["name"]}</div>'
                        f'<div class="story">{p["visits"]} visit(s)</div></div>', unsafe_allow_html=True)
            if st.button("View", key=f"vp_{p['id']}"):
                st.session_state.current_place = p["id"]; st.session_state.view = "place"; st.rerun()

def place_view():
    pid = st.session_state.current_place
    with db() as conn:
        pl = conn.execute("SELECT * FROM places WHERE id=?", (pid,)).fetchone()
        ms = conn.execute("SELECT * FROM memories WHERE place_id=? ORDER BY created_at DESC", (pid,)).fetchall()
    if not pl: st.session_state.view = "echo"; st.rerun(); return
    st.markdown(f'<div class="nexus-header"><h1>📍 {pl["name"]}</h1><p>{len(ms)} visit(s)</p></div>', unsafe_allow_html=True)
    if st.button("← Back"): st.session_state.view = "echo"; st.rerun()
    for i, m in enumerate(ms):
        with st.container(border=True):
            st.markdown(f"**Visit {len(ms)-i}** — {m['created_at'][:16]} · *{m['mood'] or '—'}*")
            c1, c2 = st.columns([1,3])
            with c1:
                if m["photo_path"] and os.path.exists(m["photo_path"]): st.image(m["photo_path"], use_container_width=True)
            with c2:
                if m["ai_description"]: st.write(f"👁️ {m['ai_description']}")
                if m["user_note"]: st.write(f"📝 {m['user_note']}")

# ==================== TUTOR ====================
def tutor_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🎓 TUTOR</h1></div>', unsafe_allow_html=True)
    with st.form("tut"):
        topic = st.text_input("Learn anything")
        if st.form_submit_button("🧠 Build Lesson", type="primary", use_container_width=True):
            if topic:
                with st.spinner("Building…"):
                    L = ai_json(f"Lesson on '{topic}'. JSON: {{\"title\":\"\",\"intro\":\"\",\"steps\":[{{\"n\":1,\"title\":\"\",\"instruction\":\"\"}}]}} 5-6 steps.", 0.6)
                if L:
                    with db() as conn:
                        conn.execute("INSERT INTO lessons (user_id,title,topic,steps,created_at) VALUES (?,?,?,?,?)",
                                     (uid, L.get("title",topic), topic, json.dumps(L), datetime.now().isoformat()))
                    st.session_state.lesson = L; award_xp(uid, 10); st.rerun()
    L = st.session_state.lesson
    if L:
        st.markdown(f"## 📖 {L.get('title','')}")
        st.info(L.get("intro",""))
        for s in L.get("steps", []):
            with st.expander(f"{s.get('n','•')}. {s.get('title','')}"): st.write(s.get("instruction",""))

# ==================== ATLAS ====================
def atlas_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🔧 ATLAS</h1></div>', unsafe_allow_html=True)
    mode = st.radio("Mode", ["🔧 Device Repair", "💊 Health Guide"], horizontal=True)
    if mode == "🔧 Device Repair":
        with st.form("rep"):
            d = st.text_input("Device"); p = st.text_area("Problem", height=80)
            if st.form_submit_button("🔧 Build Guide", type="primary", use_container_width=True):
                if d and p:
                    with st.spinner("..."):
                        g = ai_json(f"Repair {d}: {p}. JSON: {{\"title\":\"\",\"safety\":\"\",\"tools\":[],\"steps\":[{{\"n\":1,\"title\":\"\",\"instruction\":\"\"}}]}} 5-8 steps.", 0.5)
                    if g:
                        with db() as conn:
                            conn.execute("INSERT INTO repairs (user_id,device,problem,steps,created_at) VALUES (?,?,?,?,?)",
                                         (uid,d,p,json.dumps(g),datetime.now().isoformat()))
                        st.session_state.repair = g; award_xp(uid, 20); st.rerun()
        R = st.session_state.repair
        if R:
            st.markdown(f"## 🔧 {R.get('title','')}")
            if R.get("safety"): st.error(f"⚠️ {R['safety']}")
            if R.get("tools"): st.write("🧰 " + " · ".join(R["tools"]))
            for s in R.get("steps", []):
                st.markdown(f"### {s.get('n','•')}. {s.get('title','')}")
                st.write(s.get("instruction",""))
    else:
        with st.form("hl"):
            sy = st.text_area("Symptoms", height=100)
            ag = st.selectbox("Age", ["Baby","Child","Teen","Adult","Elderly"])
            if st.form_submit_button("💊 Guidance", type="primary", use_container_width=True):
                if sy:
                    with st.spinner("..."):
                        g = ai_json(f"Health guide. Symptoms: {sy}. Age: {ag}. JSON: {{\"title\":\"\",\"seriousness\":\"Mild/Moderate/Serious\",\"causes\":[],\"home_care\":[],\"warning_signs\":[],\"see_doctor\":\"\",\"safety\":\"Not a doctor\"}}", 0.4)
                    if g:
                        with db() as conn:
                            conn.execute("INSERT INTO health_guides (user_id,symptoms,guide,created_at) VALUES (?,?,?,?)",
                                         (uid,sy,json.dumps(g),datetime.now().isoformat()))
                        st.session_state.health = g; award_xp(uid, 10); st.rerun()
        H = st.session_state.health
        if H:
            st.markdown(f"## 💊 {H.get('title','')}")
            st.markdown(f"**{H.get('seriousness','')}**")
            if H.get("safety"): st.error(f"⚠️ {H['safety']}")
            st.subheader("Causes")
            for x in H.get("causes", []): st.write(f"• {x}")
            st.subheader("Home care")
            for x in H.get("home_care", []): st.write(f"• {x}")
            st.subheader("See doctor if")
            for x in H.get("warning_signs", []): st.write(f"🚨 {x}")

# ==================== NOTES ====================
def notes_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>📝 NOTES</h1></div>', unsafe_allow_html=True)
    with st.form("nt"):
        t = st.text_input("Title"); c = st.text_area("Note", height=140)
        if st.form_submit_button("💾 Save", type="primary", use_container_width=True):
            if c:
                with db() as conn:
                    conn.execute("INSERT INTO notes (user_id,title,content,created_at) VALUES (?,?,?,?)",
                                 (uid,t or c[:40],c,datetime.now().isoformat()))
                award_xp(uid, 5); st.rerun()
    with db() as conn:
        ns = conn.execute("SELECT * FROM notes WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    for n in ns:
        with st.expander(f"📝 {n['title']} — {n['created_at'][:16]}"): st.write(n["content"])

# ==================== JOURNAL ====================
def journal_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>📖 JOURNAL</h1></div>', unsafe_allow_html=True)
    with st.form("jr"):
        t = st.text_input("Title")
        mo = st.selectbox("Mood", ["😊 Happy","😌 Calm","🤔 Thoughtful","😔 Sad","😤 Frustrated","😴 Tired","🔥 Motivated","😐 Neutral"])
        c = st.text_area("Write…", height=180)
        if st.form_submit_button("📖 Save", type="primary", use_container_width=True):
            if c:
                with db() as conn:
                    conn.execute("INSERT INTO journal (user_id,title,content,mood,created_at) VALUES (?,?,?,?,?)",
                                 (uid,t or c[:40],c,mo,datetime.now().isoformat()))
                award_xp(uid, 8); st.rerun()
    with db() as conn:
        es = conn.execute("SELECT * FROM journal WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    for e in es:
        with st.expander(f"{e['mood']} {e['title']} — {e['created_at'][:16]}"):
            st.write(e["content"])
            if st.button("🤔 AI Reflect", key=f"r_{e['id']}"):
                with st.spinner("..."):
                    r = ai_chat([{"role":"system","content":"Warm journal companion. Empathetic reflection + one gentle question. Under 60 words."},
                                 {"role":"user","content":e["content"]}])
                st.info(f"💭 {r}")

# ==================== DREAMS ====================
def dreams_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🌙 DREAMS</h1></div>', unsafe_allow_html=True)
    with st.form("dr"):
        d = st.text_area("Describe your dream…", height=180)
        if st.form_submit_button("🌙 Interpret", type="primary", use_container_width=True):
            if d:
                with st.spinner("Reading…"): it = ai_dream(d, uid)
                with db() as conn:
                    conn.execute("INSERT INTO dreams (user_id,content,interpretation,dream_type,emotion,created_at) VALUES (?,?,?,?,?,?)",
                                 (uid,d,json.dumps(it),it.get("dream_type","Symbolic"),it.get("emotion","unknown"),datetime.now().isoformat()))
                award_xp(uid, 12); st.rerun()
    with db() as conn:
        ds = conn.execute("SELECT * FROM dreams WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    for d in ds:
        with st.expander(f"🌙 {d['created_at'][:16]} — {d['content'][:40]}…"):
            st.write(f"**Dream:** {d['content']}")
            try:
                i = json.loads(d["interpretation"])
                st.markdown(f'<div class="brain-card"><div class="mood">🌙 {i.get("dream_type","")} · 💭 {i.get("emotion","")}</div>'
                            f'<div class="story">{i.get("meaning","")}</div>'
                            f'<div class="story">✨ {i.get("message","")}</div>'
                            f'<div class="story">🎯 {i.get("action","")}</div></div>', unsafe_allow_html=True)
                if i.get("symbols"): st.write("**Symbols:** " + ", ".join(i["symbols"]))
            except: st.write(d["interpretation"])

# ==================== CAPSULE ====================
def capsule_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>⏳ CAPSULE</h1></div>', unsafe_allow_html=True)
    with st.form("cp"):
        m = st.text_area("Message to future you…", height=160)
        u = st.date_input("Open on", value=datetime.now().date() + timedelta(days=365))
        if st.form_submit_button("🔒 Seal", type="primary", use_container_width=True):
            if m:
                with db() as conn:
                    conn.execute("INSERT INTO capsules (user_id,message,unlock_date,created_at) VALUES (?,?,?,?)",
                                 (uid,m,str(u),datetime.now().isoformat()))
                award_xp(uid, 25); celebrate(); toast("⏳ +25 XP"); st.rerun()
    with db() as conn:
        cs = conn.execute("SELECT * FROM capsules WHERE user_id=? ORDER BY unlock_date", (uid,)).fetchall()
    for c in cs:
        try:
            ud = datetime.strptime(c["unlock_date"], "%Y-%m-%d").date()
            dl = (ud - datetime.now().date()).days
        except: dl = 999
        if dl <= 0 and not c["opened"]:
            st.success(f"🔓 Ready: {c['message']}")
            if st.button("Mark opened", key=f"o_{c['id']}"):
                with db() as conn:
                    conn.execute("UPDATE capsules SET opened=1 WHERE id=?", (c["id"],))
                st.rerun()
        else:
            st.caption(f"🔒 opens in {dl} days ({c['unlock_date']})")

# ==================== HABITS ====================
def habits_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>✅ HABITS</h1></div>', unsafe_allow_html=True)
    with st.form("hb"):
        n = st.text_input("Habit"); i = st.text_input("Emoji", value="✅")
        if st.form_submit_button("➕ Add", use_container_width=True):
            if n:
                with db() as conn:
                    conn.execute("INSERT INTO habits (user_id,name,icon,created_at) VALUES (?,?,?,?)",
                                 (uid,n,i,datetime.now().isoformat()))
                award_xp(uid, 3); st.rerun()
    today = datetime.now().date().isoformat()
    with db() as conn:
        hs = conn.execute("SELECT * FROM habits WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    for h in hs:
        c1, c2 = st.columns([3,1])
        with c1: st.markdown(f"**{h['icon']} {h['name']}** — 🔥 {h['streak']} days")
        with c2:
            if h["last_done"] == today: st.success("✅")
            else:
                if st.button("Mark", key=f"hd_{h['id']}"):
                    y = (datetime.now()-timedelta(days=1)).date().isoformat()
                    ns = (h["streak"] or 0)+1 if h["last_done"]==y else 1
                    with db() as conn:
                        conn.execute("UPDATE habits SET last_done=?,streak=? WHERE id=?", (today,ns,h["id"]))
                    award_xp(uid, 5); st.rerun()

# ==================== FOCUS ====================
def focus_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🎯 FOCUS</h1></div>', unsafe_allow_html=True)
    task = st.text_input("What are you focusing on?")
    dur = st.select_slider("Minutes", options=[5,10,15,25,30,45,60], value=25)
    if st.button("▶️ Start", type="primary", use_container_width=True):
        if not task: st.error("Name your task")
        else:
            st.session_state.focus_end = time.time() + dur*60
            st.session_state.focus_task = task; st.session_state.focus_min = dur
            st.rerun()
    if st.session_state.focus_end:
        rem = int(st.session_state.focus_end - time.time())
        if rem > 0:
            m, s = divmod(rem, 60)
            st.markdown(f'<div class="brain-card"><div class="mood">⏱️ {m:02d}:{s:02d}</div>'
                        f'<div class="story">Focus: <strong>{st.session_state.focus_task}</strong></div></div>',
                        unsafe_allow_html=True)
            if st.button("🔄 Refresh"): st.rerun()
        else:
            with db() as conn:
                conn.execute("INSERT INTO focus (user_id,duration,task,created_at) VALUES (?,?,?,?)",
                             (uid, st.session_state.focus_min, st.session_state.focus_task, datetime.now().isoformat()))
            award_xp(uid, st.session_state.focus_min)
            celebrate(); st.session_state.focus_end = None; st.rerun()

# ==================== MOOD ====================
def mood_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>😊 MOOD</h1></div>', unsafe_allow_html=True)
    with st.form("md"):
        mo = st.selectbox("Mood", ["😊 Happy","😌 Calm","🤔 Thoughtful","😔 Sad","😤 Frustrated","😴 Tired","🔥 Motivated","😐 Neutral"])
        en = st.slider("Energy", 1, 10, 5); note = st.text_input("Note")
        if st.form_submit_button("Log", type="primary", use_container_width=True):
            with db() as conn:
                conn.execute("INSERT INTO moods (user_id,mood,energy,note,created_at) VALUES (?,?,?,?,?)",
                             (uid,mo,en,note,datetime.now().isoformat()))
            award_xp(uid, 3); st.rerun()
    with db() as conn:
        ms = conn.execute("SELECT * FROM moods WHERE user_id=? ORDER BY created_at DESC LIMIT 30", (uid,)).fetchall()
    for m in ms:
        st.markdown(f'<div class="suggestion"><span class="icon">{m["mood"].split()[0]}</span>'
                    f'<span class="text"><strong>{m["created_at"][:16]}</strong> — Energy {m["energy"]}/10 {m["note"] or ""}</span></div>',
                    unsafe_allow_html=True)

# ==================== GRATITUDE ====================
def gratitude_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🙏 GRATITUDE</h1></div>', unsafe_allow_html=True)
    with st.form("gr"):
        items = st.text_area("Three things you're grateful for", height=140)
        if st.form_submit_button("💾 Save", type="primary", use_container_width=True):
            if items.strip():
                with db() as conn:
                    conn.execute("INSERT INTO gratitude (user_id,items,created_at) VALUES (?,?,?)",
                                 (uid,items,datetime.now().isoformat()))
                award_xp(uid, 5); st.rerun()
    with db() as conn:
        gs = conn.execute("SELECT * FROM gratitude WHERE user_id=? ORDER BY created_at DESC LIMIT 30", (uid,)).fetchall()
    for g in gs:
        with st.expander(f"🙏 {g['created_at'][:16]}"): st.write(g["items"])

# ==================== WINS ====================
def wins_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🏆 WINS</h1></div>', unsafe_allow_html=True)
    with st.form("wn"):
        d = st.text_input("What did you win?")
        sz = st.selectbox("Size", ["tiny","small","medium","big","massive"])
        if st.form_submit_button("➕ Log", type="primary", use_container_width=True):
            if d:
                with db() as conn:
                    conn.execute("INSERT INTO wins (user_id,description,size,created_at) VALUES (?,?,?,?)",
                                 (uid,d,sz,datetime.now().isoformat()))
                award_xp(uid, 4); st.rerun()
    with db() as conn:
        ws = conn.execute("SELECT * FROM wins WHERE user_id=? ORDER BY created_at DESC LIMIT 50", (uid,)).fetchall()
    emoji = {"tiny":"🐣","small":"✨","medium":"🌟","big":"🏆","massive":"👑"}
    for w in ws:
        st.markdown(f'<div class="suggestion"><span class="icon">{emoji.get(w["size"],"🏆")}</span>'
                    f'<span class="text"><strong>{w["created_at"][:10]}</strong> — {w["description"]}</span></div>',
                    unsafe_allow_html=True)

# ==================== READING ====================
def reading_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>📚 READING</h1></div>', unsafe_allow_html=True)
    with st.form("rd"):
        t = st.text_input("Title")
        s = st.selectbox("Status", ["Want to read","Reading","Finished"])
        if st.form_submit_button("➕ Add", use_container_width=True):
            if t:
                with db() as conn:
                    conn.execute("INSERT INTO reading (user_id,title,status,created_at) VALUES (?,?,?,?)",
                                 (uid,t,s,datetime.now().isoformat()))
                award_xp(uid, 3); st.rerun()
    with db() as conn:
        rs = conn.execute("SELECT * FROM reading WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    for r in rs:
        st.markdown(f'<div class="suggestion"><span class="icon">📖</span>'
                    f'<span class="text"><strong>{r["title"]}</strong> — {r["status"]}</span></div>',
                    unsafe_allow_html=True)

# ==================== QUOTES ====================
def quotes_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>💬 QUOTES</h1></div>', unsafe_allow_html=True)
    with st.form("qt"):
        q = st.text_area("Quote", height=80); a = st.text_input("Author")
        if st.form_submit_button("💾 Save", use_container_width=True):
            if q:
                with db() as conn:
                    conn.execute("INSERT INTO quotes (user_id,quote,author,created_at) VALUES (?,?,?,?)",
                                 (uid,q,a,datetime.now().isoformat()))
                award_xp(uid, 3); st.rerun()
    with db() as conn:
        qs = conn.execute("SELECT * FROM quotes WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    for q in qs:
        st.markdown(f'<div class="brain-card" style="text-align:center;"><div class="story">"{q["quote"]}"</div>'
                    f'<div style="font-size:13px;opacity:0.6;">— {q["author"] or "Unknown"}</div></div>',
                    unsafe_allow_html=True)

# ==================== FLASH CARDS ====================
def flash_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🃏 FLASH CARDS</h1></div>', unsafe_allow_html=True)
    with st.form("fc"):
        q = st.text_input("Question"); a = st.text_input("Answer")
        if st.form_submit_button("➕ Add", use_container_width=True):
            if q and a:
                with db() as conn:
                    conn.execute("INSERT INTO flash (user_id,question,answer,created_at) VALUES (?,?,?,?)",
                                 (uid,q,a,datetime.now().isoformat()))
                award_xp(uid, 3); st.rerun()
    with db() as conn:
        cs = conn.execute("SELECT * FROM flash WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    for c in cs:
        with st.expander(f"🃏 {c['question']}"):
            if st.button("👁️ Reveal", key=f"rv_{c['id']}"): st.success(c["answer"])

# ==================== BREATHE ====================
def breathe_view():
    st.markdown('<div class="nexus-header"><h1>🫁 BREATHE</h1></div>', unsafe_allow_html=True)
    st.markdown("### 4-7-8 Breathing — Inhale 4s · Hold 7s · Exhale 8s")
    st.components.v1.html("""
    <div style="text-align:center;padding:20px;">
        <div id="bc" style="width:180px;height:180px;margin:auto;border-radius:50%;
            background: linear-gradient(135deg,#667eea,#f093fb); display:flex; align-items:center; justify-content:center;
            color:white;font-size:20px;font-weight:700; transition: all 4s ease;">Ready</div>
        <button onclick="go()" style="margin-top:20px;padding:12px 28px;border-radius:12px;border:none;
            background:linear-gradient(135deg,#667eea,#f093fb);color:white;font-weight:700;cursor:pointer;font-size:15px;">Begin</button>
    </div>
    <script>
    function go(){
        const c = document.getElementById('bc');
        const phases = [{t:'Inhale',d:4000,s:1.4},{t:'Hold',d:7000,s:1.4},{t:'Exhale',d:8000,s:1.0}];
        let p = 0;
        function step(){
            if(p >= 3){ c.textContent='Done 🧘'; c.style.transform='scale(1)'; return; }
            const ph = phases[p];
            c.textContent = ph.t;
            c.style.transition = `all ${ph.d}ms ease`;
            c.style.transform = `scale(${ph.s})`;
            p++;
            setTimeout(step, ph.d);
        }
        step();
    }
    </script>
    """, height=280)

# ==================== MEDITATE ====================
def meditate_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🧘 MEDITATE</h1></div>', unsafe_allow_html=True)
    with st.form("mt"):
        m = st.slider("Minutes", 1, 60, 10); n = st.text_input("Note (optional)")
        if st.form_submit_button("🧘 Log session", type="primary", use_container_width=True):
            with db() as conn:
                conn.execute("INSERT INTO meditation (user_id,minutes,note,created_at) VALUES (?,?,?,?)",
                             (uid,m,n,datetime.now().isoformat()))
            award_xp(uid, m); celebrate(); st.rerun()
    with db() as conn:
        ms = conn.execute("SELECT * FROM meditation WHERE user_id=? ORDER BY created_at DESC LIMIT 20", (uid,)).fetchall()
    for m in ms:
        st.markdown(f'<div class="suggestion"><span class="icon">🧘</span>'
                    f'<span class="text">{m["minutes"]} min — {m["created_at"][:10]} {m["note"] or ""}</span></div>',
                    unsafe_allow_html=True)

# ==================== GOALS ====================
def goals_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🎯 GOALS</h1></div>', unsafe_allow_html=True)
    with st.form("gl"):
        o = st.text_input("Objective")
        d = st.date_input("Due date", value=datetime.now().date() + timedelta(days=30))
        if st.form_submit_button("➕ Add", use_container_width=True):
            if o:
                with db() as conn:
                    conn.execute("INSERT INTO goals (user_id,objective,progress,due_date,created_at) VALUES (?,?,?,?,?)",
                                 (uid,o,0,str(d),datetime.now().isoformat()))
                award_xp(uid, 5); st.rerun()
    with db() as conn:
        gs = conn.execute("SELECT * FROM goals WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    for g in gs:
        with st.container(border=True):
            st.markdown(f"### 🎯 {g['objective']}")
            st.caption(f"Due: {g['due_date']}")
            p = st.slider("Progress %", 0, 100, g["progress"] or 0, key=f"pr_{g['id']}")
            if p != (g["progress"] or 0):
                with db() as conn:
                    conn.execute("UPDATE goals SET progress=? WHERE id=?", (p,g["id"]))
                st.rerun()

# ==================== COACH ====================
def coach_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🤖 AI COACH</h1><p>Weekly check-in, guidance, accountability</p></div>', unsafe_allow_html=True)
    with db() as conn:
        logs = conn.execute("SELECT * FROM coach WHERE user_id=? ORDER BY id", (uid,)).fetchall()
    for m in logs:
        with st.chat_message(m["role"]): st.write(m["content"])
    p = st.chat_input("Talk to your coach…")
    if p:
        with db() as conn:
            conn.execute("INSERT INTO coach (user_id,role,content,created_at) VALUES (?,?,?,?)",
                         (uid,"user",p,datetime.now().isoformat()))
        with st.chat_message("user"): st.write(p)
        with st.chat_message("assistant"):
            with st.spinner("Coach listening…"):
                with db() as conn:
                    j = [x["mood"] for x in conn.execute("SELECT mood FROM journal WHERE user_id=? ORDER BY created_at DESC LIMIT 5", (uid,)).fetchall()]
                    w = [x["description"] for x in conn.execute("SELECT description FROM wins WHERE user_id=? ORDER BY created_at DESC LIMIT 5", (uid,)).fetchall()]
                    u = conn.execute("SELECT xp,streak FROM users WHERE id=?", (uid,)).fetchone()
                ctx = f"Moods: {', '.join(j) or 'none'}. Wins: {', '.join(w) or 'none'}. XP:{u['xp']} Streak:{u['streak']}."
                rep = ai_chat([{"role":"system","content":f"You are a warm, direct life coach. Ask 1 short follow-up question. {ctx}"},
                               {"role":"user","content":p}], 0.75)
            st.write(rep)
        award_xp(uid, 3)
        with db() as conn:
            conn.execute("INSERT INTO coach (user_id,role,content,created_at) VALUES (?,?,?,?)",
                         (uid,"assistant",rep,datetime.now().isoformat()))
        st.rerun()

# ==================== CHALLENGE ====================
POOL = ["Write 3 things you're grateful for","Take a photo of somewhere you pass daily",
        "Journal 5 min about today","Message someone you miss","Do one thing you've been putting off",
        "Write a note about something you learned","Take 10 slow breaths before bed","Read 15 minutes",
        "Do one kind thing for someone","Write tomorrow's most important task","Move for 20 minutes","Say no to something"]

def challenge_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>📅 DAILY CHALLENGE</h1></div>', unsafe_allow_html=True)
    today = datetime.now().date().isoformat()
    with db() as conn:
        ch = conn.execute("SELECT * FROM challenges WHERE user_id=? AND challenge_date=?", (uid,today)).fetchone()
        if not ch:
            t = random.choice(POOL)
            conn.execute("INSERT INTO challenges (user_id,challenge_date,challenge_text,created_at) VALUES (?,?,?,?)",
                         (uid,today,t,datetime.now().isoformat()))
            ch = conn.execute("SELECT * FROM challenges WHERE user_id=? AND challenge_date=?", (uid,today)).fetchone()
    st.markdown(f'<div class="brain-card"><div class="mood">📅 {today}</div>'
                f'<div class="story" style="font-size:20px;">{ch["challenge_text"]}</div></div>',
                unsafe_allow_html=True)
    if ch["completed"]: st.success("✅ Completed!")
    else:
        if st.button("✅ Mark Complete", type="primary", use_container_width=True):
            with db() as conn:
                conn.execute("UPDATE challenges SET completed=1 WHERE id=?", (ch["id"],))
            award_xp(uid, 30); celebrate(); st.rerun()

# ==================== STUDIO ====================
def studio_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🏗️ STUDIO</h1><p>Build products people want</p></div>', unsafe_allow_html=True)
    with st.form("pj"):
        n = st.text_input("Project name"); d = st.text_area("Description", height=60)
        if st.form_submit_button("➕ New Project", use_container_width=True):
            if n:
                with db() as conn:
                    conn.execute("INSERT INTO projects (user_id,name,description,created_at) VALUES (?,?,?,?)",
                                 (uid,n,d,datetime.now().isoformat()))
                award_xp(uid, 10); st.rerun()
    with db() as conn:
        ps = conn.execute("SELECT * FROM projects WHERE user_id=? ORDER BY created_at DESC", (uid,)).fetchall()
    if not ps: st.info("Create a project above."); return
    for p in ps:
        st.markdown(f'<div class="brain-card"><div class="mood">🏗️ {p["name"]}</div>'
                    f'<div class="story">{p["description"] or ""}</div>'
                    f'<div class="story">Stage: <strong>{p["stage"]}</strong></div></div>',
                    unsafe_allow_html=True)

# ==================== LEADERBOARD ====================
def leaderboard_view():
    st.markdown('<div class="nexus-header"><h1>🏆 LEADERBOARD</h1></div>', unsafe_allow_html=True)
    with db() as conn:
        us = conn.execute("SELECT name,username,xp,rank,streak,arena_wins FROM users ORDER BY xp DESC LIMIT 20").fetchall()
    for i, u in enumerate(us):
        medal = ["🥇","🥈","🥉"][i] if i < 3 else f"{i+1}."
        name = u["name"] or u["username"]
        st.markdown(f'<div class="suggestion"><span class="icon">{medal}</span>'
                    f'<span class="text"><strong>{name}</strong> — {u["xp"]} XP · '
                    f'<span class="rank-badge {rank_class(u["rank"])}">{u["rank"]}</span> '
                    f'♟️ {u["arena_wins"]}W · 🔥 {u["streak"]}</span></div>',
                    unsafe_allow_html=True)

# ==================== ACHIEVEMENTS ====================
def achievements_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>🎖️ AWARDS</h1></div>', unsafe_allow_html=True)
    with db() as conn:
        unlocked = {r["code"] for r in conn.execute("SELECT code FROM achievements WHERE user_id=?", (uid,)).fetchall()}
    for code,(name,desc,icon) in ACHIEVEMENTS.items():
        locked = code not in unlocked
        st.markdown(f'<div class="suggestion" style="opacity:{"0.4" if locked else "1"};">'
                    f'<span class="icon">{icon}</span><span class="text"><strong>{name}</strong> — {desc}</span></div>',
                    unsafe_allow_html=True)

# ==================== STATS ====================
def stats_view():
    uid = st.session_state.user_id
    st.markdown('<div class="nexus-header"><h1>📊 STATS</h1></div>', unsafe_allow_html=True)
    with db() as conn:
        for t in ["places","memories","notes","journal","dreams","capsules","lessons","repairs",
                  "health_guides","matches","habits","moods","focus","achievements","projects"]:
            try:
                n = conn.execute(f"SELECT COUNT(*) as x FROM {t} WHERE user_id=?", (uid,)).fetchone()["x"]
                st.metric(t.replace("_"," ").title(), n)
            except: pass
        u = conn.execute("SELECT xp,streak,rank,arena_wins,arena_losses FROM users WHERE id=?", (uid,)).fetchone()
    st.divider()
    st.markdown(f"**Rank:** {u['rank']} · **XP:** {u['xp']} · **Streak:** {u['streak']} · "
                f"**Chess:** {u['arena_wins']}W / {u['arena_losses']}L")

# ==================== ROUTER ====================
if st.session_state.user_id is None:
    auth_page()
else:
    sidebar()
    v = st.session_state.view
    {
        "home": home_view, "chess": chess_view, "chat": chat_view,
        "echo": echo_view, "place": place_view, "tutor": tutor_view,
        "atlas": atlas_view, "notes": notes_view, "journal": journal_view,
        "dreams": dreams_view, "capsule": capsule_view, "habits": habits_view,
        "focus": focus_view, "mood": mood_view, "gratitude": gratitude_view,
        "wins": wins_view, "reading": reading_view, "quotes": quotes_view,
        "flash": flash_view, "breathe": breathe_view, "meditate": meditate_view,
        "goals": goals_view, "coach": coach_view, "challenge": challenge_view,
        "studio": studio_view, "leaderboard": leaderboard_view,
        "achievements": achievements_view, "stats": stats_view,
    }.get(v, home_view)()
