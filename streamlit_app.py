import requests
import time
from datetime import datetime

TOKEN = "8714913319:AAF7lWfrtPbWItM-7sj0JhYMVN9zdPofGd8"
CHAT_ID = "1234119654"
API_KEY = "02b0bd12fc73d4c2b7741a7e2f3f6685"

API_URL = "http://api.aviationstack.com/v1/flights"

SAUDI_AIRPORTS = [
    "RUH","DMM","MED","GIZ","TUU","AHB","EAM","HAS",
    "ELQ","URY","AJF","ULH","RAE","SHW","NUM","DWD"
]

last_report = ""
last_alerts = set()
cached_flights = []
last_fetch_time = 0


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message})


def get_flights():
    params = {
        "access_key": API_KEY,
        "dep_iata": "JED"
    }
    response = requests.get(API_URL, params=params)
    return response.json()


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


def generate_report(flights):
    times = {}

    for f in flights:
        time_str = f["departure"]["scheduled"]
        if not time_str:
            continue

        t = datetime.fromisoformat(time_str.replace("Z",""))
        minute = "00" if t.minute < 30 else "30"
        key = t.strftime(f"%H:{minute}")

        times[key] = times.get(key, 0) + 1

    report = "📊 تقرير الرحلات - صالة 1 (دولي)\n"
    report += "👤 ريان الحميدي الحربي | 📞 0534006391\n\n"

    total = len(flights)
    report += f"✈️ عدد الرحلات: {total}\n\n"

    alerts = []

    # تحليل
    max_time = ""
    max_count = 0
    min_time = ""
    min_count = 999

    for t in sorted(times):
        count = times[t]

        if count > max_count:
            max_count = count
            max_time = t

        if count < min_count:
            min_count = count
            min_time = t

        if count >= 5:
            status = "🚨 زحمة خانقة"
            alerts.append(f"🚨 زحمة خانقة {t} ({count})")
        elif count >= 3:
            status = "⚠️ زحمة"
        else:
            status = "✅ طبيعي"

        report += f"{t} → {count} رحلات ({status})\n"

    # 🔥 إضافة التحليل
    report += "\n📈 التحليل:\n"
    report += f"🔥 أعلى زحمة: {max_time} ({max_count} رحلات)\n"
    report += f"😌 أهدأ وقت: {min_time} ({min_count} رحلات)\n"

    return report, alerts


def main_loop():
    global last_report, last_alerts, cached_flights, last_fetch_time

    send_telegram("📡 تم تشغيل النظام\n👤 ريان الحميدي الحربي\n📞 0534006391")

    while True:
        try:
            now = time.time()

            # تحديث كل ساعتين
            if now - last_fetch_time >= 7200 or not cached_flights:
                data = get_flights()
                cached_flights = filter_flights(data)
                last_fetch_time = now
                send_telegram("🔄 تم تحديث بيانات الرحلات")

            # تقرير كل 30 دقيقة
            report, alerts = generate_report(cached_flights)

            if report != last_report:
                send_telegram(report)
                last_report = report

            current_alerts = set(alerts)

            for alert in current_alerts - last_alerts:
                send_telegram(alert)

            last_alerts = current_alerts

        except Exception as e:
            send_telegram(f"❌ خطأ\nريان الحميدي الحربي\n0534006391\n{str(e)}")

        time.sleep(1800)


def run_forever():
    while True:
        try:
            main_loop()
        except Exception as e:
            send_telegram(f"🔥 إعادة تشغيل السيرفر\n{str(e)}")
            time.sleep(10)


if __name__ == "__main__":
    run_forever()