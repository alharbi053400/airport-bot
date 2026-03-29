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

    flights = []
    rows = soup.select("table tr")

    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        time = cols[3].text.strip()
        flights.append(time)

    return flights


data = get_flights()

# تحويل لأوقات
times = []
for t in data:
    try:
        parsed = dt.datetime.strptime(t, "%H:%M")
        times.append(parsed)
    except:
        continue

df = pd.DataFrame(times, columns=["time"])

# تجميع كل 30 دقيقة
df["slot"] = df["time"].dt.floor("30min")
counts = df.groupby("slot").size().reset_index(name="flights")

# تحليل
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