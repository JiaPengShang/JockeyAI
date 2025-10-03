# pages/04_Sleep_Morning_Records.py
# Sleep Diary (Morning) — weekly view (supports pages[].records / pages[].structured.records)
import json, re
from typing import Dict, Any, List, Optional

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Sleep Diary (Morning) — Weekly", layout="wide")
st.title("Sleep Diary — Morning (Weekly View)")

JSON_PATH = "JockeyDiaries230725.json"

@st.cache_data(show_spinner=False)
def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

QUALITY_MAP = {"P":"Poor","F":"Fair","G":"Good","VG":"Very Good","E":"Excellent"}
FEELING_MAP = {"Ref":"Refreshed","OK":"Okay","T":"Tired","D":"Drowsy"}

SLEEP_FIELD_KEYS = (
    "Bedtime","Bed","bed_time","WakeUpTime","Wake","wake_time","SleepLatencyMins","Latency","SleepLatency"
)

def _as_str(x) -> str:
    if x is None: return ""
    s = str(x).strip()
    return "" if s.lower() in ("null","none","nan") else s

def _parse_hhmm_to_min(s: str) -> Optional[int]:
    if not s: return None
    s = s.strip().lower()
    m = re.match(r"^\s*(\d{1,2})(?::(\d{1,2}))?\s*(am|pm)?\s*$", s)
    if not m: return None
    hh = int(m.group(1)); mm = int(m.group(2) or 0); ampm = m.group(3)
    if ampm == "pm" and hh < 12: hh += 12
    if ampm == "am" and hh == 12: hh = 0
    if 0 <= hh < 24 and 0 <= mm < 60: return hh*60 + mm
    return None

def _overnight_minutes(bed_min: Optional[int], wake_min: Optional[int]) -> Optional[int]:
    if bed_min is None or wake_min is None: return None
    return (wake_min - bed_min) if wake_min >= bed_min else (24*60 - bed_min + wake_min)

def _get_structured(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict): return obj
    if isinstance(obj, str):
        s = obj.strip()
        if not s or s.lower() in ("none","null"): return {}
        try:
            j = json.loads(s)
            return j if isinstance(j, dict) else {}
        except Exception:
            return {}
    return {}

def _looks_like_sleep_record(r: Dict[str, Any]) -> bool:
    return isinstance(r, dict) and any(k in r for k in SLEEP_FIELD_KEYS)

def _iter_week_records(pages: List[Dict[str, Any]]):
    """
    依次产出：(week_index, page_no, records_list)
    - 仅针对 category == 'sleep_diary_morning' 的页面
    - 每一个符合条件的页面视为“一周”
    - week_index 从 1 递增，保持 JSON 中出现的顺序
    """
    week_idx = 0
    for p in pages:
        cat = str(p.get("category","")).strip().lower()
        if cat and cat != "sleep_diary_morning":
            continue
        recs = None
        if isinstance(p.get("records"), list):
            recs = p["records"]
        else:
            s = _get_structured(p.get("structured"))
            if isinstance(s.get("records"), list):
                recs = s["records"]
        if isinstance(recs, list) and len(recs) > 0:
            week_idx += 1
            yield week_idx, p.get("page"), recs

def extract_sleep_weekly(raw: Dict[str, Any]) -> pd.DataFrame:
    """
    输出每一行是“某周的某一天”的计算结果：
      Week, WeekLabel, Day, Bedtime, WakeUpTime,
      InBedHours, SleepLatencyMins, SleepHours, SleepEfficiency,
      NightAwakenings, SleepQuality, MorningFeeling, DifficultyFactors, Page
    """
    pages = raw.get("pages", [])
    rows: List[Dict[str, Any]] = []
    total_weeks = 0
    for week_idx, page_no, recs in _iter_week_records(pages):
        total_weeks = max(total_weeks, week_idx)
        for r in recs:
            if not _looks_like_sleep_record(r):  # 忽略非睡眠行
                continue
            day = _as_str(r.get("Day") or r.get("day")).title()
            bt  = _as_str(r.get("Bedtime") or r.get("Bed") or r.get("bed_time"))
            wt  = _as_str(r.get("WakeUpTime") or r.get("Wake") or r.get("wake_time"))
            lat = _as_str(r.get("SleepLatencyMins") or r.get("Latency") or r.get("SleepLatency"))
            awak= _as_str(r.get("NightAwakenings") or r.get("Awakenings") or r.get("AwakeTimes"))
            qual= _as_str(r.get("SleepQuality") or r.get("Quality"))
            feel= _as_str(r.get("MorningFeeling") or r.get("Feeling"))
            difs= _as_str(r.get("DifficultyFactors") or r.get("Difficulties") or r.get("Notes"))

            bt_min = _parse_hhmm_to_min(bt)
            wt_min = _parse_hhmm_to_min(wt)
            inbed_min = _overnight_minutes(bt_min, wt_min)

            try: lat_min = int(float(lat)) if lat else 0
            except Exception: lat_min = 0
            try: awak_n = int(float(awak)) if awak else 0
            except Exception: awak_n = 0

            sleep_min = max((inbed_min or 0) - lat_min, 0) if inbed_min is not None else None
            eff = round(sleep_min / inbed_min * 100, 1) if (sleep_min is not None and inbed_min and inbed_min > 0) else None

            rows.append(dict(
                Week=week_idx,
                WeekLabel=f"Week {week_idx}",
                Day=day or None,
                Bedtime=bt or None,
                WakeUpTime=wt or None,
                InBedHours=(round(inbed_min/60, 2) if inbed_min is not None else None),
                SleepLatencyMins=lat_min,
                SleepHours=(round(sleep_min/60, 2) if sleep_min is not None else None),
                SleepEfficiency=eff,
                NightAwakenings=awak_n,
                SleepQuality=QUALITY_MAP.get(qual, qual or None),
                MorningFeeling=FEELING_MAP.get(feel, feel or None),
                DifficultyFactors=(None if difs == "" else difs),
                Page=page_no,
            ))

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # 排序：先按 Week，再按周一→周日
    df["Day"] = pd.Categorical(df["Day"].astype(str).str.title(), categories=DAY_ORDER, ordered=True)
    df = df.sort_values(["Week","Day"], kind="stable")
    return df

