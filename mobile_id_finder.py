
import os, requests, time
from dotenv import load_dotenv
load_dotenv()
TOKEN=os.getenv("RUBIKA_TOKEN")
BASE=f"https://botapi.rubika.ir/v3/{TOKEN}"
print("ربات روشن شد - فقط برای پیدا کردن آیدی")
print("1. برو تو روبیکا به رباتت پیام بده: سلام")
print("2. برو تو کانالت که ربات ادمینه یک پیام بده: تست")
print("منتظر...")
start=None
while True:
    try:
        p={}
        if start: p["start_id"]=start
        r=requests.post(f"{BASE}/getUpdates", json=p, timeout=20).json()
        d=r.get("data") or r
        updates=d.get("updates") or []
        for u in updates:
            print("\n=== پیام جدید ===")
            print(u)
            if "update" in u:
                chat=u["update"].get("chat_id")
                sender=u["update"].get("new_message",{}).get("sender_id")
                print(f"\n✅ CHAT_ID (کپی کن برای EXCHANGE_CHANNELS): {chat}")
                print(f"✅ SENDER_ID (کپی کن برای OWNER_ID): {sender}\n")
        if d.get("next_start_id"): start=d["next_start_id"]
    except Exception as e:
        print(e)
    time.sleep(3)
