import streamlit as st
import pandas as pd
import datetime as dt
import random

st.set_page_config(layout="wide")

st.title("✈️ نظام تشغيل الرحلات")

# =============================
# بيانات تشغيل (مثل PDF)
# =============================
def get_data():
    now = dt.datetime.now()

    destinations = [
        "لاهور","لندن هيثرو","القاهرة","كراتشي",
        "إسلام آباد","تونس","أبوظبي","عمان",
        "كوالالمبور","دكا","دبي","جاكرتا","الجزائر"
    ]

    airlines = ["Saudia","Flynas","Emirates","Qatar","Turkish"]

    data = []

    for i in range(20):
        t = now + dt.timedelta(minutes=15*i)

        destination = random.choice(destinations)
        flight_number = f"{random.choice(['SV','XY','EK','QR','TK'])}{random.randint(100,999)}"

        delay = random.choice([0, 0, 10, 20, 30])

        # الحالة
        if delay > 0:
            status = "متأخرة"
        else:
            status = random.choice(["وصلت","في موعدها","جاري الوصول"])

        delay_time = ""
        if delay > 0:
            delay_time = (t + dt.timedelta(minutes=delay)).strftime("%H:%M")

        data.append([
            t.strftime("%H:%M"),
            destination,
            flight_number,
            status,
            delay_time
        ])

    df = pd.DataFrame(
        data,
        columns=["الوقت","الوجهة","رقم الرحلة","الحالة","وقت التأخير"]
    )

    return df

df = get_data()

# =============================
# جدول التشغيل
# =============================
st.subheader("📋 الرحلات")

st.dataframe(df, use_container_width=True)

# =============================
# تحليل التشغيل
# =============================
st.subheader("📊 تحليل التشغيل")

# عدد المتأخر
delayed_count = df[df["الحالة"] == "متأخرة"].shape[0]

# الضغط
if delayed_count >= 7:
    level = "🔴 مرتفع"
    staff = 8
elif delayed_count >= 4:
    level = "🟡 متوسط"
    staff = 5
else:
    level = "🟢 منخفض"
    staff = 3

col1, col2, col3 = st.columns(3)

col1.metric("عدد الرحلات", len(df))
col2.metric("عدد المتأخرة", delayed_count)
col3.metric("عدد الموظفين المقترح", staff)

st.write(f"مستوى الضغط: {level}")