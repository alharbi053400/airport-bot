import streamlit as st
import pandas as pd
import requests
import datetime as dt
import random
import re
import os

st.set_page_config(layout="wide")
st.title("✈️ نظام تحليل الرحلات - AI متعلم")

st.caption(f"آخر تحديث: {dt.datetime.now().strftime('%H:%M:%S')}")

# =========================
# تحميل البيانات القديمة
# =========================
DATA_FILE = "history.csv"

def load_history():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["time","flights"])

def save_history(df):
    history = load_history()
    combined = pd.concat([history, df])
    combined.to_csv(DATA_FILE, index=False)

# =========================
# KAIA
# =========================
def get_kaia_flights():
    url = "https://www.kaia.sa/ar-SA/flights?tab=1"
    times = []

    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        matches = re.findall(r"\d{2}:\d{2}", res.text)

        for m in matches:
            parsed = dt.datetime.strptime(m, "%H:%M")
            times.append(parsed)
    except:
        pass

    return times

# =========================
# fallback
# =========================
def fallback():
    now = dt.datetime.now()
    times = []

    for i in range(24):
        base = now + dt.timedelta(minutes=30*i)
        flights = random.randint(5, 20)

        for _ in range(flights):
            times.append(base)

    return times

# =========================
# AI تعلم من البيانات
# =========================
def ai_learning_predict(df):

    history = load_history()

    if len(history) < 20:
        df["forecast"] = df["flights"] * 1.2
        return df

    history["time"] = pd.to_datetime(history["time"])
    history["hour"] = history["time"].dt.hour

    avg_by_hour = history.groupby("hour")["flights"].mean()

    predictions = []

    for _, row in df.iterrows():
        hour = row["slot"].hour
        base = row["flights"]

        if hour in avg_by_hour:
            learned = avg_by_hour[hour]
            pred = int((base + learned) / 2)
        else:
            pred = int(base * 1.2)

        predictions.append(pred)

    df["forecast"] = predictions
    return df

# =========================
# تشغيل
# =========================
data = get_kaia_flights()

if len(data) < 10:
    data = fallback()
    st.warning("⚠️ تشغيل محاكاة")
else:
    st.success("✅ بيانات حقيقية")

df = pd.DataFrame(data, columns=["time"])
df["time"] = pd.to_datetime(df["time"], errors="coerce")
df = df.dropna()

df["slot"] = df["time"].dt.floor("30min")

counts = df.groupby("slot").size().reset_index(name="flights")

# حفظ للتعلم
save_history(counts.rename(columns={"slot":"time"}))

# AI تعلم
counts = ai_learning_predict(counts)

# =========================
# عرض المقارنة
# =========================
st.subheader("🤖 AI يتعلم من البيانات")

compare = counts.copy()
compare["الوقت"] = compare["slot"].dt.strftime("%H:%M")
compare = compare[["الوقت","flights","forecast"]]
compare.columns = ["الوقت","الحالي","توقع AI"]

st.dataframe(compare, use_container_width=True)

# =========================
# تنبيه
# =========================
future_max = counts["forecast"].max()

if future_max >= 20:
    st.error(f"🚨 ضغط عالي متوقع ({future_max})")
elif future_max >= 10:
    st.warning(f"⚠️ ضغط متوسط ({future_max})")
else:
    st.success("✅ الوضع مستقر")

# =========================
# تحليل
# =========================
result = []

for _, row in counts.iterrows():

    f = row["forecast"]

    if f >= 20:
        level = "🔴 عالي"
        counters = 60
        support = 4
    elif f >= 10:
        level = "🟡 متوسط"
        counters = 50
        support = 3
    else:
        level = "🟢 طبيعي"
        counters = 40
        support = 2

    result.append([
        row["slot"],
        f,
        level,
        counters,
        support
    ])

final_df = pd.DataFrame(result, columns=[
    "الوقت","الرحلات","الحالة","الكونترات","الدعم"
])

final_df["الوقت"] = final_df["الوقت"].dt.strftime("%H:%M")

# =========================
# KPI
# =========================
c1,c2,c3 = st.columns(3)
c1.metric("إجمالي الرحلات", int(final_df["الرحلات"].sum()))
c2.metric("أعلى ضغط", int(final_df["الرحلات"].max()))
c3.metric("توقع الذروة", int(future_max))

# =========================
# عرض
# =========================
st.subheader("📊 لوحة التشغيل")

st.dataframe(final_df, use_container_width=True)

st.subheader("📈 الحركة")

st.area_chart(final_df.set_index("الوقت")["الرحلات"])