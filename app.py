import streamlit as st
import sqlite3
import hashlib
import secrets as pysecrets
import re
import json
import requests
import csv
import io
from datetime import datetime, date, timedelta

st.set_page_config(
    page_title="AI Business Suite",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "business.db"

# ⚠️ CHANGE THIS TO YOUR EMAIL — this account gets unlimited access across the app
OWNER_EMAILS = ["your-email@gmail.com"]

PLANS = {
    "free": {"name": "Free Trial", "price": 0, "actions": 20, "features": ["20 AI actions/month", "Up to 3 team members", "Basic features"]},
    "starter": {"name": "Starter", "price": 5000, "actions": 500, "features": ["500 AI actions/month", "Up to 5 team members", "All features", "Email support"]},
    "pro": {"name": "Pro", "price": 15000, "actions": 2000, "features": ["2,000 AI actions/month", "Up to 20 team members", "All features", "Priority support"]},
    "business": {"name": "Business", "price": 50000, "actions": 10000, "features": ["10,000 AI actions/month", "Unlimited team members", "All features", "24/7 support"]},
}

DATA_TABLES_FOR_MIGRATION = ["leads", "candidates", "documents", "tasks", "messages_writer", "meetings", "reports", "tickets"]

# ============================================================
# DATABASE
# ============================================================
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS workspaces (
        code TEXT PRIMARY KEY,
        company_name TEXT,
        plan TEXT DEFAULT 'free',
        plan_started TEXT,
        plan_expires TEXT,
        actions_used INTEGER DEFAULT 0,
        actions_limit INTEGER DEFAULT 20,
        anthropic_key TEXT,
        paystack_key TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        password_salt TEXT NOT NULL,
        name TEXT,
        workspace TEXT NOT NULL,
        role TEXT DEFAULT 'member',
        is_app_owner INTEGER DEFAULT 0,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace TEXT NOT NULL,
        reference TEXT UNIQUE NOT NULL,
        amount REAL NOT NULL,
        plan TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace TEXT NOT NULL,
        user_name TEXT,
        action TEXT,
        detail TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace TEXT NOT NULL, user_id INTEGER, created_by TEXT,
        name TEXT NOT NULL, email TEXT, company TEXT, value REAL DEFAULT 0,
        status TEXT DEFAULT 'New', score INTEGER DEFAULT 0, notes TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace TEXT NOT NULL, user_id INTEGER, created_by TEXT,
        name TEXT NOT NULL, position TEXT, resume TEXT, score INTEGER DEFAULT 0,
        analysis TEXT, status TEXT DEFAULT 'Screening',
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace TEXT NOT NULL, user_id INTEGER, created_by TEXT,
        title TEXT NOT NULL, content TEXT, summary TEXT, doc_type TEXT DEFAULT 'General',
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace TEXT NOT NULL, user_id INTEGER, created_by TEXT, assigned_to TEXT,
        title TEXT NOT NULL, description TEXT, priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Pending', due_date TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS messages_writer (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace TEXT NOT NULL, user_id INTEGER, created_by TEXT,
        recipient TEXT, channel TEXT, tone TEXT, purpose TEXT, body TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace TEXT NOT NULL, user_id INTEGER, created_by TEXT,
        title TEXT NOT NULL, transcript TEXT, summary TEXT, action_items TEXT, attendees TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace TEXT NOT NULL, user_id INTEGER, created_by TEXT,
        title TEXT NOT NULL, content TEXT, report_type TEXT,
        created_at TEXT NOT NULL)""")

    c.execute("""CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace TEXT NOT NULL, user_id INTEGER, created_by TEXT,
        customer TEXT, subject TEXT, message TEXT, ai_response TEXT, status TEXT DEFAULT 'Open',
        created_at TEXT NOT NULL)""")

    conn.commit()
    conn.close()


def migrate_schema():
    """Adds any missing columns so an older business.db file doesn't crash the app."""
    conn = get_db()
    c = conn.cursor()
    for table in DATA_TABLES_FOR_MIGRATION:
        c.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in c.fetchall()]
        if "workspace" not in cols:
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN workspace TEXT DEFAULT 'legacy'")
            except Exception:
                pass
        if "created_by" not in cols:
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN created_by TEXT DEFAULT ''")
            except Exception:
                pass
    c.execute("PRAGMA table_info(tasks)")
    if "assigned_to" not in [row[1] for row in c.fetchall()]:
        try:
            c.execute("ALTER TABLE tasks ADD COLUMN assigned_to TEXT DEFAULT ''")
        except Exception:
            pass
    conn.commit()
    conn.close()


def fix_app_owners():
    conn = get_db()
    c = conn.cursor()
    for email in OWNER_EMAILS:
        c.execute("SELECT workspace FROM users WHERE LOWER(email) = LOWER(?)", (email,))
        row = c.fetchone()
        if row:
            c.execute("UPDATE users SET is_app_owner = 1, role = 'admin' WHERE LOWER(email) = LOWER(?)", (email,))
            c.execute("""UPDATE workspaces SET plan = 'business', actions_limit = 999999
                WHERE code = ?""", (row["workspace"],))
    conn.commit()
    conn.close()


init_db()
migrate_schema()
fix_app_owners()

# ============================================================
# PASSWORD HASHING (salted)
# ============================================================
def hash_password(password, salt=None):
    if salt is None:
        salt = pysecrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return digest, salt


def verify_password(password, salt, expected_hash):
    digest, _ = hash_password(password, salt)
    return digest == expected_hash


def is_owner_email(email):
    return email.lower() in [e.lower() for e in OWNER_EMAILS]


def slugify(text):
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return text[:24] if text else "team"


# ============================================================
# WORKSPACE HELPERS
# ============================================================
def get_workspace(code):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM workspaces WHERE code = ?", (code,))
    row = c.fetchone()
    conn.close()
    return row


