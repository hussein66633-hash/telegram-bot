from flask import Flask
import threading, requests, time, os

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ البوت شغال والنظام ضد الخمول مفعّل!"

def run_server():
    app.run(host="0.0.0.0", port=3000)

def keep_alive():
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()

def auto_ping():
    while True:
        try:
            requests.get("https://3b77ce24-c93a-4bb2-aeab-de4ce3a56901-00-2q6tkkcrjerrd.pike.replit.dev")
            print("Ping ✅")
        except Exception as e:
            print("Ping error:", e)
        time.sleep(150)

def monitor_repl():
    while True:
        # إذا دخل خمول أو السيرفر مات، يعيد تشغيله
        if not os.path.exists("/tmp/active"):
            print("Repl entered sleep mode — restarting server!")
            keep_alive()
        time.sleep(300)

keep_alive()
threading.Thread(target=auto_ping, daemon=True).start()
threading.Thread(target=monitor_repl, daemon=True).start()

# استدعِ البوت هنا
import main3
main3.main()