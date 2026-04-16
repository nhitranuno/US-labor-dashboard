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
filtered = df[df["series_name"].isin(selected)]

# Metric cards
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

# Line chart
st.subheader("Trends Over Time")
fig = px.line(filtered, x="date", y="value", color="series_name",
              labels={"value":"Value","date":"Date","series_name":"Series"})
fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.5))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Month-over-month bar chart
st.subheader("Month-over-Month Change")
series_choice = st.selectbox("Select series:", all_series)
mom = df[df["series_name"]==series_choice].sort_values("date").copy()
mom["change"] = mom["value"].diff()
mom = mom.dropna()
mom["color"] = mom["change"].apply(lambda x: "positive" if x>=0 else "negative")
fig2 = px.bar(mom, x="date", y="change", color="color",
              color_discrete_map={"positive":"#2ecc71","negative":"#e74c3c"},
              title=f"Month-over-Month: {series_choice}")
fig2.update_layout(showlegend=False)
st.plotly_chart(fig2, use_container_width=True)

st.caption(f"Data: {df['date'].min().strftime('%b %Y')} – {df['date'].max().strftime('%b %Y')}")
