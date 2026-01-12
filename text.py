import telebot
import requests
import random
import string
import time
import threading
import os

# --- الإعدادات (املا البيانات هنا) ---
API_TOKEN = 'ضع_هنا_توكن_بوتك'
MY_ID = 12345678  # ضع هنا ID حسابك (أرقام فقط)
FILE_NAME = "يوزرات تيليجرام متاحة.txt" # تم تعديل الاسم حسب طلبك

bot = telebot.TeleBot(API_TOKEN)
is_hunting = False

def generate_premium_user():
    """توليد يوزرات مميزة بنماذج قوية"""
    letters = string.ascii_lowercase
    digits = string.digits
    style = random.choice(["4+1", "5_special"])
    
    if style == "4+1":
        char1, char2 = random.sample(letters, 2)
        pattern = random.choice([char1*3 + char2, char1 + char2*3, char1*2 + char2*2])
        num = random.choice(digits)
        user = random.choice([pattern + num, num + pattern])
    else:
        c1, c2 = random.sample(letters, 2)
        user = random.choice([c1*3 + c2*2, c1*2 + c2*3, c1+c2+c1+c2+c1, c1*4 + c2])
    return user

def hunt_task(chat_id):
    global is_hunting
    checked_count = 0
    
    while is_hunting:
        user = generate_premium_user()
        url = f"https://t.me/{user}"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            checked_count += 1
            
            if 'tgme_page_extra' not in response.text:
                # 1. إرسال إشعار للبوت
                bot.send_message(chat_id, f"🔥 تم صيد يوزر متاح!\n\nUser: @{user}")
                
                # 2. الحفظ في الملف (الاسم الجديد)
                with open(FILE_NAME, "a", encoding="utf-8") as f:
                    f.write(f"@{user}\n")
                    f.flush()
                    os.fsync(f.fileno())
            
            # تحديث كل 200 محاولة
            if checked_count % 200 == 0:
                bot.send_message(chat_id, f"📡 مستمر بالبحث... تم فحص {checked_count}")
                
            time.sleep(0.7) 
        except:
            continue

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("🚀 ابدأ الصيد")
    btn2 = telebot.types.KeyboardButton("🛑 إيقاف")
    btn3 = telebot.types.KeyboardButton("📁 تحميل الملف")
    markup.add(btn1, btn2)
    markup.add(btn3)
    bot.reply_to(message, "تم تشغيل بوت الصيد. اختر من الأزرار:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    global is_hunting
    
    if message.text == "🚀 ابدأ الصيد":
        if not is_hunting:
            is_hunting = True
            threading.Thread(target=hunt_task, args=(message.chat.id,)).start()
            bot.send_message(message.chat.id, "✅ بدأ الصيد! سيتم الحفظ في 'يوزرات تيليجرام متاحة.txt'")
        else:
            bot.send_message(message.chat.id, "البوت شغال بالفعل.")
            
    elif message.text == "🛑 إيقاف":
        is_hunting = False
        bot.send_message(message.chat.id, "🛑 تم الإيقاف.")
        
    elif message.text == "📁 تحميل الملف":
        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="إليك قائمة اليوزرات المتاحة")
        else:
            bot.send_message(message.chat.id, "لا يوجد يوزرات متاحة حالياً في الملف.")

print("البوت يعمل الآن...")
bot.infinity_polling()
