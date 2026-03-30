import streamlit as st
import pandas as pd
import datetime as dt
import requests
import random

st.set_page_config(layout="wide")

st.title("✈️ نظام تشغيل صالة 1 (دولي)")

# -----------------------------
# 🔄 زر تحديث
# -----------------------------
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
# 📊 بيانات (ثابتة وذكية)
# -----------------------------
now = dt.datetime.now()
data = []

for i in range(24):
    t = now + dt.timedelta(minutes=30 * i)

    base = 20  # صالة 1

    hour = t.hour

    if 6 <= hour <= 10:
        base *= 1.4
    elif 17 <= hour <= 21:
        base *= 1.6

    flights = int(base + random.randint(-2, 2))
    data.append([t, max(1, flights)])

df = pd.DataFrame(data, columns=["time", "flights"])

# -----------------------------
# 🧠 التوقع
# -----------------------------
df["hour"] = df["time"].dt.hour

df["forecast"] = df["flights"] * (
    1 +
    (df["hour"].between(6, 10)) * 0.3 +
    (df["hour"].between(17, 21)) * 0.4
)

if temp > 35:
    df["forecast"] *= 1.1

# --------------