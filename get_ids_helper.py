
import os, requests, time
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("RUBIKA_TOKEN")
if not TOKEN:
    print("اول RUBIKA_TOKEN رو تو .env بذار")
    exit()

url_base = f"https://botapi.rubika.ir/v3/{TOKEN}"

print("1. تست اتصال getMe...")
r = requests.post(f"{url_base}/getMe", json={})
print(r.text)
print("\n")

print("2. گرفتن چت‌ها getChats...")
r = requests.post(f"{url_base}/getChats", json={})
print(r.text[:2000])
print("\n")

print("3. منتظر پیام جدید (getUpdates) - برو تو روبیکا به رباتت یک پیام بده یا ربات رو تو کانالت ادمین کن و یک پیام بفرست...")
start_id = None
while True:
    payload = {}
    if start_id:
        payload["start_id"] = start_id
    try:
        r = requests.post(f"{url_base}/getUpdates", json=payload, timeout=20)
        data = r.json()
        # print(data)
        d = data.get("data") or data
        updates = d.get("updates") or []
        if updates:
            for u in updates:
                print("\n=== پیام جدید پیدا شد ===")
                print(u)
                # استخراج chat_id و sender_id
                if "update" in u:
                    upd = u["update"]
                    chat_id = upd.get("chat_id")
                    sender_id = upd.get("new_message",{}).get("sender_id")
                    print(f"\n>>> CHAT_ID (آیدی کانال یا چت): {chat_id}")
                    print(f">>> SENDER_ID (آیدی خودت = OWNER_ID): {sender_id}")
                    if chat_id and chat_id.startswith("b0"):
                        print(f"این آیدی کانال است! بذار تو EXCHANGE_CHANNELS")
                if "inline_message" in u:
                    print(u["inline_message"])
            start_id = d.get("next_start_id")
        else:
            print(".", end="", flush=True)
    except Exception as e:
        print(f"خطا: {e}")
    time.sleep(3)
