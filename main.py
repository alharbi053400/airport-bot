import requests
import pandas as pd
import time
import os
from datetime import datetime

# 🔐 متغيرات آمنة
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
API_KEY = os.getenv("API_KEY")

API_URL = "http://api.aviationstack.com/v1/flights"

SAUDI_AIRPORTS = [
    "RUH","DMM","MED","GIZ","TUU","AHB","EAM","HAS",
    "ELQ","URY","AJF","ULH","RAE","SHW","NUM","DWD"
]

# 📤 إرسال الملف
def send_file(file_path):
    print("📤 جاري إرسال الملف...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    with open(file_path, "rb") as f:
        res = requests.post(url, data={"chat_id": CHAT_ID}, files={"document": f})
    print("📨 تم الإرسال:", res.status_code)

# ✈️ جلب الرحلات
def get_flights():
    print("🌐 جلب البيانات...")
    params = {
        "access_key": API_KEY,
        "dep_iata": "JED"
    }
    res = requests.get(API_URL, params=params)
    print("📡 Status:", res.status_code)
    return res.json()

# 🔎 فلترة
def filter_flights(data):
    flights = data.get("data", [])
    result = []

    for f in flights:
        dep = f.get("departure", {})
        arr = f.get("arrival", {})

        if dep.get("terminal") != "1":
            continue

        if arr.get("iata") in SAUDI_AIRPORTS:
            continue

        result.append(f) كل

    print("📊 بعد الفلترة:", len(result))
    return result

# 📈 تحليل
def analyze(flights):
    times = {}

    for f in flights:
        time_str = f.get("departure", {}).get("scheduled")
        if not time_str:
            continue

        try:
            t = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            minute = "00" if t.minute < 30 else "30"
            key = t.strftime(f"%H:{minute}")
            times[key] = times.get(key, 0) + 1
        except:
            continue

    print("📈 التحليل:", times)
    return times

# 📁 إنشاء Excel
def create_excel(times):
    rows = []

    for t, count in sorted(times.items()):
        if count >=  6:
            status = "زحمة خانقة"
        elif count >= 3:
            status = "زحمة"
        else:
            status = "طبيعي"

        rows.append({
            "الوقت": t,
            "عدد الرحلات": count,
            "الحالة": status
        })

df = pd.DataFrame(rows)

filename = f"report_{datetime.now().strftime('%H_%M')}.xlsx"

df.to_excel(filename, index=False)

print("📁 تم إنشاء:", filename)
return filename

# 🚀 التشغيل
def main():
    print("🚀 بدء التشغيل")

    while True:
        try:
            data = get_flights()
            flights = filter_flights(data)
            times = analyze(flights)

            file = create_excel(times)
            send_file(file)

            print("✅ تم بنجاح")

    except Exception as e:
            print("❌ خطأ:", e)

        time.sleep(300)  # كل 5 دقائق

if __name__ == "__main__":
    main()