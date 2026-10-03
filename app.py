"""
SmithApp v3.0 — Chat, Call, Video, Movies, Echo, Fix, Workout
Run:     streamlit run smithapp.py
"""
import base64, hashlib, io, json, os, random, sqlite3, smtplib, time
from contextlib import contextmanager
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import quote

import requests
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageChops, ImageDraw

st.set_page_config(page_title="SmithApp", page_icon="💬", layout="wide", initial_sidebar_state="expanded")
DB, VAULT = "smith.db", "vault"
os.makedirs(VAULT, exist_ok=True)

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

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
    "videos(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, caption TEXT, path TEXT, likes INT DEFAULT 0, created TEXT)",
    "vcomments(id INTEGER PRIMARY KEY AUTOINCREMENT, video_id INT, user_id INT, body TEXT, created TEXT)",
    "vlikes(id INTEGER PRIMARY KEY AUTOINCREMENT, video_id INT, user_id INT)",
    "workouts(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, kind TEXT, reps INT, seconds INT, calories INT, created TEXT)",
    "challenges(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, kind TEXT, target INT, progress INT DEFAULT 0, created TEXT)",
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

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2"
POLLINATIONS = "https://text.pollinations.ai/openai"

def _try_ollama(messages, temp, timeout):
    try:
        r = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "messages": messages, "stream": False, "options": {"temperature": temp}}, timeout=timeout)
        if r.ok:
            t = r.json().get("message", {}).get("content", "").strip()
            if t: return t
    except Exception: pass
    return None

def _try_cloud(messages, temp, timeout):
    try:
        r = requests.post(POLLINATIONS, json={"model": "openai", "messages": messages, "temperature": temp}, timeout=timeout)
        if r.ok:
            t = r.json()["choices"][0]["message"]["content"]
            if t and t.strip(): return t.strip()
    except Exception: pass
    return None

def ai(messages, temp=0.6, timeout=45):
    out = _try_ollama(messages, temp, min(timeout, 60))
    if out: return out
    out = _try_cloud(messages, temp, timeout)
    if out: return out
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
    try: return json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
    except Exception: return None

def polish(text):
    out = ai([{"role": "system", "content": "Rewrite the user's message so it is clear, polite and professional. Keep the meaning, the language and roughly the length. Do not add facts. Return only the rewritten message."}, {"role": "user", "content": text}], temp=0.3, timeout=20)
    if out: return out
    t = text.strip()
    t = t[0].upper() + t[1:]
    return t if t[-1] in ".!?" else t + "."

def send_email(to_addr, subject, body):
    if not SMTP_EMAIL or not SMTP_PASS:
        return False, "Email not configured. Set SMTP_EMAIL and SMTP_PASS."
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(SMTP_EMAIL, SMTP_PASS)
            s.send_message(msg)
        return True, "Sent"
    except Exception as e:
        return False, str(e)[:120]

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

def save_video(raw, uid):
    folder = os.path.join(VAULT, str(uid), "videos")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, datetime.now().strftime("%Y%m%d%H%M%S%f") + ".mp4")
    with open(path, "wb") as f: f.write(raw)
    return path

def users_other(uid):
    with db() as c:
        return c.execute("SELECT id, username, name FROM users WHERE id != ? ORDER BY name", (uid,)).fetchall()

def send_dm(sender, receiver, body, raw=None):
    with db() as c:
        c.execute("INSERT INTO dm(sender,receiver,body,raw,created) VALUES(?,?,?,?,?)", (sender, receiver, body, raw or body, now()))

def auth():
    head("💬", "SmithApp", "Chat, call, stream, watch, fix, train — all in one")
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

