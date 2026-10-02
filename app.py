"""
Nexus SmithApp
Run:     streamlit run Nexus smithapp.py
"""
import base64, hashlib, html, io, json, math, os, random, sqlite3
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
                    st.session_state.update(uid=row["id"], name=row["name"] or row["username"])
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
    if b.button("📞 Start call", use_container_width=True):
        room = "smithapp-" + hashlib.sha256((str(min(uid, peer)) + "-" + str(max(uid, peer)) + "-smith").encode()).hexdigest()[:16]
        url = "https://meet.jit.si/" + room
        send_dm(uid, peer, "📞 Call started. Join: " + url)
        st.session_state.call = url
    if st.session_state.get("call"):
        st.link_button("Open call in new tab", st.session_state.call)
        components.iframe(st.session_state.call + "#config.prejoinPageEnabled=false", height=480)
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

def films():
    head("🎬", "Films", "Free, legal films from the Internet Archive")
    q = st.text_input("Search films")
    for d in film_se
