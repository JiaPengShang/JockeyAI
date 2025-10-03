# pages/05_Sleep_Night_Factors.py
# Sleep Diary (Night Factors) — per-week dashboard for habits before sleep
import json, re
from typing import Dict, Any, List, Optional
from collections import Counter

import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Sleep Diary (Night) — Weekly", layout="wide")
st.title("Sleep Diary — Night Factors (Weekly Dashboard)")

JSON_PATH = "JockeyDiaries230725.json"

@st.cache_data(show_spinner=False)
def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# 支持不同写法的键名（尽量鲁棒）
KEYS = {
    "Day": ["Day","day"],
    "NapTaken": ["NapTaken","Nap","DayNap","HadNap"],
    "CaffeineMorning": ["CaffeineMorningDrinks","CaffeineMorning","MorningCaffeine","MorningDrinks"],
    "CaffeineAfternoon": ["CaffeineAfternoonDrinks","CaffeineAfternoon","AfternoonCaffeine","AfternoonDrinks"],
    "CaffeineEvening": ["CaffeineEveningDrinks","CaffeineEvening","EveningCaffeine","EveningDrinks"],
    "ExerciseDuration": ["ExerciseDuration","ExerciseMins","ExerciseMinutes","WorkoutMins"],
    "Medications": ["MedicationsOrDrugsUsed","Medications","DrugsUsed","Medication"],
    "DaytimeDrowsiness": ["DaytimeDrowsiness","Drowsiness"],
    "OverallMood": ["OverallMood","Mood"],
    "PreBedActivities": ["PreBedActivities","ActivitiesBeforeBed","BedtimeActivities","PreSleepActivities"],
}

def _as_str(x) -> str:
    if x is None: return ""
    s = str(x).strip()
    return "" if s.lower() in ("null","none","nan") else s

def _get_first(r: Dict[str, Any], keys: List[str]):
    for k in keys:
        if k in r:
            return r.get(k)
    return None

def _to_bool(v) -> Optional[int]:
    """Yes/No/True/False -> 1/0；其它返回 None"""
    if v is None: return None
    if isinstance(v, (int, float)): return 1 if float(v) != 0 else 0
    s = str(v).strip().lower()
    if s in ("yes","y","true","t","1"): return 1
    if s in ("no","n","false","f","0"): return 0
    return None

def _num_or_zero(v) -> float:
    """抽取字符串中的数字；若无数字则 0"""
    if v is None: return 0.0
    if isinstance(v, (int, float)): return float(v)
    s = str(v).strip().lower()
    m = re.search(r"(-?\d+(?:\.\d+)?)", s)
    return float(m.group(1)) if m else 0.0

def _split_activities(v) -> List[str]:
    """
    将活动字符串拆分为标准 token（逗号/斜杠/分号/换行 分割；去空格；小写）。
    如果是列表就逐项处理。
    """
    if v is None:
        return []
    if isinstance(v, list):
        items = v
    else:
        s = str(v)
        # 常见分隔符
        items = re.split(r"[,\;/\n|]+", s)
    out = []
    for it in items:
        t = it.strip().lower()
        if not t:
            continue
        # 同义合并
        if t in ("mobile","cellphone","phone","smartphone"): t = "phone"
        if t in ("tv","television"): t = "tv"
        if t in ("video games","gaming","game"): t = "gaming"
        if t in ("pc","computer","laptop"): t = "computer"
        out.append(t)
    return out

