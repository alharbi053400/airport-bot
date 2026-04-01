import streamlit as st
import pandas as pd
import datetime as dt
import random

st.set_page_config(layout="wide")

st.title("✈️ نظام تشغيل صالة 1 (دولي)")

# =============================
# 1️⃣ DATA LAYER
# =============================
def get_data():
    now = dt.datetime.now()
    data = []

    destinations = [
        "دبي","القاهرة","إسطنبول","لندن","الدوحة",
        "جاكرتا","لاهور","كراتشي"
    ]

    for i in range(24):
        t = now + dt.timedelta(minutes=30*i)

        flights = random.randint(18, 25)
        passengers = flights * random.randint(120, 180)

        destination = random.choice(destinations)
        delay = random.choice([0, 0, 10, 15, 20])

        data.append([t, destination, flights, passengers, delay])

    df = pd.DataFrame(
        data,
        columns=["time","destination","flights","passengers","delay"]
    )

    return df

# =============================
# 2️⃣ LOGIC LAYER
# =============================
def analyze(df):
    df["hour"] = df["time"].dt.hour

    df["forecast"] = df["flights"] * (
        1 +
        (df["hour"].between(6,10))*0.3 +
        (df["hour"].between(17,21))*0.4
    )

    # تأثير التأخير
    df["forecast"] += df["delay"] * 0.2

    return df

# =============================
# 3️⃣ UI LAYER
# =============================
df = get_data()
df = analyze(df)

# ✈️ الرحلات المتأخرة فقط
delayed_df = df[df["delay"] > 0]

df["الوقت"] = df["time"].dt.strftime("%H:%M")

# -----------------------------
# 📊 مؤشرات
# -----------------------------
total_flights = int(df["flights"].sum())
total_passengers = int(df["passengers"].sum())
total_delay = int(df["delay"].sum())

c1, c2, c3 = st.columns(3)

c1.metric("✈️ الرحلات", total_flights)
c2.metric("👥 الركاب", total_passengers)
c3.metric("⏱️ التأخير", total_delay)

# -----------------------------
# 🚨 تنبيه
# -----------------------------
if total_delay > 200:
    st.error("🚨 تأخير عالي")
elif total_delay > 100:
    st.warning("⚠️ تأخير متوسط")
else:
    st.success("✅ طبيعي")

# -----------------------------
# 📋 الجدول الرئيسي
# -----------------------------
st.subheader("📋 جميع الرحلات")

st.dataframe(
    df[["الوقت","destination","flights","passengers","delay","forecast"]],
    use_container_width=True
)

# -----------------------------
# 🚨 الرحلات المتأخرة
# -----------------------------
st.subheader("🚨 الرحلات المتأخرة")

if delayed_df.empty:
    st.success("✅ لا توجد رحلات متأخرة")
else:
    delayed_df["الوقت"] = delayed_df["time"].dt.strftime("%H:%M")

    st.dataframe(
        delayed_df[["الوقت","destination","delay","flights","passengers"]],
        use_container_width=True
    )

# -----------------------------
# 📈 الرسم
# -----------------------------
st.line_chart(df.set_index("الوقت")[["flights","forecast"]])