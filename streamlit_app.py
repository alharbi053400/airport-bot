import requests
import time
from datetime import datetime

# بياناتك
TOKEN = "8714913319:AAF7lWfrtPbWItM-7sj0JhYMVN9zdPofGd8"
CHAT_ID = "1234119654"
API_KEY = "YOUR_API_KEY"

API_URL = "http://api.aviationstack.com/v1/flights"

# المطارات السعودية (استبعاد)
SAUDI_AIRPORTS = [
    "RUH","DMM","MED","GIZ","TUU","AHB","EAM","HAS",
    "ELQ","URY","AJF","ULH","RAE","SHW","NUM","DWD"
]

last_report = ""
last_alerts = set()


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

        # صالة 1 فقط
        if dep.get("terminal") != "1":
            continue

        # استبعاد الرحلات الداخلية
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

        # تقسيم نصف ساعة
        minute = "00" if t.minute < 30 else "30"
        key = t.strftime(f"%H:{minute}")

        times[key] = times.get(key, 0) + 1

    report = "📊 تقرير الرحلات - صالة 1 (دولي)\n"
    report += "👤 ريان الحميدي الحربي | 📞 0534006391\n\n"

    total = len(flights)
    report += f"✈️ عدد الرحلات: {total}\n\n"

    alerts = []

    for t in sorted(times):
        count = times[t]

        if count >= 5:
            status = "🚨 زحمة خانقة"
            alerts.append(f"🚨 زحمة خانقة {t} ({count})")
        elif count >= 3:
            status = "⚠️ زحمة"
        else:
            status = "✅ طبيعي"

        report += f"{t} → {count} رحلات ({status})\n"

    return report, alerts


def main_loop():
    global last_report, last_alerts

    send_telegram("📡 تم تشغيل النظام\n👤 ريان الحميدي الحربي\n📞 0534006391")

    while True:
        try:
            data = get_flights()
            flights = filter_flights(data)

            report, alerts = generate_report(flights)

            # إرسال التقرير فقط إذا تغير
            if report != last_report:
                send_telegram(report)
                last_report = report

            # إرسال تنبيهات بدون تكرار
            for alert in alerts:
                if alert not in last_alerts:
                    send_telegram(alert)
                    last_alerts.add(alert)

        except Exception as e:
            send_telegram(f"❌ خطأ\nريان الحميدي الحربي\n0534006391\n{str(e)}")

        time.sleep(7200)  # كل ساعتين


def run_forever():
    while True:
        try:
            main_loop()
        except Exception as e:
            send_telegram(f"🔥 إعادة تشغيل السيرفر\n{str(e)}")
            time.sleep(10)


if __name__ == "__main__":
    run_forever()