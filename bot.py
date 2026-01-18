import asyncio
import random
import string
import os
from telethon import TelegramClient
from telethon.tl.functions.account import CheckUsernameRequest
from telethon.errors import UsernameInvalidError, UsernameOccupiedError, FloodWaitError

# ================= إعدادات الحسابات =================
# تأكد أن اسم الـ session هو نفس اسم ملف الجلسة الموجود عندك في المجلد
ACCOUNTS = [
    {'api_id': 26928420, 'api_hash': '0facea2bb49930df0718fb74cda1790d', 'session': 'account_1'},
    {'api_id': 26928420, 'api_hash': '0facea2bb49930df0718fb74cda1790d', 'session': 'account_2'}, # أضف هنا أسماء ملفاتك
]

FILE_NAME = 'يوزرات تيليجرام.txt'

# ================= إعدادات التوليد =================
letters = string.ascii_lowercase
digits = string.digits
all_chars = letters + digits

def generate_username():
    """
    توليد الأنماط المطلوبة فقط:
    z_c_h , z_8_o , c_8_2 , e_77 , w_7_3
    """
    mode = random.choice([1, 2, 3])
    
    # ضمان البدء بحرف دائماً لتجنب الأخطاء
    start = random.choice(letters)
    
    if mode == 1:
        # نمط: حرف_حرف_حرف (مثل z_c_h) أو حرف_رقم_حرف (مثل z_8_o)
        return f"{start}_{random.choice(all_chars)}_{random.choice(all_chars)}"
        
    elif mode == 2:
        # نمط: حرف_رقم_رقم (مثل c_8_2 أو w_7_3)
        return f"{start}_{random.choice(digits)}_{random.choice(digits)}"

    elif mode == 3:
        # نمط: حرف_رقمين (مثل e_77)
        return f"{start}_{random.choice(digits)}{random.choice(digits)}"

def save_user_instantly(username):
    try:
        with open(FILE_NAME, 'a', encoding='utf-8') as f:
            f.write(f"@{username}\n")
            f.flush()
            os.fsync(f.fileno())
        print(f"\n[+] تم الحفظ: @{username}")
    except Exception as e:
        print(f"[!] خطأ في الحفظ: {e}")

# ================= منطق العمل والتبديل =================
async def run_checker():
    current_account_index = 0
    
    while True:
        acc = ACCOUNTS[current_account_index]
        print(f"\n[!] محاولة الاتصال بملف الجلسة: {acc['session']}.session")
        
        try:
            # استخدام ملف الجلسة الجاهز مباشرة
            client = TelegramClient(acc['session'], acc['api_id'], acc['api_hash'])
            await client.connect()
            
            if not await client.is_user_authorized():
                print(f"[X] الحساب {acc['session']} غير مسجل دخول أو الجلسة منتهية.")
                await client.disconnect()
            else:
                print(f"[V] الحساب {acc['session']} جاهز ويعمل..")
                
                while True:
                    username = generate_username()
                    try:
                        result = await client(CheckUsernameRequest(username))
                        if result:
                            print(f"\n[$$$] متاح !! -> @{username}")
                            save_user_instantly(username)
                        else:
                            print(f"[-] محجوز: @{username}", end='\r')
                        
                        await asyncio.sleep(0.5) # سرعة الفحص

                    except FloodWaitError as e:
                        print(f"\n[!] الحساب الحالي انحظر {e.seconds} ثانية. جاري التبديل...")
                        break 
                        
                    except Exception as e:
                        if "RPCError" in str(e): break
                        continue
                
                await client.disconnect()

        except Exception as e:
            print(f"[!] خطأ في الحساب {acc['session']}: {e}")
        
        # التبديل للحساب التالي
        current_account_index = (current_account_index + 1) % len(ACCOUNTS)
        print("[>] الانتقال للحساب التالي بعد 3 ثوانٍ...")
        await asyncio.sleep(3)

if __name__ == '__main__':
    try:
        asyncio.run(run_checker())
    except KeyboardInterrupt:
        print("\n[!] تم الإيقاف.")
