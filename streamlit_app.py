import requests
import pandas as pd
import time
from datetime import datetime

TOKEN = "حط توكنك"
CHAT_ID = "حط ايديك"
API_KEY = "حط مفتاحك"

API_URL = "http://api.aviationstack.com/v1/flights"

SAUDI_AIRPORTS = [
    "RUH","DMM","MED","GIZ","TUU","AHB","EAM","HAS",
    "ELQ","URY","AJF","ULH","RAE","SHW","NUM","DWD"
]

def send_file(file_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    with open(file_path, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"document": f})

def get_flights():
    params = {
        "access_key": API_KEY,
        "dep_iata": "JED"
    }
    res = requests.get(API_URL, params=params)
    return res.json()

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

        result.append(f)

    return result

def analyze(flights):
    times = {}

    for f in flights:
        time_str = f["departure"]["scheduled"]
        if not time_str:
            continue

        t = datetime.fromisoformat(time_str.replace("Z",""))
        minute = "00" if t.minute < 30 else "30"
        key = t.strftime(f"%H:{minute}")

        times[key] = times.get(key, 0) + 1

    return times

def create_excel(times):
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

    df = pd.DataFrame(rows)

    filename = f"report_{datetime.now().strftime('%H_%M')}.xlsx"
    df.to_excel(filename, index=False)

    return filename

def main():
    while True:
        try:
            data = get_flights()
            flights = filter_flights(data)
            times = analyze(flights)

            file = create_excel(times)
            send_file(file)

            print("تم الإرسال")

        except Exception as e:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": f"خطأ:\n{str(e)}"}
            )

        time.sleep(1800)  # كل 30 دقيقة

if __name__ == "__main__":
    main()