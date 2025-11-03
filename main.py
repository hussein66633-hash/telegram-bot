from flask import Flask
import threading
import requests
import time
import main3  # هذا ملف البوت مالك

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ تم تشغيل الروبوت ونظام مكافحة الخمول نشط!"

def run_server():
    app.run(host="0.0.0.0", port=3000)

def keep_alive():
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()

def auto_ping():
    while True:
        try:
            # 🔹 هنا خليه بالرابط الصحيح من موقع Replit مالتك
            requests.get("https://38b8afbf-0907-4152-a773-69dd44ae8158-00-2j3r8ebu6wghh.janeway.replit.dev")
            print("Ping sent ✅")
        except Exception as e:
            print("Ping error:", e)
        time.sleep(200)  # ← كل 200 ثانية

# تشغيل السيرفر والنظام
keep_alive()
threading.Thread(target=auto_ping).start()

# تشغيل البوت
main3.main()