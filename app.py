"""
SmithApp
Install: pip install streamlit requests pillow
Run:     streamlit run smithapp.py
"""
import base64, hashlib, html, io, json, math, os, random, sqlite3, time
from contextlib import contextmanager
from datetime import datetime, timedelta
from urllib.parse import quote

import requests
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageChops, ImageDraw

st.set_page_config(page_title="SmithApp", page_icon="💬", layout="wide")
DB, VAULT = "smith.db", "vault"
os.makedirs(VAULT, exist_ok=True)

SCHEMA = [
    "users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, name TEXT, pw TEXT, created TEXT)",
    "dm(id INTEGER PRIMARY KEY AUTOINCREMENT, sender INT, receiver INT, body TEXT, raw TEXT, seen INT DEFAULT 0, created TEXT)",
    "status(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, text TEXT, path TEXT, created TEXT)",
    "brain(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, role TEXT, content TEXT)",
    "facts(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, fact TEXT)",
    "notes(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, title TEXT, content TEXT, created TEXT)",
    "tasks(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, title TEXT, due TEXT, done INT DEFAULT 0)",
    "pros(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, name TEXT, skill TEXT, email TEXT, phone TEXT, area TEXT)",
    "ttt(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, result TEXT)",
    "chess(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, result TEXT, moves INT, diff TEXT)",
    "videos(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, title TEXT, descr TEXT, tags TEXT, cat TEXT, path TEXT, views INT DEFAULT 0, created TEXT)",
    "vreact(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, video_id INT)",
    "vcom(id INTEGER PRIMARY KEY AUTOINCREMENT, video_id INT, user_id INT, body TEXT, created TEXT)",
    "vhist(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, video_id INT)",
    "subs(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, channel_id INT)",
]

@contextmanager
def db():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()

with db() as c:
    for s in SCHEMA:
        c.execute("CREATE TABLE IF NOT EXISTS " + s)

def now(): return datetime.now().isoformat(timespec="seconds")

def hash_pw(pw, salt=None):
    salt = salt or os.urandom(16).hex()
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120000).hex()

def check_pw(pw, stored):
    salt, _ = stored.split("$", 1)
    return hash_pw(pw, salt) == stored

# ---------------- AI brain ----------------
API = "https://text.pollinations.ai/openai"

def ai(messages, temp=0.6, timeout=45):
    try:
        r = requests.post(API, json={"model": "openai", "messages": messages, "temperature": temp}, timeout=timeout)
        if r.ok:
            t = r.json()["choices"][0]["message"]["content"]
            if t and t.strip():
                return t.strip()
    except Exception:
        pass
    return None

def img_part(raw):
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    im.thumbnail((896, 896))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}}

def ai_json(prompt, images=None):
    text = prompt + " Reply with JSON only, no markdown."
    content = [{"type": "text", "text": text}] + [img_part(i) for i in images] if images else text
    raw = ai([{"role": "user", "content": content}])
    try:
        return json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
    except Exception:
        return None

def polish(text):
    out = ai([
        {"role": "system", "content": "Rewrite the user's message so it is clear, polite and professional. Keep the meaning, the language and roughly the length. Do not add facts. Return only the rewritten message."},
        {"role": "user", "content": text},
    ], temp=0.3, timeout=20)
    if out:
        return out
    t = text.strip()
    t = t[0].upper() + t[1:]
    return t if t[-1] in ".!?" else t + "."

# ---------------- helpers ----------------
def css():
    st.markdown("""<style>
    .stApp{background:#0b141a;color:#e9edef}
    .hero{background:linear-gradient(135deg,#00a884,#0b6e99);border-radius:16px;padding:16px 20px;color:#fff;margin-bottom:12px}
    .hero h1{margin:0;font-size:1.5rem}
    .card{background:#202c33;border-radius:14px;padding:12px 14px;margin-bottom:8px}
    .muted{color:#8696a0;font-size:.85rem}
    </style>""", unsafe_allow_html=True)

def head(icon, title, sub=""):
    st.markdown(f"<div class='hero'><h1>{icon} {title}</h1><div>{sub}</div></div>", unsafe_allow_html=True)

def pic(label, key):
    src = st.radio(label, ["Upload", "Camera"], horizontal=True, key=key + "_src")
    f = st.file_uploader(label, type=["jpg", "jpeg", "png"], key=key) if src == "Upload" else st.camera_input(label, key=key)
    return f.getvalue() if f else None

def save_pic(raw, uid):
    folder = os.path.join(VAULT, str(uid))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, datetime.now().strftime("%Y%m%d%H%M%S%f") + ".jpg")
    Image.open(io.BytesIO(raw)).convert("RGB").save(path, quality=85)
    return path

def users_other(uid):
    with db() as c:
        return c.execute("SELECT id, username, name FROM users WHERE id != ? ORDER BY name", (uid,)).fetchall()

def send_dm(sender, receiver, body, raw=None):
    with db() as c:
        c.execute("INSERT INTO dm(sender,receiver,body,raw,created) VALUES(?,?,?,?,?)", (sender, receiver, body, raw or body, now()))

# ---------------- auth ----------------
def auth():
    head("💬", "SmithApp", "Chat, call, watch, fix, and think with AI")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        t1, t2 = st.tabs(["Login", "Sign up"])
        with t1, st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                with db() as c:
                    row = c.execute("SELECT * FROM users WHERE username=?", (u.strip().lower(),)).fetchone()
                if row and check_pw(p, row["pw"]):
                    st.session_state.update(uid=row["id"], name=row["name"] or row["username"], theme=row["theme"] or "whatsapp"); upd_streak(row["id"]); check_ach(row["id"])
                    st.rerun()
                st.error("Wrong username or password.")
        with t2, st.form("signup"):
            n = st.text_input("Name")
            u = st.text_input("Username")
            p = st.text_input("Password (6+ characters)", type="password")
            if st.form_submit_button("Create account", use_container_width=True):
                if not u.strip() or len(p) < 6:
                    st.error("Add a username and a password of 6+ characters.")
                else:
                    try:
                        with db() as c:
                            c.execute("INSERT INTO users(username,name,pw,created) VALUES(?,?,?,?)", (u.strip().lower(), n, hash_pw(p), now()))
                        st.success("Account created. Log in.")
                    except sqlite3.IntegrityError:
                        st.error("Username taken.")

# ---------------- pages ----------------
def home():
    uid = st.session_state.uid
    head("🏠", "Hello, " + st.session_state.name, "Your day in one place")
    since = (datetime.now() - timedelta(hours=24)).isoformat()
    with db() as c:
        unread = c.execute("SELECT COUNT(*) x FROM dm WHERE receiver=? AND seen=0", (uid,)).fetchone()["x"]
        stat = c.execute("SELECT COUNT(*) x FROM status WHERE created>=? AND user_id!=?", (since, uid)).fetchone()["x"]
        tasks = c.execute("SELECT COUNT(*) x FROM tasks WHERE user_id=? AND done=0", (uid,)).fetchone()["x"]
    a, b, d = st.columns(3)
    a.metric("Unread messages", unread)
    b.metric("New statuses", stat)
    d.metric("Open tasks", tasks)

def chat():
    uid = st.session_state.uid
    head("💬", "Chats", "Every message can be polished by AI")
    others = users_other(uid)
    if not others:
        st.info("No one else has signed up yet. Ask a friend to create an account.")
        return
    labels = {o["id"]: (o["name"] or o["username"]) + " (@" + o["username"] + ")" for o in others}
    peer = st.selectbox("Chat with", list(labels), format_func=lambda i: labels[i])
    a, b = st.columns([1, 1])
    polish_on = a.toggle("✨ AI professional polish", value=True)
    audio = st.toggle("🎧 Voice only call", value=False)
    if b.button("📞 Start call", use_container_width=True):
        room = "smithapp-" + hashlib.sha256((str(min(uid, peer)) + "-" + str(max(uid, peer)) + "-smith").encode()).hexdigest()[:16]
        url = "https://meet.jit.si/" + room
        with db() as c:
            c.execute("INSERT INTO calls(caller,callee,url,audio,created) VALUES(?,?,?,?,?)", (uid, peer, url, int(audio), now()))
        send_dm(uid, peer, "📞 " + ("Voice" if audio else "Video") + " call started. Join: " + url)
        st.session_state.call = url
        st.session_state.call_audio = audio
    if st.session_state.get("call"):
        call_frame(st.session_state.call, st.session_state.get("call_audio", False))
        if st.button("End call view"):
            st.session_state.call = None
            st.rerun()

    def thread():
        with db() as c:
            c.execute("UPDATE dm SET seen=1 WHERE receiver=? AND sender=?", (uid, peer))
            rows = c.execute("SELECT * FROM dm WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?) ORDER BY id DESC LIMIT 60", (uid, peer, peer, uid)).fetchall()[::-1]
        for r in rows:
            with st.chat_message("user" if r["sender"] == uid else "assistant"):
                st.write(r["body"])
                if r["sender"] == uid and r["raw"] != r["body"]:
                    st.caption("✨ polished from: " + r["raw"])
                st.caption(r["created"][11:16])

    (st.fragment(run_every=4)(thread) if hasattr(st, "fragment") else thread)()
    with st.form("send", clear_on_submit=True):
        text = st.text_area("Message", height=80)
        if st.form_submit_button("Send", type="primary") and text.strip():
            with st.spinner("Polishing..." if polish_on else "Sending..."):
                body = polish(text) if polish_on else text.strip()
            send_dm(uid, peer, body, text.strip())
            st.rerun()

def status():
    uid = st.session_state.uid
    head("🟢", "Status", "Disappears after 24 hours")
    with st.form("st", clear_on_submit=True):
        text = st.text_input("What's happening?")
        raw = st.file_uploader("Photo (optional)", type=["jpg", "jpeg", "png"])
        if st.form_submit_button("Post status") and (text or raw):
            with db() as c:
                c.execute("INSERT INTO status(user_id,text,path,created) VALUES(?,?,?,?)", (uid, text, save_pic(raw.getvalue(), uid) if raw else None, now()))
            st.rerun()
    since = (datetime.now() - timedelta(hours=24)).isoformat()
    with db() as c:
        rows = c.execute("SELECT s.*, u.name, u.username FROM status s JOIN users u ON u.id=s.user_id WHERE s.created>=? ORDER BY s.id DESC", (since,)).fetchall()
    for r in rows:
        st.markdown(f"<div class='card'><b>{r['name'] or r['username']}</b> <span class='muted'>{r['created'][11:16]}</span></div>", unsafe_allow_html=True)
        if r["path"] and os.path.exists(r["path"]):
            st.image(r["path"], width=320)
        if r["text"]:
            st.write(r["text"])
        if r["user_id"] == uid and st.button("Delete", key="ds" + str(r["id"])):
            with db() as c:
                c.execute("DELETE FROM status WHERE id=?", (r["id"],))
            st.rerun()

