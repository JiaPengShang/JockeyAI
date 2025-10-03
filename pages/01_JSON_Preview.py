import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="JSON Preview", layout="wide")
st.title("JockeyDiaries230725.json Preview")

PATH = "JockeyDiaries230725.json"

with open(PATH, "r", encoding="utf-8") as f:
    raw = json.load(f)

st.subheader("Raw JSON (collapsed)")
st.json(raw, expanded=False)

def to_df(obj):
    if isinstance(obj, list):
        base = obj
    elif isinstance(obj, dict):
        for k in ["pages", "data", "records", "items", "rows", "list", "results", "result"]:
            if k in obj and isinstance(obj[k], list):
                base = obj[k]
                break
        else:
            base = [obj]
    else:
        base = [{"value": obj}]
    return pd.json_normalize(base, max_level=1)

df = to_df(raw)

st.subheader("Table view (first 200 rows)")
st.dataframe(df.head(200), width="stretch")
st.caption(f"Total {len(df)} rows × {len(df.columns)} columns")