def _extract_night_factors(raw: Dict[str, Any]) -> pd.DataFrame:
    """
    从 JSON 中抽取 category == 'sleep_diary_night' 的页面；
    每页视为一周，输出列：
      Week, WeekLabel, Day, NapTaken, CaffeineMorning, CaffeineAfternoon, CaffeineEvening,
      CaffeineTotal, ExerciseMins, Medications, DaytimeDrowsiness, OverallMood, PreBedActivities
    """
    pages = raw.get("pages", [])
    rows = []
    week_idx = 0

    for p in pages:
        cat = str(p.get("category","")).strip().lower()
        if cat and cat != "sleep_diary_night":
            continue

        # records 可能在顶层或 structured.records
        recs = None
        if isinstance(p.get("records"), list):
            recs = p["records"]
        else:
            s = p.get("structured")
            if isinstance(s, dict) and isinstance(s.get("records"), list):
                recs = s["records"]

        if not isinstance(recs, list) or not recs:
            continue

        week_idx += 1
        for r in recs:
            if not isinstance(r, dict):
                continue
            day = _as_str(_get_first(r, KEYS["Day"])).title() or None
            nap = _to_bool(_get_first(r, KEYS["NapTaken"]))
            caf_m = _num_or_zero(_get_first(r, KEYS["CaffeineMorning"]))
            caf_a = _num_or_zero(_get_first(r, KEYS["CaffeineAfternoon"]))
            caf_e = _num_or_zero(_get_first(r, KEYS["CaffeineEvening"]))
            ex_min = _num_or_zero(_get_first(r, KEYS["ExerciseDuration"]))
            meds = _to_bool(_get_first(r, KEYS["Medications"]))
            drowsy = _as_str(_get_first(r, KEYS["DaytimeDrowsiness"])).title() or None
            mood = _as_str(_get_first(r, KEYS["OverallMood"])).title() or None
            acts_raw = _get_first(r, KEYS["PreBedActivities"])
            acts = _split_activities(acts_raw)

            rows.append(dict(
                Week=week_idx,
                WeekLabel=f"Week {week_idx}",
                Day=day,
                NapTaken=nap,
                CaffeineMorning=caf_m,
                CaffeineAfternoon=caf_a,
                CaffeineEvening=caf_e,
                CaffeineTotal=caf_m + caf_a + caf_e,
                ExerciseMins=ex_min,
                Medications=meds,
                DaytimeDrowsiness=drowsy,
                OverallMood=mood,
                PreBedActivitiesList=acts,
                PreBedActivitiesRaw=_as_str(acts_raw) or None,
            ))

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # 周 & 星期顺序
    df["Week"] = pd.Categorical(df["Week"], categories=sorted(df["Week"].unique().tolist()), ordered=True)
    df["Day"] = pd.Categorical(df["Day"].astype(str).str.title(), categories=DAY_ORDER, ordered=True)

    # 分类顺序（便于画图从“差→好”）
    mood_order = ["Negative","Neutral","Positive"]
    drowsy_order = ["Never","Sometimes","Very Often"]
    df["OverallMood"] = df["OverallMood"].replace({"Very often":"Very Often"})  # 统一大小写
    df["OverallMood"] = pd.Categorical(df["OverallMood"], categories=mood_order, ordered=True)
    df["DaytimeDrowsiness"] = df["DaytimeDrowsiness"].replace({"Very often":"Very Often"})
    df["DaytimeDrowsiness"] = pd.Categorical(df["DaytimeDrowsiness"], categories=drowsy_order, ordered=True)

    return df

# ---------------- MAIN ----------------
raw = load_json(JSON_PATH)
df = _extract_night_factors(raw)

if df.empty:
    st.warning("No sleep_diary_night pages or records found.")
    st.stop()

weeks = list(df["Week"].cat.categories)
sel_week = st.selectbox("Select week", options=weeks, index=0, format_func=lambda w: f"Week {int(w)}")
week_df = df[df["Week"] == sel_week].copy()

# ===== 表 1：周内每日明细（清洗后的字段） =====
st.subheader(f"Night factors — daily detail ({week_df['Week'].iloc[0]})")
cols = [
    "WeekLabel","Day","NapTaken","CaffeineMorning","CaffeineAfternoon","CaffeineEvening",
    "CaffeineTotal","ExerciseMins","Medications","DaytimeDrowsiness","OverallMood","PreBedActivitiesRaw"
]
have = [c for c in cols if c in week_df.columns]
st.dataframe(week_df[have].sort_values(["Day"]), width="stretch")
st.caption(f"{len(week_df)} rows")

# ===== KPI =====
def _fmt_mean(s, fmt):
    if s is None or s.empty: return "—"
    v = s.dropna().mean()
    return fmt.format(v) if pd.notna(v) else "—"

k1,k2,k3,k4 = st.columns(4)
k1.metric("Total caffeine (week)", f"{week_df['CaffeineTotal'].sum():.0f}" if "CaffeineTotal" in week_df else "—")
k2.metric("Days with nap", f"{int(week_df['NapTaken'].fillna(0).sum())}" if "NapTaken" in week_df else "—")
k3.metric("Avg exercise (min/day)", _fmt_mean(week_df.get("ExerciseMins"), "{:.0f}"))
k4.metric("Days with medication", f"{int(week_df['Medications'].fillna(0).sum())}" if "Medications" in week_df else "—")

# ===== 图 1：周内咖啡因（晨/午/晚）堆叠柱 =====
caff_cols = [c for c in ["CaffeineMorning","CaffeineAfternoon","CaffeineEvening"] if c in week_df.columns]
if caff_cols:
    st.subheader("Caffeine by time of day (stacked)")
    pivot_caf = week_df[["Day"] + caff_cols].sort_values("Day")
    fig1 = px.bar(pivot_caf, x="Day", y=caff_cols, barmode="stack")
    st.plotly_chart(fig1, use_container_width=True, config={"responsive": True, "displaylogo": False})

# ===== 图 2：周内运动时长（柱） =====
if "ExerciseMins" in week_df.columns and week_df["ExerciseMins"].notna().any():
    st.subheader("Exercise duration (min) by day")
    fig2 = px.bar(week_df.sort_values("Day"), x="Day", y="ExerciseMins")
    st.plotly_chart(fig2, use_container_width=True, config={"responsive": True, "displaylogo": False})

