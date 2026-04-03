import requests
import pandas as pd
import time
from datetime import datetime

# 🔑 بياناتك
TOKEN = 8714913319:AAHzb0k4XvMfA8lbH_1NZi7iMW0jm_OqGtM
CHAT_ID = 1234119654
API_KEY = "02b0bd12fc73d4c2b7741a7e2f3f6685"

API_URL = "http://api.aviationstack.com/v1/flights"

# 📤 إرسال ملف تيليجرام
def send_file(file_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    with open(file_path, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"document": f})

# 🌐 جلب الرحلات
def get_flights():
    params = {
        "access_key": API_KEY,
        "dep_iata": "JED"
    }

    res = requests.get(API_URL, params=params)
    data = res.json()

    print("📊 API RESPONSE:", data)  # مهم للتشخيص

    return data

# 🧹 فلترة
def filter_flights(data):
    flights = []

    for f in data.get("data", []):
        try:
            flights.append({
                "رقم الرحلة": f["flight"]["iata"],
                "الوجهة": f["arrival"]["airport"],
                "شركة الطيران": f["airline"]["name"],
                "الحالة": f["flight_status"]
            })
        except:
            continue

    return flights

# 📊 إنشاء Excel
def create_excel(flights):
    if not flights:
        flights = [{"ملاحظة": "لا توجد بيانات"}]

    df = pd.DataFrame(flights)

    filename = f"report_{datetime.now().strftime('%H_%M')}.xlsx"
    df.to_excel(filename, index=False)

    return filename

# 🚀 التشغيل
def main():
    print("🚀 بدأ التشغيل")

    while True:
        try:
            print("🔄 تحديث...")

            data = get_flights()
            flights = filter_flights(data)

            file = create_excel(flights)
            send_file(file)

            print("✅ تم الإرسال")

        except Exception as e:
            print("❌ خطأ:", e)

        # ⏱️ للتجربة خليه 10 ثواني
        time.sleep(10)


main()