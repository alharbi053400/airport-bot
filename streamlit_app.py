import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime as dt
import random
from xgboost import XGBRegressor

st.set_page_config(layout="wide")

st.title("✈️ نظام تشغيل المطار - AI لكل صالة")

URL = "https://www.kaia.sa/ar-SA/flights?tab=1"

# -----------------------------
# 📡 جلب الرحلات
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
# 🧠 توزيع الصالات
# -----------------------------
def assign_terminal():
    r = random.random()
    if r < 0.6:
        return "صالة 1 (دولي)"
    elif r < 0.9:
        return "صالة شمال (داخلي)"
    else:
        return "صالة حج"

# -----------------------------
# 🧠 تدريب AI لكل صالة
# -----------------------------
def train_model(df):

    df["hour"] = df["slot"].dt.hour
    df["day"] = df["slot"].dt.day

    X = df[["hour","day"]]
    y = df["flights"]

    model = XGBRegressor(n_estimators=50)
    model.fit(X, y)

    return model

# -----------------------------
# 🔮 توقع
# -----------------------------
def predict(model, last_time):

    preds = []

    for i in range(1,5):
        t = last_time + dt.timedelta(minutes=30*i)
        p = model.predict([[t.hour, t.day]])[0]

        preds.append(round(p,1))

    return max(preds)

# -----------------------------
# 👥 توزيع الموظفين
# -----------------------------
def staff_distribution(flights):

    passengers = flights * 150  # تقدير

    counters = int(passengers / 30)
    staff = int(counters * 1.2)
    supervisors = max(1, int(counters / 20))

    return passengers, counters, staff, supervisors

# -----------------------------
# 📊 تشغيل
# -----------------------------
data = get_flights()

if len(data) == 0:
    st.warning("⚠️ محاكاة")
    now = dt.datetime.now()
    data = [now + dt.timedelta(minutes=30*i) for i in range(48)]

df = pd.DataFrame(data, columns=["time"])
df["time"] = pd.to_datetime(df["time"])
df["slot"] = df["time"].dt.floor("30min")
df["terminal"] = df["time"].apply(lambda x: assign_terminal())

# -----------------------------
# 🎛️ اختيار الصالة
# -----------------------------
terminal_choice = st.radio(
    "اختر الصالة:",
    ["الجميع", "صالة 1 (دولي)", "صالة شمال (داخلي)", "صالة حج"],
    horizontal=True
)

if terminal_choice != "الجميع":
    df = df[df["terminal"] == terminal_choice]

# -----------------------------
# 📊 تجميع
# -----------------------------
counts = df.groupby(["slot","terminal"]).size().reset_index(name="flights")

# -----------------------------
# 🧠 AI لكل صالة
# -----------------------------
final = []

for terminal in counts["terminal"].unique():

    sub = counts[counts["terminal"] == terminal]

    model = train_model(sub)

    future_peak = predict(model, sub["slot"].max())

    for _, row in sub.iterrows():

        f = row["flights"]

        passengers, counters, staff, supervisors = staff_distribution(f)

        if f >= 20:
            level = "🔴 عالي"
            decision = "🚨 تدخل فوري"
        elif f >= 10:
            level = "🟡 متوسط"
            decision = "تعزيز"
        else:
            level = "🟢 طبيعي"
            decision = "تشغيل طبيعي"

        final.append([
            row["slot"],
            terminal,
            f,
            passengers,
            counters,
            staff,
            supervisors,
            future_peak,
            level,
            decision
        ])

final_df = pd.DataFrame(final, columns=[
    "الوقت","الصالة","الرحلات","الركاب","الكونترات",
    "الموظفين","المشرفين","توقع الذروة","الحالة","القرار"
])

final_df["الوقت"] = final_df["الوقت"].dt.strftime("%H:%M")

# -----------------------------
# 📊 KPI
# -----------------------------
st.subheader("📊 مؤشرات التشغيل")

c1,c2,c3 = st.columns(3)

c1.metric("إجمالي الركاب", int(final_df["الركاب"].sum()))
c2.metric("أعلى ضغط", int(final_df["الرحلات"].max()))
c3.metric("أعلى توقع", int(final_df["توقع الذروة"].max()))

# -----------------------------
# 📋 جدول
# -----------------------------
st.subheader("📋 نظام التشغيل الذكي")

st.dataframe(final_df, use_container_width=True)

# -----------------------------
# 📈 رسم
# -----------------------------
st.subheader("📈 الضغط")

chart = final_df.pivot(index="الوقت", columns="الصالة", values="الرحلات")

st.line_chart(chart)

# -----------------------------
# 🗺️ خريطة
# -----------------------------
st.subheader("🗺️ خريطة المطار")
st.image(
    "https://upload.wikimedia.org/wikipedia/commons/6/6f/Jeddah_map.png",
    use_container_width=True
)

# -----------------------------
# ⏱️ تحديث
# -----------------------------
st.caption(f"آخر تحديث: {dt.datetime.now().strftime('%H:%M:%S')}")