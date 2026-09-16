# ربات تبادل روبیکا - نسخه کامل

این نسخه دقیقا مثل تلگرام کار میکنه ولی برای روبیکا.

## تفاوت‌های مهم روبیکا با تلگرام
- توکن از BotFather@ داخل خود روبیکا میگیری (از 29 تیر 1404 رسمی شده)
- بیس URL: https://botapi.rubika.ir/v3/{token}/{method}
- متدها: getMe, getUpdates, sendMessage, deleteMessage, getChats
- برای گرفتن آیدی کانال: متد getChats یا فوروارد یک پیام از کانال به ربات @BotFather
- ربات حتما باید ادمین کانال‌های شما باشد تا بتواند پست و حذف کند.

## نصب قدم به قدم
1. روبیکا -> برو به @BotFather -> /newbot -> اسم -> توکن بگیر
2. ربات را ادمین کانال‌های خود کن
3. .env را پر کن:
```
RUBIKA_TOKEN=توکن
OWNER_ID=آیدی عددی خودت در روبیکا (از getMe)
EXCHANGE_CHANNELS=b0c1xxxxxx,b0c2yyyyyy
```
چطور آیدی کانال روبیکا را پیدا کنم؟
- ساده‌ترین: ربات را به کانال اضافه کن، یک پیام بفرست، سپس getUpdates را صدا بزن chat_id را میبینی که با b0 شروع میشه
- یا از متد getChats استفاده کن

4. اجرا:
```
pip install -r requirements.txt
python bot.py
```

## دیپلوی روی سرور
- Railway / Render / VPS ایرانی (مثل پارس پک) عالیه چون روبیکا تحریم نیست و سرعتش با سرور ایران بهتره
- Webhook هم میشه: باید متد updateBotEndpoints را صدا بزنی و url سرورت را بدهی:
```
POST https://botapi.rubika.ir/v3/{token}/updateBotEndpoints
{
  "url": "https://yourdomain.com/webhook",
  "type": "ReceiveUpdate"
}
```
اما برای سادگی همین polling کفایت میکنه.

## نکته تایید پست
در روبیکا هم مثل تلگرام، ربات نمیتونه بره کانال دیگران را بخواند. پس همون ترفند فوروارد را استفاده میکنیم:
طرف بنر تو را در کانالش میذارد و همان پیام را Forward میکند به ربات. چون forward_from_chat_id دارد، تایید میشود.
