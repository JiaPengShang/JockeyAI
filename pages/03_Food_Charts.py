# pages/03_Food_By_Person.py
# Person-centric Food Diary with phrase + quantity awareness and category dashboard
import json, re, ast
from collections import Counter
import pandas as pd
import streamlit as st
import plotly.express as px
from typing import Optional

st.set_page_config(page_title="Food Diary by Person", layout="wide")
st.title("Food Diary — Person-centric View")

JSON_PATH = "JockeyDiaries230725.json"

@st.cache_data(show_spinner=False)
def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ---------- Helpers ----------
def _get_field(row, df_cols, key):
    """Prefer flattened structured.key, else structured dict."""
    flat = f"structured.{key}"
    if flat in df_cols:
        v = row.get(flat)
        if isinstance(v, str) and v.strip().lower() in ("none", "null", ""):
            v = None
        if pd.notna(v):
            return v
    s = row.get("structured")
    if isinstance(s, dict):
        return s.get(key)
    return None

def _safe_to_days_dict(val):
    """days can be dict / JSON string / Python literal string / plain text."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        s0 = val.strip()
        if not s0 or s0.lower() in ("none", "null"):
            return {}
        # Try JSON
        try:
            obj = json.loads(s0)
            return obj if isinstance(obj, dict) else {}
        except Exception:
            # Try Python literal (single quotes, etc.)
            try:
                obj = ast.literal_eval(s0)
                return obj if isinstance(obj, dict) else {}
            except Exception:
                # Treat as one text under an unknown day/meal
                return {"Unknown": {"text": s0}}
    return {}

# --- Stop words / filters ---
UNITS_STOP = set("""
g gram grams kg ml l tsp tbsp cup cups oz mg litre liters gram(s) ml(s)
mm cm kg(s) x
""".split())
GEN_STOP = set("and with of the to a in on for at by or an & + /".split())
TIME_STOP = set("am pm".split())
MEAL_WORDS = set("breakfast lunch dinner snack snacks supper".split())

# Treat as "no meal"
SKIP_PHRASES = {
    "nothing", "none", "nil", "n/a", "na", "-", "—",
    "no", "no food", "no meal", "no breakfast", "no lunch", "no dinner",
    "skip", "skipped"
}
SKIP_PATTERN = re.compile(
    r"(?:\bdid(?:n'?t)?\s*(?:eat|have)\b)|(?:\bno\s+(?:food|meal|breakfast|lunch|dinner|anything)\b)",
    re.IGNORECASE,
)

# ===== Phrase & quantity awareness =====
# 1) Common multi-word phrases (aliases -> canonical)
PHRASE_ALIASES = [
    (re.compile(r"\bmu[e]?sli\s+bar\b", re.I), "muesli bar"),
    (re.compile(r"\bprotein\s+bar\b", re.I), "protein bar"),
    (re.compile(r"\bpeanut\s+butter\b", re.I), "peanut butter"),
    (re.compile(r"\bice\s+cream\b", re.I), "ice cream"),
    (re.compile(r"\bbanana\s+bread\b", re.I), "banana bread"),
    (re.compile(r"\bbutter\s+chicken\b", re.I), "butter chicken"),
    (re.compile(r"\bfried\s+rice\b", re.I), "fried rice"),
    (re.compile(r"\bgreek\s+yogurt\b", re.I), "greek yogurt"),
    (re.compile(r"\bsavou?ry\s+pie[s]?\b", re.I), "savory pie"),
]

# 2) Head nouns for pattern <num>? <adj>? <head>
HEAD_NOUNS = {
    "pie","bar","bread","milk","yogurt","rice","pasta","noodles","toast",
    "sandwich","burger","steak","soup","salad","pudding",
    # common foods so "two apples" -> "apple x2"
    "apple","banana","orange","grape","pear","peach","plum",
    "berry","strawberry","blueberry","raspberry","kiwi","mango"
}

# 3) Number words mapping
NUM_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}
NUM_WORD_SET = set(NUM_WORDS.keys())

# 4) Single-word adjective / noise to drop if left alone
ADJ_STOP = set("""
savory savoury sweet spicy grilled fried roasted baked boiled steamed fresh cold hot warm
large small big little
""".split())
OTHER_STOP = set("""
out takeaway take-away takeout leftovers leftover home some
ate eat had have having
""".split())

# map single words to canonical forms (for leftover tokens)
WORD_CANON = {
    "yoghurt": "yogurt",
    "musli": "muesli",
}

def is_food_like(text: str) -> bool:
    """First-pass filter: drop obvious non-food / skip statements."""
    s = (text or "").strip().lower()
    if not s or s in SKIP_PHRASES or SKIP_PATTERN.search(s):
        return False
    if s in ("null", "na", "n/a"):
        return False
    return True  # detailed parsing later

def singularize(word: str) -> str:
    """Very light singularization: pies->pie, bars->bar (avoid over-stemming)."""
    w = word.lower()
    if w.endswith("ies"):
        return w[:-3] + "y"
    if w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w

def extract_terms_from_text(text: str) -> Counter:
    """
    Phrase-first term extraction with quantity handling.
    - Count canonical multi-word phrases (PHRASE_ALIASES)
    - Then match <num>? <adj>? <head> (HEAD_NOUNS), e.g., "two savory pies" -> "savory pie" x2
    - Finally count remaining words (filter stopwords/units/numbers/adjectives/other noise)
      and ignore lone head nouns
    """
    terms = Counter()
    s = " " + (text or "").lower() + " "
    if not is_food_like(s):
        return terms

    # 1) Fixed phrases / aliases
    for pat, canon in PHRASE_ALIASES:
        for _ in pat.finditer(s):
            terms[canon] += 1
        s = pat.sub(" ", s)

    # 2) Generic pattern: <num>? <adj>? <head>(s)?
    head_regex = r"(?:%s)" % "|".join(map(re.escape, HEAD_NOUNS))
    num_alt = "|".join(NUM_WORDS)  # a|an|one|two|...
    pattern = re.compile(
        rf"\b(?:(\d+|{num_alt})\s+)?(?:([a-z]+)\s+)?({head_regex})s?\b", re.I
    )

    def qty(x):
        if not x:
            return 1
        x = x.lower()
        return NUM_WORDS.get(x, int(x)) if (x.isdigit() or x in NUM_WORDS) else 1

    for m in pattern.finditer(s):
        q = qty(m.group(1))
        adj = (m.group(2) or "").lower()
        head = singularize(m.group(3))
        canon = f"{adj} {head}".strip() if adj else head
        terms[canon] += q
    s = pattern.sub(" ", s)

    # 3) Remaining single words
    tokens = re.split(r"[^a-zA-Z0-9]+", s)
    for t in tokens:
        t = t.strip().lower()
        if not t or len(t) < 2:
            continue
        # drop pure numbers & number-words (two/three/2/3...)
        if t.isdigit() or t in NUM_WORD_SET:
            continue
        # stop words / units / time / meal words / adjectives / other noise
        if (t in GEN_STOP) or (t in UNITS_STOP) or (t in TIME_STOP) or (t in MEAL_WORDS) or (t in ADJ_STOP) or (t in OTHER_STOP):
            continue
        # ignore lone head nouns like 'bar', 'pie'
        if t in HEAD_NOUNS:
            continue
        # canonicalize
        t = WORD_CANON.get(t, t)
        terms[t] += 1

    return terms

def extract_food_by_person(raw) -> pd.DataFrame:
    """Output columns: Person, Day, meal, food"""
    pages = raw.get("pages", [])
    df_pages = pd.json_normalize(pages, max_level=1)
    if "category" not in df_pages.columns:
        return pd.DataFrame()

    # Normalize category
    df_pages["__cat__"] = df_pages["category"].astype(str).str.strip().str.lower()
    df_food = df_pages[df_pages["__cat__"] == "food_diary"].copy()
    if df_food.empty:
        return pd.DataFrame()

    rows = []
    for _, r in df_food.iterrows():
        person = _get_field(r, df_food.columns, "name") or "Unknown"
        days_val = _get_field(r, df_food.columns, "days")
        days = _safe_to_days_dict(days_val)
        if not isinstance(days, dict):
            continue

        for day_name, meals in days.items():
            day_label = str(day_name).title()
            # Day -> plain text
            if not isinstance(meals, dict):
                txt = str(meals).strip()
                if is_food_like(txt):
                    rows.append(dict(Person=person, Day=day_label, meal="text", food=txt))
                continue

            for meal_name, meal_value in meals.items():
                meal_key = str(meal_name).lower()
                if meal_key.startswith("snack"):  # snack1/2/3 -> snacks
                    meal_key = "snacks"

                if isinstance(meal_value, list):
                    for item in meal_value:
                        if isinstance(item, dict):
                            txt = item.get("text") or item.get("name") or ""
                        else:
                            txt = str(item)
                        txt = txt.strip()
                        if is_food_like(txt):
                            rows.append(dict(Person=person, Day=day_label, meal=meal_key, food=txt))
                else:
                    if isinstance(meal_value, dict):
                        txt = meal_value.get("text") or meal_value.get("name") or ""
                    else:
                        txt = str(meal_value)
                    txt = txt.strip()
                    if is_food_like(txt):
                        rows.append(dict(Person=person, Day=day_label, meal=meal_key, food=txt))

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Weekday order
    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    df["Day"] = pd.Categorical(df["Day"], categories=day_order, ordered=True)
    return df

# ---------------- category classifier ----------------
@st.cache_resource(show_spinner=False)
def make_classifier():
    """
    Try to load FoodClassifier from local file. If fails, return a rule-based classifier.
    """
    # Fallback rule-based mapping: category -> keywords
    RULES = {
        "Fruit": ["apple","banana","orange","grape","pear","peach","plum","berry","strawberry","blueberry","raspberry","kiwi","mango","fruit"],
        "Vegetable": ["salad","lettuce","tomato","cucumber","spinach","broccoli","carrot","veggie","vegetable"],
        "Grain & Cereal": ["bread","toast","rice","noodles","pasta","oats","muesli","granola","cereal","wrap","tortilla"],
        "Protein": ["chicken","beef","pork","steak","egg","tofu","fish","salmon","tuna","yogurt","protein bar","peanut butter"],
        "Dairy": ["milk","yogurt","cheese","butter","ice cream"],
        "Sweets & Snacks": ["chocolate","lollies","candy","dessert","pudding","cake","cookie","biscuit","muesli bar","banana bread","savory pie","pie","chips"],
        "Beverage": ["coffee","tea","juice","water","soda","cola","drink","smoothie"],
        "Fast/Takeaway": ["burger","fried rice","pizza","kebab","takeaway","take-out","take out"],
        "Condiment/Other": ["sauce","dressing","salt","pepper","oil"],
    }

    def rule_based(text: str) -> str:
        s = (text or "").lower()
        for cat, kws in RULES.items():
            for k in kws:
                if k in s:
                    return cat
        return "Unclassified"

    # Try local ML classifier
    try:
        from food_classifier import FoodClassifier  # your local module
        try:
            clf = FoodClassifier(model_path="food_classifier_model.pkl",
                                 mapping_path="Food_Classification.xlsx")
        except TypeError:
            # some versions use positional args or only model
            try:
                clf = FoodClassifier("food_classifier_model.pkl", "Food_Classification.xlsx")
            except Exception:
                try:
                    clf = FoodClassifier()
                except Exception:
                    clf = None
    except Exception:
        clf = None

    # Wrap as a callable
    def classify(text: str) -> str:
        if not text:
            return "Unclassified"
        if clf is not None:
            for m in ("predict_category","predict","classify","__call__"):
                if hasattr(clf, m):
                    try:
                        out = getattr(clf, m)(text)
                        if isinstance(out, (list, tuple)) and out:
                            out = out[0]
                        if out:
                            return str(out)
                    except Exception:
                        pass
        return rule_based(text)

    return classify

# ---------------- main ----------------
raw = load_json(JSON_PATH)
df = extract_food_by_person(raw)

if df.empty:
    st.warning("No food entries found after normalization / filtering.")
    st.stop()

# Person selector
people = sorted(df["Person"].dropna().astype(str).unique().tolist())
person = st.selectbox("Person", options=people, index=0)

person_df = df[df["Person"] == person].copy()

# TABLE 1: raw entries (Person/Day/meal/food)
st.subheader(f"Raw entries — {person}")
show_cols = ["Person","Day","meal","food"]
st.dataframe(person_df[show_cols].sort_values(["Day","meal","food"]), width="stretch")
st.caption(f"{len(person_df)} rows")

# CHART 1: meals by weekday (stacked)
st.subheader("Meals by weekday (stacked)")
counts = (person_df.groupby(["Day","meal"], as_index=False, observed=False)
                    .size()
                    .sort_values(["Day","meal"]))
pivot_day = counts.pivot(index="Day", columns="meal", values="size").fillna(0).reset_index()
meal_cols = [c for c in ["breakfast","lunch","dinner","snacks","text"] if c in pivot_day.columns]
if meal_cols:
    fig1 = px.bar(pivot_day, x="Day", y=meal_cols, barmode="stack")
    st.plotly_chart(fig1, config={"responsive": True, "displaylogo": False}, use_container_width=True)

# TABLE + CHART 2: phrase-aware top terms for this person
st.subheader("Top foods/phrases for this person")
term_counter = Counter()
for t in person_df["food"].dropna().astype(str).tolist():
    term_counter.update(extract_terms_from_text(t))

freq = (pd.DataFrame(term_counter.items(), columns=["term","count"])
          .sort_values("count", ascending=False)
          .reset_index(drop=True))

topn = st.slider("Top N", 5, 30, 15, step=1)
st.dataframe(freq.head(topn), width="stretch")
fig2 = px.bar(freq.head(topn), x="term", y="count")
st.plotly_chart(fig2, config={"responsive": True, "displaylogo": False}, use_container_width=True)

# ===== NEW: 食物分类比例仪表板 =====
st.header("Food categories — dashboard")

classifier = make_classifier()
person_df["Category"] = person_df["food"].astype(str).map(classifier)

# 表：食物 -> 分类（便于核对）
st.subheader("Food → Category (detail)")
st.dataframe(
    person_df[["Day","meal","food","Category"]]
    .sort_values(["Day","meal","Category","food"]),
    width="stretch"
)

# 分类占比（环形）
st.subheader("Category share (donut)")
cat_counts = (person_df.assign(Category=person_df["Category"].fillna("Unclassified"))
                        .groupby("Category", as_index=False, observed=False)
                        .size()
                        .rename(columns={"size":"count"})
                        .sort_values("count", ascending=False))
if not cat_counts.empty:
    cat_counts["percent"] = (cat_counts["count"] / cat_counts["count"].sum() * 100).round(1)
    fig_donut = px.pie(cat_counts, names="Category", values="count", hole=0.5)
    st.plotly_chart(fig_donut, config={"responsive": True, "displaylogo": False}, use_container_width=True)
    st.caption("Tip: hover to see percentage; legend can toggle categories.")

# 按星期的分类堆叠柱
st.subheader("By weekday — category stacked bars")
by_day = (person_df.groupby(["Day","Category"], as_index=False, observed=False)
                    .size()
                    .rename(columns={"size":"count"}))
if not by_day.empty:
    pivot = by_day.pivot(index="Day", columns="Category", values="count").fillna(0).reset_index()
    y_cols = [c for c in pivot.columns if c != "Day"]
    fig_stack = px.bar(pivot, x="Day", y=y_cols, barmode="stack")
    st.plotly_chart(fig_stack, config={"responsive": True, "displaylogo": False}, use_container_width=True)

# DOWNLOAD (Person/Day/meal/food + Category)
with st.expander("Download"):
    st.download_button(
        f"Download entries for {person} (CSV)",
        data=person_df[["Person","Day","meal","food","Category"]].to_csv(index=False).encode("utf-8"),
        file_name=f"food_entries_{person}_with_category.csv",
        mime="text/csv",
    )