def brain():
    uid = st.session_state.uid
    head("🧠", "Brain", "An AI that remembers you")
    with db() as c:
        facts = [r["fact"] for r in c.execute("SELECT fact FROM facts WHERE user_id=?", (uid,))]
        hist = c.execute("SELECT role, content FROM brain WHERE user_id=? ORDER BY id DESC LIMIT 14", (uid,)).fetchall()[::-1]
    with st.expander("What I remember (" + str(len(facts)) + ")"):
        st.write("\n".join("- " + f for f in facts) or "Nothing yet.")
        if facts and st.button("Forget everything"):
            with db() as c:
                c.execute("DELETE FROM facts WHERE user_id=?", (uid,))
            st.rerun()
    for m in hist:
        with st.chat_message(m["role"]):
            st.write(m["content"])
    q = st.chat_input("Ask anything")
    if q:
        sysmsg = "You are Smith Brain, a sharp, kind assistant. Be accurate and practical; say when unsure. What you know about the user: " + ("; ".join(facts) or "nothing yet") + "."
        reply = ai([{"role": "system", "content": sysmsg}] + [{"role": m["role"], "content": m["content"]} for m in hist] + [{"role": "user", "content": q}], timeout=60) or "I can't reach my AI service right now. Please try again."
        with db() as c:
            c.execute("INSERT INTO brain(user_id,role,content) VALUES(?,?,?)", (uid, "user", q))
            c.execute("INSERT INTO brain(user_id,role,content) VALUES(?,?,?)", (uid, "assistant", reply))
        if len(q) > 25:
            f = ai_json('From this message, extract one lasting personal fact worth remembering (name, goals, preferences) as {"fact":"..."}; use "" if none. Message: ' + q)
            if f and f.get("fact"):
                with db() as c:
                    c.execute("INSERT INTO facts(user_id,fact) VALUES(?,?)", (uid, str(f["fact"])[:200]))
        st.rerun()

def diff_image(a_raw, b_raw):
    a = Image.open(io.BytesIO(a_raw)).convert("RGB")
    a.thumbnail((800, 800))
    b = Image.open(io.BytesIO(b_raw)).convert("RGB").resize(a.size)
    n = 24
    d = ImageChops.difference(a, b).convert("L").resize((n, n), Image.BOX)
    out, draw, hits = b.copy(), ImageDraw.Draw(b.copy()), 0
    draw = ImageDraw.Draw(out)
    cw, ch = a.size[0] / n, a.size[1] / n
    for y in range(n):
        for x in range(n):
            if d.getpixel((x, y)) > 40:
                hits += 1
                draw.rectangle([x * cw, y * ch, (x + 1) * cw, (y + 1) * ch], outline=(255, 60, 60), width=2)
    return out, round(100 * hits / (n * n))

def echo():
    head("📸", "Echo", "Spot what changed or is missing between two photos")
    t1, t2 = st.tabs(["Compare two photos", "Identify one photo"])
    with t1:
        a_raw, b_raw = pic("Photo 1 (before)", "ea"), pic("Photo 2 (after)", "eb")
        if st.button("Compare", type="primary") and a_raw and b_raw:
            with st.spinner("Looking closely..."):
                marked, pct = diff_image(a_raw, b_raw)
                res = ai_json('You are given two photos of the same scene: photo 1 (before) then photo 2 (after). Identify objects in both. Return {"summary":"","missing":[],"added":[],"moved":[],"changed":[],"unsure":[]}. Be specific (colour, position). Only report what you can actually see.', [a_raw, b_raw])
            st.image(marked, caption="Red boxes: pixel changes in photo 2 (" + str(pct) + "% of the frame)")
            if res:
                st.subheader(res.get("summary", ""))
                for k, icon in (("missing", "❌ Missing"), ("added", "➕ New"), ("moved", "↔️ Moved"), ("changed", "🔄 Changed"), ("unsure", "❓ Not sure")):
                    if res.get(k):
                        st.markdown("**" + icon + "**\n" + "\n".join("- " + str(i) for i in res[k]))
            else:
                st.warning("AI vision is unreachable, so only the pixel comparison above is available.")
    with t2:
        raw = pic("Photo to identify", "ei")
        if st.button("Identify") and raw:
            with st.spinner("Thinking..."):
                res = ai([{"role": "user", "content": [{"type": "text", "text": "List every object you can recognise in this photo, then say what the scene is. Short and concrete."}, img_part(raw)]}], timeout=60)
            st.write(res or "AI vision is unreachable right now.")

