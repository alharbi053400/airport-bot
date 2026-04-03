import requests
import pandas as pd
import time
from datetime import datetime

TOKEN = "8714913319:AAF7lWfrtPbWItM-7sj0JhYMVN9zdPofGd8"
CHAT_ID = "1234119654"
API_KEY = "02b0bd12fc73d4c2b7741a7e2f3f6685"

API_URL = "http://api.aviationstack.com/v1/flights"

def send_file(file_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    with open(file_path, "rb") as f:
        res = requests.post(url, data={"chat_id": CHAT_ID}, files={"document": f})
    print(res.text)

def get_flights():
    params = {
        "access_key": API_KEY,
        "dep_iata": "JED"
    }
    res = requests.get(API_URL, params=params)
    print("STATUS:", res.status_code)
    return res.json()

def filter_flights(data):
    flights = []

    if "data" not in data:
        return flights

    for f in data["data"]:
        try:
            flights.append({
                "رقم الرحلة": f.get("flight", {}).get("iata"),
                "شركة الطيران": f.get("airline", {}).get("name"),
                "من": f.get("departure", {}).get("airport"),
                "إلى": f.get("arrival", {}).get("airport"),
                "الوقت": f.get("departure", {}).get("scheduled"),
                "الحالة": f.get("flight_status")
            })
        except:
            continue

    return flights

def create_excel(flights):
    if not flights:
        flights = [{"ملاحظة": "لا توجد بيانات"}]

    df = pd.DataFrame(flights)

    filename = f"report_{datetime.now().strftime('%H_%M')}.xlsx"
    df.to_excel(filename, index=False)

    return filename

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
            import traceback
            print("❌ خطأ:")
            traceback.print_exc()

        time.sleep(10)

main()