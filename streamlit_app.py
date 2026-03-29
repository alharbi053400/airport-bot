import streamlit as st
import pandas as pd
import datetime as dt
import requests
from bs4 import BeautifulSoup
import random
import re

st.set_page_config(layout="wide")

st.title("✈️ نظام التشغيل الذكي")

# -----------------------------
# 🧭 اختيار الصالة
# -----------------------------
terminal = st.selectbox(
    "🧭 اختر الصالة",
    [
        "صالة 1 (دولي)",
        "الصالة الشمالية (دولي)",
        "صالة الحج والعمرة"
    ]
)

# زر تحديث
if st.button("🔄 تحديث"):
    st.rerun()

# -----------------------------
# 🌦️ الطقس
# -----------------------------
def get_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=21.5&longitude=39.2&current_weather=true"
        data = requests.get(url).json()
        return data["current_weather"]["temperature"]
    except:
        return 30

temp = get_weather()

# -----------------------------
# 📡 بيانات حقيقية (محاولة)
# -----------------------------
def get_real_data():
    try:
        url = "https://www.kaia.sa/ar-SA/Flights?tab=1"
        headers = {"User-Agent": "Mozilla/5.0"}

        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")

        times = []

        for tr in soup.select("table tr"):
            text = tr.get_text(" ", strip=True)

            # فلترة الصالة
            if terminal == "صالة 1 (دولي)" and "1" not in text:
                continue
            if terminal == "الصالة الشمالية (دولي)" and "شمال" not in text:
                continue
            if terminal == "صالة الحج والعمرة" and "حج" not in text:
                continue

            match = re.search(r"\d{2}:\d{2}", text)
            if match:
                t = dt.datetime.strptime(match.group(), "%H:%M")
                times.append(t)

        if len(times) == 0:
            return None

        df = pd.DataFrame(times, columns=["time"])
        df["slot"] = df["time"].dt.floor("30min")

        df = df.groupby("slot").size().reset_index(name="flights")
        df.rename(columns={"slot":"time"}, inplace=True)

        return df

    except:
        return None

# -----------------------------
# 🤖 AI fallback
# -----------------------------
def generate_ai_data():
    now = dt.datetime.now()
    data = []

    for i in range(24):
        t = now + dt.timedelta(minutes=30*i)

        if terminal == "صالة 1 (دولي)":
            base = 20
        elif terminal == "الصالة الشمالية (دولي)":
            base = 14
        else:
            base = 8

        hour = t.hour

        if 6 <= hour <= 10:
            base *= 1.4
        elif 17 <= hour <= 21:
            base *= 1.6

        flights = int(base + random.randint(-2, 2))

        data.append([t, max(1, flights)])

    df = pd.DataFrame(data, columns=["time","flights"])
    return df

# -----------------------------
# 🎯 اختيار المصدر
# -----------------------------
df = get_real_data()

if df is not None:
    st.success("📡 بيانات حقيقية")
else:
    st.warning("⚠️ تم استخدام AI بدل البيانات الحقيقية")
    df = generate_ai_data()

# -----------------------------
# 🧠 التوقع
# -----------------------------
df["hour"] = df["time"].dt.hour

df["forecast"] = df["flights"] * (
    1 +
    (df["hour"].between(6,10))*0.3 +
    (df["hour"].between(17,21))*0.4
)

if temp > 35:
    df["forecast"] *= 1.1

peak = int(df["flights"].max())
future_peak = int(df["forecast"].max())

# -----------------------------
# 📊 مؤشرات
# -----------------------------
c1, c2, c3 = st.columns(3)

c1.metric("✈️ الرحلات", int(df["flights"].sum()))
c2.metric("📈 أعلى ضغط", peak)
c3.metric("🔮 التوقع", future_peak)

# -----------------------------
# 🚨 تنبيه
# -----------------------------
if future_peak >= 25:
    st.error("🚨 ضغط عالي جداً")
elif future_peak >= 12:
    st.warning("⚠️ ضغط متوسط")
else:
    st.success("✅ طبيعي")

# -----------------------------
# 📋 جدول
# -----------------------------
df["الوقت"] = df["time"].dt.strftime("%H:%M")

st.dataframe(df[["الوقت","flights","forecast"]], use_container_width=True)

# -----------------------------
# 📈 رسم
# -----------------------------
st.line_chart(df.set_index("الوقت")[["flights","forecast"]])