import streamlit as st
import pandas as pd
import requests
import datetime as dt
import random

st.set_page_config(page_title="Airport Dashboard", layout="wide")

st.title("✈️ نظام تحليل صالة 1 - الرحلات الدولية")

# =========================
# جلب البيانات (API + fallback)
# =========================
@st.cache_data
def get_flights():

    url = "https://api.kaia.sa/api/flights/departures"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=5)
        data = res.json()

        times = []

        for flight in data.get("data", []):
            t = flight.get("scheduledTime")
            if t:
                parsed = dt.datetime.fromisoformat(t)
                times.append(parsed)

        if len(times) > 5:
            return times, "real"

    except:
        pass

    # =========================
    # fallback (محاكاة ذكية)
    # =========================
    now = dt.datetime.now().replace(minute=0, second=0)

    times = []
    for i in range(24):

        base = now + dt.timedelta(minutes=30 * i)
        hour = base.hour

        if 6 <= hour <= 10:
            flights = random.randint(10, 20)
        elif 17 <= hour <= 22:
            flights = random.randint(12, 25)
        else:
            flights = random.randint(3, 8)

        for _ in range(flights):
            times.append(base)

    return times, "simulated"


# =========================
# تشغيل النظام
# =========================
data, mode = get_flights()

if mode == "simulated":
    st.warning("⚠️ يتم تشغيل وضع المحاكاة (البيانات غير متاحة حالياً)")
else:
    st.success("✅ بيانات حقيقية محدثة")

df = pd.DataFrame(data, columns=["time"])

df["time"] = pd.to_datetime(df["time"], errors="coerce")
df = df.dropna()

# تقسيم الوقت
df["slot"] = df["time"].dt.floor("30min")

# تجميع الرحلات
counts = df.groupby("slot").size().reset_index(name="flights")

# =========================
# التحليل الذكي
# =========================
result = []

for _, row in counts.iterrows():

    f = row["flights"]
    employees = min(f * 3, 50)

    if f >= 20:
        level = "🔴 عالي"
        dist = 4
        counters = 60
        action = "زيادة فورية + فتح كل الكونترات"
    elif f >= 10:
        level = "🟡 متوسط"
        dist = 3
        counters = 50
        action = "تعزيز جزئي"
    else:
        level = "🟢 طبيعي"
        dist = 2
        counters = 40
        action = "تشغيل طبيعي"

    result.append([
        row["slot"],
        f,
        employees,
        level,
        dist,
        counters,
        action
    ])

final_df = pd.DataFrame(result, columns=[
    "الوقت",
    "الرحلات",
    "الموظفين",
    "الحالة",
    "الدعم",
    "الكونترات",
    "التوصية"
])

# ترتيب وتحسين الوقت
final_df = final_df.sort_values("الوقت")
final_df["الوقت"] = final_df["الوقت"].dt.strftime("%H:%M")

# =========================
# KPI
# =========================
st.subheader("📊 مؤشرات التشغيل")

col1, col2, col3 = st.columns(3)

col1.metric("إجمالي الرحلات", int(final_df["الرحلات"].sum()))
col2.metric("أعلى ضغط", int(final_df["الرحلات"].max()))
col3.metric("متوسط الرحلات", round(final_df["الرحلات"].mean(), 1))

# =========================
# تنبيه
# =========================
if final_df["الرحلات"].max() >= 20:
    st.error("🚨 ضغط عالي جداً - تدخل فوري")
elif final_df["الرحلات"].max() >= 10:
    st.warning("⚠️ ضغط متوسط - راقب التشغيل")
else:
    st.success("✅ الوضع مستقر")

# =========================
# الجدول
# =========================
st.subheader("📋 جدول الرحلات")

st.dataframe(final_df, use_container_width=True)

# =========================
# الرسم البياني
# =========================
st.subheader("📈 حركة الرحلات")

chart_df = final_df.set_index("الوقت")

st.area_chart(chart_df["الرحلات"])

# =========================
# تنبيه الذروة
# =========================
peak = final_df[final_df["الرحلات"] == final_df["الرحلات"].max()]

if not peak.empty:
    st.error(f"🚨 ذروة التشغيل عند: {peak.iloc[0]['الوقت']}")