def chat():
    uid = st.session_state.uid
    head("💬", "Chats", "AI polishes every message into professional writing")
    others = users_other(uid)
    if not others:
        st.info("No one else has signed up yet.")
        return
    labels = {o["id"]: (o["name"] or o["username"]) + " (@" + o["username"] + ")" for o in others}
    peer = st.selectbox("Chat with", list(labels), format_func=lambda i: labels[i])
    a, b, c = st.columns(3)
    polish_on = a.toggle("✨ AI professional polish", value=True)
    if b.button("📞 Start call", use_container_width=True):
        room = "smithapp-" + hashlib.sha256((str(min(uid, peer)) + "-" + str(max(uid, peer)) + "-smith").encode()).hexdigest()[:16]
        url = "https://meet.jit.si/" + room
        send_dm(uid, peer, "📞 Call started. Join: " + url)
        st.session_state.call = url
    if c.button("🎥 Video call", use_container_width=True):
        room = "smithapp-vid-" + hashlib.sha256((str(min(uid, peer)) + "-" + str(max(uid, peer)) + "-v").encode()).hexdigest()[:16]
        url = "https://meet.jit.si/" + room
        send_dm(uid, peer, "🎥 Video call started. Join: " + url)
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
        if r["path"] and os.path.exists(r["path"]): st.image(r["path"], width=320)
        if r["text"]: st.write(r["text"])
        if r["user_id"] == uid and st.button("Delete", key="ds" + str(r["id"])):
            with db() as c:
                c.execute("DELETE FROM status WHERE id=?", (r["id"],))
            st.rerun()

def video_feed():
    uid = st.session_state.uid
    head("📱", "Video Feed", "Vertical scroll — like, comment, share")
    t1, t2 = st.tabs(["🔥 For You", "⬆️ Upload"])
    with t2:
        with st.form("vupload"):
            cap = st.text_input("Caption")
            up = st.file_uploader("Video file (mp4, mov)", type=["mp4", "mov", "webm"])
            if st.form_submit_button("Post", type="primary") and up:
                path = save_video(up.getvalue(), uid)
                with db() as c:
                    c.execute("INSERT INTO videos(user_id,caption,path,created) VALUES(?,?,?,?)", (uid, cap, path, now()))
                st.success("Posted!")
                st.rerun()
    with t1:
        with db() as c:
            vids = c.execute("SELECT v.*, u.name, u.username FROM videos v JOIN users u ON u.id=v.user_id ORDER BY v.id DESC LIMIT 30").fetchall()
        if not vids:
            st.info("No videos yet. Upload one to start the feed.")
            return
        for v in vids:
            with st.container():
                c1, c2 = st.columns([1, 4])
                with c1:
                    avatar = "https://ui-avatars.com/api/?name=" + quote(v["name"] or v["username"]) + "&background=00a884&color=fff"
                    st.image(avatar, width=48)
                with c2:
                    st.markdown(f"**@{v['username']}** · {v['created'][11:16]}")
                    if v["caption"]: st.write(v["caption"])
                if os.path.exists(v["path"]): st.video(v["path"])
                with db() as c:
                    likes = c.execute("SELECT COUNT(*) x FROM vlikes WHERE video_id=?", (v["id"],)).fetchone()["x"]
                    comments = c.execute("SELECT COUNT(*) x FROM vcomments WHERE video_id=?", (v["id"],)).fetchone()["x"]
                    already = c.execute("SELECT 1 FROM vlikes WHERE video_id=? AND user_id=?", (v["id"], uid)).fetchone()
                lc1, lc2, lc3 = st.columns(3)
                like_label = ("❤️ " if already else "🤍 ") + str(likes)
                if lc1.button(like_label, key=f"lk_{v['id']}"):
                    with db() as c:
                        if already: c.execute("DELETE FROM vlikes WHERE video_id=? AND user_id=?", (v["id"], uid))
                        else: c.execute("INSERT INTO vlikes(video_id,user_id) VALUES(?,?)", (v["id"], uid))
                    st.rerun()
                with lc2:
                    if st.button("💬 " + str(comments), key=f"cm_{v['id']}"):
                        st.session_state[f"showcm_{v['id']}"] = not st.session_state.get(f"showcm_{v['id']}", False)
                if lc3.button("↗️ Share", key=f"sh_{v['id']}"):
                    st.toast("Share link copied!")
                if st.session_state.get(f"showcm_{v['id']}"):
                    with db() as c:
                        cms = c.execute("SELECT vc.*, u.name, u.username FROM vcomments vc JOIN users u ON u.id=vc.user_id WHERE video_id=? ORDER BY vc.id DESC", (v["id"],)).fetchall()
                    for cm in cms:
                        st.markdown(f"<div class='card'><b>@{cm['username']}</b> {cm['body']}</div>", unsafe_allow_html=True)
                    with st.form(f"cf_{v['id']}", clear_on_submit=True):
                        newcm = st.text_input("Add a comment", key=f"inp_{v['id']}")
                        if st.form_submit_button("Post"):
                            if newcm:
                                with db() as c:
                                    c.execute("INSERT INTO vcomments(video_id,user_id,body,created) VALUES(?,?,?,?)", (v["id"], uid, newcm, now()))
                                st.rerun()
                st.divider()

