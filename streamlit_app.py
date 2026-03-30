import streamlit as st
import pandas as pd
import datetime as dt
import requests
import url = "https://opensky-network.org/api/flights/departure?airport=OEJN"

st.set_page_config(layout="wide")

st.title("✈️ نظام تشغيل صالة 1 (دولي)")

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
# 📊 البيانات
# -----------------------------
def get_real_flights():
    try:
        url = "https://opensky-network.org/api/flights/departure?airport=OEJN"
        r = requests.get(url, timeout=10)

        if r.status_code != 200:
            return None

        data = r.json()

        times = []

        for flight in data:
            if flight.get("firstSeen"):
                t = dt.datetime.fromtimestamp(flight["firstSeen"])
                times.append(t)

        if len(times) == 0:
            return None

        df = pd.DataFrame(times, columns=["time"])

        df["slot"] = df["time"].dt.floor("30min")

        df = df.groupby("slot").size().reset_index(name="flights")
        df.rename(columns={"slot":"time"}, inplace=True)

        # تقدير الركاب
        df["passengers"] = df["flights"] * 150

        return df

    except:
        return None
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

# -----------------------------
# 📊 المؤشرات
# -----------------------------
peak = int(df["flights"].max())
future_peak = int(df["forecast"].max())
total_passengers = int(df["passengers"].sum())

c1, c2, c3, c4 = st.columns(4)

c1.metric("✈️ الرحلات", int(df["flights"].sum()))
c2.metric("👥 الركاب", total_passengers)
c3.metric("📈 أعلى ضغط", peak)
c4.metric("🔮 التوقع", future_peak)

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
    df[["الوقت","flights","passengers","forecast"]],
    use_container_width=True
)

# -----------------------------
# 📈 رسم (مهم يكون سطر واحد)
# -----------------------------
st.line_chart(df.set_index("الوقت")[["flights","forecast"]])