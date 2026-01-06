import asyncio, os, sys
from telethon import TelegramClient, errors
from pathlib import Path

API_ID = 26928420
API_HASH = '0facea2bb49930df0718fb74cda1790d'

def downloads_path():
    home = Path.home()
    cand = home / "Downloads"
    if cand.exists():
        return cand
    android_dl = Path("/sdcard/Download")
    if android_dl.exists():
        return android_dl
    return Path.cwd()

OUT_DIR = downloads_path()

async def create_session_for(phone, out_dir):
    filename = out_dir / f"{phone.replace('+','')}.session"
    client = TelegramClient(str(filename), API_ID, API_HASH)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            try:
                await client.send_code_request(phone)
                code = input(f"أدخل كود التحقق الذي وصلك على {phone}: ").strip()
                try:
                    await client.sign_in(phone, code)
                except errors.SessionPasswordNeededError:
                    pw = input("الحساب محمي بكلمة مرور، أدخلها: ").strip()
                    await client.sign_in(password=pw)
            except:
                return False
        await client.disconnect()
        return True
    except:
        try:
            await client.disconnect()
        except:
            pass
        return False

async def check_session(file_path):
    client = TelegramClient(str(file_path), API_ID, API_HASH)
    try:
        await client.connect()
    except:
        return False

    try:
        ok = await client.is_user_authorized()
        await client.disconnect()
        return ok
    except:
        return False

async def delete_invalid_sessions():
    print("\nفحص الملفات وحذف الغير مفعّل...")
    files = list(OUT_DIR.glob("*.session")) + list(OUT_DIR.glob("*.session-journal"))

    removed = 0
    for f in files:
        ok = await check_session(f)
        if not ok:
            try:
                f.unlink()
                print("تم حذف حساب غير مفعّل:", f.name)
                removed += 1
            except:
                pass
        else:
            print("حساب شغّال ✔:", f.name)

    print("\nتم الحذف:", removed)

async def count_sessions():
    print("\nجاري فحص الحسابات...")
    files = list(OUT_DIR.glob("*.session")) + list(OUT_DIR.glob("*.session-journal"))

    print("عدد ملفات الجلسات التي وجدها البرنامج:", len(files))

    total = 0
    active = 0
    inactive = 0

    for f in files:
        total += 1
        ok = await check_session(f)
        if ok:
            active += 1
        else:
            inactive += 1

    print("\n=== تقرير الحسابات ===")
    print("إجمالي الجلسات:", total)
    print("الحسابات الفعّالة:", active)
    print("الحسابات الغير فعّالة:", inactive)
    print()

def parse_count_input(s):
    s = s.strip()
    if ':' in s:
        try:
            a,b = s.split(':',1)
            a,b = int(a),int(b)
            if b < a: a, b = b, a
            return list(range(a,b+1))
        except:
            return None
    else:
        try:
            n=int(s)
            if n<=0: return None
            return list(range(1,n+1))
        except:
            return None

async def main():
    while True:
        print("\nالقائمة الرئيسية:")
        print("1) تسجيل دخول")
        print("2) حذف الحسابات الغير مفعّلة")
        print("3) عرض عدد الحسابات")
        print("0) خروج")
        choice = input("اختر رقم: ").strip()

        if choice == "0":
            return
        elif choice == "2":
            await delete_invalid_sessions()
        elif choice == "3":
            await count_sessions()
        elif choice == "1":
            cnt_input = input("كم عدد الحسابات؟ مثال 5 أو 1:5: ").strip()
            indices = parse_count_input(cnt_input)
            if not indices:
                continue
            for i in indices:
                print(f"\n=== حساب رقم {i} ===")
                phone = input("أدخل رقم الهاتف: ").strip()
                if not phone:
                    continue
                ok = await create_session_for(phone, OUT_DIR)
                if not ok:
                    r = input("فشل إنشاء الجلسة. إعادة المحاولة؟ (y/n): ").strip().lower()
                    if r == "y":
                        await create_session_for(phone, OUT_DIR)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)