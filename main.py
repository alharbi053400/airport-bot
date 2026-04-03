def main():
    print("🚀 بدأ التشغيل")

    try:
        data = get_flights()
        print("جاب البيانات")

        flights = filter_flights(data)
        print("فلترها")

        file = create_excel(flights)
        print("سوى ملف")

        send_file(file)
        print("تم الإرسال ✅")

    except Exception as e:
        print("🔥 خطأ:", e)

main()