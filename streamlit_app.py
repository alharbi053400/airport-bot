import os
import re
import json
import datetime as dt
from typing import Any, Dict, List

import requests
import pandas as pd
import streamlit as st


# =========================
# إعدادات أساسية
# =========================
st.set_page_config(page_title="KAIA Live Dashboard", layout="wide")
st.title("✈️ صالة 1 - رحلات حقيقية + تحديث مباشر")

ORIGIN = "JED"
BASE_URL = os.getenv("AMADEUS_BASE_URL", "https://test.api.amadeus.com")
API_KEY = os.getenv("AMADEUS_API_KEY", st.secrets.get("AMADEUS_API_KEY", ""))
API_SECRET = os.getenv("AMADEUS_API_SECRET", st.secrets.get("AMADEUS_API_SECRET", ""))

st.caption(f"آخر تحديث: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


# =========================
# أدوات مساعدة
# =========================
def _parse_datetime(value: str):
    if not isinstance(value, str):
        return None

    v = value.strip()

    # ISO datetime
    if "T" in v:
        try:
            return dt.datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None

    # HH:MM or HH:MM:SS
    if re.fullmatch(r"\d{2}:\d{2}(:\d{2})?", v):
        try:
            today = dt.date.today().isoformat()
            return dt.datetime.fromisoformat(f"{today}T{v}")
        except Exception:
            return None

    return None


def _collect_datetimes(obj: Any) -> List[dt.datetime]:
    out: List[dt.datetime] = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                out.extend(_collect_datetimes(v))
            else:
                # نلتقط أي قيمة تبدو كوقت/تاريخ-وقت
                parsed = _parse_datetime(v) if isinstance(v, str) else None
                if parsed:
                    out.append(parsed)

    elif isinstance(obj, list):
        for item in obj:
            out.extend(_collect_datetimes(item))

    elif isinstance(obj, str):
        parsed = _parse_datetime(obj)
        if parsed:
            out.append(parsed)

    return out


# =========================
# Amadeus: Token
# =========================
@st.cache_data(ttl=25 * 60)
def get_token() -> str:
    if not API_KEY or not API_SECRET:
        return ""

    token_url = f"{BASE_URL}/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": API_SECRET,
    }

    r = requests.post(token_url, headers=headers, data=body, timeout=20)
    r.raise_for_status()
    return r.json().get("access_token", "")


# =========================
# Amadeus: routes from JED
# =========================
@st.cache_data(ttl=20 * 60)
def get_direct_destinations(origin: str = ORIGIN, max_results: int = 200) -> List[str]:
    token = get_token()
    if not token:
        return []

    url = f"{BASE_URL}/v1/airport/direct-destinations"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"departureAirportCode": origin, "max": max_results}

    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()

    payload = r.json()
    dests = []

    for item in payload.get("data", []):
        code = item.get("iataCode")
        if code and code != origin:
            dests.append(code)

    # إزالة التكرار مع الحفاظ على الترتيب
    seen = set()
    unique = []
    for d in dests:
        if d not in seen:
            unique.append(d)
            seen.add(d)

    return unique


