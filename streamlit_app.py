import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime as dt
import random

st.set_page_config(layout="wide")

st.title("✈️ نظام تشغيل صالة 1 + AI + خريطة")

URL = "https://www.kaia.sa/ar-SA/flights?tab=1"

# -----------------------------
# 📡 جلب الرحلات (محاولة)
# -----------------------------
@st.cache_data(ttl=60)
def get_flights():
    try:
        res = requests.get(URL, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        times = []
        rows = soup.select("table tr")

        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            t = cols[3].text.strip()

            try:
                parsed = dt.datetime.strptime(t, "%H:%M")
                times.append(parsed)
            except:
                continue

        return times

    except:
        return []

# -----------------------------
# 🧠 AI بسيط للتوقع
# -----------------------------
def predict_next(hour_counts):
    predictions = []
    for i in range(len(hour_counts)):
        window = hour_counts[max(0, i-2):i+1]
        avg = sum(window) / len(window)
        predictions.append(round(avg, 1))
    return predictions

# -----------------------------
# 📊 معالجة البيانات
# -----------------------------
data = get_flights()

if len(data) == 0:
    st.warning("⚠️ يتم تشغيل وضع المحاكاة (البيانات غير متاحة حالياً)")

    now = dt.datetime.now()
    data = [now + dt.timedelta(minutes=30*i) for i in range(48)]

df = pd.DataFrame(data, columns=["time"])
df["time"] = pd.to_datetime(df["time"], errors="coerce")
df = df.dropna()

df["slot"] = df["time"].dt.floor("30min")

counts = df.groupby("slot").size().reset_index(name="flights")

# -----------------------------
# 🧠 AI prediction
# -----------------------------
counts["prediction"] = predict_next(counts["flights"].tolist())

# -----------------------------
# ⚙️ تحليل التشغيل
# -----------------------------
result = []

for _, row in counts.iterrows():
    f = row["prediction"]
    total = min(int(f * 3), 60)

    if f >= 20:
        level = "🔴 عالي"
        dist = 4
        counters = 60
        decision = "🚨 تدخل فوري"
    elif f >= 10:
        level = "🟡 متوسط"
        dist = 3
        counters = 50
        decision = "تعزيز"
    else:
        level = "🟢 طبيعي"
        dist = 2
        counters = 40
        decision = "تشغيل طبيعي"

    result.append([
        row["slot"],
        round(f,1),
        total,
        level,
        dist,
        counters,
        decision
    ])

final_df = pd.DataFrame(result, columns=[
    "الوقت", "الرحلات", "الموظفين",
    "الحالة", "الدعم", "الكونترات", "القرار"
])

# -----------------------------
# 📊 مؤشرات
# -----------------------------
st.subheader("📊 مؤشرات التشغيل")

col1, col2, col3 = st.columns(3)

col1.metric("إجمالي الرحلات", int(final_df["الرحلات"].sum()))
col2.metric("أعلى ضغط", int(final_df["الرحلات"].max()))
col3.metric("توقع الذروة", int(final_df["الرحلات"].max()))

# -----------------------------
# 🚨 تنبيه
# -----------------------------
if final_df["الرحلات"].max() >= 20:
    st.error("🚨 ضغط عالي جداً - تدخل فوري")

# -----------------------------
# 📋 الجدول
# -----------------------------
st.subheader("📋 لوحة التشغيل")
st.dataframe(final_df, use_container_width=True)

# -----------------------------
# 📈 الرسم
# -----------------------------
st.subheader("📈 الحركة")
st.line_chart(final_df.set_index("الوقت")["الرحلات"])

# -----------------------------
# 🗺️ الخريطة (محاكاة)
# -----------------------------
st.subheader("🗺️ الطائرات حول جدة (محاكاة)")

st.image(
    "https://upload.wikimedia.org/wikipedia/commons/6/6f/Jeddah_map.png",
    use_container_width=True
)

planes = []

for i in range(random.randint(5, 15)):
    lat = 21.3 + random.uniform(-0.3, 0.3)
    lon = 39.1 + random.uniform(-0.3, 0.3)

    planes.append({
        "الطائرة": f"FLT{i}",
        "الموقع": f"{lat:.2f}, {lon:.2f}",
        "الوصول": f"{random.randint(10,90)} دقيقة"
    })

planes_df = pd.DataFrame(planes)

st.dataframe(planes_df, use_container_width=True)

# -----------------------------
# ⏱️ آخر تحديث
# -----------------------------
st.caption(f"آخر تحديث: {dt.datetime.now().strftime('%H:%M:%S')}")