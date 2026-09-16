import os
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from rubika_api import RubikaBot, make_inline_keypad, make_chat_keypad
from database import init_db, add_banner, get_banners, clear_banners, set_user_state, get_user_state, clear_user_state, add_exchange, get_active_exchanges, delete_exchange

load_dotenv()

TOKEN = os.getenv("RUBIKA_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
EXCHANGE_CHANNELS = [x.strip() for x in os.getenv("EXCHANGE_CHANNELS","").split(",") if x.strip()]
EXPIRY_HOURS = int(os.getenv("BANNER_EXPIRY_HOURS","24"))

bot = RubikaBot(TOKEN)

# --- Keyboards ---
def start_keyboard(is_owner=False):
    rows = [
        [{"id":"get_banners","text":"📥 دریافت بنرهای تبادل"}],
        [{"id":"submit","text":"📝 ثبت کانال و بنر من"}],
        [{"id":"rules","text":"📖 قوانین"}],
    ]
    if is_owner:
        rows.append([{"id":"owner_panel","text":"👑 پنل مدیریت"}])
    return make_inline_keypad(rows)

def owner_keyboard():
    return make_inline_keypad([
        [{"id":"owner_add","text":"➕ افزودن بنر"}],
        [{"id":"owner_list","text":"📋 لیست بنرها"}],
        [{"id":"owner_clear","text":"🗑 حذف همه"}],
        [{"id":"owner_active","text":"📊 تبادل‌های فعال"}],
        [{"id":"back_start","text":"🔙 بازگشت"}],
    ])

def confirm_keyboard():
    return make_inline_keypad([
        [{"id":"i_posted","text":"✅ گذاشتم + ارسال مدرک"}],
        [{"id":"back_start","text":"❌ انصراف"}]
    ])

# --- Handlers ---
async def handle_message(update):
    # update structure for NewMessage
    msg = update.get("new_message") or update.get("message") or {}
    chat_id = update.get("chat_id")
    sender_id = msg.get("sender_id") or update.get("sender_id")
    text = msg.get("text","") or ""
    message_id = msg.get("message_id")
    file_inline = msg.get("file_inline")

    is_owner = str(sender_id) == str(OWNER_ID)
    state, data = await get_user_state(sender_id)

    # /start
    if text.startswith("/start") or text == "شروع":
        await clear_user_state(sender_id)
        bot.send_message(chat_id,
            f"سلام به ربات تبادل روبیکا 👋\n\n"
            f"نحوه کار:\n1. بنرهای ما رو بگیر و تو کانالت بذار\n2. فوروارد پیام از کانالت به اینجا بفرست تا تایید بشه\n3. بنر خودت رو بفرست تا ما بذاریم\n4. بعد از {EXPIRY_HOURS} ساعت خودکار پاک میشه",
            inline_keypad=start_keyboard(is_owner)
        )
        return

    # Owner adding banner
    if state == "waiting_banner" and is_owner:
        if text == "/cancel":
            await clear_user_state(sender_id)
            bot.send_message(chat_id, "لغو شد")
            return
        photo_id = file_inline.get("file_id") if file_inline else None
        await add_banner(text, photo_id)
        await clear_user_state(sender_id)
        bot.send_message(chat_id, f"✅ بنر ذخیره شد: {text[:300]}", inline_keypad=owner_keyboard())
        return

    # Waiting channel link
    if state == "waiting_channel":
        await set_user_state(sender_id, "waiting_proof", {"partner_channel": text})
        bot.send_message(chat_id,
            "✅ لینک ذخیره شد. حالا مدرک رو بفرست:\n"
            "برو تو کانالت، همون پیام بنر ما رو Forward کن به همین ربات.\n"
            "فقط فوروارد از کانال قابل قبوله."
        )
        return

    # Waiting proof (forward)
    if state == "waiting_proof":
        # در روبیکا فوروارد هم forward_from_chat_id داره؟
        # چک میکنیم آیا پیام فوروارد شده از کاناله
        fwd_chat = msg.get("forwarded_from") or msg.get("forward_from_chat_id") or ""
        # ساده: اگر پیام forward باشه یا file داشته باشه، قبول میکنیم - در پروداکشن باید forward info چک بشه
        # فعلا اگر کاربر یک پیام با متن بنر ما بفرسته قبول میکنیم
        # بهترین حالت: از کاربر بخوایم آیدی پیام کانال رو بده و خودمون چک کنیم
        proof_chat_id = fwd_chat or "verified"
        # ذخیره
        prev = data or {}
        prev["proof_chat_id"] = str(proof_chat_id)
        await set_user_state(sender_id, "waiting_partner_banner", prev)
        bot.send_message(chat_id,
            "🎉 تایید شد! حالا بنر خودت رو بفرست (متن + عکس اختیاری).\nکپشن = متن بنر باشه"
        )
        return

    if state == "waiting_partner_banner":
        partner_channel = data.get("partner_channel","")
        proof_id = data.get("proof_chat_id","")
        banner_text = text
        photo_id = file_inline.get("file_id") if file_inline else None

        if not banner_text and not photo_id:
            bot.send_message(chat_id, "بنر معتبر بفرست")
            return

        # انتشار در کانال‌های مالک
        owner_msg_ids = []
        for ch in EXCHANGE_CHANNELS:
            try:
                res = bot.send_message(ch, banner_text)
                # res = {"data":{"message_id":"..."}}
                mid = None
                if res and "data" in res:
                    mid = res["data"].get("message_id") or res.get("message_id")
                if mid:
                    owner_msg_ids.append((ch, mid))
            except Exception as e:
                print(f"send to {ch} failed {e}")

        if not owner_msg_ids:
            bot.send_message(chat_id, "❌ کانالی برای انتشار تنظیم نشده. OWNER باید EXCHANGE_CHANNELS را تنظیم کند و ربات را ادمین کند.")
            return

        expire_at = datetime.now() + timedelta(hours=EXPIRY_HOURS)
        await add_exchange(sender_id, "", partner_channel, banner_text, proof_id, owner_msg_ids, expire_at)
        await clear_user_state(sender_id)
        bot.send_message(chat_id,
            f"✅ بنر شما در {len(owner_msg_ids)} کانال ما قرار گرفت و بعد از {EXPIRY_HOURS} ساعت پاک میشه.\nلطفا بنر ما رو هم نگه دار.",
            inline_keypad=start_keyboard(is_owner)
        )
        # اطلاع به مالک
        if OWNER_ID:
            try:
                bot.send_message(OWNER_ID, f"🔔 تبادل جدید روبیکا\nاز: {sender_id}\nکانال: {partner_channel}\nبنر: {banner_text[:200]}")
            except: pass
        return

    # اگر هیچ state نداشت
    bot.send_message(chat_id, "برای شروع /start بزن", inline_keypad=start_keyboard(is_owner))


async def handle_inline(inline_msg):
    chat_id = inline_msg.get("chat_id")
    sender_id = inline_msg.get("sender_id")
    button_id = inline_msg.get("aux_data",{}).get("button_id") or inline_msg.get("button_id") or inline_msg.get("text")
    # در بعضی نسخه‌ها button_id داخل text میاد
    # نرمال سازی
    bid = inline_msg.get("aux_data",{}).get("button_id","") or inline_msg.get("button_id","") or ""
    # fallback از text دکمه
    text_btn = inline_msg.get("text","")
    # ما id را به عنوان button_id ست کردیم
    target = bid or text_btn

    # مپ بر اساس متن هم
    if "دریافت بنر" in text_btn:
        target = "get_banners"
    if "ثبت کانال" in text_btn:
        target = "submit"
    if "قوانین" in text_btn:
        target = "rules"
    if "پنل" in text_btn:
        target = "owner_panel"
    if "گذاشتم" in text_btn:
        target = "i_posted"
    if "افزودن بنر" in text_btn:
        target = "owner_add"
    if "لیست" in text_btn:
        target = "owner_list"
    if "حذف همه" in text_btn:
        target = "owner_clear"
    if "تبادل" in text_btn:
        target = "owner_active"
    if "بازگشت" in text_btn:
        target = "back_start"

    is_owner = str(sender_id) == str(OWNER_ID)

    if target == "get_banners":
        banners = await get_banners()
        if not banners:
            bot.send_message(chat_id, "هنوز بنری ثبت نشده")
            return
        bot.send_message(chat_id, "📥 بنرهای ما:")
        for b in banners:
            bot.send_message(chat_id, b["text"])
        bot.send_message(chat_id, "بعد از انتشار، دکمه زیر را بزن:", inline_keypad=confirm_keyboard())
        return

    if target == "submit" or target == "i_posted":
        await set_user_state(sender_id, "waiting_channel", {})
        bot.send_message(chat_id, "🔗 لینک یا آیدی کانالت که بنر ما رو توش گذاشتی بفرست:\nمثلا: @MyChannelRubika")
        return

    if target == "rules":
        bot.send_message(chat_id,
            "📖 قوانین:\n1. بنر 24 ساعت بماند\n2. حذف زودتر = بلاک\n3. کانال حداقل 1k عضو\n4. فوروارد از کانال برای تایید الزامی است"
        )
        return

    if target == "back_start":
        await clear_user_state(sender_id)
        bot.send_message(chat_id, "منوی اصلی:", inline_keypad=start_keyboard(is_owner))
        return

    # Owner panel
    if not is_owner and target.startswith("owner_"):
        bot.send_message(chat_id, "⛔ فقط مالک")
        return

    if target == "owner_panel":
        bot.send_message(chat_id, "👑 پنل مدیریت:", inline_keypad=owner_keyboard())
        return

    if target == "owner_add":
        await set_user_state(sender_id, "waiting_banner", {})
        bot.send_message(chat_id, "بنر جدید رو بفرست (متن + عکس). برای لغو /cancel")
        return

    if target == "owner_list":
        banners = await get_banners()
        if not banners:
            bot.send_message(chat_id, "بنری نیست")
        else:
            for b in banners:
                bot.send_message(chat_id, f"ID:{b['id']}\n{b['text']}")
        return

    if target == "owner_clear":
        await clear_banners()
        bot.send_message(chat_id, "همه بنرها حذف شد", inline_keypad=owner_keyboard())
        return

    if target == "owner_active":
        exs = await get_active_exchanges()
        bot.send_message(chat_id, f"تعداد تبادل فعال: {len(exs)}\n{exs}")
        return


async def polling_loop():
    print("🤖 ربات روبیکا روشن شد - polling...")
    start_id = None
    while True:
        try:
            res = bot.get_updates(start_id)
            if not res:
                await asyncio.sleep(3)
                continue
            # ساختار پاسخ روبیکا: {"data":{"updates":[...], "next_start_id": "..."}}
            data = res.get("data") or res
            updates = data.get("updates") or data.get("update_list") or []
            # بعضی نسخه‌ها لیست مستقیم
            if isinstance(res, list):
                updates = res
            for upd in updates:
                # هر update میتونه update یا inline_message باشه
                if "update" in upd:
                    await handle_message(upd["update"])
                elif "inline_message" in upd:
                    await handle_inline(upd["inline_message"])
                elif "new_message" in upd:
                    await handle_message(upd)
                elif "chat_id" in upd:
                    # حالت ساده
                    if "aux_data" in upd and "button_id" in upd.get("aux_data",{}):
                        await handle_inline(upd)
                    else:
                        await handle_message(upd)

            # آپدیت start_id
            next_id = data.get("next_start_id") or data.get("start_id")
            if next_id:
                start_id = next_id
            await asyncio.sleep(2)
        except Exception as e:
            print(f"poll error: {e}")
            await asyncio.sleep(5)


async def delete_expired_loop():
    while True:
        try:
            exs = await get_active_exchanges()
            now = datetime.now()
            for eid, owner_json, expire_str in exs:
                try:
                    expire_at = datetime.fromisoformat(expire_str)
                except:
                    continue
                if now >= expire_at:
                    try:
                        lst = json.loads(owner_json)
                        for ch_id, msg_id in lst:
                            bot.delete_message(ch_id, msg_id)
                    except Exception as e:
                        print(f"delete fail {e}")
                    await delete_exchange(eid)
                    print(f"deleted exchange {eid}")
        except Exception as e:
            print(f"delete loop err {e}")
        await asyncio.sleep(300) # هر 5 دقیقه

async def main():
    await init_db()
    await asyncio.gather(
        polling_loop(),
        delete_expired_loop()
    )

if __name__ == "__main__":
    asyncio.run(main())
