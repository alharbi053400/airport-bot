import streamlit as st
import pandas as pd
import datetime as dt
import requests
import random

st.set_page_config(layout="wide")

st.title("✈️ نظام التشغيل الذكي")

terminal = st.selectbox(
    "اختر الصالة",
    ["صالة 1 (دولي)", "صالة شمال (داخلي)", "صالة حج"]
)

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
# 📡 محاولة بيانات حقيقية
# -----------------------------
def try_real_data():
    try:
        url = "https://www.kaia.sa/ar-SA/Flights?tab=1"
        r = requests.get(url, timeout=5)

        if "Flights" in r.text:
            return True
        else:
            return False
    except:
        return False

real = try_real_data()

# -----------------------------
# 📊 البيانات (ذكية)
# -----------------------------
now = dt.datetime.now()
data = []

for i in range(24):
    t = now + dt.timedelta(minutes=30*i)

    if terminal == "صالة 1 (دولي)":
        base = 18
    elif terminal == "صالة شمال (داخلي)":
        base = 10
    else:
        base = 6

    # ذروة صباح / مساء
    hour = t.hour
    peak_factor = 1

    if 6 <= hour <= 10:
        peak_factor = 1.4
    elif 17 <= hour <= 21:
        peak_factor = 1.6

    flights = int(base * peak_factor + random.randint(-2, 2))

    data.append([t, max(1, flights)])

df = pd.DataFrame(data, columns=["time","flights"])

# -----------------------------
# 🧠 AI ذكي
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
    st.audio("https://www.soundjay.com/buttons/sounds/beep-07.mp3", autoplay=True)
elif future_peak >= 12:
    st.warning("⚠️ ضغط متوسط")
else:
    st.success("✅ طبيعي")

# -----------------------------
# 📢 حالة البيانات
# -----------------------------
if real:
    st.success("📡 تم الاتصال بالموقع (لكن البيانات محدودة)")
else:
    st.info("ℹ️ الموقع لا يسمح بجلب البيانات حالياً - يتم استخدام AI ذكي")

# -----------------------------
# 📋 جدول
# -----------------------------
df["الوقت"] = df["time"].dt.strftime("%H:%M")

st.dataframe(df[["الوقت","flights","forecast"]], use_container_width=True)

# -----------------------------
# 📈 رسم
# -----------------------------
st.line_chart(df.set_index("الوقت")[["flights","forecast"]])