import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime as dt

st.title("✈️ تحليل الرحلات - صالة 1")

URL = "https://www.kaia.sa/ar-SA/flights?tab=1"


@st.cache_data
def get_flights():
    res = requests.get(URL)
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


# تشغيل الدالة
data = get_flights()

df = pd.DataFrame(data, columns=["time"])

df["time"] = pd.to_datetime(df["time"], errors="coerce")
df = df.dropna()

# إذا ما فيه بيانات → محاكاة
if df.empty:
    st.warning("⚠️ يتم تشغيل وضع المحاكاة")

    now = dt.datetime.now()
    times = [now + dt.timedelta(minutes=30*i) for i in range(24)]

    df = pd.DataFrame(times, columns=["time"])


# تقسيم الوقت
df["slot"] = df["time"].dt.floor("30min")

# التجميع
counts = df.groupby("slot").size().reset_index(name="flights")

result = []

for _, row in counts.iterrows():
    f = row["flights"]
    total = min(f * 3, 50)

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

    result.append([
        row["slot"],
        f,
        total,
        level,
        dist,
        counters
    ])


final_df = pd.DataFrame(result, columns=[
    "الوقت", "الرحلات", "الموظفين", "الحالة", "الدعم", "الكونترات"
])

st.dataframe(final_df, use_container_width=True)

st.subheader("📊 الرسم البياني")
st.line_chart(final_df.set_index("الوقت")["الرحلات"])