def movies():
    head("🎬", "Movies", "Search any film — every Fast & Furious, any blockbuster")
    if not TMDB_API_KEY:
        st.warning("Set TMDB_API_KEY at the top of the file to enable movie search.")
        return
    q = st.text_input("Search movies", placeholder="Fast & Furious, Dune, Inception...")
    url = "https://api.themoviedb.org/3/search/movie" if q else "https://api.themoviedb.org/3/movie/popular"
    params = {"api_key": TMDB_API_KEY, "query": q} if q else {"api_key": TMDB_API_KEY}
    try:
        r = requests.get(url, params=params, timeout=15)
        results = r.json().get("results", [])
    except: st.error("Could not reach TMDB."); return
    if not results: st.info("No results found."); return
    for mv in results[:15]:
        mid = mv["id"]; title = mv.get("title", "?")
        year = (mv.get("release_date") or "?")[:4]
        rating = mv.get("vote_average", 0); poster = mv.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w200{poster}" if poster else "https://via.placeholder.com/80x120?text=No+Poster"
        c1, c2 = st.columns([1, 4])
        with c1: st.image(poster_url, width=100)
        with c2:
            st.subheader(f"{title} ({year})")
            st.caption(f"⭐ {rating:.1f}/10")
            st.write((mv.get("overview") or "")[:220])
            if st.button("📍 Where to Watch", key=f"w_{mid}"):
                try:
                    wr = requests.get(f"https://api.themoviedb.org/3/movie/{mid}/watch/providers", params={"api_key": TMDB_API_KEY}, timeout=15)
                    regions = wr.json().get("results", {})
                    for reg in ["US", "GB", "CA", "NG", "AU"]:
                        if reg in regions:
                            data = regions[reg]
                            if data.get("link"): st.markdown(f"[🔗 All options on JustWatch ({reg})]({data['link']})")
                            for ptype in ["flatrate", "rent", "buy"]:
                                if data.get(ptype):
                                    names = [p["provider_name"] for p in data[ptype]]
                                    st.write(f"**{ptype.title()}:** {', '.join(names)}")
                except: st.error("Could not fetch provider data.")
        st.divider()

def brain():
    uid = st.session_state.uid
    head("🧠", "Brain", "AI that remembers you")
    with db() as c:
        facts = [r["fact"] for r in c.execute("SELECT fact FROM facts WHERE user_id=?", (uid,))]
        hist = c.execute("SELECT role, content FROM brain WHERE user_id=? ORDER BY id DESC LIMIT 14", (uid,)).fetchall()[::-1]
    with st.expander("What I remember (" + str(len(facts)) + ")"):
        st.write("\n".join("- " + f for f in facts) or "Nothing yet.")
        if facts and st.button("Forget everything"):
            with db() as c: c.execute("DELETE FROM facts WHERE user_id=?", (uid,))
            st.rerun()
    for m in hist:
        with st.chat_message(m["role"]): st.write(m["content"])
    q = st.chat_input("Ask anything")
    if q:
        sysmsg = "You are Smith Brain, sharp, kind assistant. Be accurate, practical. About the user: " + ("; ".join(facts) or "nothing yet") + "."
        reply = ai([{"role": "system", "content": sysmsg}] + [{"role": m["role"], "content": m["content"]} for m in hist] + [{"role": "user", "content": q}], timeout=90) or "AI unreachable. Try again."
        with db() as c:
            c.execute("INSERT INTO brain(user_id,role,content) VALUES(?,?,?)", (uid, "user", q))
            c.execute("INSERT INTO brain(user_id,role,content) VALUES(?,?,?)", (uid, "assistant", reply))
        if len(q) > 25:
            f = ai_json('Extract one lasting personal fact as {"fact":"..."}; use "" if none. Message: ' + q)
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
    out = b.copy(); draw = ImageDraw.Draw(out)
    hits = 0
    cw, ch = a.size[0] / n, a.size[1] / n
    for y in range(n):
        for x in range(n):
            if d.getpixel((x, y)) > 40:
                hits += 1
                draw.rectangle([x * cw, y * ch, (x + 1) * cw, (y + 1) * ch], outline=(255, 60, 60), width=2)
    return out, round(100 * hits / (n * n))

