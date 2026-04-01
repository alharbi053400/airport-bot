import streamlit as st
import pandas as pd
import requests
import datetime as dt
import random
import re

st.set_page_config(layout="wide")
st.title("✈️ نظام تحليل الرحلات - صالة 1")

# =========================
# KAIA (محاولة سحب)
# =========================
def get_kaia_flights():
    url = "https://www.kaia.sa/ar-SA/flights?tab=1"
    times = []

    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        matches = re.findall(r"\d{2}:\d{2}", res.text)

        for m in matches:
            try:
                parsed = dt.datetime.strptime(m, "%H:%M")
                times.append(parsed)
            except:
                continue
    except:
        pass

    return times

# =========================
# fallback ذكي
# =========================
def fallback():
    now = dt.datetime.now()
    times = []

    for i in range(24):
        base = now + dt.timedelta(minutes=30*i)
        flights = random.randint(5, 20)

        for _ in range(flights):
            times.append(base)

    return times

# =========================
# AI تصحيح
# =========================
def ai_correction(df):

    corrected = []

    for _, row in df.iterrows():

        base = row["flights"]
        hour = row["slot"].hour

        if 6 <= hour <= 10:
            factor = 1.3
        elif 17 <= hour <= 23:
            factor = 1.5
        else:
            factor = 1.1

        new_val = int(base * factor)

        if new_val < base:
            new_val = base

        corrected.append(new_val)

    df["ai_flights"] = corrected
    return df

# =========================
# تشغيل البيانات
# =========================
data = get_kaia_flights()

if len(data) < 10:
    data = fallback()
    st.warning("⚠️ تشغيل محاكاة ذكية")
else:
    st.success("✅ بيانات من الموقع")

df = pd.DataFrame(data, columns=["time"])
df["time"] = pd.to_datetime(df["time"], errors="coerce")
df = df.dropna()

df["slot"] = df["time"].dt.floor("30min")

counts = df.groupby("slot").size().reset_index(name="flights")

# AI
counts = ai_correction(counts)

# =========================
# مقارنة AI
# =========================
st.subheader("🤖 تصحيح الذكاء الصناعي")

compare_df = counts[["slot","flights","ai_flights"]].copy()
compare_df.columns = ["الوقت","الفعلي","بعد AI"]
compare_df["الوقت"] = compare_df["الوقت"].dt.strftime("%H:%M")

st.dataframe(compare_df, use_container_width=True)

# =========================
# التحليل
# =========================
result = []

for _, row in counts.iterrows():

    f = row["ai_flights"]

    if f >= 20:
        level = "🔴 عالي"
        counters = 60
        support = 4
    elif f >= 10:
        level = "🟡 متوسط"
        counters = 50
        support = 3
    else:
        level = "🟢 طبيعي"
        counters = 40
        support = 2

    result.append([
        row["slot"],
        f,
        level,
        counters,
        support
    ])

final_df = pd.DataFrame(result, columns=[
    "الوقت","الرحلات","الحالة","الكونترات","الدعم"
])

final_df = final_df.sort_values("الوقت")
final_df["الوقت"] = final_df["الوقت"].dt.strftime("%H:%M")

# =========================
# عرض
# =========================
st.subheader("📊 لوحة التشغيل")

st.dataframe(final_df, use_container_width=True)

st.subheader("📈 الحركة")
st.area_chart(final_df.set_index("الوقت")["الرحلات"])