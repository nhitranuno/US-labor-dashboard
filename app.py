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
filtered = df[df["series_name"].isin(selected)].copy()

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
def index_series(group):
    first_val = group.sort_values("date")["value"].iloc[0]
    group = group.copy()
    group["indexed_value"] = (group["value"] / first_val) * 100
    return group

indexed = filtered.groupby("series_name", group_keys=False).apply(index_series)

fig = px.line(
    indexed, x="date", y="indexed_value", color="series_name",
    labels={"indexed_value": "Index (First Month = 100)", "date": "Date", "series_name": "Series"},
)
fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.5))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ---- Month-over-Month % Change Bar Chart ----
st.subheader("📊 Month-over-Month % Change")
st.caption("Percentage change from the previous month, making the magnitude of changes comparable across series.")

series_choice = st.selectbox("Select series:", all_series)
mom = df[df["series_name"] == series_choice].sort_values("date").copy()
mom["pct_change"] = mom["value"].pct_change() * 100  # percentage change
mom = mom.dropna(subset=["pct_change"])
mom["color"] = mom["pct_change"].apply(lambda x: "positive" if x >= 0 else "negative")

fig2 = px.bar(
    mom, x="date", y="pct_change",
    color="color",
    color_discrete_map={"positive": "#2ecc71", "negative": "#e74c3c"},
    title=f"Month-over-Month % Change: {series_choice}",
    labels={"pct_change": "% Change", "date": "Date"}
)
fig2.update_layout(showlegend=False)
fig2.add_hline(y=0, line_color="gray", opacity=0.5)
st.plotly_chart(fig2, use_container_width=True)

st.caption(f"Data: {df['date'].min().strftime('%b %Y')} – {df['date'].max().strftime('%b %Y')}")