def echo():
    head("📸", "Echo 2.0", "Highest-upgrade photo intelligence")
    t1, t2, t3 = st.tabs(["Compare two photos", "Identify one photo", "Find difference"])
    with t1:
        a_raw, b_raw = pic("Before", "ea"), pic("After", "eb")
        if st.button("Compare", type="primary") and a_raw and b_raw:
            with st.spinner("Analyzing..."):
                marked, pct = diff_image(a_raw, b_raw)
                res = ai_json('Two photos of same scene: before then after. Return {"summary":"","missing":[],"added":[],"moved":[],"changed":[],"unsure":[]}. Be specific.', [a_raw, b_raw])
            st.image(marked, caption=f"Red boxes: {pct}% of frame changed")
            if res:
                st.subheader(res.get("summary", ""))
                for k, icon in (("missing","❌ Missing"),("added","➕ New"),("moved","↔️ Moved"),("changed","🔄 Changed"),("unsure","❓ Not sure")):
                    if res.get(k): st.markdown("**" + icon + "**\n" + "\n".join("- " + str(i) for i in res[k]))
            else: st.warning("AI unreachable, showing pixel diff only.")
    with t2:
        raw = pic("Photo to identify", "ei")
        if st.button("Identify") and raw:
            with st.spinner("Thinking..."):
                res = ai([{"role": "user", "content": [{"type": "text", "text": "List every object in this photo, then describe the scene. Short and concrete."}, img_part(raw)]}], timeout=90)
            st.write(res or "AI vision unreachable.")
    with t3:
        st.info("Upload two similar images to highlight exact pixel differences.")
        a_raw, b_raw = pic("Image A", "da"), pic("Image B", "db")
        if st.button("Find differences") and a_raw and b_raw:
            marked, pct = diff_image(a_raw, b_raw)
            st.image(marked, caption=f"{pct}% of frame differs")

def fixit():
    uid = st.session_state.uid
    head("🔧", "Fix-it", "Diagnose anything — email a technician directly")
    item = st.text_input("What is broken? (TV, phone, fridge, pipe...)")
    problem = st.text_area("What is happening?")
    raw = pic("Photo (optional)", "fx")
    if st.button("Diagnose", type="primary") and item and problem:
        with st.spinner("Diagnosing..."):
            r = ai_json('Home-repair triage for "' + item + '": ' + problem + '. Return {"likely_cause":"","safe_checks":[],"stop_if":[],"pro_skill":"","keywords":[]}. safe_checks must be harmless.', [raw] if raw else None)
        st.session_state.fix = {"item": item, "problem": problem, "r": r or {"likely_cause": "Unknown", "safe_checks": ["Check power and cables.", "Restart it."], "stop_if": ["Smoke, burning smell, sparks, or water near power."], "pro_skill": item + " repair", "keywords": [item]}}
    fx = st.session_state.get("fix")
    if fx:
        r = fx["r"]
        st.markdown("**Likely cause:** " + str(r.get("likely_cause", "")))
        st.markdown("**Safe checks**\n" + "\n".join("- " + str(i) for i in r.get("safe_checks", [])))
        st.error("Stop and call a pro if: " + "; ".join(map(str, r.get("stop_if", []))))
        words = [w for w in (r.get("keywords", []) + [fx["item"], r.get("pro_skill", "")]) if w]
        if words:
            q = " OR ".join(["skill LIKE ? OR name LIKE ?"] * len(words))
            args = [x for w in words for x in ("%" + w + "%", "%" + w + "%")]
            with db() as c:
                pros = c.execute("SELECT * FROM pros WHERE " + q, args).fetchall()
        else:
            pros = []
        st.subheader("Technicians in SmithApp")
        if not pros: st.info("No technician registered yet. Scroll down to register one.")
        for p in pros:
            st.markdown(f"<div class='card'><b>{p['name']}</b> · {p['skill']}<div class='muted'>{p['area'] or ''} · {p['phone'] or ''}</div>{p['email'] or ''}</div>", unsafe_allow_html=True)
            draft_prompt = f"Write a short professional repair request email. Item: {fx['item']}. Problem: {fx['problem']}. To a technician named {p['name']}. Under 120 words. Ask for availability and quote."
            with st.expander("📧 Email directly from SmithApp"):
                with st.form(f"em_{p['id']}"):
                    if st.form_submit_button("✨ Generate AI draft"):
                        with st.spinner("Drafting..."):
                            default_body = ai([{"role":"user","content":draft_prompt}], timeout=30) or ""
                        st.session_state[f"drafted_{p['id']}"] = default_body
                    body = st.text_area("Email body", value=st.session_state.get(f"drafted_{p['id']}", ""), height=150, key=f"body_{p['id']}")
                    subj = st.text_input("Subject", value=f"Repair request: {fx['item']}", key=f"subj_{p['id']}")
                    if st.form_submit_button("📤 Send email now", type="primary"):
                        ok, msg = send_email(p["email"] or "", subj, body)
                        if ok: st.success("✅ Email sent to " + p["email"])
                        else: st.error("Send failed: " + msg)
        st.caption("Or click to open in your mail app:")
        for p in pros:
            subj_e, body_e = quote("Repair request: " + fx["item"]), quote(fx["problem"])
            st.link_button(f"✉️ {p['name']} ({p['email']})", "mailto:" + (p["email"] or "") + "?subject=" + subj_e + "&body=" + body_e)
    with st.expander("I'm a technician: list me"):
        with st.form("pro"):
            n = st.text_input("Business or name")
            s = st.text_input("Skills (e.g. television, phone, plumbing)")
            e = st.text_input("Email")
            ph = st.text_input("Phone")
            a = st.text_input("Area")
            if st.form_submit_button("Register") and n and s and e:
                with db() as c:
                    c.execute("INSERT INTO pros(user_id,name,skill,email,phone,area) VALUES(?,?,?,?,?,?)", (uid, n, s, e, ph, a))
                st.success("Listed.")