def fixit():
    uid = st.session_state.uid
    head("🔧", "Fix-it", "Diagnose, then contact a technician")
    item = st.text_input("What is broken? (TV, phone, fridge, pipe...)")
    problem = st.text_area("What is happening?")
    raw = pic("Photo (optional)", "fx")
    if st.button("Diagnose", type="primary") and item and problem:
        with st.spinner("Diagnosing..."):
            r = ai_json('Home-repair triage for "' + item + '": ' + problem + '. Return {"likely_cause":"","safe_checks":[],"stop_if":[],"pro_skill":"","keywords":[]}. safe_checks must be harmless (no opening mains-powered devices, no gas, no chemicals). keywords are 2-4 words to match technicians.', [raw] if raw else None)
        st.session_state.fix = {"item": item, "problem": problem, "r": r or {"likely_cause": "Unknown", "safe_checks": ["Check power and cables.", "Restart it."], "stop_if": ["Smoke, burning smell, sparks, or water near power."], "pro_skill": item + " repair", "keywords": [item]}}
    fx = st.session_state.get("fix")
    if fx:
        r = fx["r"]
        st.markdown("**Likely cause:** " + str(r.get("likely_cause", "")))
        st.markdown("**Safe checks**\n" + "\n".join("- " + str(i) for i in r.get("safe_checks", [])))
        st.error("Stop and call a pro if: " + "; ".join(map(str, r.get("stop_if", []))))
        words = [w for w in (r.get("keywords", []) + [fx["item"], r.get("pro_skill", "")]) if w]
        q = " OR ".join(["skill LIKE ? OR name LIKE ?"] * len(words))
        args = [x for w in words for x in ("%" + w + "%", "%" + w + "%")]
        with db() as c:
            pros = c.execute("SELECT * FROM pros WHERE " + q, args).fetchall()
        st.subheader("Technicians in SmithApp")
        if not pros:
            st.info("No technician for this is registered yet. Share SmithApp with one and ask them to register below.")
        for p in pros:
            st.markdown(f"<div class='card'><b>{p['name']}</b> · {p['skill']}<div class='muted'>{p['area'] or ''} · {p['phone'] or ''}</div>{p['email'] or ''}</div>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            subj, body = quote("Repair request: " + fx["item"]), quote(fx["problem"])
            c1.link_button("✉️ Email", "mailto:" + (p["email"] or "") + "?subject=" + subj + "&body=" + body)
            if p["user_id"] != uid and c2.button("💬 Message in app", key="pm" + str(p["id"])):
                send_dm(uid, p["user_id"], "Hello, I need help with my " + fx["item"] + ": " + fx["problem"])
                st.success("Sent. Find the reply in Chats.")
    with st.expander("I'm a technician: list me"):
        with st.form("pro"):
            n, s = st.text_input("Business or name"), st.text_input("Skills (e.g. television, phone, plumbing)")
            e, p, a = st.text_input("Email"), st.text_input("Phone"), st.text_input("Area")
            if st.form_submit_button("Register") and n and s and e:
                with db() as c:
                    c.execute("INSERT INTO pros(user_id,name,skill,email,phone,area) VALUES(?,?,?,?,?,?)", (uid, n, s, e, p, a))
                st.success("Listed.")

@st.cache_data(ttl=600)
def film_search(q):
    qs = "mediatype:movies AND (collection:feature_films OR collection:moviesandfilms)" + (" AND title:(" + q + ")" if q else "")
    try:
        r = requests.get("https://archive.org/advancedsearch.php", params={"q": qs, "fl[]": ["identifier", "title", "year"], "sort[]": "downloads desc", "rows": 12, "output": "json"}, timeout=20)
        return r.json()["response"]["docs"]
    except Exception:
        return []

@st.cache_data(ttl=3600)
def film_file(ident):
    try:
        files = requests.get("https://archive.org/metadata/" + ident, timeout=20).json().get("files", [])
        for f in files:
            if f["name"].lower().endswith(".mp4"):
                return "https://archive.org/download/" + ident + "/" + quote(f["name"])
    except Exception:
        pass
    return None

def films_archive():
    q = st.text_input("Search films")
    for d in film_search(q.strip()):
        i = d["identifier"]
        with st.expander(str(d.get("title", i)) + " (" + str(d.get("year", "?")) + ")"):
            if st.button("▶ Watch", key="w" + i):
                st.session_state.watch = i
            if st.session_state.get("watch") == i:
                components.iframe("https://archive.org/embed/" + i, height=420)
            url = film_file(i)
            st.link_button("⬇ Download", url or "https://archive.org/details/" + i)

def win(b):
    for x, y, z in [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]:
        if b[x] == b[y] == b[z] != " ":
            return b[x]

def ttt_ai(b):
    empty = [i for i, v in enumerate(b) if v == " "]
    if random.random() < 0.35:  # deliberate blunder
        return random.choice(empty)
    for mark, chance in (("O", 1.0), ("X", 0.6)):  # win always, block only 60%
        if random.random() <= chance:
            for i in empty:
                b[i] = mark
                hit = win(b) == mark
                b[i] = " "
                if hit:
                    return i
    if b[4] == " " and random.random() < 0.6:
        return 4
    return random.choice(empty)

def ttt_game():
    uid = st.session_state.uid
    pass
    g = st.session_state.setdefault("ttt", {"b": [" "] * 9, "msg": ""})
    cols = st.columns(3)
    for i in range(9):
        if cols[i % 3].button(g["b"][i] if g["b"][i] != " " else "·", key="t" + str(i), use_container_width=True) and not g["msg"] and g["b"][i] == " ":
            g["b"][i] = "X"
            if not win(g["b"]) and " " in g["b"]:
                g["b"][ttt_ai(g["b"])] = "O"
            w = win(g["b"])
            if w or " " not in g["b"]:
                g["msg"] = "You win! 🎉" if w == "X" else "AI wins" if w == "O" else "Draw"
                with db() as c:
                    c.execute("INSERT INTO ttt(user_id,result) VALUES(?,?)", (uid, "win" if w == "X" else "loss" if w else "draw"))
                award_xp(uid, 12 if w == "X" else 2)
            st.rerun()
    if g["msg"]:
        st.info(g["msg"])
    if st.button("New game"):
        st.session_state.ttt = None
        st.rerun()
    with db() as c:
        rec = {r["result"]: r["n"] for r in c.execute("SELECT result, COUNT(*) n FROM ttt WHERE user_id=? GROUP BY result", (uid,))}
    st.caption(f"Record: {rec.get('win', 0)}W · {rec.get('loss', 0)}L · {rec.get('draw', 0)}D")

def notes():
    uid = st.session_state.uid
    head("📝", "Notes & tasks")
    t1, t2 = st.tabs(["Notes", "Tasks"])
    with t1:
        with st.form("n", clear_on_submit=True):
            title, body = st.text_input("Title"), st.text_area("Note")
            if st.form_submit_button("Save") and body:
                with db() as c:
                    c.execute("INSERT INTO notes(user_id,title,content,created) VALUES(?,?,?,?)", (uid, title or body[:40], body, now()))
                st.rerun()
        with db() as c:
            rows = c.execute("SELECT * FROM notes WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
        for r in rows:
            with st.expander(r["title"]):
                st.write(r["content"])
    with t2:
        with st.form("t", clear_on_submit=True):
            title, due = st.text_input("Task"), st.date_input("Due")
            if st.form_submit_button("Add") and title:
                with db() as c:
                    c.execute("INSERT INTO tasks(user_id,title,due) VALUES(?,?,?)", (uid, title, str(due)))
                st.rerun()
        with db() as c:
            rows = c.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY done, due", (uid,)).fetchall()
        for r in rows:
            c1, c2 = st.columns([5, 1])
            c1.write(("✅ " if r["done"] else "⬜ ") + r["title"] + " · " + r["due"])
            if not r["done"] and c2.button("Done", key="d" + str(r["id"])):
                with db() as c:
                    c.execute("UPDATE tasks SET done=1 WHERE id=?", (r["id"],))
                st.rerun()

def settings():
    uid = st.session_state.uid
    head("⚙️", "Settings")
    name = st.text_input("Display name", value=st.session_state.name)
    if st.button("Save name"):
        with db() as c:
            c.execute("UPDATE users SET name=? WHERE id=?", (name, uid))
        st.session_state.name = name
        st.success("Saved.")
    old, new = st.text_input("Current password", type="password"), st.text_input("New password", type="password")
    if st.button("Change password"):
        with db() as c:
            row = c.execute("SELECT pw FROM users WHERE id=?", (uid,)).fetchone()
            if not check_pw(old, row["pw"]) or len(new) < 6:
                st.error("Wrong current password, or new one is under 6 characters.")
            else:
                c.execute("UPDATE users SET pw=? WHERE id=?", (hash_pw(new), uid))
                st.success("Updated.")
    st.divider()
    if st.text_input("Type DELETE to erase your account") == "DELETE" and st.button("Delete account"):
        with db() as c:
            for t, col in (("dm", "sender"), ("dm", "receiver"), ("status", "user_id"), ("brain", "user_id"), ("facts", "user_id"), ("notes", "user_id"), ("tasks", "user_id"), ("pros", "user_id"), ("ttt", "user_id"), ("chess", "user_id"), ("videos", "user_id"), ("vreact", "user_id"), ("vcom", "user_id"), ("vhist", "user_id"), ("subs", "user_id")) + tuple((k, "user_id") for k in LOGS):
                c.execute(f"DELETE FROM {t} WHERE {col}=?", (uid,))
            c.execute("DELETE FROM users WHERE id=?", (uid,))
        st.session_state.clear()
        st.rerun()

# ======================= CHESS =======================
UNI = {k: g + "\ufe0e" for k, g in zip("KQRBNPkqrbnp", "♚♛♜♝♞♟♚♛♜♝♞♟")}
PV = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000}
KN = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
RD = ((-1, 0), (1, 0), (0, -1), (0, 1))
BD = ((-1, -1), (-1, 1), (1, -1), (1, 1))

def inb(r, c): return 0 <= r < 8 and 0 <= c < 8
def mine_(p, q): return q != "." and p.isupper() == q.isupper()
def sq(r, c): return chr(97 + c) + str(8 - r)

def find_king(b, w):
    t = "K" if w else "k"
    return next(((r, c) for r in range(8) for c in range(8) if b[r][c] == t), None)

def pseudo(b, r, c, s):
    p = b[r][c]; w = p.isupper(); k = p.upper(); out = []
    if k == "P":
        d = -1 if w else 1; pr = 0 if w else 7
        if inb(r + d, c) and b[r + d][c] == ".":
            out.append((r + d, c, "promo" if r + d == pr else ""))
            if r == (6 if w else 1) and b[r + 2 * d][c] == ".":
                out.append((r + 2 * d, c, "double"))
        for dc in (-1, 1):
            nr, nc = r + d, c + dc
            if not inb(nr, nc):
                continue
            if b[nr][nc] != "." and not mine_(p, b[nr][nc]):
                out.append((nr, nc, "promo" if nr == pr else ""))
            elif b[nr][nc] == "." and s.get("ep") == (nr, nc):
                out.append((nr, nc, "ep"))
    elif k in "NK":
        for a, e in (KN if k == "N" else RD + BD):
            nr, nc = r + a, c + e
            if inb(nr, nc) and not mine_(p, b[nr][nc]):
                out.append((nr, nc, ""))
        if k == "K":
            row = 7 if w else 0; cs = s.get("castling") or {}; rk = "R" if w else "r"
            if r == row and c == 4:
                if cs.get("K" if w else "k") and b[row][5] == b[row][6] == "." and b[row][7] == rk:
                    out.append((row, 6, "ck"))
                if cs.get("Q" if w else "q") and b[row][1] == b[row][2] == b[row][3] == "." and b[row][0] == rk:
                    out.append((row, 2, "cq"))
    else:
        for a, e in {"B": BD, "R": RD, "Q": RD + BD}[k]:
            nr, nc = r + a, c + e
            while inb(nr, nc):
                if b[nr][nc] == ".":
                    out.append((nr, nc, ""))
                else:
                    if not mine_(p, b[nr][nc]):
                        out.append((nr, nc, ""))
                    break
                nr += a; nc += e
    return out

def apply(b, s, fr, fc, tr, tc, sp):
    nb = [row[:] for row in b]
    cs = dict(s.get("castling") or {"K": 1, "Q": 1, "k": 1, "q": 1})
    p = nb[fr][fc]; w = p.isupper()
    if sp == "ep": nb[fr][tc] = "."
    nb[tr][tc] = p; nb[fr][fc] = "."
    if sp == "promo": nb[tr][tc] = "Q" if w else "q"
    if sp == "ck": nb[tr][5], nb[tr][7] = nb[tr][7], "."
    if sp == "cq": nb[tr][3], nb[tr][0] = nb[tr][0], "."
    if p in "Kk": cs.update({"K": 0, "Q": 0} if w else {"k": 0, "q": 0})
    for q_, fl in (((7, 0), "Q"), ((7, 7), "K"), ((0, 0), "q"), ((0, 7), "k")):
        if (fr, fc) == q_ or (tr, tc) == q_:
            cs[fl] = 0
    return nb, {"castling": cs, "ep": ((fr + tr) // 2, fc) if sp == "double" else None}

def attacked(b, r, c, byw):
    pw, n, k, rq, bq = ("P", "N", "K", "RQ", "BQ") if byw else ("p", "n", "k", "rq", "bq")
    d = 1 if byw else -1
    for dc in (-1, 1):
        if inb(r + d, c + dc) and b[r + d][c + dc] == pw: return True
    for a, e in KN:
        if inb(r + a, c + e) and b[r + a][c + e] == n: return True
    for a, e in RD + BD:
        if inb(r + a, c + e) and b[r + a][c + e] == k: return True
    for dirs, ps in ((RD, rq), (BD, bq)):
        for a, e in dirs:
            nr, nc = r + a, c + e
            while inb(nr, nc):
                if b[nr][nc] != ".":
                    if b[nr][nc] in ps: return True
                    break
                nr += a; nc += e
    return False

def in_check(b, w):
    k = find_king(b, w)
    return bool(k and attacked(b, k[0], k[1], not w))

def legal(b, s, w):
    out = []
    for r in range(8):
        for c in range(8):
            p = b[r][c]
            if p == "." or p.isupper() != w:
                continue
            for tr, tc, sp in pseudo(b, r, c, s):
                if sp in ("ck", "cq"):
                    row = 7 if w else 0
                    if any(attacked(b, row, x, not w) for x in ((4, 5, 6) if sp == "ck" else (4, 3, 2))):
                        continue
                nb, _ = apply(b, s, r, c, tr, tc, sp)
                if not in_check(nb, w):
                    out.append((r, c, tr, tc, sp))
    return out

def evalb(b):
    sc = 0
    for r in range(8):
        for c in range(8):
            p = b[r][c]
            if p != ".":
                v = PV[p.upper()] + (12 if 2 <= r <= 5 and 2 <= c <= 5 else 0)
                sc += v if p.isupper() else -v
    return sc

def minimax(b, s, d, al, be, w):
    if d == 0:
        return evalb(b), None
    ms = legal(b, s, w)
    if not ms:
        return (0 if not in_check(b, w) else (-1e5 - d if w else 1e5 + d)), None
    ms.sort(key=lambda m: -PV.get(b[m[2]][m[3]].upper(), 0))
    best, val = None, (-math.inf if w else math.inf)
    for m in ms:
        nb, ns = apply(b, s, *m)
        sc, _ = minimax(nb, ns, d - 1, al, be, not w)
        if (sc > val) if w else (sc < val):
            val, best = sc, m
        al, be = (max(al, val), be) if w else (al, min(be, val))
        if be <= al:
            break
    return val, best

def chess_ai(b, s, diff):
    ms = legal(b, s, False)
    if not ms: return None
    if diff == "easy" and random.random() < 0.45: return random.choice(ms)
    return minimax(b, s, {"easy": 1, "medium": 2, "hard": 3}[diff], -math.inf, math.inf, False)[1] or random.choice(ms)

def san(b, m):
    fr, fc, tr, tc, sp = m; p = b[fr][fc]
    if sp == "ck": return "O-O"
    if sp == "cq": return "O-O-O"
    cap = b[tr][tc] != "." or sp == "ep"; pawn = p.upper() == "P"
    return ("" if pawn else p.upper()) + (chr(97 + fc) if cap and pawn else "") + ("x" if cap else "") + sq(tr, tc) + ("=Q" if sp == "promo" else "")

def board_html(g):
    b, last = g["board"], g["last"]
    chk = [find_king(b, w) for w in (True, False) if in_check(b, w)]
    h = "<div style='line-height:0'>"
    for r in range(8):
        h += "<div>"
        for c in range(8):
            hl = ""
            if last and (r, c) in ((last[0], last[1]), (last[2], last[3])): hl = "box-shadow:inset 0 0 0 3px #00a884;"
            if (r, c) in chk: hl = "box-shadow:inset 0 0 0 4px #ff5a5a;"
            col = "#fff;text-shadow:0 0 2px #000,0 0 2px #000" if b[r][c].isupper() else "#000"
            h += f"<span style='width:40px;height:40px;display:inline-flex;align-items:center;justify-content:center;font-size:27px;background:{'#f0d9b5' if (r + c) % 2 == 0 else '#b58863'};{hl}color:{col}'>{UNI.get(b[r][c], '')}</span>"
        h += "</div>"
    return h + "</div>"

def chess():
    uid = st.session_state.uid
    head("♟️", "Chess", "Castling, en passant, promotion, check and mate")
    g = st.session_state.get("chess")
    if not g:
        d = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
        if st.button("Start game", type="primary"):
            st.session_state.chess = {"board": [list("rnbqkbnr"), list("pppppppp")] + [["."] * 8 for _ in range(4)] + [list("PPPPPPPP"), list("RNBQKBNR")],
                                      "state": {"castling": {"K": 1, "Q": 1, "k": 1, "q": 1}, "ep": None}, "turn": "w", "hist": [], "capw": [], "capb": [], "diff": d, "last": None, "over": None}
            st.rerun()
        with db() as c:
            rec = {r["result"]: r["n"] for r in c.execute("SELECT result, COUNT(*) n FROM chess WHERE user_id=? GROUP BY result", (uid,))}
        st.caption(f"Record: {rec.get('win', 0)}W · {rec.get('loss', 0)}L · {rec.get('draw', 0)}D")
        return
    b, s = g["board"], g["state"]

    def end(res):
        g["over"] = {"win": "Checkmate. You win! 🏆", "loss": "Checkmate. The AI wins.", "draw": "Draw."}[res]
        with db() as c:
            c.execute("INSERT INTO chess(user_id,result,moves,diff) VALUES(?,?,?,?)", (uid, res, len(g["hist"]), g["diff"]))
        award_xp(uid, 40 if res == "win" else 8)
        st.rerun()

    if not g["over"] and g["turn"] == "b":
        with st.spinner("AI is thinking..."):
            m = chess_ai(b, s, g["diff"])
        if m is None:
            end("win" if in_check(b, False) else "draw")
        cap = b[m[2]][m[3]]
        g["hist"].append(san(b, m))
        g["board"], g["state"] = apply(b, s, *m); g["last"] = m[:4]
        if cap != ".": g["capw"].append(cap)
        g["turn"] = "w"
        st.rerun()
    wm = legal(b, s, True)
    if not g["over"] and not wm:
        end("loss" if in_check(b, True) else "draw")
    st.markdown(board_html(g), unsafe_allow_html=True)
    st.write(g["over"] or ("Your move" + (" — check!" if in_check(b, True) else "")))
    if not g["over"]:
        frs = sorted({(m[0], m[1]) for m in wm})
        i = st.selectbox("Piece", range(len(frs)), format_func=lambda i: UNI[b[frs[i][0]][frs[i][1]]] + " " + sq(*frs[i]))
        tos = [m for m in wm if (m[0], m[1]) == frs[i]]
        j = st.selectbox("Move to", range(len(tos)), format_func=lambda j: sq(tos[j][2], tos[j][3]) + {"ck": " (castle)", "cq": " (castle)", "promo": " (promote)", "ep": " (en passant)"}.get(tos[j][4], ""))
        if st.button("Play move", type="primary"):
            m = tos[j]; cap = b[m[2]][m[3]]
            g["hist"].append(san(b, m))
            g["board"], g["state"] = apply(b, s, *m); g["last"] = m[:4]
            if cap != ".": g["capb"].append(cap)
            g["turn"] = "b"
            st.rerun()
        if st.button("💡 Hint"):
            h = minimax(b, s, 2, -math.inf, math.inf, True)[1]
            if h: st.info("Try " + san(b, h))
    if st.button("New game"):
        st.session_state.chess = None
        st.rerun()
    st.caption("You took: " + (" ".join(UNI[p] for p in g["capb"]) or "—") + " · AI took: " + (" ".join(UNI[p] for p in g["capw"]) or "—"))
    st.text(" ".join(g["hist"][-20:]))

# ======================= SMITHTUBE =======================
VSEL = "SELECT v.*, u.name, u.username FROM videos v JOIN users u ON u.id=v.user_id"
VCATS = ["Education", "Music", "Gaming", "Comedy", "How-to", "Sports", "Vlog", "Other"]

def tagset(t): return {x.strip().lower() for x in (t or "").split(",") if x.strip()}

def interests(uid):
    with db() as c:
        rows = c.execute("SELECT v.tags FROM videos v JOIN vhist h ON h.video_id=v.id WHERE h.user_id=? UNION ALL SELECT v.tags FROM videos v JOIN vreact r ON r.video_id=v.id WHERE r.user_id=?", (uid, uid)).fetchall()
    return set().union(*[tagset(r["tags"]) for r in rows]) if rows else set()

def vscore(v, mine): return 3 * len(tagset(v["tags"]) & mine) + math.log1p(v["views"])

def vcard(v, key):
    st.markdown(f"<div class='card'><b>{html.escape(v['title'] or '')}</b><div class='muted'>{html.escape(v['name'] or v['username'])} · {v['views']} views · {html.escape(v['cat'] or '')}</div></div>", unsafe_allow_html=True)
    if st.button("▶ Watch", key=key + str(v["id"])):
        st.session_state.vid = v["id"]
        st.rerun()

def watch(vid):
    uid = st.session_state.uid
    seen = st.session_state.setdefault("seenv", set())
    with db() as c:
        if vid not in seen:
            seen.add(vid)
            c.execute("UPDATE videos SET views=views+1 WHERE id=?", (vid,))
            c.execute("INSERT INTO vhist(user_id,video_id) VALUES(?,?)", (uid, vid))
        v = c.execute(VSEL + " WHERE v.id=?", (vid,)).fetchone()
        likes = c.execute("SELECT COUNT(*) x FROM vreact WHERE video_id=?", (vid,)).fetchone()["x"]
        liked = c.execute("SELECT 1 FROM vreact WHERE video_id=? AND user_id=?", (vid, uid)).fetchone()
        subbed = c.execute("SELECT 1 FROM subs WHERE user_id=? AND channel_id=?", (uid, v["user_id"] if v else 0)).fetchone()
        coms = c.execute("SELECT m.*, u.name, u.username FROM vcom m JOIN users u ON u.id=m.user_id WHERE m.video_id=? ORDER BY m.id DESC", (vid,)).fetchall()
    if not v or not os.path.exists(v["path"]):
        st.session_state.vid = None
        st.rerun()
    if st.button("← Back"):
        st.session_state.vid = None
        st.rerun()
    st.video(v["path"])
    st.subheader(v["title"])
    st.caption(f"{v['views']} views · {v['name'] or v['username']} · {v['created'][:10]} · {v['tags'] or ''}")
    st.write(v["descr"] or "")
    a, b, c3 = st.columns(3)
    if a.button(("👍 Liked " if liked else "👍 Like ") + str(likes), use_container_width=True):
        with db() as c:
            c.execute("DELETE FROM vreact WHERE user_id=? AND video_id=?", (uid, vid))
            if not liked: c.execute("INSERT INTO vreact(user_id,video_id) VALUES(?,?)", (uid, vid))
        st.rerun()
    if v["user_id"] != uid and b.button("✔ Subscribed" if subbed else "🔔 Subscribe", use_container_width=True):
        with db() as c:
            c.execute("DELETE FROM subs WHERE user_id=? AND channel_id=?", (uid, v["user_id"]))
            if not subbed: c.execute("INSERT INTO subs(user_id,channel_id) VALUES(?,?)", (uid, v["user_id"]))
        st.rerun()
    if v["user_id"] == uid and c3.button("🗑 Delete video", use_container_width=True):
        with db() as c:
            for t in ("videos", "vhist", "vreact", "vcom"):
                c.execute(f"DELETE FROM {t} WHERE " + ("id" if t == "videos" else "video_id") + "=?", (vid,))
        os.remove(v["path"])
        st.session_state.vid = None
        st.rerun()
    others = users_other(uid)
    if others:
        with st.expander("Share to a chat"):
            peer = st.selectbox("Send to", [o["id"] for o in others], format_func=lambda i: next(o["name"] or o["username"] for o in others if o["id"] == i))
            if st.button("Send"):
                send_dm(uid, peer, "🎬 Watch on SmithTube: " + v["title"])
                st.success("Sent.")
    with st.expander("✨ Ask AI about this video"):
        qn = st.text_input("Question (blank = summary)", key="vq")
        if st.button("Ask AI"):
            ctx = f"Title: {v['title']}. Description: {v['descr']}. Tags: {v['tags']}. Comments: " + " | ".join(m["body"] for m in coms[:8])
            st.write(ai([{"role": "system", "content": "You only know this text about a video and cannot see the video itself; say so if the answer is not here. " + ctx}, {"role": "user", "content": qn or "Summarize this video and what viewers think."}]) or "AI is unavailable right now.")
    st.markdown("#### Comments (" + str(len(coms)) + ")")
    with st.form("vc", clear_on_submit=True):
        body = st.text_input("Add a comment")
        if st.form_submit_button("Post") and body.strip():
            r = ai_json('Is this comment abusive, hateful, threatening, or spam? Return {"abusive": true or false}. Comment: ' + body)
            if r and r.get("abusive"):
                st.error("That comment was blocked by AI moderation.")
            else:
                with db() as c:
                    c.execute("INSERT INTO vcom(video_id,user_id,body,created) VALUES(?,?,?,?)", (vid, uid, body.strip(), now()))
                st.rerun()
    for m in coms[:30]:
        st.markdown(f"**{html.escape(m['name'] or m['username'])}** · <span class='muted'>{m['created'][:10]}</span>", unsafe_allow_html=True)
        st.write(m["body"])
    st.markdown("#### Up next")
    with db() as c:
        rest = [x for x in c.execute(VSEL).fetchall() if x["id"] != vid]
    mine = interests(uid) | tagset(v["tags"])
    for x in sorted(rest, key=lambda x: -vscore(x, mine))[:4]:
        vcard(x, "n")

def tube():
    uid = st.session_state.uid
    head("▶️", "SmithTube", "Upload, watch, subscribe. The feed learns what you like.")
    if st.session_state.get("vid"):
        return watch(st.session_state.vid)
    t1, t2, t3 = st.tabs(["For you", "Upload", "My channel"])
    with t1:
        a, b, c3 = st.columns([3, 2, 2])
        q = a.text_input("Search", placeholder="Search videos", label_visibility="collapsed")
        sort = b.selectbox("Sort", ["For you", "Newest", "Most viewed"], label_visibility="collapsed")
        only = c3.toggle("Subscriptions")
        with db() as c:
            vids = c.execute(VSEL).fetchall()
            subs = {r["channel_id"] for r in c.execute("SELECT channel_id FROM subs WHERE user_id=?", (uid,))}
        mine = interests(uid)
        vids = [v for v in vids if q.lower() in ((v["title"] or "") + " " + (v["descr"] or "") + " " + (v["tags"] or "")).lower() and (not only or v["user_id"] in subs)]
        key = {"For you": lambda v: -vscore(v, mine), "Newest": lambda v: -v["id"], "Most viewed": lambda v: -v["views"]}[sort]
        for v in sorted(vids, key=key)[:30]:
            vcard(v, "f")
        if not vids:
            st.info("No videos yet. Upload the first one!")
    with t2:
        f = st.file_uploader("Video file", type=["mp4", "mov", "webm"])
        idea = st.text_area("What is it about? (AI uses this)")
        title = st.text_input("Title (blank = AI writes it)")
        descr = st.text_area("Description (blank = AI writes it)")
        tags = st.text_input("Tags, comma separated (blank = AI picks)")
        cat = st.selectbox("Category", VCATS)
        if st.button("Publish", type="primary") and f:
            if not (title and descr and tags):
                with st.spinner("AI is writing your details..."):
                    r = ai_json('Write video metadata for a video about: ' + (idea or title or f.name) + '. Return {"title":"max 70 chars","description":"2-3 sentences","tags":["5 to 8 lowercase tags"]}.') or {}
                title = title or r.get("title") or f.name
                descr = descr or r.get("description") or idea
                tags = tags or ",".join(map(str, r.get("tags") or [cat.lower()]))
            folder = os.path.join(VAULT, "videos")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, datetime.now().strftime("%Y%m%d%H%M%S%f") + os.path.splitext(f.name)[1].lower())
            with open(path, "wb") as o:
                o.write(f.getbuffer())
            with db() as c:
                c.execute("INSERT INTO videos(user_id,title,descr,tags,cat,path,created) VALUES(?,?,?,?,?,?,?)", (uid, title, descr, tags, cat, path, now()))
            award_xp(uid, 15)
            st.success("Published: " + title)
    with t3:
        with db() as c:
            mine_v = c.execute(VSEL + " WHERE v.user_id=? ORDER BY v.id DESC", (uid,)).fetchall()
            nsub = c.execute("SELECT COUNT(*) x FROM subs WHERE channel_id=?", (uid,)).fetchone()["x"]
        m1, m2, m3 = st.columns(3)
        m1.metric("Subscribers", nsub); m2.metric("Videos", len(mine_v)); m3.metric("Total views", sum(v["views"] for v in mine_v))
        for v in mine_v:
            vcard(v, "m")

# ======================= RESTORED NEXUS FEATURES =======================
THEMES = {"whatsapp": ("#0b141a", "#202c33", "#e9edef", "#8696a0", "#00a884", "#0b6e99"),
          "cosmic": ("#0b1020", "#151b2e", "#eef2ff", "#9aa6c3", "#7c5cff", "#f093fb"),
          "forest": ("#0e1712", "#16241c", "#e8f6ee", "#9bb5a6", "#3dd68c", "#b6f36b"),
          "ocean": ("#07141c", "#102433", "#e7f4ff", "#8eb4cc", "#3aa0ff", "#67e8f9"),
          "sunrise": ("#1a120c", "#2a1c14", "#fff6ec", "#d2b59a", "#ff8a3d", "#ffd166")}

def css():
    bg, card, ink, muted, a1, a2 = THEMES.get(st.session_state.get("theme") or "whatsapp", THEMES["whatsapp"])
    st.markdown(f"<style>.stApp{{background:{bg};color:{ink}}}.hero{{background:linear-gradient(135deg,{a1},{a2});border-radius:16px;padding:16px 20px;color:#fff;margin-bottom:12px}}.hero h1{{margin:0;font-size:1.5rem}}.card{{background:{card};border-radius:14px;padding:12px 14px;margin-bottom:8px}}.muted{{color:{muted};font-size:.85rem}}</style>", unsafe_allow_html=True)

def td(): return str(datetime.now().date())

# ---- generic tracker engine: one config entry = one full feature ----
MOODS = ["Happy", "Calm", "Thoughtful", "Sad", "Frustrated", "Tired", "Motivated", "Neutral"]

def L(icon, title, fields, xp=3, **kw): return dict(icon=icon, title=title, fields=fields, xp=xp, **kw)

def _avg(rows):
    b = {}
    for r in rows: b.setdefault(r["subject"], []).append(r["score"] / (r["out_of"] or 1) * 100)
    return " · ".join(f"{k} {sum(v) / len(v):.0f}%" for k, v in b.items())

def _bal(rows): return f"{sum(r['amount'] if r['kind'] == 'in' else -r['amount'] for r in rows):.2f}"

LOGS = {
    "journal": L("📖", "Journal", [("title", "Title", "text"), ("mood", "Mood", MOODS), ("content", "Write", "area")], 6, need="content",
                 ai="Warm journal companion for a teenager. Give an empathetic reflection and one gentle question, under 60 words. Entry: {}"),
    "dreams": L("🌙", "Dreams", [("content", "What do you remember?", "area"), ("reading", "", "hidden")], 6, need="content",
                on_save=("reading", "Give a gentle, non-scary dream reflection for a teenager in under 80 words: feelings, symbols, one calm action. Not a prediction. Dream: {}")),
    "gratitude": L("🙏", "Gratitude", [("items", "Three good things", "area")], 4, need="items"),
    "wins": L("🏆", "Wins", [("description", "What went well?", "text"), ("size", "Size", ["tiny", "small", "medium", "big"])], 4, need="description"),
    "reading": L("📚", "Reading list", [("title", "Title", "text"), ("status", "Status", ["Want to read", "Reading", "Finished"])], 2, need="title"),
    "flash": L("🃏", "Flashcards", [("question", "Question", "text"), ("answer", "Answer", "text")], 2, need="question", hide=["answer"]),
    "kindness": L("💛", "Kindness log", [("act", "A kind thing you did or noticed", "text")], 5, need="act"),
    "quotes": L("❝", "Quotes", [("quote", "Quote", "area"), ("author", "Author", "text")], 0, need="quote"),
    "mood": L("😊", "Mood", [("mood", "Mood", MOODS), ("energy", "Energy", (1, 10, 5)), ("note", "Note", "text")], 2),
    "meditation": L("🧘", "Meditate", [("minutes", "Minutes", (1, 30, 5)), ("note", "Note", "text")], lambda v: v["minutes"]),
    "sleep": L("😴", "Sleep", [("hours", "Hours", "float"), ("quality", "Quality", (1, 10, 7))], 3),
    "workout": L("🏃", "Workout", [("type", "Type", ["Walk", "Run", "Sport", "Stretch", "Dance", "Other"]), ("duration", "Minutes", "int"), ("notes", "Notes", "text")], lambda v: max(1, v["duration"] // 5)),
    "water": L("💧", "Water", [("glasses", "Glasses", (1, 4, 1))], lambda v: v["glasses"]),
    "goals": L("🎯", "Goals", [("objective", "Goal", "text"), ("due_date", "Due", "date"), ("progress", "Progress %", (0, 100, 0))], 3, need="objective"),
    "projects": L("🏗️", "Studio", [("name", "Project", "text"), ("description", "What is it?", "area"), ("stage", "Stage", ["idea", "building", "paused", "done"])], 3, need="name"),
    "homework": L("📚", "Homework", [("subject", "Subject", "text"), ("title", "Assignment", "text"), ("due", "Due date", "date")], 4, need="title", done=10),
    "exams": L("🗓️", "Exam countdown", [("subject", "Subject", "text"), ("title", "Exam name", "text"), ("exam_date", "Date", "date"), ("notes", "Study notes", "area")], 5, need="title", date="exam_date"),
    "events": L("📌", "Events", [("title", "Event", "text"), ("event_date", "Date", "date"), ("note", "Note", "text")], 0, need="title", date="event_date"),
    "grades": L("📈", "Grades", [("subject", "Subject", "text"), ("title", "Test or project", "text"), ("score", "Score", "float"), ("out_of", "Out of", "float")], 3, need="subject", summary=("Averages", _avg)),
    "money": L("🪙", "Allowance", [("kind", "Type", ["in", "out"]), ("amount", "Amount", "float"), ("note", "Note", "text")], 0, summary=("Balance", _bal)),
    "bookmarks": L("🔖", "Bookmarks", [("title", "Title", "text"), ("url", "Link", "text"), ("tag", "Tag", "text")], 0, need="title"),
    "capsule": L("⏳", "Time capsule", [("message", "Note to future you", "area"), ("unlock_date", "Open on", "date30")], 10, need="message", lock="unlock_date"),
}

def _sql(kind): return "INT" if kind == "int" or isinstance(kind, tuple) else "REAL" if kind == "float" else "TEXT"

with db() as c:
    for k, cfg in LOGS.items():
        cols = ", ".join(f[0] + " " + _sql(f[2]) for f in cfg["fields"])
        c.execute(f"CREATE TABLE IF NOT EXISTS {k}(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, {cols}, done INT DEFAULT 0, created TEXT)")
    for t in ("ach(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, code TEXT, name TEXT, icon TEXT, at TEXT)",
              "habits(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, name TEXT, icon TEXT, streak INT DEFAULT 0, last_done TEXT, created TEXT)",
              "focus(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, duration INT, task TEXT, created TEXT)",
              "challenges(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, cd TEXT, ct TEXT, completed INT DEFAULT 0, created TEXT)",
              "wordle(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, word TEXT, guesses TEXT, won INT DEFAULT 0, day TEXT)",
              "places(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, name TEXT, mood TEXT, note TEXT, path TEXT, ai TEXT, created TEXT)"):
        c.execute("CREATE TABLE IF NOT EXISTS " + t)
    have = {r[1] for r in c.execute("PRAGMA table_info(users)")}
    for col, ddl in (("xp", "INT DEFAULT 0"), ("streak", "INT DEFAULT 0"), ("last_active", "TEXT"), ("rank", "TEXT DEFAULT 'Bronze'"), ("theme", "TEXT DEFAULT 'whatsapp'")):
        if col not in have:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")

def logview(key):
    cfg, uid = LOGS[key], st.session_state.uid
    head(cfg["icon"], cfg["title"])
    with st.form("f" + key, clear_on_submit=True):
        vals = {}
        for col, label, kind in cfg["fields"]:
            if kind == "hidden": continue
            if kind == "area": vals[col] = st.text_area(label)
            elif kind == "text": vals[col] = st.text_input(label)
            elif kind == "int": vals[col] = int(st.number_input(label, 1, 100000, 20))
            elif kind == "float": vals[col] = float(st.number_input(label, 0.0, 100000.0, 100.0 if col == "out_of" else 8.0 if col == "hours" else 1.0, 0.5))
            elif kind in ("date", "date30"): vals[col] = str(st.date_input(label, value=datetime.now().date() + timedelta(days=30 if kind == "date30" else 0)))
            elif isinstance(kind, tuple): vals[col] = st.slider(label, *kind)
            else: vals[col] = st.selectbox(label, kind)
        ok = st.form_submit_button("Save")
    need = cfg.get("need")
    if ok and (not need or str(vals[need]).strip()):
        if "on_save" in cfg:
            col, pr = cfg["on_save"]
            with st.spinner("Reflecting..."):
                vals[col] = ai([{"role": "user", "content": pr.format(vals["content"])}], timeout=30) or ""
        cols = list(vals)
        with db() as c:
            c.execute(f"INSERT INTO {key}(user_id,{','.join(cols)},created) VALUES(?{',?' * len(cols)},?)", (uid, *vals.values(), now()))
        award_xp(uid, cfg["xp"](vals) if callable(cfg["xp"]) else cfg["xp"])
        st.rerun()
    with db() as c:
        rows = c.execute(f"SELECT * FROM {key} WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    if cfg.get("summary") and rows:
        st.metric(cfg["summary"][0], cfg["summary"][1](rows))
    shown = [f[0] for f in cfg["fields"] if f[2] != "hidden" and f[0] not in cfg.get("hide", [])]
    for r in rows[:60]:
        if cfg.get("lock") and r[cfg["lock"]] > td():
            st.caption("🔒 Sealed until " + r[cfg["lock"]])
            continue
        line = " · ".join(str(r[x]) for x in shown if r[x] not in (None, ""))
        if cfg.get("date"):
            line += f" ({(datetime.strptime(r[cfg['date']], '%Y-%m-%d').date() - datetime.now().date()).days} days)"
        c1, c2 = st.columns([5, 1])
        if cfg.get("hide"):
            with c1.expander(line):
                st.write(" ".join(str(r[h]) for h in cfg["hide"]))
        else:
            c1.write(("✅ " if r["done"] else "") + line)
        if cfg.get("on_save") and r[cfg["on_save"][0]]:
            st.caption(r[cfg["on_save"][0]])
        if cfg.get("done") and not r["done"] and c2.button("Done", key=f"{key}d{r['id']}"):
            with db() as c:
                c.execute(f"UPDATE {key} SET done=1 WHERE id=?", (r["id"],))
            award_xp(uid, cfg["done"])
            st.rerun()
        if cfg.get("ai") and c2.button("AI", key=f"{key}a{r['id']}"):
            st.info(ai([{"role": "user", "content": cfg["ai"].format(r["content"])}]) or "AI is unavailable right now.")

# ---- XP, ranks, streaks, awards ----
def rank_of(xp): return next(n for t, n in ((5000, "Legend"), (2500, "Diamond"), (1000, "Platinum"), (500, "Gold"), (150, "Silver"), (0, "Bronze")) if xp >= t)

ACH = {"first_" + k: (v["title"], v["icon"]) for k, v in LOGS.items()}
ACH.update({"first_chess": ("Gladiator", "♟️"), "chess5": ("Champion", "🏆"), "streak3": ("Consistent", "🔥"), "streak7": ("Committed", "💎"),
            "xp100": ("Apprentice", "🥉"), "xp500": ("Adept", "🥈"), "xp2000": ("Master", "🥇"), "first_video": ("Creator", "▶️"),
            "first_task": ("Planner", "✅"), "first_note": ("Thinker", "📝"), "wordle_win": ("Wordsmith", "🔤")})

def award_xp(uid, n):
    if n <= 0: return
    with db() as c:
        c.execute("UPDATE users SET xp=COALESCE(xp,0)+? WHERE id=?", (n, uid))
        xp = c.execute("SELECT xp FROM users WHERE id=?", (uid,)).fetchone()["xp"]
        c.execute("UPDATE users SET rank=? WHERE id=?", (rank_of(xp), uid))
    check_ach(uid)

def upd_streak(uid):
    with db() as c:
        u = c.execute("SELECT streak, last_active FROM users WHERE id=?", (uid,)).fetchone()
        if not u or u["last_active"] == td(): return
        y = str((datetime.now() - timedelta(days=1)).date())
        c.execute("UPDATE users SET streak=?, last_active=? WHERE id=?", ((u["streak"] or 0) + 1 if u["last_active"] == y else 1, td(), uid))

def check_ach(uid):
    with db() as c:
        have = {r["code"] for r in c.execute("SELECT code FROM ach WHERE user_id=?", (uid,))}
        n = lambda sql: c.execute(sql, (uid,)).fetchone()[0]
        ok = {"first_" + k: n(f"SELECT COUNT(*) FROM {k} WHERE user_id=?") >= 1 for k in LOGS}
        wins = n("SELECT COUNT(*) FROM chess WHERE user_id=? AND result='win'")
        u = c.execute("SELECT xp, streak FROM users WHERE id=?", (uid,)).fetchone()
        xp, sk = u["xp"] or 0, u["streak"] or 0
        ok.update(first_chess=wins >= 1, chess5=wins >= 5, streak3=sk >= 3, streak7=sk >= 7, xp100=xp >= 100, xp500=xp >= 500, xp2000=xp >= 2000,
                  first_video=n("SELECT COUNT(*) FROM videos WHERE user_id=?") >= 1, first_task=n("SELECT COUNT(*) FROM tasks WHERE user_id=?") >= 1,
                  first_note=n("SELECT COUNT(*) FROM notes WHERE user_id=?") >= 1, wordle_win=n("SELECT COUNT(*) FROM wordle WHERE user_id=? AND won=1") >= 1)
        for code, v in ok.items():
            if v and code not in have:
                c.execute("INSERT INTO ach(user_id,code,name,icon,at) VALUES(?,?,?,?,?)", (uid, code, *ACH[code], now()))
                st.toast(ACH[code][1] + " " + ACH[code][0])

# ---- AI helpers (tutor, wellness, decide, email, resume) ----
AIT = {
    "tutor": ("🎓", "Tutor", "A five-step lesson", [("What do you want to learn?", "text")],
              "Build a clear 5-step mini-lesson on: {0}. Short intro, then 5 numbered steps, each with a title and a small practice task. Student-friendly.", 8),
    "wellness": ("🩺", "Wellness", "A note to share with a parent", [("How do you feel?", "area"), ("Who is this about?", ["Me", "A younger sibling with a parent present"])],
                 "Write a short wellness note, NOT a diagnosis, for a teenager. Feeling: {0}. About: {1}. Include possible everyday causes, simple home care, warning signs to tell an adult about right away, when to see a doctor, and always say to tell a parent or guardian. Never suggest medicines or doses.", 4),
    "decide": ("🎲", "Decide", "Talk big choices over with a parent", [("What are you deciding?", "area"), ("Options, one per line", "area")],
               "Help a teenager think through a decision safely. Question: {0}. Options: {1}. Give pros, cons and one careful suggestion. Under 160 words.", 0),
    "email": ("💌", "Email drafts", "School notes", [("Type", ["Thank you", "Request", "Follow-up", "Apology", "Club intro", "Polite concern", "Leaving a club"]), ("Who is it for?", "text"), ("What should it say?", "area"), ("Tone", ["Formal", "Professional", "Friendly", "Warm"])],
              "Write a short polite {0} note to {1}. Tone: {3}. Content: {2}. School-appropriate, under 140 words, include a subject line.", 4),
    "resume": ("📄", "Resume helper", "School and club bullets", [("Target role or club", "text"), ("What you did", "area")],
               "Write 5 school-friendly resume bullets for {0}. Experience: {1}. Start with action verbs. No adult job claims.", 4),
}

def aitool(key):
    icon, title, sub, fields, prompt, xp = AIT[key]
    head(icon, title, sub)
    if key == "wellness":
        st.warning("Not a doctor. Tell a parent or guardian. Do not take medicine unless they or a doctor say so.")
    vals = [st.text_area(l) if k == "area" else st.text_input(l) if k == "text" else st.selectbox(l, k) for l, k in fields]
    if st.button("Generate", type="primary") and all(str(v).strip() for v in vals):
        with st.spinner("Thinking..."):
            out = ai([{"role": "user", "content": prompt.format(*vals)}], timeout=60)
        if key == "wellness" and not out:
            out = "Please tell a parent or guardian how you feel. If you have trouble breathing, severe pain, fainting, or it gets worse, get help right away."
        st.write(out or "AI is unreachable right now. Try again.")
        award_xp(st.session_state.uid, xp)

def weekly():
    uid = st.session_state.uid
    head("📊", "Weekly report", "Your week, plus habit ideas")
    a, b = st.columns(2)
    if a.button("Build report", use_container_width=True):
        since = (datetime.now() - timedelta(days=7)).isoformat()
        with db() as c:
            stats = {t: c.execute(f"SELECT COUNT(*) FROM {t} WHERE user_id=? AND created>=?", (uid, since)).fetchone()[0] for t in ("journal", "notes", "homework", "focus", "wins", "mood", "dreams")}
        st.write(ai([{"role": "user", "content": "Weekly report for a student. Counts: " + str(stats) + ". Two kind sentences, one win, one next step."}]) or "AI is unreachable right now.")
    if b.button("Habit ideas", use_container_width=True):
        with db() as c:
            j = [r["content"][:80] for r in c.execute("SELECT content FROM journal WHERE user_id=? ORDER BY id DESC LIMIT 3", (uid,))]
            m = [r["mood"] for r in c.execute("SELECT mood FROM mood WHERE user_id=? ORDER BY id DESC LIMIT 3", (uid,))]
        st.write(ai([{"role": "user", "content": "Suggest 3 small habits for a student. Journals: " + "; ".join(j) + ". Moods: " + ", ".join(m) + ". Under 120 words."}]) or "AI is unreachable right now.")
        award_xp(uid, 3)

def search():
    uid = st.session_state.uid
    head("🔍", "Search", "Across your notes, journal, tasks and more")
    q = st.text_input("Search")
    if len(q) < 2: return
    with db() as c:
        for t, col in (("notes", "content"), ("tasks", "title"), ("journal", "content"), ("homework", "title"), ("quotes", "quote"), ("wins", "description"), ("goals", "objective"), ("flash", "question")):
            for r in c.execute(f"SELECT {col} AS t FROM {t} WHERE user_id=? AND {col} LIKE ? LIMIT 8", (uid, "%" + q + "%")):
                st.write(t + ": " + str(r["t"])[:140])

# ---- habits, focus, challenge, breathe, places ----
def habits():
    uid = st.session_state.uid
    head("✅", "Habits", "Build streaks")
    with st.form("hb", clear_on_submit=True):
        name, icon = st.text_input("Habit"), st.text_input("Emoji", value="✅")
        if st.form_submit_button("Add habit") and name:
            with db() as c:
                c.execute("INSERT INTO habits(user_id,name,icon,created) VALUES(?,?,?,?)", (uid, name, icon, now()))
            st.rerun()
    with db() as c:
        rows = c.execute("SELECT * FROM habits WHERE user_id=?", (uid,)).fetchall()
    for r in rows:
        c1, c2 = st.columns([4, 1])
        c1.write(f"{r['icon']} {r['name']} · {r['streak']} days")
        if r["last_done"] == td():
            c2.success("Done")
        elif c2.button("Mark", key="h" + str(r["id"])):
            y = str((datetime.now() - timedelta(days=1)).date())
            with db() as c:
                c.execute("UPDATE habits SET last_done=?, streak=? WHERE id=?", (td(), (r["streak"] or 0) + 1 if r["last_done"] == y else 1, r["id"]))
            award_xp(uid, 5)
            st.rerun()

def focus():
    uid = st.session_state.uid
    head("🎯", "Focus", "A simple study timer")
    task = st.text_input("Task", value=st.session_state.get("ftask", ""))
    mins = st.select_slider("Minutes", [5, 10, 15, 25, 45], value=25)
    if st.button("Start"):
        if not task: st.error("Name the task.")
        else:
            st.session_state.update(fend=time.time() + mins * 60, ftask=task, fmin=mins)
            st.rerun()
    end = st.session_state.get("fend")
    if end:
        left = int(end - time.time())
        if left > 0:
            m, s = divmod(left, 60)
            st.metric(st.session_state.ftask, f"{m:02d}:{s:02d}")
            st.button("Refresh timer")
        else:
            with db() as c:
                c.execute("INSERT INTO focus(user_id,duration,task,created) VALUES(?,?,?,?)", (uid, st.session_state.fmin, st.session_state.ftask, now()))
            award_xp(uid, st.session_state.fmin)
            st.session_state.fend = None
            st.balloons()
            st.success("Session complete!")

POOL = ["Write three things you are grateful for", "Pack your bag for tomorrow", "Read for 15 minutes", "Drink a glass of water before homework",
        "Tell a family member one kind thing", "Review one flashcard set", "Tidy your desk for five minutes", "Write tomorrow's first task"]

def challenge():
    uid = st.session_state.uid
    head("📅", "Daily challenge")
    with db() as c:
        r = c.execute("SELECT * FROM challenges WHERE user_id=? AND cd=?", (uid, td())).fetchone()
        if not r:
            c.execute("INSERT INTO challenges(user_id,cd,ct,created) VALUES(?,?,?,?)", (uid, td(), random.choice(POOL), now()))
            r = c.execute("SELECT * FROM challenges WHERE user_id=? AND cd=?", (uid, td())).fetchone()
    st.markdown("<div class='card'><b>" + html.escape(r["ct"]) + "</b></div>", unsafe_allow_html=True)
    if r["completed"]: st.success("Completed")
    elif st.button("Mark complete"):
        with db() as c:
            c.execute("UPDATE challenges SET completed=1 WHERE id=?", (r["id"],))
        award_xp(uid, 15)
        st.balloons()
        st.rerun()

def breathe():
    head("🫁", "Breathe", "In 4 · hold 4 · out 6")
    components.html("<div style='text-align:center;font-family:sans-serif;color:#eef2ff'><div id='c' style='width:140px;height:140px;margin:20px auto;border-radius:50%;background:#00a884;display:flex;align-items:center;justify-content:center'>Ready</div><button onclick='go()' style='padding:8px 16px;border:0;border-radius:10px'>Begin</button></div><script>async function go(){const c=document.getElementById('c');const steps=[['In',4],['Hold',4],['Out',6]];for(let n=0;n<3;n++){for(const [name,sec] of steps){c.textContent=name;await new Promise(r=>setTimeout(r,sec*1000));}}c.textContent='Done';}</script>", height=260)

def places():
    uid = st.session_state.uid
    head("📍", "Places", "Places you want to remember")
    raw = pic("Photo", "pl")
    name, mood, note = st.text_input("Place name"), st.selectbox("Mood", ["Peaceful", "Busy", "Warm", "Quiet", "Joyful", "Bright", "Still"]), st.text_area("Note")
    if st.button("Save place") and raw and name:
        with st.spinner("Looking at your photo..."):
            desc = ai([{"role": "user", "content": [{"type": "text", "text": "This photo is of a place called " + name + ". Describe it in one warm sentence under 25 words. Mood: " + mood}, img_part(raw)]}], timeout=45) or ""
        with db() as c:
            c.execute("INSERT INTO places(user_id,name,mood,note,path,ai,created) VALUES(?,?,?,?,?,?,?)", (uid, name, mood, note, save_pic(raw, uid), desc, now()))
        award_xp(uid, 12)
        st.rerun()
    with db() as c:
        rows = c.execute("SELECT * FROM places WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    for r in rows:
        st.markdown(f"**{html.escape(r['name'])}** · {r['mood']} · {r['created'][:10]}")
        if r["path"] and os.path.exists(r["path"]): st.image(r["path"], width=300)
        st.write(r["ai"] or "")
        if r["note"]: st.caption(r["note"])

# ---- games: tic-tac-toe (above), memory, wordle ----
WORDS = ["apple", "beach", "chair", "dance", "eagle", "flame", "grape", "house", "light", "mango", "night", "ocean", "piano", "river", "stone", "tiger", "water", "youth", "zebra", "cloud"]

def games():
    uid = st.session_state.uid
    head("🎮", "Games")
    t1, t2, t3 = st.tabs(["Tic-tac-toe", "Memory", "Wordle"])
    with t1:
        ttt_game()
    with t2:
        m = st.session_state.get("mem")
        if not m:
            cards = ["🌟", "🌙", "📚", "♟️", "💧", "🎯", "🌱", "🔥"] * 2
            random.shuffle(cards)
            m = st.session_state.mem = {"cards": cards, "up": [], "done": []}
        cols = st.columns(4)
        for i, cd in enumerate(m["cards"]):
            shown = i in m["done"] or i in m["up"]
            if cols[i % 4].button(cd if shown else "?", key=f"m{i}", use_container_width=True) and not shown:
                if len(m["up"]) == 2: m["up"] = []
                m["up"].append(i)
                if len(m["up"]) == 2 and m["cards"][m["up"][0]] == m["cards"][m["up"][1]]:
                    m["done"] += m["up"]; m["up"] = []
                    award_xp(uid, 2)
                st.rerun()
        st.caption(f"Matched {len(m['done']) // 2}/8")
        if st.button("New memory game"):
            st.session_state.mem = None
            st.rerun()
    with t3:
        with db() as c:
            row = c.execute("SELECT * FROM wordle WHERE user_id=? AND day=?", (uid, td())).fetchone()
            if not row:
                c.execute("INSERT INTO wordle(user_id,word,guesses,won,day) VALUES(?,?,?,0,?)", (uid, random.choice(WORDS), "", td()))
                row = c.execute("SELECT * FROM wordle WHERE user_id=? AND day=?", (uid, td())).fetchone()
        guesses = [g for g in (row["guesses"] or "").split(",") if g]
        for g in guesses:
            st.markdown("".join(f"<span style='display:inline-block;width:32px;text-align:center;background:{'#3dd68c' if row['word'][i] == ch else '#ffd166' if ch in row['word'] else '#666'};margin:2px;border-radius:6px;color:#000'>{ch.upper()}</span>" for i, ch in enumerate(g)), unsafe_allow_html=True)
        if row["won"]: st.success("Solved!")
        elif len(guesses) >= 6: st.error("The word was " + row["word"].upper())
        else:
            g = st.text_input("5-letter guess", max_chars=5, key="wg").lower()
            if st.button("Submit guess") and len(g) == 5 and g.isalpha():
                guesses.append(g)
                won = int(g == row["word"])
                with db() as c:
                    c.execute("UPDATE wordle SET guesses=?, won=? WHERE id=?", (",".join(guesses), won, row["id"]))
                if won:
                    award_xp(uid, 20)
                    st.balloons()
                st.rerun()

# ---- me: home, leaderboard, awards, stats, settings ----
WHISPERS = ["Small steps still count. Pick one thing and finish it.", "Curiosity is a skill. Ask one better question today.", "Rest is part of the work, not a break from it.", "Kindness is a habit you can practice on purpose."]

def home():
    uid = st.session_state.uid
    since = (datetime.now() - timedelta(hours=24)).isoformat()
    with db() as c:
        u = c.execute("SELECT xp, rank, streak FROM users WHERE id=?", (uid,)).fetchone()
        aw = c.execute("SELECT COUNT(*) x FROM ach WHERE user_id=?", (uid,)).fetchone()["x"]
        unread = c.execute("SELECT COUNT(*) x FROM dm WHERE receiver=? AND seen=0", (uid,)).fetchone()["x"]
        stat = c.execute("SELECT COUNT(*) x FROM status WHERE created>=? AND user_id!=?", (since, uid)).fetchone()["x"]
        tasks = c.execute("SELECT COUNT(*) x FROM tasks WHERE user_id=? AND done=0", (uid,)).fetchone()["x"]
    hr = datetime.now().hour
    head("🏠", ("Good morning" if hr < 12 else "Good afternoon" if hr < 17 else "Good evening") + ", " + st.session_state.name, "Your day in one place")
    a, b, c3, d = st.columns(4)
    a.metric("XP", u["xp"] or 0); b.metric("Streak", "🔥 " + str(u["streak"] or 0)); c3.metric("Rank", u["rank"] or "Bronze"); d.metric("Awards", aw)
    e, f, g = st.columns(3)
    e.metric("Unread", unread); f.metric("New statuses", stat); g.metric("Open tasks", tasks)
    if "whisper" not in st.session_state: st.session_state.whisper = random.choice(WHISPERS)
    st.markdown("<div class='card'><div class='muted'>Today's whisper</div><b>" + st.session_state.whisper + "</b></div>", unsafe_allow_html=True)

def leaderboard():
    head("🏆", "Leaderboard")
    with db() as c:
        rows = c.execute("SELECT name, username, xp, rank, streak, (SELECT COUNT(*) FROM chess WHERE chess.user_id=users.id AND result='win') cw FROM users ORDER BY xp DESC LIMIT 20").fetchall()
    for i, r in enumerate(rows, 1):
        st.write(f"{i}. {r['name'] or r['username']} — {r['xp'] or 0} XP · {r['rank'] or 'Bronze'} · 🔥 {r['streak'] or 0} · chess {r['cw']}")

def awards():
    head("🎖️", "Awards")
    with db() as c:
        have = {r["code"] for r in c.execute("SELECT code FROM ach WHERE user_id=?", (st.session_state.uid,))}
    for code, (name, icon) in ACH.items():
        st.write(icon + " " + name + (" ✅" if code in have else " 🔒"))

def stats():
    uid = st.session_state.uid
    head("📊", "Stats")
    with db() as c:
        u = c.execute("SELECT xp, rank, streak FROM users WHERE id=?", (uid,)).fetchone()
        st.write(f"{u['rank']} · {u['xp']} XP · streak {u['streak']}")
        res = {r["result"]: r["n"] for r in c.execute("SELECT result, COUNT(*) n FROM chess WHERE user_id=? GROUP BY result", (uid,))}
        st.write(f"Chess: {res.get('win', 0)}W / {res.get('loss', 0)}L / {res.get('draw', 0)}D")
        cols = st.columns(3)
        for i, t in enumerate(["notes", "tasks", "videos", "places", "habits"] + list(LOGS)):
            cols[i % 3].metric(t, c.execute(f"SELECT COUNT(*) FROM {t} WHERE user_id=?", (uid,)).fetchone()[0])

_settings0 = settings

def settings():
    uid = st.session_state.uid
    _settings0()
    st.divider()
    st.subheader("Theme & data")
    cur = st.session_state.get("theme") or "whatsapp"
    th = st.selectbox("Theme", list(THEMES), index=list(THEMES).index(cur) if cur in THEMES else 0)
    if st.button("Save theme"):
        with db() as c:
            c.execute("UPDATE users SET theme=? WHERE id=?", (th, uid))
        st.session_state.theme = th
        st.rerun()
    if st.button("Prepare export"):
        out = {}
        with db() as c:
            for t in ["notes", "tasks", "videos", "chess", "ttt", "places", "habits"] + list(LOGS):
                out[t] = [dict(r) for r in c.execute(f"SELECT * FROM {t} WHERE user_id=?", (uid,))]
        st.session_state.export = json.dumps(out, indent=1, default=str)
    if st.session_state.get("export"):
        st.download_button("Download JSON", st.session_state.export, file_name=f"smithapp_{uid}.json")

# ======================= CALL RINGING + FILM FINDER =======================
with db() as c:
    c.execute("CREATE TABLE IF NOT EXISTS calls(id INTEGER PRIMARY KEY AUTOINCREMENT, caller INT, callee INT, url TEXT, audio INT DEFAULT 0, status TEXT DEFAULT 'ringing', created TEXT)")

def call_frame(url, audio=False):
    frag = "#config.prejoinPageEnabled=false" + ("&config.startWithVideoMuted=true" if audio else "")
    st.link_button("Open call in new tab", url + frag)
    components.iframe(url + frag, height=480)

def ring_banner():
    uid = st.session_state.uid
    since = (datetime.now() - timedelta(seconds=90)).isoformat(timespec="seconds")
    with db() as c:
        r = c.execute("SELECT k.*, u.name, u.username FROM calls k JOIN users u ON u.id=k.caller WHERE k.callee=? AND k.status='ringing' AND k.created>=? ORDER BY k.id DESC LIMIT 1", (uid, since)).fetchone()
    if not r:
        return
    st.warning(f"📞 Incoming {'voice' if r['audio'] else 'video'} call from {r['name'] or r['username']}")
    a, b = st.columns(2)
    for label, status, col in (("Answer", "answered", a), ("Decline", "declined", b)):
        if col.button(label, key=f"{status}{r['id']}", use_container_width=True):
            with db() as c:
                c.execute("UPDATE calls SET status=? WHERE id=?", (status, r["id"]))
            if status == "answered":
                st.session_state.joined = {"url": r["url"], "audio": bool(r["audio"])}
            st.rerun()

def live_calls():
    (st.fragment(run_every=4)(ring_banner) if hasattr(st, "fragment") else ring_banner)()
    j = st.session_state.get("joined")
    if j:
        call_frame(j["url"], j["audio"])
        if st.button("📴 Leave call"):
            st.session_state.joined = None
            st.rerun()

CATALOG = {
    "🏎️ Fast & Furious (all films, in order)": [("The Fast and the Furious", 2001), ("2 Fast 2 Furious", 2003), ("The Fast and the Furious: Tokyo Drift", 2006), ("Fast & Furious", 2009),
                                    ("Fast Five", 2011), ("Fast & Furious 6", 2013), ("Furious 7", 2015), ("The Fate of the Furious", 2017),
                                    ("Hobbs & Shaw", 2019), ("F9", 2021), ("Fast X", 2023)],
    "🩸 Revenge & gangster noir, like Mercy for None (18+)": [("My Name", 2021), ("Bloodhounds", 2023), ("Kill Boksoon", 2023), ("The Outlaws", 2017),
                                                              ("The Roundup", 2022), ("New World", 2013), ("The Man from Nowhere", 2010), ("The Glory", 2022)],
    "🕶️ Korean vigilante": [("Vigilante", 2023), ("Taxi Driver", 2021), ("The Uncanny Counter", 2020)],
    "🥊 Korean high-school action": [("Weak Hero Class 1", 2022), ("Weak Hero Class 2", 2025), ("All of Us Are Dead", 2022), ("Duty After School", 2023)],
}

def jw(t): return "https://www.justwatch.com/search?q=" + quote(t)
def yt(t): return "https://www.youtube.com/results?search_query=" + quote(t + " official trailer")

def films():
    head("🎬", "Films & series", "New releases through official platforms · free classics here")
    t1, t2 = st.tabs(["🆕 New films & series", "📼 Free classics"])
    with t2:
        films_archive()
    with t1:
        st.info("SmithApp can't host or download copyrighted films and episodes. These buttons open the official services where you can watch, rent or download them legally. \"Where to watch\" shows which platform has every episode in your country.")
        q = st.text_input("Look up any film or series (new releases too)")
        if q.strip():
            c1, c2 = st.columns(2)
            c1.link_button("Where to watch", jw(q.strip()), use_container_width=True)
            c2.link_button("Trailer", yt(q.strip()), use_container_width=True)
        for grp, items in CATALOG.items():
            with st.expander(grp):
                for title, yr in items:
                    st.write(f"**{title}** ({yr})")
                    c1, c2 = st.columns(2)
                    c1.link_button("Where to watch", jw(title), use_container_width=True)
                    c2.link_button("Trailer", yt(title), use_container_width=True)
        st.caption("Fast X: Part 2 (the final film) had no confirmed release date when I checked. Type it in the box above to see if it is out.")

def lg(k): return lambda: logview(k)
def at(k): return lambda: aitool(k)

GROUPS = {
    "💬 Social": {"🏠 Home": home, "💬 Chats": chat, "🟢 Status": status, "▶️ SmithTube": tube, "🎬 Films": films},
    "🧠 AI": {"🧠 Brain": brain, "📸 Echo": echo, "📍 Places": places, "🔧 Fix-it": fixit, "🎓 Tutor": at("tutor"), "🩺 Wellness": at("wellness"),
              "🎲 Decide": at("decide"), "💌 Email": at("email"), "📄 Resume": at("resume"), "📊 Weekly": weekly, "🔍 Search": search},
    "🎮 Play": {"♟️ Chess": chess, "🎮 Games": games},
    "📚 School": {"📝 Notes & tasks": notes, "📚 Homework": lg("homework"), "🗓️ Exams": lg("exams"), "📈 Grades": lg("grades"),
                  "🃏 Flashcards": lg("flash"), "📖 Reading list": lg("reading"), "🎯 Focus": focus},
    "🌱 Wellbeing": {"📖 Journal": lg("journal"), "🌙 Dreams": lg("dreams"), "🙏 Gratitude": lg("gratitude"), "🏆 Wins": lg("wins"), "💛 Kindness": lg("kindness"),
                     "😊 Mood": lg("mood"), "🧘 Meditate": lg("meditation"), "🫁 Breathe": breathe, "💧 Water": lg("water"), "😴 Sleep": lg("sleep"), "🏃 Workout": lg("workout")},
    "🗂️ Life": {"✅ Habits": habits, "🎯 Goals": lg("goals"), "📅 Challenge": challenge, "🏗️ Studio": lg("projects"), "⏳ Capsule": lg("capsule"),
                "📌 Events": lg("events"), "🪙 Allowance": lg("money"), "🔖 Bookmarks": lg("bookmarks"), "❝ Quotes": lg("quotes")},
    "🏅 Me": {"🏆 Leaderboard": leaderboard, "🎖️ Awards": awards, "📊 Stats": stats, "⚙️ Settings": settings},
}

def main():
    css()
    if not st.session_state.get("uid"):
        auth()
        return
    uid = st.session_state.uid
    with st.sidebar:
        st.markdown("### " + st.session_state.name)
        with db() as c:
            u = c.execute("SELECT xp, rank, streak FROM users WHERE id=?", (uid,)).fetchone()
        st.caption(f"{u['rank'] or 'Bronze'} · {u['xp'] or 0} XP · 🔥 {u['streak'] or 0}")
        grp = st.selectbox("Section", list(GROUPS))
        page = st.radio("Go to", list(GROUPS[grp]), label_visibility="collapsed", key="pg_" + grp)
        if st.button("Log out", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    live_calls()
    GROUPS[grp][page]()

main()
