import streamlit as st
import requests
from datetime import datetime

st.set_page_config(layout="wide")

st.title("✈️ نظام تشغيل صالة (بيانات حقيقية)")

API_KEY = "02b0bd12fc73d4c2b7741a7e2f3f6685"

flight_number = st.text_input("ادخل رقم الرحلة (مثال: SV102)")

if flight_number:

    url = "http://api.aviationstack.com/v1/flights"

    params = {
        "access_key": API_KEY,
        "flight_iata": flight_number
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "data" in data and len(data["data"]) > 0:

        flight = data["data"][0]

        destination = flight["arrival"]["airport"]
        scheduled = flight["arrival"]["scheduled"]
        estimated = flight["arrival"]["estimated"]
        actual = flight["arrival"]["actual"]
        status = flight["flight_status"]

        st.subheader("📊 معلومات الرحلة")

        c1, c2, c3 = st.columns(3)

        c1.metric("🌍 الوجهة", destination)
        c2.metric("📡 الحالة", status)
        c3.metric("✈️ الرحلة", flight_number)

        st.write("⏰ المجدول:", scheduled)
        st.write("🔮 المتوقع:", estimated)
        st.write("✅ الفعلي:", actual)

        # حساب التأخير
        if scheduled and actual:
            fmt = "%Y-%m-%dT%H:%M:%S%z"

            try:
                s = datetime.strptime(scheduled, fmt)
                a = datetime.strptime(actual, fmt)

                delay = int((a - s).total_seconds() / 60)

                st.metric("⏱️ التأخير (دقائق)", delay)

                if delay > 30:
                    st.error("🚨 تأخير عالي")
                elif delay > 10:
                    st.warning("⚠️ تأخير متوسط")
                else:
                    st.success("✅ في الوقت")

            except:
                st.warning("⚠️ مشكلة في قراءة الوقت")

        else:
            st.info("ℹ️ الرحلة لم تصل بعد")

    else:
        st.error("❌ الرحلة غير موجودة")