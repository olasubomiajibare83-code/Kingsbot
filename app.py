import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import io

st.set_page_config(page_title="Decision Tracker", page_icon="🧭", layout="wide")

# ---------------------------------------------------------
# Data setup — kept in session, loadable/savable as CSV
# ---------------------------------------------------------

COLUMNS = ["title", "owner", "date_made", "review_date", "expected_outcome", "status", "actual_outcome"]

if "decisions" not in st.session_state:
    st.session_state.decisions = pd.DataFrame({
        "title": ["Switch to new invoicing vendor", "Freeze hiring in Q3", "Raise prices 8%"],
        "owner": ["Sam (Ops)", "Priya (Finance)", "Marcus (Sales)"],
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
    })

# ---------------------------------------------------------
# Sidebar — add a new decision
# ---------------------------------------------------------

st.sidebar.header("Log a new decision")
with st.sidebar.form("new_decision", clear_on_submit=True):
    title = st.text_input("Decision")
    owner = st.text_input("Owner")
    date_made = st.date_input("Date decided", value=datetime.today().date())
    review_date = st.date_input("Review this by", value=datetime.today().date() + timedelta(days=30))
    expected_outcome = st.text_area("Expected outcome", help="What are we predicting will happen?")
    submitted = st.form_submit_button("Add decision", type="primary")

    if submitted and title.strip():
        new_row = pd.DataFrame([{
            "title": title, "owner": owner, "date_made": date_made,
            "review_date": review_date, "expected_outcome": expected_outcome,
            "status": "Open", "actual_outcome": "",
        }])
        st.session_state.decisions = pd.concat([st.session_state.decisions, new_row], ignore_index=True)
        st.sidebar.success("Decision logged.")

st.sidebar.divider()
st.sidebar.caption("Data only lives in this browser session unless you export it below.")
csv_buffer = io.StringIO()
st.session_state.decisions.to_csv(csv_buffer, index=False)
st.sidebar.download_button("⬇ Export as CSV", csv_buffer.getvalue(), "decisions.csv", "text/csv")

uploaded = st.sidebar.file_uploader("⬆ Import a saved CSV", type="csv")
if uploaded is not None:
    st.session_state.decisions = pd.read_csv(uploaded, parse_dates=["date_made", "review_date"])
    st.sidebar.success("Imported.")

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

st.title("🧭 Decision Log & Follow-Through Tracker")
st.caption("Most tools track tasks. This tracks whether decisions actually got revisited — and what happened.")

df = st.session_state.decisions.copy()
df["date_made"] = pd.to_datetime(df["date_made"])
df["review_date"] = pd.to_datetime(df["review_date"])

today = pd.Timestamp(datetime.today().date())
overdue = df[(df["status"] == "Open") & (df["review_date"] < today)]
upcoming = df[(df["status"] == "Open") & (df["review_date"] >= today)]
closed = df[df["status"] != "Open"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total decisions logged", len(df))
col2.metric("Overdue for review", len(overdue))
col3.metric("Upcoming reviews", len(upcoming))
col4.metric("Reviewed / closed", len(closed))

if len(overdue) > 0:
    st.error(f"⚠️ {len(overdue)} decision(s) are past their review date and nobody has followed up. "
             f"These are the ones most likely to be silently forgotten or quietly repeated.")

st.divider()

# ---------------------------------------------------------
# Table with inline review
# ---------------------------------------------------------

st.subheader("All decisions")
st.write("Mark a decision as reviewed once you know what actually happened, so the log stays honest.")

edited = st.data_editor(
    df,
    column_config={
        "title": st.column_config.TextColumn("Decision", width="medium"),
        "owner": st.column_config.TextColumn("Owner"),
        "date_made": st.column_config.DateColumn("Date decided"),
        "review_date": st.column_config.DateColumn("Review by"),
        "expected_outcome": st.column_config.TextColumn("Expected outcome", width="large"),
        "status": st.column_config.SelectboxColumn("Status", options=["Open", "Confirmed correct", "Turned out wrong", "Abandoned"]),
        "actual_outcome": st.column_config.TextColumn("What actually happened", width="large"),
    },
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
)
st.session_state.decisions = edited

st.divider()

# ---------------------------------------------------------
# Pattern view
# ---------------------------------------------------------

st.subheader("Patterns")

reviewed = edited[edited["status"] != "Open"]
if len(reviewed) > 0:
    outcome_counts = reviewed["status"].value_counts().reset_index()
    outcome_counts.columns = ["Outcome", "Count"]
    fig = px.bar(outcome_counts, x="Outcome", y="Count", color="Outcome",
                 color_discrete_map={
                     "Confirmed correct": "#16a34a",
                     "Turned out wrong": "#dc2626",
                     "Abandoned": "#6b7280",
                 })
    fig.update_layout(showlegend=False, height=350, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

    wrong_rate = (reviewed["status"] == "Turned out wrong").mean() * 100
    st.caption(f"Of decisions reviewed so far, {wrong_rate:.0f}% turned out wrong. "
               f"Tracking this over time shows whether decision quality is improving.")
else:
    st.info("Once you mark some decisions as reviewed above, patterns will show up here — "
            "for example, which owners' predictions tend to hold up, or how often decisions get abandoned.")

st.divider()
st.caption(
    "Why this matters for a larger org: decisions made in meetings routinely vanish with no owner and no "
    "follow-up, so bad calls never get corrected and the same debates resurface months later. "
    "This log makes the follow-through visible."
)