# =========================
# Amadeus: flight availability per route
# =========================
def get_route_availability(token: str, origin: str, destination: str, date_str: str) -> Dict[str, Any]:
    url = f"{BASE_URL}/v1/shopping/availability/flight-availabilities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-HTTP-Method-Override": "POST",
    }

    body = {
        "originDestinations": [
            {
                "id": "1",
                "originLocationCode": origin,
                "destinationLocationCode": destination,
                "departureDateTimeRange": {"date": date_str},
            }
        ],
        "travelers": [{"id": "1", "travelerType": "ADULT"}],
        "sources": ["GDS"],
    }

    r = requests.post(url, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    return r.json()


# =========================
# تحميل كل الرحلات
# =========================
@st.cache_data(ttl=10 * 60)
def load_all_flights() -> pd.DataFrame:
    token = get_token()
    if not token:
        return pd.DataFrame(columns=["time", "destination", "source"])

    destinations = get_direct_destinations(ORIGIN, 200)
    today = dt.date.today().isoformat()

    rows = []

    for dest in destinations:
        try:
            payload = get_route_availability(token, ORIGIN, dest, today)
            datetimes = _collect_datetimes(payload)

            for t in datetimes:
                rows.append(
                    {
                        "time": t,
                        "destination": dest,
                        "source": "Amadeus",
                    }
                )
        except Exception:
            # إذا مسار معيّن فشل، نكمل على الباقي
            continue

    if not rows:
        return pd.DataFrame(columns=["time", "destination", "source"])

    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna()
    df = df.drop_duplicates(subset=["time", "destination"])
    return df


# =========================
# عرض مباشر كل دقيقة
# =========================
@st.fragment(run_every="60s")
def live_dashboard():
    if not API_KEY or not API_SECRET:
        st.error("أدخل AMADEUS_API_KEY و AMADEUS_API_SECRET أولًا.")
        st.stop()

    flights_df = load_all_flights()

    if flights_df.empty:
        st.warning(
            "لم أستطع استخراج بيانات صالحة من الاستجابة الحالية. "
            "إذا كنت على Test environment فهذا قد يكون بسبب حدود/كاش Amadeus."
        )
        st.stop()

    now = dt.datetime.now()
    next_60 = now + dt.timedelta(minutes=60)

    # الرحلات خلال الساعة القادمة
    upcoming = flights_df[(flights_df["time"] >= now) & (flights_df["time"] <= next_60)].copy()
    upcoming["slot"] = upcoming["time"].dt.floor("30min")

    counts = upcoming.groupby("slot").size().reset_index(name="flights")

    if counts.empty:
        # إذا ما فيه رحلات في الساعة القادمة، اعرض أقرب 24 ساعة حتى لا تكون الصفحة فارغة
        future = flights_df[flights_df["time"] >= now].copy()
        future["slot"] = future["time"].dt.floor("30min")
        counts = future.groupby("slot").size().reset_index(name="flights")

    result = []
    for _, row in counts.iterrows():
        f = int(row["flights"])
        employees = min(f * 3, 50)

        if f >= 20:
            level = "🔴 عالي"
            support = 4
            counters = 60
            decision = "تدخل فوري"
        elif f >= 10:
            level = "🟡 متوسط"
            support = 3
            counters = 50
            decision = "مراقبة وتعزيز"
        else:
            level = "🟢 طبيعي"
            support = 2
            counters = 40
            decision = "تشغيل عادي"

        result.append(
            {
                "الوقت": row["slot"],
                "الرحلات": f,
                "الموظفين": employees,
                "الحالة": level,
                "الدعم": support,
                "الكونترات": counters,
                "القرار": decision,
            }
        )

    final_df = pd.DataFrame(result)
    final_df = final_df.sort_values("الوقت")
    final_df["الوقت"] = final_df["الوقت"].dt.strftime("%H:%M")

    total_flights = int(final_df["الرحلات"].sum())
    peak_flights = int(final_df["الرحلات"].max())
    avg_flights = round(final_df["الرحلات"].mean(), 1)

    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي الرحلات", total_flights)
    c2.metric("أعلى ضغط", peak_flights)
    c3.metric("متوسط الرحلات", avg_flights)

    if peak_flights >= 20:
        st.error(f"🚨 ضغط عالي جداً ({peak_flights} رحلة) - تدخل فوري")
    elif peak_flights >= 10:
        st.warning(f"⚠️ ضغط متوسط ({peak_flights} رحلة) - راقب التشغيل")
    else:
        st.success("✅ الوضع مستقر")

    def highlight(row):
        if row["الحالة"] == "🔴 عالي":
            return ["background-color: #ff4b4b"] * len(row)
        if row["الحالة"] == "🟡 متوسط":
            return ["background-color: #f1c40f"] * len(row)
        return ["background-color: #2ecc71"] * len(row)

    st.subheader("📋 خطة التشغيل القادمة")
    st.dataframe(final_df.style.apply(highlight, axis=1), use_container_width=True)

    st.subheader("📈 حركة الرحلات")
    st.area_chart(final_df.set_index("الوقت")["الرحلات"])

    peak_row = final_df[final_df["الرحلات"] == peak_flights].iloc[0]
    st.info(f"ذروة التشغيل المتوقعة عند {peak_row['الوقت']}، والقرار: {peak_row['القرار']}")

    with st.expander("عرض الرحلات الخام"):
        st.dataframe(upcoming.sort_values("time"), use_container_width=True)


live_dashboard()