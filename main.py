print("🔥🔥🔥 اشتغل الملف 🔥🔥🔥")
import requests
import pandas as pd
import time
from datetime import datetime

TOKEN = "8714913319:AAF7lWfrtPbWItM-7sj0JhYMVN9zdPofGd8"
CHAT_ID = "1234119654"
API_KEY = "02b0bd12fc73d4c2b7741a7e2f3f6685"

API_URL = "http://api.aviationstack.com/v1/flights"

def send_file(file_path):
    print("📤 إرسال الملف...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    with open(file_path, "rb") as f:
        res = requests.post(url, data={"chat_id": CHAT_ID}, files={"document": f})
    print("📨 Telegram:", res.text)

def get_flights():
    print("🌐 جلب البيانات...")
    params = {
        "access_key": API_KEY,
        "dep_iata": "JED"
    }
    res = requests.get(API_URL, params=params)
    print("📡 STATUS:", res.status_code)
    return res.json()

def filter_flights(data):
    flights = []

    for f in data.get("data", []):
        flights.append({
            "رقم الرحلة": f.get("flight", {}).get("iata"),
            "شركة الطيران": f.get("airline", {}).get("name"),
            "من": f.get("departure", {}).get("airport"),
            "إلى": f.get("arrival", {}).get("airport"),
            "الوقت": f.get("departure", {}).get("scheduled"),
            "الحالة": f.get("flight_status")
        })

    print("✈️ عدد الرحلات:", len(flights))
    return flights

def create_excel(flights):
    if not flights:
        flights = [{"ملاحظة": "لا توجد بيانات"}]

    df = pd.DataFrame(flights)
    filename = f"report_{datetime.now().strftime('%H_%M')}.xlsx"
    df.to_excel(filename, index=False)

    return filename

def main():
    print("🚀 البوت اشتغل")

    while True:
        try:
            data = get_flights()
            flights = filter_flights(data)

            file = create_excel(flights)
            send_file(file)

            print("✅ تم الإرسال")

        except Exception as e:
            print("❌ خطأ:", str(e))

        time.sleep(10)

if __name__=="__main__":
    main()