def create_workspace(code, company_name, unlimited=False):
    conn = get_db()
    c = conn.cursor()
    plan = "business" if unlimited else "free"
    limit = 999999 if unlimited else 20
    c.execute("""INSERT OR IGNORE INTO workspaces (code, company_name, plan, actions_limit, created_at)
        VALUES (?, ?, ?, ?, ?)""", (code, company_name, plan, limit, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def log_activity(workspace, user_name, action, detail=""):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO activity_log (workspace, user_name, action, detail, created_at)
        VALUES (?, ?, ?, ?, ?)""", (workspace, user_name, action, detail, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def can_use_ai(workspace_row, is_app_owner):
    if is_app_owner:
        return True
    if workspace_row["plan"] == "free" and workspace_row["actions_used"] >= workspace_row["actions_limit"]:
        return False
    if workspace_row["plan_expires"] and datetime.fromisoformat(workspace_row["plan_expires"]) < datetime.now():
        return False
    return True


def increment_usage(workspace_code):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE workspaces SET actions_used = actions_used + 1 WHERE code = ?", (workspace_code,))
    conn.commit()
    conn.close()


# ============================================================
# AI — official Anthropic API only, shared team key, template fallback.
# No unofficial/keyless third-party proxies.
# ============================================================
def call_claude(prompt, api_key, max_tokens=800):
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]},
            timeout=60,
        )
        if resp.status_code == 200:
            return resp.json()["content"][0]["text"], True
        return f"(API error {resp.status_code}: {resp.text[:200]})", False
    except Exception as e:
        return f"(Could not reach Anthropic API: {e})", False


def parse_json_safe(text, fallback):
    try:
        return json.loads(text.strip().replace("```json", "").replace("```", "").strip())
    except Exception:
        return fallback


# ============================================================
# PAYSTACK (legit Nigerian payment gateway — optional, admin sets their own key)
# ============================================================
def init_paystack_payment(email, amount_naira, plan, secret_key):
    try:
        ref = "AIBS-" + pysecrets.token_hex(8).upper()
        r = requests.post(
            "https://api.paystack.co/transaction/initialize",
            headers={"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"},
            json={"email": email, "amount": int(amount_naira * 100), "reference": ref, "metadata": {"plan": plan}},
            timeout=30,
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("status"):
                return {"url": data["data"]["authorization_url"], "ref": ref}
    except Exception:
        pass
    return None


def verify_paystack(ref, secret_key):
    try:
        r = requests.get(f"https://api.paystack.co/transaction/verify/{ref}",
                          headers={"Authorization": f"Bearer {secret_key}"}, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") and data["data"]["status"] == "success":
                return data["data"]
    except Exception:
        pass
    return None


def activate_plan(workspace_code, plan, ref, amount):
    conn = get_db()
    c = conn.cursor()
    limit = PLANS[plan]["actions"]
    expires = (datetime.now() + timedelta(days=30)).isoformat()
    c.execute("""UPDATE workspaces SET plan = ?, plan_started = ?, plan_expires = ?,
        actions_used = 0, actions_limit = ? WHERE code = ?""",
        (plan, datetime.now().isoformat(), expires, limit, workspace_code))
    c.execute("""INSERT INTO payments (workspace, reference, amount, plan, status, created_at)
        VALUES (?, ?, ?, ?, 'success', ?)""", (workspace_code, ref, amount, plan, datetime.now().isoformat()))
    conn.commit()
    conn.close()


# ============================================================
# BUSINESS HELPERS — real-AI path + template fallback
# ============================================================
def analyze_lead(name, company, value, notes, api_key):
    if api_key:
        prompt = (f"Analyze this sales lead. Return ONLY JSON with keys score (0-100), priority "
                  f"(Hot/Warm/Cold), insight (one sentence), next_action (one sentence).\n\n"
                  f"Lead: {name}\nCompany: {company}\nValue: {value}\nNotes: {notes}")
        text, ok = call_claude(prompt, api_key)
        if ok:
            return parse_json_safe(text, {"score": 50, "priority": "Warm", "insight": text[:150], "next_action": "Follow up"}), True
    score = min(100, 30 + int(value / 10000))
    priority = "Hot" if score >= 70 else "Warm" if score >= 40 else "Cold"
    return {"score": score, "priority": priority,
            "insight": f"Estimated priority based on deal size (${value:,.0f}).",
            "next_action": "Reach out within 48 hours." if priority == "Hot" else "Add to regular follow-up cadence."}, False


def screen_resume(name, position, resume, api_key):
    if api_key:
        prompt = (f"Screen this candidate. Return ONLY JSON with keys score (0-100), strengths (list), "
                  f"concerns (list), verdict (Recommend/Maybe/Reject), interview_questions (list of 3).\n\n"
                  f"Position: {position}\nCandidate: {name}\nResume: {resume[:2000]}")
        text, ok = call_claude(prompt, api_key)
        if ok:
            return parse_json_safe(text, {"score": 50, "strengths": [], "concerns": [], "verdict": "Maybe", "interview_questions": []}), True
    return {"score": 50, "strengths": ["Not AI-screened — add a team API key for real analysis"], "concerns": [],
            "verdict": "Maybe", "interview_questions": [f"Tell me about your experience relevant to {position}.",
                                                          "What's a challenge you overcame recently?", "Why this role?"]}, False


def summarize_meeting(title, transcript, api_key):
    if api_key:
        prompt = (f"Summarize this meeting. Return ONLY JSON with keys summary (2-3 sentences), "
                  f"action_items (list), decisions (list), next_steps (list).\n\nMeeting: {title}\nTranscript: {transcript[:3000]}")
        text, ok = call_claude(prompt, api_key)
        if ok:
            return parse_json_safe(text, {"summary": text[:300], "action_items": [], "decisions": [], "next_steps": []}), True
    return {"summary": "Add a team API key in Settings to get an AI-generated summary.",
            "action_items": [], "decisions": [], "next_steps": []}, False


def summarize_document(title, content, api_key):
    if api_key:
        prompt = f"Summarize this document in 3-5 bullets plus a one-sentence TL;DR.\n\nTitle: {title}\nContent: {content[:3000]}"
        text, ok = call_claude(prompt, api_key)
        if ok:
            return text, True
    return f"TL;DR: Not AI-summarized (no team API key set). {len(content.split())} words — read below.", False


MESSAGE_TEMPLATES = {
    "Email": "Subject: {purpose}\n\nHi {recipient},\n\n{purpose}.\n\nBest regards,",
    "WhatsApp": "Hey {recipient}! 👋 Just following up — {purpose}.",
    "SMS": "{purpose}. Reply to discuss.",
    "LinkedIn": "Hi {recipient}, reaching out regarding {purpose}. Would love to connect.",
    "Slack": "Hey {recipient} — quick one: {purpose}.",
}


def draft_professional_message(channel, recipient, purpose, tone, extra, api_key):
    if api_key:
        prompt = (f"Write a professional {channel} message. Recipient: {recipient}. Purpose: {purpose}. "
                  f"Tone: {tone}. Extra context: {extra}. Write only the message body, no labels.")
        text, ok = call_claude(prompt, api_key)
        if ok:
            return text, True
    template = MESSAGE_TEMPLATES.get(channel, "{purpose}")
    return template.format(recipient=recipient or "there", purpose=purpose), False


def answer_ticket(customer, subject, message, api_key):
    if api_key:
        prompt = (f"You are a customer support agent. Write a helpful, empathetic response under 150 words.\n\n"
                  f"Customer: {customer}\nSubject: {subject}\nMessage: {message}")
        text, ok = call_claude(prompt, api_key)
        if ok:
            return text, True
    return (f"Hi {customer}, thanks for reaching out about \"{subject}\". We've received your message "
            f"and will follow up shortly. (Add a team API key for an AI-drafted response.)"), False


def generate_report(title, data, report_type, api_key):
    if api_key:
        prompt = f"Write a professional {report_type}. Title: {title}. Data: {data}. Include Executive Summary, Key Findings, Recommendations."
        text, ok = call_claude(prompt, api_key)
        if ok:
            return text, True
    return (f"# {title}\n\n## Executive Summary\n(Add a team API key for an AI-generated summary.)\n\n"
            f"## Raw Data\n{data}\n\n## Recommendations\n(Add a team API key for AI-generated recommendations.)"), False


def rows_to_csv(rows, columns):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r[k] for k in columns})
    return buf.getvalue()


# ============================================================
# SESSION STATE
# ============================================================
for key, default in [("user_id", None), ("buy_plan", None)]:
    if key not in st.session_state:
        st.session_state[key] = default


# ============================================================
# AUTH PAGES
# ============================================================
def auth_page():
    st.markdown("""
    <div style="text-align:center; padding:40px 0;">
        <h1 style="font-size:48px;">🏢 AI Business Suite</h1>
        <p style="opacity:0.7; font-size:18px;">Leads, HR, docs, tasks, reports — shared across your whole team.</p>
        <p style="color:#667eea; font-size:14px;">✨ 20 free AI actions/month • No credit card required</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Log In", "✨ Sign Up"])

        with tab1:
            with st.form("login"):
                u = st.text_input("Username or Email")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Log In", use_container_width=True):
                    if not u or not p:
                        st.error("Fill all fields")
                    else:
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("SELECT * FROM users WHERE username = ? OR email = ?", (u, u))
                        user = c.fetchone()
                        conn.close()
                        if user and verify_password(p, user["password_salt"], user["password_hash"]):
                            st.session_state.user_id = user["id"]
                            st.rerun()
                        else:
                            st.error("Invalid credentials.")

        with tab2:
            st.caption("Leave **Team code** blank to start a brand-new team. Enter your teammate's code to join theirs instead.")
            with st.form("signup"):
                n = st.text_input("Full Name")
                co = st.text_input("Company Name")
                team_code = st.text_input("Team code (optional)", placeholder="e.g. acme-4f2a — ask a teammate for this")
                u = st.text_input("Username")
                e = st.text_input("Email")
                p = st.text_input("Password", type="password")
                p2 = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    if not u or not e or not p or not n:
                        st.error("Fill all required fields")
                    elif p != p2:
                        st.error("Passwords don't match")
                    elif len(p) < 8:
                        st.error("Password must be 8+ characters")
                    else:
                        owner = is_owner_email(e)
                        if team_code.strip():
                            workspace_code = slugify(team_code)
                            existing = get_workspace(workspace_code)
                            role = "member" if existing else "admin"
                            if not existing:
                                create_workspace(workspace_code, co, unlimited=owner)
                        else:
                            workspace_code = f"{slugify(co)}-{pysecrets.token_hex(2)}"
                            role = "admin"
                            create_workspace(workspace_code, co, unlimited=owner)
                        if owner:
                            role = "admin"

                        try:
                            digest, salt = hash_password(p)
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("""INSERT INTO users (username, email, password_hash, password_salt,
                                name, workspace, role, is_app_owner, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (u, e, digest, salt, n, workspace_code, role, 1 if owner else 0, datetime.now().isoformat()))
                            conn.commit()
                            conn.close()
                            log_activity(workspace_code, n, "joined the team" if role == "member" else "created the team")
                            st.success(f"✅ Account created! Your team code is **{workspace_code}** — save this to invite teammates. Log in now.")
                        except sqlite3.IntegrityError:
                            st.error("Username or email already exists")


# ============================================================
# MAIN APP
# ============================================================
def main_app():
    user_id = st.session_state.user_id
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if not user:
        st.session_state.user_id = None
        st.rerun()
        return

    workspace_code = user["workspace"]
    ws = get_workspace(workspace_code)
    is_app_owner = bool(user["is_app_owner"])
    is_admin = user["role"] == "admin" or is_app_owner
    api_key = (ws["anthropic_key"] if ws else "") or ""
    remaining = "∞" if is_app_owner else (max(0, (ws["actions_limit"] or 20) - (ws["actions_used"] or 0)) if ws else 0)

    with st.sidebar:
        st.markdown("### 🏢 AI Business Suite")
        st.caption(f"👤 {user['name']} · {user['role'].title()}")
        if ws and ws["company_name"]:
            st.caption(f"🏢 {ws['company_name']}")
        st.divider()
        st.metric("💬 Team AI Actions Left", remaining)
        st.caption(f"📦 Plan: **{PLANS.get(ws['plan'], PLANS['free'])['name'] if ws else 'Free Trial'}**")
        if not api_key:
            st.warning("No team API key set — AI features use basic templates.")
        if is_app_owner:
            st.success("👑 App owner — unlimited")
        st.divider()
        page = st.radio("Navigation", [
            "📊 Dashboard", "🎯 Sales & Leads", "👥 HR & Hiring", "📄 Documents",
            "📝 Meeting Notes", "✉️ Message Writer", "🎫 Support Tickets",
            "✅ Task Manager", "📊 Reports", "🧑‍🤝‍🧑 Team", "🔔 Activity Log",
            "💳 Billing", "⚙️ Settings",
        ], label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Log Out", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    def use_ai_action():
        if not ws or not can_use_ai(ws, is_app_owner):
            st.error("❌ Team is out of AI actions for this plan. An admin can upgrade in Billing — templates still work for free.")
            return False
        if api_key:
            increment_usage(workspace_code)
        return True

    def team_members():
        conn = get_db()
        rows = conn.execute("SELECT name FROM users WHERE workspace = ? ORDER BY name", (workspace_code,)).fetchall()
        conn.close()
        return [r["name"] for r in rows]

    # --------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------
    if page == "📊 Dashboard":
        st.title(f"Welcome, {user['name']} 👋")
        if ws and ws["company_name"]:
            st.caption(f"🏢 {ws['company_name']} — team code: `{workspace_code}`")

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as x, COALESCE(SUM(value),0) as v FROM leads WHERE workspace = ?", (workspace_code,))
        lead_row = c.fetchone()
        c.execute("SELECT COUNT(*) as x FROM candidates WHERE workspace = ?", (workspace_code,))
        cands = c.fetchone()["x"]
        c.execute("SELECT COUNT(*) as x FROM tickets WHERE workspace = ? AND status = 'Open'", (workspace_code,))
        tickets = c.fetchone()["x"]
        c.execute("SELECT COUNT(*) as x FROM tasks WHERE workspace = ? AND status = 'Pending'", (workspace_code,))
        tasks = c.fetchone()["x"]
        conn.close()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🎯 Leads", lead_row["x"], f"₦{lead_row['v']:,.0f} pipeline")
        c2.metric("👥 Candidates", cands)
        c3.metric("🎫 Open Tickets", tickets)
        c4.metric("✅ Pending Tasks", tasks)

        st.divider()
        st.subheader("🔍 Search everything")
        query = st.text_input("Search leads, candidates, tasks, tickets by name/title", label_visibility="collapsed", placeholder="Type to search...")
        if query:
            conn = get_db()
            like = f"%{query}%"
            l = conn.execute("SELECT name, company FROM leads WHERE workspace=? AND (name LIKE ? OR company LIKE ?)", (workspace_code, like, like)).fetchall()
            cd = conn.execute("SELECT name, position FROM candidates WHERE workspace=? AND (name LIKE ? OR position LIKE ?)", (workspace_code, like, like)).fetchall()
            ts = conn.execute("SELECT title, status FROM tasks WHERE workspace=? AND title LIKE ?", (workspace_code, like)).fetchall()
            tix = conn.execute("SELECT subject, customer FROM tickets WHERE workspace=? AND (subject LIKE ? OR customer LIKE ?)", (workspace_code, like, like)).fetchall()
            conn.close()
            if not (l or cd or ts or tix):
                st.caption("No matches.")
            for row in l:
                st.write(f"🎯 Lead: **{row['name']}** — {row['company']}")
            for row in cd:
                st.write(f"👤 Candidate: **{row['name']}** — {row['position']}")
            for row in ts:
                st.write(f"✅ Task: **{row['title']}** — {row['status']}")
            for row in tix:
                st.write(f"🎫 Ticket: **{row['subject']}** — {row['customer']}")

        st.divider()
        try:
            import plotly.express as px
            import pandas as pd
            conn = get_db()
            leads_df_rows = conn.execute("SELECT status, COUNT(*) as n FROM leads WHERE workspace = ? GROUP BY status", (workspace_code,)).fetchall()
            conn.close()
            if leads_df_rows:
                chart_df = pd.DataFrame([dict(r) for r in leads_df_rows])
                fig = px.pie(chart_df, names="status", values="n", title="Lead pipeline by status", hole=0.4)
                fig.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

    # --------------------------------------------------
    # SALES
    # --------------------------------------------------
    elif page == "🎯 Sales & Leads":
        st.title("🎯 Sales & Lead Management")

        with st.expander("➕ Add New Lead", expanded=False):
            with st.form("new_lead"):
                c1, c2 = st.columns(2)
                with c1:
                    name = st.text_input("Lead Name")
                    email = st.text_input("Email")
                with c2:
                    company = st.text_input("Company")
                    value = st.number_input("Deal Value (₦)", 0.0, 100000000.0, 500000.0, 50000.0)
                notes = st.text_area("Notes", height=80)
                if st.form_submit_button("Analyze & Save", use_container_width=True):
                    if not name:
                        st.error("Name required")
                    elif not use_ai_action():
                        pass
                    else:
                        with st.spinner("Analyzing..."):
                            a, was_ai = analyze_lead(name, company, value, notes, api_key)
                        tag = "🤖" if was_ai else "📐"
                        conn = get_db(); c = conn.cursor()
                        c.execute("""INSERT INTO leads (workspace, user_id, created_by, name, email, company, value, status, score, notes, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (workspace_code, user_id, user["name"], name, email, company, value, a.get("priority", "Warm"),
                             a.get("score", 50), notes + f"\n\n{tag} {a.get('insight','')}\n➡️ {a.get('next_action','')}",
                             datetime.now().isoformat()))
                        conn.commit(); conn.close()
                        log_activity(workspace_code, user["name"], "added a lead", name)
                        st.success(f"Score: {a.get('score',50)}/100 — {a.get('priority','Warm')}")
                        st.rerun()

        st.divider()
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM leads WHERE workspace = ? ORDER BY created_at DESC", (workspace_code,))
        leads = c.fetchall(); conn.close()

        if not leads:
            st.info("No leads yet.")
        else:
            with st.expander("🔍 Filter"):
                status_filter = st.multiselect("Status", sorted(set(l["status"] for l in leads)))
            shown = [l for l in leads if not status_filter or l["status"] in status_filter]
            total = sum(l["value"] for l in shown)
            avg = sum(l["score"] for l in shown) / len(shown) if shown else 0
            c1, c2, c3 = st.columns(3)
            c1.metric("Leads shown", len(shown))
            c2.metric("Pipeline", f"₦{total:,.0f}")
            c3.metric("Avg Score", f"{avg:.0f}/100")
            st.download_button("⬇ Export leads CSV", rows_to_csv(shown, ["name", "email", "company", "value", "status", "score", "notes", "created_by", "created_at"]),
                                "leads.csv", "text/csv")
            for l in shown:
                with st.expander(f"🎯 {l['name']} — {l['company']} — Score: {l['score']}/100"):
                    st.write(f"**Value:** ₦{l['value']:,.0f}  ·  **Added by:** {l['created_by'] or '—'}")
                    st.write(f"**Status:** {l['status']}")
                    st.text(l["notes"] or "")
                    if st.button("🗑️ Delete", key=f"dl_{l['id']}"):
                        conn = get_db(); c = conn.cursor()
                        c.execute("DELETE FROM leads WHERE id = ?", (l["id"],))
                        conn.commit(); conn.close()
                        log_activity(workspace_code, user["name"], "deleted a lead", l["name"])
                        st.rerun()

    # --------------------------------------------------
    # HR
    # --------------------------------------------------
    elif page == "👥 HR & Hiring":
        st.title("👥 HR & Hiring")
        with st.expander("➕ Screen New Candidate", expanded=False):
            with st.form("new_cand"):
                name = st.text_input("Candidate Name")
                position = st.text_input("Position")
                resume = st.text_area("Resume / CV Text", height=200)
                if st.form_submit_button("Screen Resume", use_container_width=True):
                    if not name or not resume:
                        st.error("Name and resume required")
                    elif not use_ai_action():
                        pass
                    else:
                        with st.spinner("Screening..."):
                            a, was_ai = screen_resume(name, position, resume, api_key)
                        conn = get_db(); c = conn.cursor()
                        c.execute("""INSERT INTO candidates (workspace, user_id, created_by, name, position, resume, score, analysis, status, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (workspace_code, user_id, user["name"], name, position, resume, a.get("score", 50),
                             json.dumps(a), a.get("verdict", "Maybe"), datetime.now().isoformat()))
                        conn.commit(); conn.close()
                        log_activity(workspace_code, user["name"], "screened a candidate", name)
                        st.success(f"Score: {a.get('score',50)}/100 — {a.get('verdict','Maybe')}")
                        st.rerun()

        st.divider()
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM candidates WHERE workspace = ? ORDER BY created_at DESC", (workspace_code,))
        cands = c.fetchall(); conn.close()
        if cands:
            st.download_button("⬇ Export candidates CSV", rows_to_csv(cands, ["name", "position", "score", "status", "created_by", "created_at"]),
                                "candidates.csv", "text/csv")
        for cand in cands:
            with st.expander(f"👤 {cand['name']} — {cand['position']} — {cand['score']}/100"):
                a = parse_json_safe(cand["analysis"], {})
                st.caption(f"Screened by {cand['created_by'] or '—'}")
                st.write(f"**Strengths:** {', '.join(a.get('strengths', []))}")
                st.write(f"**Concerns:** {', '.join(a.get('concerns', []))}")
                st.write(f"**Verdict:** {a.get('verdict','Maybe')}")
                st.write("**Interview Questions:**")
                for q in a.get("interview_questions", []):
                    st.write(f"- {q}")
                if st.button("🗑️ Delete", key=f"dc_{cand['id']}"):
                    conn = get_db(); c = conn.cursor()
                    c.execute("DELETE FROM candidates WHERE id = ?", (cand["id"],))
                    conn.commit(); conn.close(); st.rerun()

    # --------------------------------------------------
    # DOCUMENTS
    # --------------------------------------------------
    elif page == "📄 Documents":
        st.title("📄 Document Analyzer")
        with st.form("new_doc"):
            title = st.text_input("Document Title")
            doc_type = st.selectbox("Type", ["Contract", "Report", "Policy", "General", "Research", "Legal"])
            content = st.text_area("Paste Content", height=250)
            if st.form_submit_button("Summarize", use_container_width=True):
                if not title or not content:
                    st.error("Title and content required")
                elif not use_ai_action():
                    pass
                else:
                    with st.spinner("Summarizing..."):
                        s, was_ai = summarize_document(title, content, api_key)
                    conn = get_db(); c = conn.cursor()
                    c.execute("""INSERT INTO documents (workspace, user_id, created_by, title, content, summary, doc_type, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (workspace_code, user_id, user["name"], title, content, s, doc_type, datetime.now().isoformat()))
                    conn.commit(); conn.close()
                    log_activity(workspace_code, user["name"], "summarized a document", title)
                    st.success("Analyzed!"); st.rerun()

        st.divider()
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM documents WHERE workspace = ? ORDER BY created_at DESC", (workspace_code,))
        docs = c.fetchall(); conn.close()
        if docs:
            st.download_button("⬇ Export documents CSV", rows_to_csv(docs, ["title", "doc_type", "summary", "created_by", "created_at"]),
                                "documents.csv", "text/csv")
        for d in docs:
            with st.expander(f"📄 {d['title']} ({d['doc_type']})"):
                st.caption(f"Added by {d['created_by'] or '—'}")
                st.write(d["summary"])
                if st.button("🗑️ Delete", key=f"dd_{d['id']}"):
                    conn = get_db(); c = conn.cursor()
                    c.execute("DELETE FROM documents WHERE id = ?", (d["id"],))
                    conn.commit(); conn.close(); st.rerun()

    # --------------------------------------------------
    # MEETINGS
    # --------------------------------------------------
    elif page == "📝 Meeting Notes":
        st.title("📝 Meeting Summarizer")
        with st.form("new_meeting"):
            title = st.text_input("Meeting Title")
            attendees = st.text_input("Attendees (comma separated)")
            transcript = st.text_area("Paste Transcript", height=250)
            if st.form_submit_button("Summarize", use_container_width=True):
                if not title or not transcript:
                    st.error("Title and transcript required")
                elif not use_ai_action():
                    pass
                else:
                    with st.spinner("Analyzing..."):
                        r, was_ai = summarize_meeting(title, transcript, api_key)
                    conn = get_db(); c = conn.cursor()
                    c.execute("""INSERT INTO meetings (workspace, user_id, created_by, title, transcript, summary, action_items, attendees, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (workspace_code, user_id, user["name"], title, transcript, r.get("summary", ""),
                         json.dumps(r.get("action_items", [])), attendees, datetime.now().isoformat()))
                    conn.commit(); conn.close()
                    log_activity(workspace_code, user["name"], "summarized a meeting", title)
                    st.success("Analyzed!"); st.rerun()

        st.divider()
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM meetings WHERE workspace = ? ORDER BY created_at DESC", (workspace_code,))
        meetings = c.fetchall(); conn.close()
        for m in meetings:
            with st.expander(f"📝 {m['title']} — {m['created_at'][:19]}"):
                st.caption(f"Logged by {m['created_by'] or '—'}")
                st.write(f"**Attendees:** {m['attendees'] or '—'}")
                st.write("**Summary:**"); st.write(m["summary"])
                items = parse_json_safe(m["action_items"], [])
                if items:
                    st.write("**Action Items:**")
                    for i in items:
                        st.write(f"✅ {i}")

    # --------------------------------------------------
    # MESSAGE WRITER
    # --------------------------------------------------
    elif page == "✉️ Message Writer":
        st.title("✉️ Professional Message Writer")
        st.caption("Email • WhatsApp • SMS • LinkedIn • Slack")
        with st.form("new_message"):
            c1, c2 = st.columns(2)
            with c1:
                channel = st.selectbox("Channel", ["Email", "WhatsApp", "SMS", "LinkedIn", "Slack"])
                recipient = st.text_input("Recipient", placeholder="Name or role")
            with c2:
                tone = st.selectbox("Tone", ["Professional", "Friendly", "Formal", "Casual", "Persuasive", "Urgent"])
                purpose = st.text_input("Purpose", placeholder="e.g. Follow up on quote")
            extra = st.text_area("Extra context (optional)", height=100)
            if st.form_submit_button("Draft Message", use_container_width=True):
                if not purpose:
                    st.error("Purpose required")
                elif not use_ai_action():
                    pass
                else:
                    with st.spinner(f"Writing {channel}..."):
                        body, was_ai = draft_professional_message(channel, recipient, purpose, tone, extra, api_key)
                    conn = get_db(); c = conn.cursor()
                    c.execute("""INSERT INTO messages_writer (workspace, user_id, created_by, recipient, channel, tone, purpose, body, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (workspace_code, user_id, user["name"], recipient, channel, tone, purpose, body, datetime.now().isoformat()))
                    conn.commit(); conn.close()
                    st.success("Draft ready!"); st.rerun()

        st.divider()
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM messages_writer WHERE workspace = ? ORDER BY created_at DESC", (workspace_code,))
        msgs = c.fetchall(); conn.close()
        for m in msgs:
            with st.expander(f"✉️ [{m['channel']}] → {m['recipient']} — {m['tone']}"):
                st.write(m["body"])
                st.download_button("📥 Download", m["body"], f"{m['channel']}_{m['id']}.txt", key=f"dm_{m['id']}")

    # --------------------------------------------------
    # SUPPORT TICKETS
    # --------------------------------------------------
    elif page == "🎫 Support Tickets":
        st.title("🎫 Customer Support")
        with st.form("new_ticket"):
            customer = st.text_input("Customer Name")
            subject = st.text_input("Subject")
            message = st.text_area("Customer Message", height=150)
            if st.form_submit_button("Draft Response", use_container_width=True):
                if not message:
                    st.error("Message required")
                elif not use_ai_action():
                    pass
                else:
                    with st.spinner("Drafting..."):
                        r, was_ai = answer_ticket(customer, subject, message, api_key)
                    conn = get_db(); c = conn.cursor()
                    c.execute("""INSERT INTO tickets (workspace, user_id, created_by, customer, subject, message, ai_response, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (workspace_code, user_id, user["name"], customer, subject, message, r, datetime.now().isoformat()))
                    conn.commit(); conn.close()
                    st.success("Ready!"); st.rerun()

        st.divider()
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM tickets WHERE workspace = ? ORDER BY created_at DESC", (workspace_code,))
        tickets = c.fetchall(); conn.close()
        if tickets:
            st.download_button("⬇ Export tickets CSV", rows_to_csv(tickets, ["customer", "subject", "status", "created_by", "created_at"]),
                                "tickets.csv", "text/csv")
        for t in tickets:
            with st.expander(f"🎫 [{t['status']}] {t['subject']} — {t['customer']}"):
                st.write("**Customer:**"); st.write(t["message"])
                st.write("**Response:**"); st.write(t["ai_response"])
                if t["status"] == "Open":
                    if st.button("✅ Resolve", key=f"rt_{t['id']}"):
                        conn = get_db(); c = conn.cursor()
                        c.execute("UPDATE tickets SET status = 'Resolved' WHERE id = ?", (t["id"],))
                        conn.commit(); conn.close()
                        log_activity(workspace_code, user["name"], "resolved a ticket", t["subject"])
                        st.rerun()

    # --------------------------------------------------
    # TASKS
    # --------------------------------------------------
    elif page == "✅ Task Manager":
        st.title("✅ Task Manager")
        members = team_members()
        with st.form("new_task"):
            title = st.text_input("Task")
            desc = st.text_area("Details", height=80)
            c1, c2, c3 = st.columns(3)
            with c1:
                priority = st.selectbox("Priority", ["Low", "Medium", "High", "Urgent"])
            with c2:
                due = st.date_input("Due date", value=date.today())
            with c3:
                assignee = st.selectbox("Assign to", ["Unassigned"] + members)
            if st.form_submit_button("Add Task", use_container_width=True):
                if not title:
                    st.error("Task required")
                else:
                    conn = get_db(); c = conn.cursor()
                    c.execute("""INSERT INTO tasks (workspace, user_id, created_by, assigned_to, title, description, priority, due_date, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending', ?)""",
                        (workspace_code, user_id, user["name"], assignee, title, desc, priority, str(due), datetime.now().isoformat()))
                    conn.commit(); conn.close()
                    log_activity(workspace_code, user["name"], "added a task", title)
                    st.rerun()

        st.divider()
        view_mine = st.toggle("Show only my tasks", value=False)
        conn = get_db(); c = conn.cursor()
        c.execute("""SELECT * FROM tasks WHERE workspace = ?
            ORDER BY CASE priority WHEN 'Urgent' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, due_date""", (workspace_code,))
        tasks = c.fetchall(); conn.close()
        if view_mine:
            tasks = [t for t in tasks if t["assigned_to"] == user["name"]]
        if tasks:
            st.download_button("⬇ Export tasks CSV", rows_to_csv(tasks, ["title", "description", "priority", "status", "due_date", "assigned_to", "created_by", "created_at"]),
                                "tasks.csv", "text/csv")
        overdue_ids = {t["id"] for t in tasks if t["status"] == "Pending" and t["due_date"] < str(date.today())}
        if overdue_ids:
            st.error(f"⚠️ {len(overdue_ids)} task(s) overdue.")
        for t in tasks:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    icon = {"Urgent": "🔴", "High": "🟠", "Medium": "🟡"}.get(t["priority"], "🟢")
                    late = " ⏰ OVERDUE" if t["id"] in overdue_ids else ""
                    st.write(f"{icon} **{t['title']}**{late}")
                    st.caption(f"Due: {t['due_date']} • {t['priority']} • Assigned to: {t['assigned_to'] or 'Unassigned'}")
                with c2:
                    st.write(f"**{t['status']}**")
                with c3:
                    if t["status"] == "Pending":
                        if st.button("✅", key=f"done_{t['id']}"):
                            conn = get_db(); c = conn.cursor()
                            c.execute("UPDATE tasks SET status = 'Done' WHERE id = ?", (t["id"],))
                            conn.commit(); conn.close()
                            log_activity(workspace_code, user["name"], "completed a task", t["title"])
                            st.rerun()
                    else:
                        if st.button("🗑️", key=f"dt_{t['id']}"):
                            conn = get_db(); c = conn.cursor()
                            c.execute("DELETE FROM tasks WHERE id = ?", (t["id"],))
                            conn.commit(); conn.close(); st.rerun()

    # --------------------------------------------------
    # REPORTS
    # --------------------------------------------------
    elif page == "📊 Reports":
        st.title("📊 Report Generator")
        with st.form("new_report"):
            title = st.text_input("Report Title")
            report_type = st.selectbox("Type", ["Sales Report", "Performance Review", "Market Analysis", "Financial Summary", "Project Status", "Weekly Update"])
            data = st.text_area("Data / Context", height=200)
            if st.form_submit_button("Generate Report", use_container_width=True):
                if not title or not data:
                    st.error("Title and data required")
                elif not use_ai_action():
                    pass
                else:
                    with st.spinner("Writing..."):
                        content, was_ai = generate_report(title, data, report_type, api_key)
                    conn = get_db(); c = conn.cursor()
                    c.execute("""INSERT INTO reports (workspace, user_id, created_by, title, content, report_type, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (workspace_code, user_id, user["name"], title, content, report_type, datetime.now().isoformat()))
                    conn.commit(); conn.close()
                    log_activity(workspace_code, user["name"], "generated a report", title)
                    st.rerun()

        st.divider()
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM reports WHERE workspace = ? ORDER BY created_at DESC", (workspace_code,))
        reports = c.fetchall(); conn.close()
        for r in reports:
            with st.expander(f"📊 {r['title']} ({r['report_type']})"):
                st.caption(f"By {r['created_by'] or '—'}")
                st.write(r["content"])
                st.download_button("📥 Download", r["content"], f"{r['title']}.txt", key=f"dr_{r['id']}")

    # --------------------------------------------------
    # TEAM
    # --------------------------------------------------
    elif page == "🧑‍🤝‍🧑 Team":
        st.title("🧑‍🤝‍🧑 Team")
        st.write("Share this code with teammates so they can join your workspace during sign up:")
        st.code(workspace_code, language=None)
        st.divider()
        conn = get_db()
        members = conn.execute("SELECT name, email, role, created_at FROM users WHERE workspace = ? ORDER BY created_at", (workspace_code,)).fetchall()
        conn.close()
        st.subheader(f"{len(members)} member(s)")
        for m in members:
            c1, c2 = st.columns([3, 1])
            c1.write(f"**{m['name']}** — {m['email']}")
            c2.write(f"`{m['role']}`")

    # --------------------------------------------------
    # ACTIVITY LOG
    # --------------------------------------------------
    elif page == "🔔 Activity Log":
        st.title("🔔 Activity Log")
        st.caption("Everything your team has done in this app, most recent first.")
        conn = get_db()
        rows = conn.execute("SELECT * FROM activity_log WHERE workspace = ? ORDER BY created_at DESC LIMIT 200", (workspace_code,)).fetchall()
        conn.close()
        if not rows:
            st.info("No activity yet.")
        for r in rows:
            st.write(f"**{r['user_name']}** {r['action']}" + (f" — *{r['detail']}*" if r["detail"] else "") + f"  \n{r['created_at'][:19]}")
            st.divider()

    # --------------------------------------------------
    # BILLING
    # --------------------------------------------------
    elif page == "💳 Billing":
        st.title("💳 Billing & Subscription")
        if is_app_owner:
            st.success("👑 App owner — unlimited free access")

        c1, c2, c3 = st.columns(3)
        c1.metric("Team Plan", PLANS.get(ws["plan"], PLANS["free"])["name"] if ws else "Free Trial")
        c2.metric("AI Actions Left", remaining if isinstance(remaining, int) else "∞")
        c3.metric("Used this cycle", ws["actions_used"] if ws else 0)
        if ws and ws["plan_expires"]:
            st.caption(f"📅 Renews: {ws['plan_expires'][:10]}")

        if not is_admin:
            st.info("Only a team admin can change the plan. Ask your team admin to upgrade if you need more AI actions.")
        else:
            st.divider()
            st.subheader("Plans")
            cols = st.columns(4)
            for col, (key, plan) in zip(cols, PLANS.items()):
                with col:
                    with st.container(border=True):
                        st.subheader(plan["name"])
                        price_label = "Free" if plan["price"] == 0 else f"₦{plan['price']:,}/mo"
                        st.markdown(f"### {price_label}")
                        st.caption(f"{plan['actions']:,} AI actions")
                        for f in plan["features"][:3]:
                            st.write(f"✅ {f}")
                        if ws and key == ws["plan"]:
                            st.info("Current plan")
                        elif key == "free":
                            st.caption("—")
                        else:
                            if st.button("Buy", key=f"buy_{key}", use_container_width=True):
                                st.session_state.buy_plan = key
                                st.rerun()

            paystack_key = (ws["paystack_key"] if ws else "") or ""
            if st.session_state.get("buy_plan"):
                plan = st.session_state.buy_plan
                st.divider()
                st.subheader(f"Checkout — {PLANS[plan]['name']}")
                st.write(f"**Amount:** ₦{PLANS[plan]['price']:,}")
                if not paystack_key:
                    st.info("Payments aren't configured yet. Add a Paystack secret key in Settings first.")
                else:
                    if "pending_ref" not in st.session_state:
                        pay = init_paystack_payment(user["email"], PLANS[plan]["price"], plan, paystack_key)
                        if pay:
                            st.session_state.pending_ref = pay["ref"]
                            st.markdown(f"[👉 Click here to pay ₦{PLANS[plan]['price']:,}]({pay['url']})")
                        else:
                            st.error("Couldn't start payment. Check the Paystack key.")
                    else:
                        st.markdown("Complete payment in the tab that opened, then click below.")
                        if st.button("✅ I've paid — verify"):
                            result = verify_paystack(st.session_state.pending_ref, paystack_key)
                            if result:
                                activate_plan(workspace_code, plan, st.session_state.pending_ref, PLANS[plan]["price"])
                                del st.session_state.pending_ref
                                st.session_state.buy_plan = None
                                log_activity(workspace_code, user["name"], "upgraded the team plan", plan)
                                st.success("Plan activated!")
                                st.rerun()
                            else:
                                st.warning("Payment not confirmed yet.")
                if st.button("← Back to plans"):
                    st.session_state.buy_plan = None
                    st.session_state.pop("pending_ref", None)
                    st.rerun()

        st.divider()
        st.subheader("Payment History")
        conn = get_db()
        payments = conn.execute("SELECT * FROM payments WHERE workspace = ? ORDER BY created_at DESC", (workspace_code,)).fetchall()
        conn.close()
        if not payments:
            st.info("No payments yet.")
        else:
            for p in payments:
                st.write(f"💳 ₦{p['amount']:,.0f} — {p['plan'].title()} — {p['status']} — {p['created_at'][:19]}")

    # --------------------------------------------------
    # SETTINGS
    # --------------------------------------------------
    elif page == "⚙️ Settings":
        st.title("Settings")
        st.subheader("Your Account")
        st.write(f"**Name:** {user['name']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Role:** {user['role'].title()}")
        st.write(f"**Team:** {ws['company_name'] if ws else '—'} (`{workspace_code}`)")

        st.divider()
        st.subheader("🔑 Team AI (Anthropic) API Key")
        st.caption("Shared by everyone on your team. Without it, AI features fall back to simple built-in "
                    "templates — still functional, just not AI-generated. Get a key at console.anthropic.com.")
        if is_admin:
            new_key = st.text_input("Anthropic API key", value=api_key, type="password")
            if st.button("💾 Save Team API Key"):
                conn = get_db(); c = conn.cursor()
                c.execute("UPDATE workspaces SET anthropic_key = ? WHERE code = ?", (new_key, workspace_code))
                conn.commit(); conn.close()
                st.success("Saved!"); st.rerun()
        else:
            st.info("Only a team admin can change the shared API key.")
            st.write("Key is currently " + ("set ✅" if api_key else "not set ❌"))

        if is_admin:
            st.divider()
            st.subheader("👑 Admin: Payments")
            st.caption("Add a Paystack secret key to enable real billing for your team. Get one at dashboard.paystack.com.")
            pk = st.text_input("Paystack Secret Key", type="password", value=(ws["paystack_key"] if ws else "") or "")
            if st.button("💾 Save Paystack Key"):
                conn = get_db(); c = conn.cursor()
                c.execute("UPDATE workspaces SET paystack_key = ? WHERE code = ?", (pk, workspace_code))
                conn.commit(); conn.close()
                st.success("Saved!"); st.rerun()

        if is_app_owner:
            st.divider()
            st.subheader("🛠️ App Owner Panel")
            conn = get_db()
            tu = conn.execute("SELECT COUNT(*) as x FROM users").fetchone()["x"]
            tw = conn.execute("SELECT COUNT(*) as x FROM workspaces").fetchone()["x"]
            rev = conn.execute("SELECT COALESCE(SUM(amount),0) as s FROM payments WHERE status='success'").fetchone()["s"]
            conn.close()
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Users", tu)
            c2.metric("Total Teams", tw)
            c3.metric("Total Revenue", f"₦{rev:,.0f}")


# ============================================================
# ROUTER
# ============================================================
if st.session_state.user_id is None:
    auth_page()
else:
    main_app()