# ===== 图 3：情绪分布 / 困倦分布（条形） =====
c3a, c3b = st.columns(2)
with c3a:
    if "OverallMood" in week_df.columns:
        st.markdown("**Mood distribution (week)**")
        mood_cnt = week_df["OverallMood"].value_counts(dropna=True).reindex(["Negative","Neutral","Positive"])
        mood_cnt = mood_cnt.fillna(0).rename_axis("Mood").reset_index(name="count")
        fig3a = px.bar(mood_cnt, x="Mood", y="count")
        st.plotly_chart(fig3a, use_container_width=True, config={"responsive": True, "displaylogo": False})
with c3b:
    if "DaytimeDrowsiness" in week_df.columns:
        st.markdown("**Drowsiness distribution (week)**")
        d_cnt = week_df["DaytimeDrowsiness"].value_counts(dropna=True).reindex(["Never","Sometimes","Very Often"])
        d_cnt = d_cnt.fillna(0).rename_axis("Drowsiness").reset_index(name="count")
        fig3b = px.bar(d_cnt, x="Drowsiness", y="count")
        st.plotly_chart(fig3b, use_container_width=True, config={"responsive": True, "displaylogo": False})

# ===== 图 4：睡前活动 Top-N（条形） =====
st.subheader("Pre-bed activities — Top N")
acts = []
for lst in week_df.get("PreBedActivitiesList", []):
    if isinstance(lst, list):
        acts.extend(lst)
topn = st.slider("Top N", 3, 15, 8, step=1)
if acts:
    cnt = Counter(acts)
    top_df = pd.DataFrame(cnt.most_common(topn), columns=["activity","count"])
    fig4 = px.bar(top_df, x="activity", y="count")
    st.plotly_chart(fig4, use_container_width=True, config={"responsive": True, "displaylogo": False})
else:
    st.info("No pre-bed activities recorded this week.")

# ===== 跨周汇总表（均值/计数） —— 修复版 =====
st.subheader("Weekly summary (aggregates)")

# 动态构建聚合映射：只聚合实际存在的列
agg_spec = {}
if "CaffeineTotal" in df.columns:
    agg_spec["CaffeineTotal"] = "mean"
if "ExerciseMins" in df.columns:
    agg_spec["ExerciseMins"] = "mean"
if "NapTaken" in df.columns:
    # 确保是数值以便求和
    df["NapTaken"] = pd.to_numeric(df["NapTaken"], errors="coerce")
    agg_spec["NapTaken"] = "sum"       # 周内午睡天数
if "Medications" in df.columns:
    df["Medications"] = pd.to_numeric(df["Medications"], errors="coerce")
    agg_spec["Medications"] = "sum"    # 周内用药天数

if agg_spec:
    weekly_summary = (
        df.groupby(["Week","WeekLabel"], observed=False)
          .agg(agg_spec)                # 只聚合存在的列
          .reset_index()
          .round(2)
          .sort_values("Week")
    )
    rename_map = {
        "CaffeineTotal": "Avg Caffeine/Day",
        "ExerciseMins": "Avg Exercise(min)/Day",
        "NapTaken": "Nap Days",
        "Medications": "Medication Days",
    }
    weekly_summary = weekly_summary.rename(
        columns={k: v for k, v in rename_map.items() if k in weekly_summary.columns}
    )
    st.dataframe(weekly_summary, width="stretch")
else:
    st.info("No numeric fields to summarize across weeks.")

# ===== 多周对比：选择一个指标（线图） =====
available_metrics = [c for c in ["CaffeineTotal","ExerciseMins"] if c in df.columns]
if available_metrics:
    st.subheader("Compare weeks — pick one metric")
    metric = st.selectbox("Metric", options=available_metrics, index=0)
    sel_weeks = st.multiselect("Weeks to compare", options=weeks, default=[weeks[0]], format_func=lambda w: f"Week {int(w)}")
    cmp_df = df[df["Week"].isin(sel_weeks)]
    if not cmp_df.empty:
        fig_cmp = px.line(cmp_df.sort_values(["Week","Day"]), x="Day", y=metric, color="WeekLabel", markers=True)
        st.plotly_chart(fig_cmp, use_container_width=True, config={"responsive": True, "displaylogo": False})

# ===== 下载 =====
with st.expander("Download"):
    st.download_button(
        "Download selected week detail (CSV)",
        data=week_df[have].sort_values(["Day"]).to_csv(index=False).encode("utf-8"),
        file_name=f"sleep_night_factors_week_{int(sel_week)}.csv",
        mime="text/csv",
    )
    if agg_spec:
        st.download_button(
            "Download weekly summary (CSV)",
            data=weekly_summary.to_csv(index=False).encode("utf-8"),
            file_name="sleep_night_factors_weekly_summary.csv",
            mime="text/csv",
        )
