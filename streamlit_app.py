import requests
import pandas as pd
import time
from datetime import datetime

# 🔐 بياناتك (عدّل فقط CHAT_ID)
TOKEN = "8714913319:AAF7lWfrtPbWItM-7sj0JhYMVN9zdPofGd8"
CHAT_ID = "1234119654"
API_KEY = "02b0bd12fc73d4c2b7741a7e2f3f6685"

API_URL = "http://api.aviationstack.com/v1/flights"

SAUDI_AIRPORTS = [
    "RUH","DMM","MED","GIZ","TUU","AHB","EAM","HAS",
    "ELQ","URY","AJF","ULH","RAE","SHW","NUM","DWD"
]

# 📤 إرسال ملف
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
    print("🔍 فلترة الرحلات...")
    flights = data.get("data", [])
    result = []

    for f in flights:
        dep = f.get("departure", {})
        arr = f.get("arrival", {})

        if dep.get("terminal") != "1":
            continue

        if arr.get("iata") in SAUDI_AIRPORTS:
            continue

        result.append(f)

    print("📊 عدد الرحلات بعد الفلترة:", len(result))
    return result

# 📊 تحليل
def analyze(flights):
    print("📈 تحليل البيانات...")
    times = {}

    for f in flights:
        time_str = f.get("departure", {}).get("scheduled")
        if not time_str:
            continue

        try:
            t = datetime.fromisoformat(time_str.replace("Z",""))
        except:
            continue

        minute = "00" if t.minute < 30 else "30"
        key = t.strftime(f"%H:{minute}")

        times[key] = times.get(key, 0) + 1

    return times

# 📁 Excel
def create_excel(times):
    print("📁 إنشاء ملف Excel...")
    rows = []

    for t, count in sorted(times.items()):
        if count >= 5:
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

    if not rows:
        rows = [{"ملاحظة": "لا توجد بيانات"}]

    df = pd.DataFrame(rows)

    filename = f"report_{datetime.now().strftime('%H_%M')}.xlsx"
    df.to_excel(filename, index=False)

    print("✅ تم إنشاء الملف:", filename)
    return filename

# 🚀 التشغيل
def main():
    print("🚀 بدأ التشغيل")

    while True:
        try:
            print("🔄 تحديث جديد...")

            data = get_flights()
            flights = filter_flights(data)
            times = analyze(flights)

            file = create_excel(times)
            send_file(file)

            print("✅ تم الإرسال بنجاح")

        except Exception as e:
            print("❌ خطأ:", e)
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": f"خطأ:\n{str(e)}"}
            )

        time.sleep(60)  # للتجربة كل دقيقة

if __name__ == "__main__":
    main()