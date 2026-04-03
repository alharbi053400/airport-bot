import requests
import pandas as pd
import time
from datetime import datetime

# ==============================
# بياناتك
# ==============================

TOKEN = "8714913319:AAF71WfrtPbWItM-7sj0JhYMVN9zdPoFGd8"
CHAT_ID = "1234119654"
API_KEY = "02b0bd12fc73d4c2b7741a7e2f3f6685"


# ==============================
# جلب الرحلات
# ==============================
def get_flights():
    params = {
        "access_key": API_KEY,
        "dep_iata": "JED"
    }
    res = requests.get(API_URL, params=params)
    return res.json()


# ==============================
# فلترة الرحلات
# ==============================
def filter_flights(data):
    flights = []

    if "data" not in data:
        return flights

    for f in data["data"]:
        try:
            flights.append({
                "الرحلة": f["flight"]["iata"],
                "الوجهة": f["arrival"]["airport"],
                "الوقت": f["departure"]["scheduled"],
                "الحالة": f["flight_status"]
            })
        except:
            continue

    return flights


# ==============================
# إنشاء Excel
# ==============================
def create_excel(data):
    df = pd.DataFrame(data)

    if df.empty:
        df = pd.DataFrame([{
            "الرحلة": "لا يوجد",
            "الوجهة": "-",
            "الوقت": "-",
            "الحالة": "-"
        }])

    filename = f"report_{datetime.now().strftime('%H_%M')}.xlsx"
    df.to_excel(filename, index=False)
    return filename


# ==============================
# إرسال تيليجرام
# ==============================
def send_file(file_path):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    with open(file_path, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"document": f})


# ==============================
# إرسال خطأ (لو صار)
# ==============================
def send_error(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )


# ==============================
# التشغيل الرئيسي
# ==============================
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
            send_error(f"❌ خطأ:\n{str(e)}")

        # كل 30 دقيقة
        time.sleep(1800)


# تشغيل
main()
def create_excel(data):
    import pandas as pd
    from datetime import datetime

    df = pd.DataFrame([{"حالة": "شغال"}])
    filename = f"test_{datetime.now().strftime('%H_%M')}.xlsx"
    df.to_excel(filename, index=False)
    return filename


def main():
    file = create_excel([])
    send_file(file)
    print("تم الإرسال")


main()