import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import time

# 🔐 Secrets
TOKEN = st.secrets["TELEGRAM_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
API_KEY = st.secrets["API_KEY"]

API_URL = "http://api.aviationstack.com/v1/flights"

SAUDI_AIRPORTS = [
    "RUH","DMM","MED","GIZ","TUU","AHB","EAM","HAS",
    "ELQ","URY","AJF","ULH","RAE","SHW","NUM","DWD"
]

# 📡 جلب البيانات
@st.cache_data(ttl=7200)
def get_flights():
    params = {
        "access_key": API_KEY,
        "dep_iata": "JED"
    }
    response = requests.get(API_URL, params=params)
    return response.json()

# ✈️ فلترة
def filter_flights(data):
    flights = data.get("data", [])
    result = []

    for f in flights:
        dep = f.get("departure", {})
        arr = f.get("arrival", {})

        if dep.get("terminal") != "1":
            continue

        if arr.get("iata") in SAUDI_AIRPORTS:
            continue

        result.append(f)

    return result

# 📊 تحليل
def analyze(flights):
    times = {}

    for f in flights:
        time_str = f["departure"]["scheduled"]
        if not time_str:
            continue

        t = datetime.fromisoformat(time_str.replace("Z",""))
        minute = "00" if t.minute < 30 else "30"
        key = t.strftime(f"%H:{minute}")

        times[key] = times.get(key, 0) + 1

    return times

# 🔮 توقع
def predict(times):
    pred = {}
    keys = sorted(times.keys())

    for i in range(len(keys)):
        now = times[keys[i]]

        if i < len(keys)-1:
            nxt = times[keys[i+1]]
            pred[keys[i]] = int((now + nxt) / 2)
        else:
            pred[keys[i]] = now

    return pred

# 🤖 ارسال تلجرام
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ================= UI =================

st.set_page_config(page_title="Airport Dashboard", layout="wide")

st.title("✈️ Dashboard صالة 1 (دولي)")
st.markdown("👤 ريان الحميدي الحربي | 📞 0534006391")

# تحديث تلقائي
refresh = st.button("🔄 تحديث الآن")

data = get_flights()
flights = filter_flights(data)
times = analyze(flights)
prediction = predict(times)

# 📊 احصائيات
col1, col2, col3 = st.columns(3)

total = len(flights)
peak = max(times.values()) if times else 0
low = min(times.values()) if times else 0

col1.metric("✈️ عدد الرحلات", total)
col2.metric("🔥 أعلى زحمة", peak)
col3.metric("😌 أهدأ وقت", low)

# 📈 رسم
if times:
    df = pd.DataFrame({
        "Time": list(times.keys()),
        "Flights": list(times.values())
    })

    st.subheader("📊 الزحمة")
    st.line_chart(df.set_index("Time"))

# 🔮 التوقع
if prediction:
    st.subheader("🔮 التوقع القادم")
    df2 = pd.DataFrame({
        "Time": list(prediction.keys()),
        "Predicted": list(prediction.values())
    })

    st.line_chart(df2.set_index("Time"))

# 🚨 تنبيه
for t, count in times.items():
    if count >= 5:
        st.error(f"🚨 زحمة خانقة {t} ({count})")
    elif count >= 3:
        st.warning(f"⚠️ زحمة {t} ({count})")
    else:
        st.success(f"✅ طبيعي {t} ({count})")

# 📤 ارسال تقرير
if st.button("📤 ارسال تقرير تيليجرام"):
    report = f"📊 تقرير صالة 1\n✈️ {total} رحلات\n"

    for t, c in times.items():
        report += f"{t} → {c}\n"

    send_telegram(report)
    st.success("تم الإرسال ✅")

# 🔁 تحديث تلقائي كل 30 ثانية (Live)
time.sleep(30)
st.rerun()