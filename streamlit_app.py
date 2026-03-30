import streamlit as st
import pandas as pd
import datetime as dt
import requests
import random

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
# 📡 بيانات حقيقية (OpenSky)
# -----------------------------
def get_real_data():
    try:
        url = "https://opensky-network.org/api/flights/arrival?airport=OEJN"
        r = requests.get(url, timeout=5)

        # 🔍 Debug
        st.write("STATUS:", r.status_code)

        if r.status_code != 200:
            return None

        data = r.json()

        st.write("DATA LENGTH:", len(data) if data else 0)

        if not data:
            return None

        times = []

        for flight in data:
            if flight.get("lastSeen"):
                t = dt.datetime.fromtimestamp(flight["lastSeen"])
                times.append(t)

        if len(times) == 0:
            return None

        df = pd.DataFrame(times, columns=["time"])
        df["slot"] = df["time"].dt.floor("30min")

        df = df.groupby("slot").size().reset_index(name="flights")
        df.rename(columns={"slot": "time"}, inplace=True)

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
        data