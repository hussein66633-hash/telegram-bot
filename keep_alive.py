from flask import Flask
from threading import Thread
import requests, time

app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host='0.0.0.0', port=3000)

def ping():
    url = "https://38b8afbf-0907-4152-a773-69dd44ae8158-00-2j3r8ebu6wghh.janeway.replit.dev/"
    while True:
        try:
            requests.get(url)
            print("Ping sent ✅")
        except Exception as e:
            print("Ping error ❌", e)
        time.sleep(200)  # كل 200 ثانية

def keep_alive():
    t1 = Thread(target=run)
    t2 = Thread(target=ping)
    t1.start()
    t2.start()