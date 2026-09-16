import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="Cash Flow Risk Predictor", page_icon="💸", layout="wide")

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def call_claude(prompt: str, api_key: str) -> str:
    """Call Claude API for a plain-English summary. Returns text or an error message."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        return f"(Could not reach Claude API: {e})"


def project_balance(starting_balance: float, bills_df: pd.DataFrame, days_ahead: int, avg_daily_net: float):
    """Build a day-by-day projected balance, combining known bills/invoices
    with an estimated background daily net cash flow (income - routine expenses)."""
    today = pd.Timestamp(datetime.today().date())
    dates = pd.date_range(today, today + timedelta(days=days_ahead))
    balance = pd.Series(starting_balance, index=dates, dtype=float)

    running = starting_balance
    for d in dates:
        running += avg_daily_net
        # apply any known bills/invoices due on this day
        todays_items = bills_df[bills_df["date"] == d]
        if not todays_items.empty:
            running += todays_items["amount"].sum()
        balance[d] = running

    return balance


# ---------------------------------------------------------
# Sidebar — inputs
# ---------------------------------------------------------

st.sidebar.header("1. Starting point")
starting_balance = st.sidebar.number_input("Current bank balance ($)", min_value=0.0, value=10000.0, step=100.0)
avg_daily_net = st.sidebar.number_input(
    "Average daily net cash flow ($)",
    value=0.0,
    step=10.0,
    help="Rough day-to-day income minus routine expenses, excluding the big known bills/invoices you'll list below. "
         "Use a negative number if your business normally burns cash day-to-day.",
)
days_ahead = st.sidebar.slider("Project how many days ahead?", 14, 180, 60)

st.sidebar.header("2. Optional: AI summary")
api_key = st.sidebar.text_input("Anthropic API key (optional)", type="password",
                                 help="If provided, Claude will write a plain-English summary of your risk.")

# ---------------------------------------------------------
# Main — known bills & invoices
# ---------------------------------------------------------

st.title("💸 Cash Flow Risk Predictor")
st.caption("Find out the exact week you'll run short — before it happens.")

st.subheader("Upcoming bills & expected income")
st.write("Add every known upcoming payment (bills, payroll, rent) as **negative** amounts, "
         "and expected incoming payments (invoices, sales) as **positive** amounts.")

default_rows = pd.DataFrame({
    "description": ["Payroll", "Rent", "Invoice #221 (client)"],
    "date": [datetime.today().date() + timedelta(days=7),
             datetime.today().date() + timedelta(days=10),
             datetime.today().date() + timedelta(days=5)],
    "amount": [-4200.0, -1800.0, 3000.0],
})

edited = st.data_editor(
    default_rows,
    num_rows="dynamic",
    column_config={
        "description": st.column_config.TextColumn("Description"),
        "date": st.column_config.DateColumn("Date"),
        "amount": st.column_config.NumberColumn("Amount ($)", help="Negative = outgoing, positive = incoming"),
    },
    use_container_width=True,
)

bills_df = edited.copy()
bills_df["date"] = pd.to_datetime(bills_df["date"])
bills_df = bills_df.dropna(subset=["date", "amount"])

# ---------------------------------------------------------
# Projection
# ---------------------------------------------------------

if st.button("Run projection", type="primary"):
    balance = project_balance(starting_balance, bills_df, days_ahead, avg_daily_net)

    below_zero = balance[balance < 0]
    first_shortfall = below_zero.index[0] if len(below_zero) > 0 else None
    min_balance = balance.min()
    min_date = balance.idxmin()

    col1, col2, col3 = st.columns(3)
    col1.metric("Lowest projected balance", f"${min_balance:,.0f}", f"on {min_date.strftime('%b %d, %Y')}")
    if first_shortfall is not None:
        col2.metric("First date you go negative", first_shortfall.strftime("%b %d, %Y"))
        days_until = (first_shortfall - pd.Timestamp(datetime.today().date())).days
        col3.metric("Days until shortfall", days_until)
    else:
        col2.metric("First date you go negative", "None projected ✅")
        col3.metric("Days until shortfall", "—")

    # Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=balance.index, y=balance.values, mode="lines", name="Projected balance",
                              line=dict(color="#2563eb", width=3)))
    fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.error(
            f"⚠️ At current pace, you'll run short on **{first_shortfall.strftime('%B %d, %Y')}** "
            f"({days_until} days from now), dropping to about **${balance[first_shortfall]:,.0f}**. "
            f"Consider moving up any pending invoices, delaying non-critical expenses, "
            f"or lining up a short-term buffer before that date."
        )
    else:
        st.success(f"✅ Based on current inputs, your balance stays positive through the next {days_ahead} days. "
                   f"Lowest point is ${min_balance:,.0f} on {min_date.strftime('%b %d, %Y')}.")

    # AI summary (optional)
    if api_key:
        with st.spinner("Asking Claude for a summary..."):
            bills_summary = bills_df.sort_values("date").to_string(index=False)
            prompt = (
                "You are a plainspoken financial assistant for a small business owner. "
                "Given this cash flow projection, write a 3-4 sentence summary in plain English: "
                "what the biggest risk is, when it happens, and one or two concrete actions they could take. "
                "Be direct and specific, no fluff.\n\n"
                f"Starting balance: ${starting_balance:,.0f}\n"
                f"Average daily net cash flow: ${avg_daily_net:,.0f}\n"
                f"Known upcoming items:\n{bills_summary}\n\n"
                f"Lowest projected balance: ${min_balance:,.0f} on {min_date.strftime('%Y-%m-%d')}\n"
                f"First negative date: {first_shortfall.strftime('%Y-%m-%d') if first_shortfall is not None else 'None'}"
            )
            summary = call_claude(prompt, api_key)
        st.subheader("🤖 AI summary")
        st.write(summary)
    else:
        st.info("Add an Anthropic API key in the sidebar to get a plain-English AI summary of this projection.")

else:
    st.info("Fill in your starting balance and upcoming bills/invoices, then click **Run projection**.")

st.divider()
st.caption(
    "This is a simple projection tool, not accounting software. It assumes your average daily cash flow "
    "stays constant between known bill/invoice dates. For real decisions, double-check against your bank and books."
)
