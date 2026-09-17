import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os
import uuid
import requests

st.set_page_config(page_title="Decision Tracker", page_icon="🧭", layout="wide")

DATA_DIR = "data"
DECISIONS_FILE = os.path.join(DATA_DIR, "decisions.csv")
AUDIT_FILE = os.path.join(DATA_DIR, "audit_log.csv")

DECISION_COLUMNS = [
    "id", "title", "owner", "category", "priority", "date_made", "review_date",
    "expected_outcome", "status", "actual_outcome", "created_by",
    "last_updated_by", "last_updated_at",
]
AUDIT_COLUMNS = ["timestamp", "user", "action", "decision_id", "details"]

CATEGORIES = ["Hiring", "Finance/Budget", "Product", "Vendor/Contract", "Pricing", "Process", "Other"]
PRIORITIES = ["High", "Medium", "Low"]
STATUSES = ["Open", "Confirmed correct", "Turned out wrong", "Abandoned"]


# ---------------------------------------------------------
# Storage — shared CSV files on the server
# ---------------------------------------------------------

def ensure_storage():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DECISIONS_FILE):
        seed = pd.DataFrame({
            "id": [str(uuid.uuid4())[:8] for _ in range(3)],
            "title": ["Switch to new invoicing vendor", "Freeze hiring in Q3", "Raise prices 8%"],
            "owner": ["Sam (Ops)", "Priya (Finance)", "Marcus (Sales)"],
            "category": ["Vendor/Contract", "Hiring", "Pricing"],
            "priority": ["Medium", "High", "High"],
            "date_made": [datetime.today().date() - timedelta(days=70),
                           datetime.today().date() - timedelta(days=40),
                           datetime.today().date() - timedelta(days=10)],
            "review_date": [datetime.today().date() - timedelta(days=10),
                             datetime.today().date() + timedelta(days=5),
                             datetime.today().date() + timedelta(days=80)],
            "expected_outcome": ["Save 15% on processing fees", "Reduce burn by $40k/month",
                                  "Improve margin without losing >5% of customers"],
            "status": ["Open", "Open", "Open"],
            "actual_outcome": ["", "", ""],
            "created_by": ["system", "system", "system"],
            "last_updated_by": ["system", "system", "system"],
            "last_updated_at": [datetime.today()] * 3,
        })
        seed.to_csv(DECISIONS_FILE, index=False)
    if not os.path.exists(AUDIT_FILE):
        pd.DataFrame(columns=AUDIT_COLUMNS).to_csv(AUDIT_FILE, index=False)


def load_decisions():
    df = pd.read_csv(DECISIONS_FILE)
    df["date_made"] = pd.to_datetime(df["date_made"], errors="coerce")
    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
    return df


def save_decisions(df):
    df.to_csv(DECISIONS_FILE, index=False)


def log_audit(user, action, decision_id, details=""):
    entry = pd.DataFrame([{
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user": user, "action": action, "decision_id": decision_id, "details": details,
    }])
    entry.to_csv(AUDIT_FILE, mode="a", header=False, index=False)


def load_audit():
    return pd.read_csv(AUDIT_FILE)


# ---------------------------------------------------------
# Slack
# ---------------------------------------------------------

