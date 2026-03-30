import streamlit as st
import pandas as pd
import datetime as dt
import requests
import random

st.set_page_config(layout="wide")

st.title("✈️ نظام تشغيل صالة 1 (دولي)")

if st.button("🔄 تحديث"):
    st.rerun()

def get_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=21.5&longitude=39.2&current_weather=true"
        data = requests.get(url).json()
        return data["current_weather"]["temperature"]
    except:
        return 30

temp = get_weather()

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

    data.append([t, flights, passengers])

df = pd.DataFrame(data, columns=["time","flights","passengers"])

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
total_passengers = int(df["passengers"].sum())

c1, c2, c3, c4 = st.columns(4)

c1.metric("✈️ الرحلات", int(df["flights"].sum()))
c2.metric("👥 الركاب", total_passengers)
c3.metric("📈 أعلى ضغط", peak)
c4.metric("🔮 التوقع", future_peak)

if future_peak >= 25:
    st.error("🚨 ضغط عالي جداً")
elif future_peak >= 12:
    st.warning("⚠️ ضغط متوسط")
else:
    st.success("✅ طبيعي")

df["الوقت"] = df["time"].dt.strftime("%H:%M")

st.dataframe(df[["الوقت","flights","passengers","forecast"]], use_container_width=True)

st.line_chart(df.set_index("الوقت")[["flights","forecast"]])