# ================= MAIN =================
raw = load_json(JSON_PATH)
df = extract_sleep_weekly(raw)

if df.empty:
    st.warning("No weekly sleep-morning records found.")
    st.stop()

weeks = sorted(df["Week"].unique().tolist())
week_labels = {w: f"Week {w}" for w in weeks}

# —— 表 1：选择某一周的“每日明细表” ——
c1, c2 = st.columns([1,3])
with c1:
    sel_week = st.selectbox("Select week", options=weeks, format_func=lambda w: week_labels[w], index=0)
with c2:
    st.caption("Daily sleep detail for the selected week")

week_df = df[df["Week"] == sel_week].copy()
detail_cols = ["WeekLabel","Day","Bedtime","WakeUpTime","InBedHours","SleepLatencyMins","SleepHours","SleepEfficiency","NightAwakenings","SleepQuality","MorningFeeling","DifficultyFactors","Page"]
detail_cols = [c for c in detail_cols if c in week_df.columns]
st.subheader(f"Daily sleep detail — {week_labels[sel_week]}")
st.dataframe(week_df[detail_cols], width="stretch")
k1,k2,k3 = st.columns(3)
k1.metric("Avg sleep hours (week)", f"{week_df['SleepHours'].dropna().mean():.2f} h" if "SleepHours" in week_df else "—")
k2.metric("Avg efficiency (week)", f"{week_df['SleepEfficiency'].dropna().mean():.1f} %" if "SleepEfficiency" in week_df else "—")
k3.metric("Total awakenings (week)", f"{int(week_df['NightAwakenings'].dropna().sum())}" if "NightAwakenings" in week_df else "—")

# —— 图 1：该周“每天的睡眠时长” ——
if "SleepHours" in week_df.columns:
    st.subheader(f"Sleep hours by day — {week_labels[sel_week]}")
    fig1 = px.line(week_df, x="Day", y="SleepHours", markers=True)
    st.plotly_chart(fig1, use_container_width=True, config={"responsive": True, "displaylogo": False})

# —— 图 2：该周“每天的夜醒次数” ——
if "NightAwakenings" in week_df.columns:
    st.subheader(f"Night awakenings by day — {week_labels[sel_week]}")
    fig2 = px.bar(week_df, x="Day", y="NightAwakenings")
    st.plotly_chart(fig2, use_container_width=True, config={"responsive": True, "displaylogo": False})

# —— 对比：每周的“周均指标”表（每周一行） ——
st.subheader("Weekly summary (mean per week)")
num_cols = [c for c in ["InBedHours","SleepHours","SleepLatencyMins","SleepEfficiency","NightAwakenings"] if c in df.columns]
weekly_summary = (df.groupby(["Week","WeekLabel"], as_index=False, observed=False)[num_cols]
                    .mean().round(2)
                    .sort_values("Week"))
st.dataframe(weekly_summary, width="stretch")

# —— 可选：多周对比曲线（睡眠时长） ——
st.subheader("Compare weeks — sleep hours by day")
sel_weeks = st.multiselect("Weeks to compare", options=weeks, default=[sel_week], format_func=lambda w: week_labels[w])
cmp_df = df[df["Week"].isin(sel_weeks)]
if not cmp_df.empty and "SleepHours" in cmp_df.columns:
    fig_cmp = px.line(cmp_df, x="Day", y="SleepHours", color="WeekLabel", markers=True)
    st.plotly_chart(fig_cmp, use_container_width=True, config={"responsive": True, "displaylogo": False})

# —— 下载 ——
with st.expander("Download"):
    st.download_button(
        "Download selected week detail (CSV)",
        data=week_df.to_csv(index=False).encode("utf-8"),
        file_name=f"sleep_morning_detail_{week_labels[sel_week].replace(' ','_').lower()}.csv",
        mime="text/csv",
    )
    st.download_button(
        "Download weekly summary (CSV)",
        data=weekly_summary.to_csv(index=False).encode("utf-8"),
        file_name="sleep_morning_weekly_summary.csv",
        mime="text/csv",
    )
