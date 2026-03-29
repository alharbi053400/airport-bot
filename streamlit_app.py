import streamlit as st
import pandas as pd
import requests
import datetime as dt
import random

st.title("✈️ تحليل الرحلات - صالة 1")

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

        # لو جاب بيانات فعلاً
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

        # توزيع ذكي للزحام
        hour = base.hour

        if 6 <= hour <= 10:
            flights = random.randint(10, 20)  # صباح
        elif 17 <= hour <= 22:
            flights = random.randint(12, 25)  # مساء (زحمة)
        else:
            flights = random.randint(3, 8)   # عادي

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

# تقسيم كل 30 دقيقة
df["slot"] = df["time"].dt.floor("30min")

# عدد الرحلات
counts = df.groupby("slot").size().reset_index(name="flights")

# =========================
# التحليل الذكي
# =========================
result = []

for _, row in counts.iterrows():

    f = row["flights"]

    # حساب الموظفين
    employees = min(f * 3, 50)

    # تحديد الحالة
    if f >= 20:
        level = "🔴 عالي"
        dist = 4
        counters = 60
    elif f >= 10:
        level = "🟡 متوسط"
        dist = 3
        counters = 50
    else:
        level = "🟢 طبيعي"
        dist = 2
        counters = 40

    # توصية تشغيل
    if f >= 20:
        action = "زيادة فورية + فتح كل الكونترات"
    elif f >= 10:
        action = "تعزيز جزئي"
    else:
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

# =========================
# عرض البيانات
# =========================
st.dataframe(final_df, use_container_width=True)

# =========================
# تنبيه الذروة
# =========================
peak = final_df[final_df["الرحلات"] == final_df["الرحلات"].max()]

if not peak.empty:
    st.error(f"🚨 ذروة التشغيل عند: {peak.iloc[0]['الوقت']}")

# =========================
# الرسم البياني
# =========================
st.subheader("📊 الرسم البياني")

st.line_chart(final_df.set_index("الوقت")["الرحلات"])