def send_slack_message(webhook_url, text):
    try:
        resp = requests.post(webhook_url, json={"text": text}, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------
# Simple access gate (name required, optional shared password)
# ---------------------------------------------------------

ensure_storage()

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

team_password = st.secrets.get("TEAM_PASSWORD", None) if hasattr(st, "secrets") else None

if not st.session_state.user_name:
    st.title("🧭 Decision Log & Follow-Through Tracker")
    st.write("Enter your name to continue. This is used to track who logged and reviewed each decision — "
             "it is not a secure login, just attribution.")
    name_input = st.text_input("Your name")
    pw_input = st.text_input("Team password", type="password") if team_password else None
    if st.button("Continue", type="primary"):
        if not name_input.strip():
            st.warning("Please enter your name.")
        elif team_password and pw_input != team_password:
            st.error("Incorrect team password.")
        else:
            st.session_state.user_name = name_input.strip()
            st.rerun()
    st.stop()

current_user = st.session_state.user_name

# ---------------------------------------------------------
# Sidebar — add decision, filters, Slack, export
# ---------------------------------------------------------

st.sidebar.write(f"Logged in as **{current_user}**")
if st.sidebar.button("Switch user"):
    st.session_state.user_name = ""
    st.rerun()

st.sidebar.divider()
st.sidebar.header("Log a new decision")
with st.sidebar.form("new_decision", clear_on_submit=True):
    title = st.text_input("Decision")
    owner = st.text_input("Owner", value=current_user)
    category = st.selectbox("Category", CATEGORIES)
    priority = st.selectbox("Priority", PRIORITIES, index=1)
    date_made = st.date_input("Date decided", value=datetime.today().date())
    review_date = st.date_input("Review this by", value=datetime.today().date() + timedelta(days=30))
    expected_outcome = st.text_area("Expected outcome")
    submitted = st.form_submit_button("Add decision", type="primary")

    if submitted and title.strip():
        df = load_decisions()
        new_id = str(uuid.uuid4())[:8]
        new_row = pd.DataFrame([{
            "id": new_id, "title": title, "owner": owner, "category": category,
            "priority": priority, "date_made": date_made, "review_date": review_date,
            "expected_outcome": expected_outcome, "status": "Open", "actual_outcome": "",
            "created_by": current_user, "last_updated_by": current_user,
            "last_updated_at": datetime.now(),
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        save_decisions(df)
        log_audit(current_user, "created", new_id, title)
        st.sidebar.success("Decision logged.")
        st.rerun()

st.sidebar.divider()
st.sidebar.header("Slack alerts (optional, free)")
st.sidebar.caption("Create a free incoming webhook in your Slack workspace settings, then paste the URL here.")
webhook_url = st.sidebar.text_input("Slack webhook URL", type="password")

st.sidebar.divider()
st.sidebar.header("Backup")
st.sidebar.caption("Download regularly — data can be lost if the app restarts.")
decisions_now = load_decisions()
st.sidebar.download_button("⬇ Export decisions CSV", decisions_now.to_csv(index=False), "decisions.csv", "text/csv")
st.sidebar.download_button("⬇ Export audit log CSV", load_audit().to_csv(index=False), "audit_log.csv", "text/csv")

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

st.title("🧭 Decision Log & Follow-Through Tracker")
st.caption("Tracks whether decisions actually got revisited — and what happened. Shared across everyone using this app.")

df = load_decisions()
today = pd.Timestamp(datetime.today().date())

# Filters
with st.expander("🔍 Filter"):
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    f_status = fcol1.multiselect("Status", STATUSES)
    f_owner = fcol2.multiselect("Owner", sorted(df["owner"].dropna().unique().tolist()))
    f_category = fcol3.multiselect("Category", CATEGORIES)
    f_priority = fcol4.multiselect("Priority", PRIORITIES)
    search = st.text_input("Search title")

filtered = df.copy()
if f_status:
    filtered = filtered[filtered["status"].isin(f_status)]
if f_owner:
    filtered = filtered[filtered["owner"].isin(f_owner)]
if f_category:
    filtered = filtered[filtered["category"].isin(f_category)]
if f_priority:
    filtered = filtered[filtered["priority"].isin(f_priority)]
if search:
    filtered = filtered[filtered["title"].str.contains(search, case=False, na=False)]

overdue = df[(df["status"] == "Open") & (df["review_date"] < today)]
upcoming = df[(df["status"] == "Open") & (df["review_date"] >= today)]
closed = df[df["status"] != "Open"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total decisions", len(df))
col2.metric("Overdue for review", len(overdue))
col3.metric("Upcoming reviews", len(upcoming))
col4.metric("Reviewed / closed", len(closed))

if len(overdue) > 0:
    st.error(f"⚠️ {len(overdue)} decision(s) are overdue for review.")
    if webhook_url:
        if st.button("📣 Send overdue summary to Slack"):
            lines = [f"*Decision Tracker — {len(overdue)} overdue review(s):*"]
            for _, row in overdue.iterrows():
                lines.append(f"• *{row['title']}* (owner: {row['owner']}) — was due {row['review_date'].strftime('%b %d, %Y')}")
            ok = send_slack_message(webhook_url, "\n".join(lines))
            if ok:
                st.success("Sent to Slack.")
            else:
                st.error("Couldn't reach Slack. Check the webhook URL.")

st.divider()

# ---------------------------------------------------------
# Table with inline review
# ---------------------------------------------------------

st.subheader(f"Decisions ({len(filtered)} shown)")
st.write("Edit a row to update it. Every change is logged to the audit trail below.")

edited = st.data_editor(
    filtered,
    column_config={
        "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
        "title": st.column_config.TextColumn("Decision", width="medium"),
        "owner": st.column_config.TextColumn("Owner"),
        "category": st.column_config.SelectboxColumn("Category", options=CATEGORIES),
        "priority": st.column_config.SelectboxColumn("Priority", options=PRIORITIES),
        "date_made": st.column_config.DateColumn("Date decided"),
        "review_date": st.column_config.DateColumn("Review by"),
        "expected_outcome": st.column_config.TextColumn("Expected outcome", width="large"),
        "status": st.column_config.SelectboxColumn("Status", options=STATUSES),
        "actual_outcome": st.column_config.TextColumn("What actually happened", width="large"),
        "created_by": st.column_config.TextColumn("Created by", disabled=True),
        "last_updated_by": st.column_config.TextColumn("Last updated by", disabled=True),
        "last_updated_at": st.column_config.TextColumn("Last updated at", disabled=True),
    },
    num_rows="fixed",
    use_container_width=True,
    hide_index=True,
    key="editor",
)

if st.button("💾 Save changes"):
    full_df = load_decisions()
    changed = 0
    for _, row in edited.iterrows():
        idx = full_df[full_df["id"] == row["id"]].index
        if len(idx) == 0:
            continue
        i = idx[0]
        before = full_df.loc[i].to_dict()
        for col in DECISION_COLUMNS:
            if col in row and str(full_df.loc[i, col]) != str(row[col]):
                full_df.loc[i, col] = row[col]
        if before != full_df.loc[i].to_dict():
            full_df.loc[i, "last_updated_by"] = current_user
            full_df.loc[i, "last_updated_at"] = datetime.now()
            log_audit(current_user, "updated", row["id"], row["title"])
            changed += 1
    save_decisions(full_df)
    st.success(f"Saved. {changed} decision(s) updated.")
    st.rerun()

st.divider()

# ---------------------------------------------------------
# Patterns
# ---------------------------------------------------------

st.subheader("Patterns")
reviewed = df[df["status"] != "Open"]

pcol1, pcol2 = st.columns(2)

with pcol1:
    if len(reviewed) > 0:
        outcome_counts = reviewed["status"].value_counts().reset_index()
        outcome_counts.columns = ["Outcome", "Count"]
        fig = px.bar(outcome_counts, x="Outcome", y="Count", color="Outcome",
                     color_discrete_map={"Confirmed correct": "#16a34a", "Turned out wrong": "#dc2626", "Abandoned": "#6b7280"})
        fig.update_layout(showlegend=False, height=320, margin=dict(l=10, r=10, t=30, b=10), title="Outcomes overall")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Mark some decisions as reviewed to see outcome patterns.")

with pcol2:
    if len(reviewed) > 0:
        by_owner = reviewed.groupby("owner")["status"].apply(
            lambda s: (s == "Turned out wrong").mean() * 100
        ).reset_index()
        by_owner.columns = ["Owner", "Wrong rate (%)"]
        by_owner = by_owner.sort_values("Wrong rate (%)", ascending=False)
        fig2 = px.bar(by_owner, x="Owner", y="Wrong rate (%)", title="Wrong-call rate by owner")
        fig2.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Per-owner accuracy will appear here once decisions are reviewed.")

st.divider()

# ---------------------------------------------------------
# Audit trail
# ---------------------------------------------------------

with st.expander("📜 Audit trail (who changed what, and when)"):
    audit = load_audit()
    if len(audit) > 0:
        st.dataframe(audit.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.caption("No changes logged yet.")

st.caption(
    "Note: data is stored on the app server and shared by everyone using this app, but is not guaranteed "
    "to survive a redeploy or restart — export a backup regularly using the sidebar buttons."
)