def workout():
    uid = st.session_state.uid
    head("💪", "Workout", "Push-ups, squats, planks, and more")
    t1, t2, t3 = st.tabs(["🏋️ Log workout", "🎯 Challenges", "📊 Progress"])
    with t1:
        with st.form("wl"):
            kind = st.selectbox("Exercise", ["Push-ups","Squats","Sit-ups","Plank (sec)","Burpees","Jumping jacks","Lunges","Pull-ups","Running (min)"])
            reps = st.number_input("Reps / count", 0, 1000, 20)
            secs = st.number_input("Seconds (for holds)", 0, 3600, 0)
            cal = st.number_input("Calories (0 = auto)", 0, 5000, 0)
            if st.form_submit_button("Log workout", type="primary"):
                auto_cal = cal or int(reps * 0.5 + secs * 0.15)
                with db() as c:
                    c.execute("INSERT INTO workouts(user_id,kind,reps,seconds,calories,created) VALUES(?,?,?,?,?,?)", (uid, kind, reps, secs, auto_cal, now()))
                st.success(f"Logged! +{auto_cal} cal")
                st.rerun()
    with t2:
        with st.form("ch"):
            kind = st.selectbox("Challenge", ["30-day push-ups (30/day)","100 squats/day","Plank 5 min/day","1000 push-ups in a week"])
            target = st.number_input("Target", 1, 100000, 30)
            if st.form_submit_button("Start challenge"):
                with db() as c:
                    c.execute("INSERT INTO challenges(user_id,kind,target,created) VALUES(?,?,?,?)", (uid, kind, target, now()))
                st.rerun()
        with db() as c:
            chs = c.execute("SELECT * FROM challenges WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
        for ch in chs:
            prog = ch["progress"] or 0
            pct = min(1.0, prog / max(ch["target"], 1))
            st.markdown(f"**{ch['kind']}** — {prog}/{ch['target']}")
            st.progress(pct)
            if st.button("+1 progress", key=f"chp_{ch['id']}"):
                with db() as c:
                    c.execute("UPDATE challenges SET progress=progress+1 WHERE id=?", (ch["id"],))
                st.rerun()
    with t3:
        with db() as c:
            logs = c.execute("SELECT * FROM workouts WHERE user_id=? ORDER BY id DESC LIMIT 50", (uid,)).fetchall()
        total_cal = sum(l["calories"] or 0 for l in logs)
        total_reps = sum(l["reps"] or 0 for l in logs)
        a, b = st.columns(2)
        a.metric("Total calories", total_cal)
        b.metric("Total reps", total_reps)
        by_day = {}
        for l in logs:
            d = l["created"][:10]
            by_day[d] = by_day.get(d, 0) + (l["calories"] or 0)
        if by_day:
            st.line_chart({"calories": [by_day[d] for d in sorted(by_day)]})
        for l in logs[:20]:
            st.markdown(f"<div class='card'>{l['created'][:16]} — <b>{l['kind']}</b> {l['reps']} reps · {l['calories']} cal</div>", unsafe_allow_html=True)

def win(b):
    for x, y, z in [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]:
        if b[x] == b[y] == b[z] != " ": return b[x]

def ttt_ai(b):
    empty = [i for i, v in enumerate(b) if v == " "]
    if random.random() < 0.35: return random.choice(empty)
    for mark, chance in (("O",1.0),("X",0.6)):
        if random.random() <= chance:
            for i in empty:
                b[i] = mark
                hit = win(b) == mark
                b[i] = " "
                if hit: return i
    if b[4] == " " and random.random() < 0.6: return 4
    return random.choice(empty)

def games():
    uid = st.session_state.uid
    head("⭕", "Game", "Beat the AI")
    g = st.session_state.setdefault("ttt", {"b": [" "]*9, "msg": ""})
    cols = st.columns(3)
    for i in range(9):
        if cols[i%3].button(g["b"][i] if g["b"][i] != " " else "·", key="t"+str(i), use_container_width=True) and not g["msg"] and g["b"][i] == " ":
            g["b"][i] = "X"
            if not win(g["b"]) and " " in g["b"]:
                g["b"][ttt_ai(g["b"])] = "O"
            w = win(g["b"])
            if w or " " not in g["b"]:
                g["msg"] = "You win! 🎉" if w == "X" else "AI wins" if w == "O" else "Draw"
                with db() as c:
                    c.execute("INSERT INTO ttt(user_id,result) VALUES(?,?)", (uid, "win" if w == "X" else "loss" if w else "draw"))
            st.rerun()
    if g["msg"]: st.info(g["msg"])
    if st.button("New game"):
        st.session_state.ttt = None; st.rerun()
    with db() as c:
        rec = {r["result"]: r["n"] for r in c.execute("SELECT result, COUNT(*) n FROM ttt WHERE user_id=? GROUP BY result", (uid,))}
    st.caption(f"Record: {rec.get('win',0)}W · {rec.get('loss',0)}L · {rec.get('draw',0)}D")

def notes():
    uid = st.session_state.uid
    head("📝", "Notes & Tasks")
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
            with st.expander(r["title"]): st.write(r["content"])
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
            if not r["done"] and c2.button("Done", key="d"+str(r["id"])):
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
            for t, col in [("dm","sender"),("dm","receiver"),("status","user_id"),("brain","user_id"),("facts","user_id"),("notes","user_id"),("tasks","user_id"),("pros","user_id"),("ttt","user_id"),("videos","user_id"),("workouts","user_id"),("challenges","user_id")]:
                c.execute(f"DELETE FROM {t} WHERE {col}=?", (uid,))
            c.execute("DELETE FROM users WHERE id=?", (uid,))
        st.session_state.clear(); st.rerun()

PAGES = {
    "🏠 Home": lambda: head("🏠", "Hello, " + st.session_state.name, "Your world in one app"),
    "💬 Chats": chat,
    "🟢 Status": status,
    "🧠 Brain": brain,
    "📱 Video Feed": video_feed,
    "🎬 Movies": movies,
    "📸 Echo": echo,
    "🔧 Fix-it": fixit,
    "💪 Workout": workout,
    "⭕ Game": games,
    "📝 Notes": notes,
    "⚙️ Settings": settings,
}

def main():
    css()
    if not st.session_state.get("uid"):
        auth(); return
    with st.sidebar:
        st.markdown("### " + st.session_state.name)
        page = st.radio("Go to", list(PAGES), label_visibility="collapsed")
        if st.button("Log out", use_container_width=True):
            st.session_state.clear(); st.rerun()
    PAGES[page]()

main()
