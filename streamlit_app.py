import os
import re
import datetime as dt

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from xgboost import XGBRegressor

st.set_page_config(page_title="Airport Dashboard", layout="wide")

# =========================
# الشكل العام
# =========================
st.markdown(
    """
    <style>
    .main {background-color:#0e1117;color:white;}
    div[data-testid="metric-container"] {
        background:#1c1f26;
        padding:14px;
        border-radius:14px;
        text-align:center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("✈️ نظام التشغيل الذكي")

# =========================
# إعدادات
# =========================
DATA_FILE = "history.csv"
KAIA_URL = "https://www.kaia.sa/ar-SA/Flights?tab=1"

TERMINAL_MAP = {
    "صالة 1 (دولي)": ["1", "دولي", "international", "intl"],
    "صالة شمال (داخلي)": ["شمال", "داخلي", "domestic", "north"],
    "صالة حج": ["حج", "hajj", "umrah", "seasonal"],
}

# =========================
# واجهة
# =========================
terminal = st.selectbox(
    "🧭 اختر الصالة",
    ["صالة 1 (دولي)", "صالة شمال (داخلي)", "صالة حج"],
    index=0,
)

if st.button("🔄 تحديث البيانات"):
    st.rerun()

# =========================
# الطقس (مجاني)
# =========================
@st.cache_data(ttl=15 * 60)
def get_weather():
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=21.5&longitude=39.2&current_weather=true"
        )
        data = requests.get(url, timeout=10).json()
        temp = float(data["current_weather"]["temperature"])
        wind = float(data["current_weather"]["windspeed"])
        return temp, wind
    except Exception:
        return 30.0, 10.0


# =========================
# حفظ / تحميل التاريخ
# =========================
def load_history() -> pd.DataFrame:
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if not df.empty:
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
        return df
    return pd.DataFrame(
        columns=["time", "terminal", "flights", "temp", "wind"]
    )


def save_history(df: pd.DataFrame) -> None:
    history = load_history()
    combined = pd.concat([history, df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["time", "terminal", "flights"])
    combined.to_csv(DATA_FILE, index=False)


# =========================
# جلب بيانات حقيقية من صفحة KAIA العامة
# =========================
def _match_terminal(text: str, chosen_terminal: str) -> bool:
    hay = (text or "").lower()
    keywords = TERMINAL_MAP.get(chosen_terminal, [])
    return any(k.lower() in hay for k in keywords)


def _extract_time(text: str):
    m = re.search(r"\b([0-2]?\d:[0-5]\d)\b", text)
    if not m:
        return None
    try:
        t = dt.datetime.strptime(m.group(1), "%H:%M").time()
        return t
    except Exception:
        return None


@st.cache_data(ttl=60)
def fetch_kaia_real_flights(chosen_terminal: str) -> pd.DataFrame:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(KAIA_URL, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        page_text = soup.get_text(" ", strip=True)
        if "No Departures Found" in page_text or "لا توجد" in page_text:
            return pd.DataFrame(columns=["time", "terminal"])

        rows_data = []

        for tr in soup.select("table tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) < 2:
                continue

            row_text = " ".join(cells)

            # فلترة الصالة المختارة
            if not _match_terminal(row_text, chosen_terminal):
                continue

            # وقت الرحلة من أي خلية
            time_obj = None
            for cell in cells:
                time_obj = _extract_time(cell)
                if time_obj:
                    break

            if time_obj is None:
                time_obj = _extract_time(row_text)

            if time_obj is None:
                continue

            # نحولها إلى تاريخ اليوم
            flight_dt = dt.datetime.combine(dt.date.today(), time_obj)

            rows_data.append(
                {
                    "time": flight_dt,
                    "terminal": chosen_terminal,
                }
            )

        return pd.DataFrame(rows_data)

    except Exception:
        return pd.DataFrame(columns=["time", "terminal"])


# =========================
# AI يتعلم من البيانات
# =========================
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["hour"] = out["time"].dt.hour
    out["weekday"] = out["time"].dt.dayofweek
    out["month"] = out["time"].dt.month
    return out


def train_xgb(history: pd.DataFrame):
    feats = build_features(history)
    X = feats[["hour", "weekday", "month", "temp", "wind"]]
    y = feats["flights"]

    model = XGBRegressor(
        n_estimators=120,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
    )
    model.fit(X, y)
    return model


def predict_next_3h(model, base_time: dt.datetime, temp: float, wind: float) -> pd.DataFrame:
    future_rows = []
    for i in range(1, 7):  # 3 ساعات = 6 فترات × 30 دقيقة
        t = base_time + dt.timedelta(minutes=30 * i)
        pred = float(model.predict(pd.DataFrame([{
            "hour": t.hour,
            "weekday": t.weekday(),
            "month": t.month,
            "temp": temp,
            "wind": wind,
        }]))[0])

        future_rows.append({"time": t, "forecast": max(0.0, round(pred, 1))})

    return pd.DataFrame(future_rows)


# =========================
# تشغيل البيانات
# =========================
temp, wind = get_weather()

current_df = fetch_kaia_real_flights(terminal)

if current_df.empty:
    history = load_history()
    history_terminal = history[history["terminal"] == terminal].copy() if not history.empty else pd.DataFrame()

    if history_terminal.empty:
        st.error("❌ ما قدرنا نجلب بيانات حقيقية الآن، وما فيه تاريخ محفوظ للصالة المختارة.")
        st.stop()

    st.warning("⚠️ الصفحة الحالية ما عرضت رحلات، لذلك تم استخدام آخر بيانات حقيقية محفوظة.")
    current_df = history_terminal[["time", "terminal"]].copy()
else:
    # حفظ القراءة الحقيقية الحالية مع الطقس
    current_df["temp"] = temp
    current_df["wind"] = wind
    save_history(current_df[["time", "terminal", "temp", "wind"]])

# =========================
# تجميع الرحلات
# =========================
current_df["slot"] = current_df["time"].dt.floor("30min")
counts = current_df.groupby("slot").size().reset_index(name="flights")

# نضيف الطقس والتاريخ
counts["temp"] = temp
counts["wind"] = wind

# تحديث التاريخ الخاص بالتعلم
history = load_history()
if not history.empty:
    hist = history[history["terminal"] == terminal].copy()
else:
    hist = pd.DataFrame()

# إذا ما فيه تاريخ كفاية، نستخدم الحالي
train_source = hist if len(hist) >= 20 else counts.rename(columns={"slot": "time"}).copy()
if "time" not in train_source.columns:
    train_source = train_source.rename(columns={"slot": "time"})

train_source["time"] = pd.to_datetime(train_source["time"], errors="coerce")
train_source = train_source.dropna()

if len(train_source) >= 5:
    train_source = train_source.copy()
    train_source["flights"] = train_source["flights"].astype(float)
    model = train_xgb(train_source[["time", "flights", "temp", "wind"]].copy())
    future_df = predict_next_3h(model, counts["slot"].max(), temp, wind)
else:
    future_df = pd.DataFrame([
        {"time": counts["slot"].max() + dt.timedelta(minutes=30 * i), "forecast": float(counts["flights"].max())}
        for i in range(1, 7)
    ])

# =========================
# التحليل التشغيلي
# =========================
result = []
for _, row in counts.iterrows():
    f = int(row["flights"])
    passengers = f * 150
    counters = int(passengers / 25)
    staff = max(1, int(counters * 1.2))

    if f >= 20:
        level = "🔴 عالي"
        decision = "🚨 تدخل فوري"
    elif f >= 10:
        level = "🟡 متوسط"
        decision = "تعزيز"
    else:
        level = "🟢 طبيعي"
        decision = "تشغيل طبيعي"

    result.append([
        row["slot"].strftime("%H:%M"),
        f,
        passengers,
        counters,
        staff,
        level,
        decision,
    ])

final_df = pd.DataFrame(result, columns=[
    "الوقت", "الرحلات", "الركاب", "الكونترات", "الموظفين", "الحالة", "القرار"
])

# =========================
# لوحة تحكم بسيطة وواضحة
# =========================
st.subheader("📊 الحالة الآن")

peak = int(final_df["الرحلات"].max()) if not final_df.empty else 0
future_peak = int(future_df["forecast"].max()) if not future_df.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("✈️ الرحلات", int(final_df["الرحلات"].sum()) if not final_df.empty else 0)
c2.metric("📈 أعلى ضغط", peak)
c3.metric("🔮 توقع 3 ساعات", future_peak)
c4.metric("🌡️ الحرارة", f"{temp:.0f}°")

if future_peak >= 20:
    st.error(f"🚨 ضغط عالي متوقع خلال 3 ساعات ({future_peak})")
    st.audio("https://www.soundjay.com/buttons/sounds/beep-07.mp3", autoplay=True)
elif future_peak >= 10:
    st.warning(f"⚠️ ضغط متوسط متوقع خلال 3 ساعات ({future_peak})")
else:
    st.success("✅ الوضع مستقر خلال الساعات القادمة")

st.subheader("📋 جدول التشغيل")
st.dataframe(final_df, use_container_width=True)

st.subheader("🔮 توقع الذكاء الصناعي")
future_df["الوقت"] = future_df["time"].dt.strftime("%H:%M")
st.dataframe(future_df[["الوقت", "forecast"]], use_container_width=True)

st.subheader("📈 الحركة")
if not final_df.empty:
    st.line_chart(final_df.set_index("الوقت")["الرحلات"])

st.caption(f"آخر تحديث: {dt.datetime.now().strftime('%H:%M:%S')}")