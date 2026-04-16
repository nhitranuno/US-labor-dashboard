import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# US Labor Statistics Dashboard
# Data source: BLS Public API | Auto-updated monthly via GitHub Actions
# ============================================================

st.set_page_config(
    page_title="US Labor Market Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---- Load Data ----
@st.cache_data
def load_data():
    """Load labor data from CSV. Cached so it doesn't reload on every interaction."""
    df = pd.read_csv("data/labor_data.csv", parse_dates=["date"])
    return df

df = load_data()

# ---- Sidebar Filters ----
st.sidebar.title("🔎 Filters")

# Date range slider
min_date = df["date"].min()
max_date = df["date"].max()
start_date, end_date = st.sidebar.date_input(
    "Date Range",
    value=[min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Series selector
all_series = df["series_name"].unique().tolist()
selected_series = st.sidebar.multiselect(
    "Select Series to Display",
    options=all_series,
    default=all_series
)

# Filter data
mask = (
    (df["date"] >= pd.Timestamp(start_date)) &
    (df["date"] <= pd.Timestamp(end_date)) &
    (df["series_name"].isin(selected_series))
)
filtered = df[mask].copy()

# ---- Header ----
st.title("📊 US Labor Market Dashboard")
st.markdown("**Data source:** Bureau of Labor Statistics (BLS) | Updated monthly via GitHub Actions")
st.markdown("---")

# ---- Metric Cards (latest values) ----
st.subheader("📌 Latest Values")

# Get the most recent value and month-over-month change for each series
latest = df.sort_values("date").groupby("series_name").last().reset_index()
prev   = df.sort_values("date").groupby("series_name").nth(-2).reset_index()
merged = latest.merge(prev[["series_name","value"]], on="series_name", suffixes=("","_prev"))
merged["change"] = merged["value"] - merged["value_prev"]

cols = st.columns(4)
for i, row in merged.iterrows():
    with cols[i % 4]:
        delta_str = f"{row['change']:+.2f}"
        st.metric(
            label=row["series_name"],
            value=f"{row['value']:,.1f}",
            delta=delta_str
        )

st.markdown("---")

# ---- Line Charts ----
st.subheader("📈 Trends Over Time")

# Group series into two categories for cleaner layout
employment_series = [
    "Total Nonfarm Employment",
    "Construction Employment",
    "Manufacturing Employment",
    "Education & Health Employment"
]
rate_series = [
    "Unemployment Rate",
    "Labor Force Participation Rate",
    "Avg Hourly Earnings",
    "Avg Weekly Hours"
]

col1, col2 = st.columns(2)

with col1:
    emp_data = filtered[filtered["series_name"].isin(employment_series)]
    if not emp_data.empty:
        fig = px.line(
            emp_data, x="date", y="value",
            color="series_name",
            title="Employment by Sector (thousands)",
            labels={"value": "Thousands", "date": "Date", "series_name": "Series"}
        )
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.4))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    rate_data = filtered[filtered["series_name"].isin(rate_series)]
    if not rate_data.empty:
        fig2 = px.line(
            rate_data, x="date", y="value",
            color="series_name",
            title="Rates & Earnings",
            labels={"value": "Value", "date": "Date", "series_name": "Series"}
        )
        fig2.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.4))
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ---- Month-over-Month Bar Charts ----
st.subheader("📊 Month-over-Month Changes")

series_choice = st.selectbox("Select a series to inspect:", options=selected_series)

mom_data = filtered[filtered["series_name"] == series_choice].copy()
mom_data = mom_data.sort_values("date")
mom_data["mom_change"] = mom_data["value"].diff()
mom_data = mom_data.dropna(subset=["mom_change"])
mom_data["color"] = mom_data["mom_change"].apply(lambda x: "positive" if x >= 0 else "negative")

fig3 = px.bar(
    mom_data, x="date", y="mom_change",
    color="color",
    color_discrete_map={"positive": "#2ecc71", "negative": "#e74c3c"},
    title=f"Month-over-Month Change: {series_choice}",
    labels={"mom_change": "Change", "date": "Date"}
)
fig3.update_layout(showlegend=False)
st.plotly_chart(fig3, use_container_width=True)

# ---- Footer ----
st.markdown("---")
st.caption(f"📅 Data from {df['date'].min().strftime('%B %Y')} to {df['date'].max().strftime('%B %Y')} | Built with Streamlit & Plotly")
