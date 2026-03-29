import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt

st.set_page_config(page_title="Airport Dashboard", layout="wide")

st.title("✈️ تحليل صالة 1 - الرحلات الدولية")

now = dt.datetime.now()
times = [now + dt.timedelta(minutes=30*i) for i in range(48)]

data = []
for t in times:
    flights = np.random.randint(2, 12)
    passengers = flights * np.random.randint(80, 150)

    if passengers > 1000:
        status = "🔴 عالي"
        distribution = 4
        counters = 60
    else:
        status = "🟢 طبيعي"
        distribution = 2
        counters = 40

    data.append([t, flights, passengers, status, distribution, counters])

df = pd.DataFrame(data, columns=[
    "الوقت", "عدد الرحلات", "عدد الركاب", "الحالة", "التوزيع", "الكونترات"
])

st.dataframe(df, use_container_width=True)

st.subheader("📊 الرسم البياني")
st.line_chart(df.set_index("الوقت")["عدد الركاب"])

st.subheader("🚨 تنبيه ذكي")
alert = df[df["الحالة"] == "🔴 عالي"]

if not alert.empty:
    st.error("🚨 يوجد ضغط عالي خلال الساعة القادمة")
else:
    st.success("✅ الوضع طبيعي")
