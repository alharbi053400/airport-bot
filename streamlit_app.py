import streamlit as st
import pandas as pd
import requests
import datetime as dt
import random
import os
from xgboost import XGBRegressor

st.set_page_config(layout="wide")
st.title("✈️ نظام تشغيل صالة 1 + AI + خريطة")

st.caption(f"آخر تحديث: {dt.datetime.now().strftime('%H:%M:%S')}")

DATA_FILE = "history.csv"

# =========================
# تحميل / حفظ البيانات
# =========================
def load_history():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["time","flights"])

def save_history(df):
    history = load_history()
    combined = pd.concat([history, df])
    combined.to_csv(DATA_FILE, index=False)

# =========================
# جلب الطائرات (مستقر)
# =========================
def get_live_aircraft():
    url = "https://opensky-network.org/api/states/all"
    planes = []

    try:
        res = requests.get(url, timeout=5)
        data = res.json()

        for p in data.get("states", []):
            lat = p[6]
            lon = p[5]

            if lat and lon:
                if 20 <= lat <= 25 and 37 <= lon <= 42:
                    planes.append({"lat": lat, "lon": lon})

    except Exception as e:
        st.warning("⚠️ تعذر جلب الطائرات")

    return pd.DataFrame(planes)

# =========================
# تحويل الطائرات إلى رحلات
# =========================
def aircraft_to_flights():
    planes = get_live_aircraft()
    times = []

    now = dt.datetime.now()

    for _ in range(len(planes)):
        eta = now + dt.timedelta(minutes=random.randint(10, 90))
        times.append(eta)

    return times

# =========================
# fallback قوي
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
# AI (XGBoost)
# =========================
def ai_model(df):
    history = load_history()

    if len(history) < 50:
        df["forecast"] = df["flights"] * 1.2
        return df

    history["time"] = pd.to_datetime(history["time"])
    history["hour"] = history["time"].dt.hour
    history["day"] = history["time"].dt.dayofweek

    X = history[["hour","day"]]
    y = history["flights"]

    model = XGBRegressor(n_estimators=50)
    model.fit(X, y)

    preds = []

    for _, row in df.iterrows():
        h = row["slot"].hour
        d = row["slot"].dayofweek

        p = model.predict([[h,d]])[0]
        final = int((p + row["flights"]) / 2)

        if final < row["flights"]:
            final = row["flights"]

        preds.append(final)

    df["forecast"] = preds
    return df

# =========================
# تشغيل النظام
# =========================
try:
    times = aircraft_to_flights()
except:
    times = []

if len(times) < 5:
    st.warning("⚠️ تشغيل وضع المحاكاة")
    times = fallback()
else:
    st.success("✅ بيانات طائرات مباشرة")

df = pd.DataFrame(times, columns=["time"])
df["time"] = pd.to_datetime(df["time"], errors="coerce")
df = df.dropna()

df["slot"] = df["time"].dt.floor("30min")

counts = df.groupby("slot").size().reset_index(name="flights")

save_history(counts.rename(columns={"slot":"time"}))

counts = ai_model(counts)

# =========================
# الخريطة
# =========================
st.subheader("🗺️ الطائرات حول جدة")

map_df = get_live_aircraft()

if map_df.empty:
    st.warning("⚠️ لا توجد بيانات - عرض نقطة افتراضية")
    map_df = pd.DataFrame({"lat":[21.5],"lon":[39.2]})

st.map(map_df)

# =========================
# التحليل
# =========================
result = []

for _, row in counts.iterrows():
    f = row["forecast"]

    if f >= 20:
        level = "🔴 عالي"
        counters = 60
        support = 4
        decision = "تدخل فوري"
    elif f >= 10:
        level = "🟡 متوسط"
        counters = 50
        support = 3
        decision = "تعزيز"
    else:
        level = "🟢 طبيعي"
        counters = 40
        support = 2
        decision = "تشغيل طبيعي"

    result.append([
        row["slot"],
        f,
        level,
        counters,
        support,
        decision
    ])

final_df = pd.DataFrame(result, columns=[
    "الوقت","الرحلات","الحالة","الكونترات","الدعم","القرار"
])

final_df["الوقت"] = final_df["الوقت"].dt.strftime("%H:%M")

# =========================
# KPI
# =========================
c1,c2,c3 = st.columns(3)
c1.metric("إجمالي الرحلات", int(final_df["الرحلات"].sum()))
c2.metric("أعلى ضغط", int(final_df["الرحلات"].max()))
c3.metric("توقع الذروة", int(counts["forecast"].max()))

# =========================
# الجدول
# =========================
st.subheader("📊 لوحة التشغيل")

st.dataframe(final_df, use_container_width=True)

# =========================
# الرسم
# =========================
st.subheader("📈 الحركة")

st.line_chart(final_df.set_index("الوقت")["الرحلات"])