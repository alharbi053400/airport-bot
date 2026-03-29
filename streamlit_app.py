import streamlit as st
import pandas as pd
import datetime as dt
import requests
import random

st.set_page_config(layout="wide")

# -----------------------------
# 🎨 تصميم (أبشر ستايل)
# -----------------------------
st.markdown("""
<style>
.main {background-color:#0e1117;color:white;}
div[data-testid="metric-container"] {
    background:#1c1f26;
    padding:15px;
    border-radius:12px;
    text-align:center;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 🎯 عنوان
# -----------------------------
st.title("✈️ نظام تشغيل الصالة")

# -----------------------------
# 🧭 اختيار الصالة
# -----------------------------
terminal = st.selectbox(
    "🧭 اختر الصالة",
    ["صالة 1 (دولي)", "صالة شمال (داخلي)", "صالة حج"]
)

# -----------------------------
# 🔘 زر تحديث
# -----------------------------
if st.button("🔄 تحديث"):
    st.rerun()

# -----------------------------
# 🌦️ الطقس (حقيقي)
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
# 📊 بيانات (بديلة عن Selenium)
# -----------------------------
@st.cache_data(ttl=60)
def get_data():

    now = dt.datetime.now()
    data = []

    for i in range(24):
        t = now.replace(minute=0, second=0) + dt.timedelta(minutes=30*i)

        if terminal == "صالة 1 (دولي)":
            flights = random.randint(10, 25)
        elif terminal == "صالة شمال (داخلي)":
            flights = random.randint(5, 15)
        else:
            flights = random.randint(3, 10)

        data.append([t, flights])

    return pd.DataFrame(data, columns=["time","flights"])

df = get_data()

# -----------------------------
# 📊 تحليل
# -----------------------------
peak = int(df["flights"].max())
total = int(df["flights"].sum())

# -----------------------------
# 📊 مؤشرات
# -----------------------------
st.subheader("📊 الحالة")

c1, c2, c3, c4 = st.columns(4)

c1.metric("✈️ الرحلات", total)
c2.metric("📈 أعلى ضغط", peak)
c3.metric("🔮 التوقع", peak + 3)
c4.metric("🌡️ الحرارة", f"{temp}°")

# -----------------------------
# 🚨 تنبيه
# -----------------------------
st.subheader("🚨 الحالة")

if peak >= 20:
    st.error("🚨 ضغط عالي - تدخل فوري")
    st.audio("https://www.soundjay.com/buttons/sounds/beep-07.mp3", autoplay=True)
elif peak >= 10:
    st.warning("⚠️ ضغط متوسط")
else:
    st.success("✅ طبيعي")

# -----------------------------
# 📋 جدول
# -----------------------------
st.subheader("📋 جدول التشغيل")

df["الوقت"] = df["time"].dt.strftime("%H:%M")

st.dataframe(df[["الوقت","flights"]], use_container_width=True)

# -----------------------------
# 📈 رسم
# -----------------------------
st.subheader("📈 الحركة")

st.line_chart(df.set_index("الوقت")["flights"])