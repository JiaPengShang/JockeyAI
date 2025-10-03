# pages/02_Riding_Charts.py
import json
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Riding Diary Charts", layout="wide")
st.title("Riding Diary — Weekly Performance")

JSON_PATH = "JockeyDiaries230725.json"

@st.cache_data(show_spinner=False)
def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_riding_records_with_week(raw) -> pd.DataFrame:
    """Flatten riding_diary records and attach a Week label per parent page."""
    pages = raw.get("pages", [])
    df_pages = pd.json_normalize(pages, max_level=1)

    # filter riding diary pages
    if "category" not in df_pages.columns:
        return pd.DataFrame()
    df_riding_pages = df_pages[df_pages["category"] == "riding_diary"].copy()

    if df_riding_pages.empty or "structured.records" not in df_riding_pages.columns:
        return pd.DataFrame()

    # build week labels: prefer structured.* week info if present, else enumerate by page order
    week_label = None
    for cand in ["structured.week", "structured.week_start", "structured.date_range", "structured.week_label"]:
        if cand in df_riding_pages.columns:
            week_label = cand
            break

    df_riding_pages = df_riding_pages.reset_index(drop=True)
    if week_label and df_riding_pages[week_label].notna().any():
        df_riding_pages["__Week__"] = df_riding_pages[week_label].astype(str)
    else:
        df_riding_pages["__Week__"] = "Week " + (df_riding_pages.index + 1).astype(str)

    # explode records and carry week label + page no
    exploded = df_riding_pages[["page", "__Week__", "structured.records"]].explode("structured.records").dropna()
    if exploded.empty:
        return pd.DataFrame()

    rec_df = pd.json_normalize(exploded["structured.records"])
    rec_df["Week"] = exploded["__Week__"].values
    rec_df["ParentPage"] = exploded["page"].values

    # normalize Day
    if "Day" in rec_df.columns:
        day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        rec_df["Day"] = rec_df["Day"].astype(str).str.title()
        rec_df["Day"] = pd.Categorical(rec_df["Day"], categories=day_order, ordered=True)

    # to numeric for candidate metrics
    for c in ["Horses ridden","Falls","Trackwork","Gallops","Jumpouts","Trials","Races"]:
        if c in rec_df.columns:
            rec_df[c] = pd.to_numeric(rec_df[c], errors="coerce")

    return rec_df

raw = load_json(JSON_PATH)
df = extract_riding_records_with_week(raw)

if df.empty:
    st.warning("No riding_diary records found.")
    st.stop()

# ---- 1) 保留：原始明细表（新增 Week 列便于追踪来源周） ----
st.subheader("Raw riding records")
st.dataframe(df, width="stretch")

# ---- 2) 按周汇总（每周一行的“周表现”） ----
st.subheader("Weekly summary (one row per week)")

# 可选指标
all_numeric = [c for c in ["Horses ridden","Races","Falls","Trackwork","Gallops","Jumpouts","Trials"] if c in df.columns]
default_y = [c for c in ["Horses ridden","Races"] if c in all_numeric] or all_numeric[:1]

c1, c2 = st.columns([2,1])
with c1:
    y_cols = st.multiselect("Metrics (Y)", options=all_numeric, default=default_y)
with c2:
    agg = st.selectbox("Aggregation", ["sum","mean","median","min","max"], index=0)

if not y_cols:
    st.info("Select at least one metric to summarize.")
    st.stop()

agg_map = {c: agg for c in y_cols}
weekly = df.groupby("Week", as_index=False, observed=False).agg(agg_map).sort_values("Week")
weekly = weekly.fillna(0)

st.dataframe(weekly, width="stretch")

# ---- 3) 可视化（按周） ----
st.subheader("Weekly charts")

# 分组柱状：每周 Horses ridden / Races 等
fig1 = px.bar(weekly, x="Week", y=y_cols, barmode="group", title="Weekly metrics")
st.plotly_chart(fig1, use_container_width=True, config={"responsive": True, "displaylogo": False})

# 堆叠柱状：训练构成（如果列存在）
train_cols = [c for c in ["Trackwork","Gallops","Jumpouts","Trials"] if c in weekly.columns]
if train_cols:
    fig2 = px.bar(weekly, x="Week", y=train_cols, barmode="stack", title="Weekly training composition")
    st.plotly_chart(fig2, use_container_width=True, config={"responsive": True, "displaylogo": False})

with st.expander("Download"):
    st.download_button(
        "Download weekly summary (CSV)",
        data=weekly.to_csv(index=False).encode("utf-8"),
        file_name="riding_weekly_summary.csv",
        mime="text/csv",
    )
