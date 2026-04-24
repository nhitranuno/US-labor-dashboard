import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# US Labor Statistics Dashboard
# ============================================================

st.set_page_config(page_title="US Labor Dashboard", page_icon="📊", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("data/labor_data.csv", parse_dates=["date"])
    return df

df = load_data()

st.title("📊 US Labor Market Dashboard")
st.markdown("**Source:** Bureau of Labor Statistics | Auto-updated monthly")
st.markdown("---")

# Sidebar
st.sidebar.title("Filters")
all_series = df["series_name"].unique().tolist()
selected = st.sidebar.multiselect("Series", all_series, default=all_series)

# Date range slider
min_date = df["date"].min().to_pydatetime()
max_date = df["date"].max().to_pydatetime()
start_date, end_date = st.sidebar.slider(
    "Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="MMM YYYY"
)

# Filter data by both series and date range
filtered = df[
    (df["series_name"].isin(selected)) &
    (df["date"] >= start_date) &
    (df["date"] <= end_date)
].copy()

# ---- Metric Cards ----
st.subheader("Latest Values")
latest = df.sort_values("date").groupby("series_name").last().reset_index()
prev   = df.sort_values("date").groupby("series_name").nth(-2).reset_index()
merged = latest.merge(prev[["series_name","value"]], on="series_name", suffixes=("","_prev"))
merged["change"] = merged["value"] - merged["value_prev"]

cols = st.columns(4)
for i, row in merged.iterrows():
    with cols[i % 4]:
        st.metric(row["series_name"], f"{row['value']:,.1f}", f"{row['change']:+.2f}")

st.markdown("---")

# ---- Indexed Line Chart (base 100) ----
st.subheader("📈 Trends Over Time (Indexed to 100 at Start)")
st.caption("All series normalized so the first month = 100. Values above 100 mean growth; below 100 means decline.")

# For each series, divide every value by its first value and multiply by 100
# Normalize each series to 100 at first data point
indexed_frames = []
for name, group in filtered.groupby("series_name"):
    group = group.sort_values("date").copy()
    first_val = group["value"].iloc[0]
    group["indexed_value"] = (group["value"] / first_val) * 100
    indexed_frames.append(group)
indexed = pd.concat(indexed_frames, ignore_index=True)

fig = px.line(
    indexed, x="date", y="indexed_value", color="series_name",
    labels={"indexed_value": "Index (First Month = 100)", "date": "Date", "series_name": "Series"},
)
fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)

# Annotate major economic events
events = [
    {"date": "2024-09-01", "label": "Fed begins rate cuts", "color": "blue"},
    {"date": "2025-10-01", "label": "Govt shutdown\n(data gap)", "color": "red"},
    {"date": "2025-01-01", "label": "Trump 2nd term begins", "color": "gray"},
]
for event in events:
    fig.add_vline(
        x=event["date"],
        line_dash="dot",
        line_color=event["color"],
        opacity=0.5
    )
    fig.add_annotation(
        x=event["date"],
        y=103,
        text=event["label"],
        showarrow=False,
        font=dict(size=10, color=event["color"]),
        textangle=-90,
        xanchor="left"
    )
fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.5))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ---- Month-over-Month % Change Bar Chart ----
st.subheader("📊 Month-over-Month % Change")
st.caption("Percentage change from the previous month. The black line shows the 3-month rolling average to smooth out noise.")

series_choice = st.selectbox("Select series:", all_series)
mom = df[df["series_name"] == series_choice].sort_values("date").copy()
mom["pct_change"] = mom["value"].pct_change() * 100
mom = mom.dropna(subset=["pct_change"])
mom["color"] = mom["pct_change"].apply(lambda x: "positive" if x >= 0 else "negative")

# 3-month rolling average
mom["rolling_avg"] = mom["pct_change"].rolling(window=3).mean()

import plotly.graph_objects as go

fig2 = px.bar(
    mom, x="date", y="pct_change",
    color="color",
    color_discrete_map={"positive": "#2ecc71", "negative": "#e74c3c"},
    title=f"Month-over-Month % Change: {series_choice}",
    labels={"pct_change": "% Change", "date": "Date"}
)

# Overlay rolling average line
fig2.add_trace(go.Scatter(
    x=mom["date"],
    y=mom["rolling_avg"],
    mode="lines",
    name="3-Month Avg",
    line=dict(color="black", width=2.5, dash="solid")
))

fig2.add_hline(y=0, line_color="gray", opacity=0.4)
fig2.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.2))

# Annotate government shutdown gap
fig2.add_vline(x="2025-10-01", line_dash="dot", line_color="red", opacity=0.5)
fig2.add_annotation(
    x="2025-10-01", y=mom["pct_change"].max() * 0.9,
    text="Data gap\n(Govt shutdown)",
    showarrow=False,
    font=dict(size=10, color="red"),
    textangle=-90, xanchor="left"
)

st.plotly_chart(fig2, use_container_width=True)

# ---- Summary Stats Table ----
st.subheader("📋 Summary Statistics")
st.caption(f"Monthly % change statistics for: {series_choice}")

avg   = mom["pct_change"].mean()
best  = mom.loc[mom["pct_change"].idxmax()]
worst = mom.loc[mom["pct_change"].idxmin()]
total = ((df[df["series_name"]==series_choice].sort_values("date")["value"].iloc[-1] /
          df[df["series_name"]==series_choice].sort_values("date")["value"].iloc[0]) - 1) * 100
positive_months = (mom["pct_change"] > 0).sum()
negative_months = (mom["pct_change"] < 0).sum()

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Avg Monthly Change", f"{avg:+.3f}%")
with col2:
    st.metric(f"Best Month ({best['date'].strftime('%b %Y')})", f"{best['pct_change']:+.3f}%")
with col3:
    st.metric(f"Worst Month ({worst['date'].strftime('%b %Y')})", f"{worst['pct_change']:+.3f}%")
with col4:
    st.metric("Total Change since Jan 2024", f"{total:+.2f}%")
with col5:
    st.metric("Months Up / Down", f"{positive_months} / {negative_months}")
