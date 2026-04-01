import streamlit as st
import pandas as pd
import datetime as dt
import random

st.set_page_config(layout="wide")

st.title("✈️ نظام تشغيل صالة 1 (دولي)")

# زر تحديث
if st.button("🔄 تحديث"):
    st.rerun()

# زر البيانات الحقيقية
st.link_button(
    "📡 عرض الرحلات الحقيقية من المطار",
    "https://www.kaia.sa/ar-SA/Flights/Departure"
)

# -----------------------------
# 🌍 وجهات
# -----------------------------
destinations = [
    "دبي", "القاهرة", "إسطنبول", "الرياض", "الدوحة"
]

# -----------------------------
# 📊 البيانات
# -----------------------------
now = dt.datetime.now()
data = []

for i in range(24):
    t = now + dt.timedelta(minutes=30*i)

    base = 20
    hour = t.hour

    if 6 <= hour <= 10:
        base *= 1.4
    elif 17 <= hour <= 21:
        base *= 1.6

    flights = int(base + random.randint(-2, 2))
    passengers = flights * random.randint(120, 180)

    # الوجهة
    destination = random.choice(destinations)

    # التأخير (واقعي)
    delay = random.choice([0, 0, 10, 15])

    data.append([t, flights, passengers, destination, delay])

df = pd.DataFrame(
    data,
    columns=["time","flights","passengers","destination","delay"]
)

# -----------------------------
# 🧠 التوقع
# -----------------------------
df["hour"] = df["time"].dt.hour

df["forecast"] = df["flights"] * (
    1 +
    (df["hour"].between(6,10))*0.3 +
    (df["hour"].between(17,21))*0.4
)

# -----------------------------
# 📊 المؤشرات
# -----------------------------
peak = int(df["flights"].max())
future_peak = int(df["forecast"].max())
total_passengers = int(df["passengers"].sum())

c1, c2, c3 = st.columns(3)

c1.metric("✈️ الرحلات", int(df["flights"].sum()))
c2.metric("👥 الركاب", total_passengers)
c3.metric("📈 أعلى ضغط", peak)

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

st.dataframe(
    df[["الوقت","destination","flights","passengers","delay","forecast"]],
    use_container_width=True
)

# -----------------------------
# 📈 رسم
# -----------------------------
st.line_chart(df.set_index("الوقت")[["flights","forecast"]])