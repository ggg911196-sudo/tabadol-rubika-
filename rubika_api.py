import requests
import time
import json
from typing import Optional

class RubikaBot:
    def __init__(self, token: str):
        self.token = token
        self.base = f"https://botapi.rubika.ir/v3/{token}"

    def _post(self, method, data):
        import os
        url = f"{self.base}/{method}"
        proxies = None
        proxy_url = os.getenv('RUBIKA_PROXY') or os.getenv('HTTP_PROXY') or os.getenv('http_proxy')
        if proxy_url:
            proxies = {'http': proxy_url, 'https': proxy_url}
        try:
            r = requests.post(url, json=data, timeout=20, proxies=proxies)
            # print(method, r.text[:500])
            return r.json()
        except Exception as e:
            print(f"API error {method}: {e}")
            return None

    def get_me(self):
        return self._post("getMe", {})

    def get_updates(self, start_id: Optional[str]=None):
        payload = {}
        if start_id:
            payload["start_id"] = start_id
        return self._post("getUpdates", payload)

    def send_message(self, chat_id: str, text: str, inline_keypad=None, chat_keypad=None, chat_keypad_type="New"):
        data = {
            "chat_id": chat_id,
            "text": text,
        }
        if inline_keypad:
            data["inline_keypad"] = inline_keypad
        if chat_keypad:
            data["chat_keypad"] = chat_keypad
            data["chat_keypad_type"] = chat_keypad_type
        return self._post("sendMessage", data)

    def send_photo(self, chat_id: str, file_id: str, caption: str=""):
        # در روبیکا ارسال عکس با sendMessage و file_inline انجام میشه
        # برای سادگی اول متن میفرستیم بعد عکس را با file_id
        # در نسخه v3: باید از uploadFile استفاده کنی یا file_id آماده
        # اینجا ساده: caption + file
        data = {
            "chat_id": chat_id,
            "text": caption,
            "file_inline": {
                "file_id": file_id,
                "type": "Image"
            } if file_id else None
        }
        # اگر file_id نداریم فقط متن
        if not file_id:
            del data["file_inline"]
        return self._post("sendMessage", data)

    def delete_message(self, chat_id: str, message_id: str):
        return self._post("deleteMessage", {"chat_id": chat_id, "message_id": message_id})

    def get_chats(self):
        return self._post("getChats", {})

# Helper keypad builders
def make_inline_keypad(buttons):
    # buttons = [[{"id":"get_banners","text":"دریافت بنرها"}, ...]]
    rows = []
    for row in buttons:
        btns = []
        for b in row:
            btns.append({
                "id": b["id"],
                "type": "Simple",
                "button_text": b["text"]
            })
        rows.append({"buttons": btns})
    return {"rows": rows}

def make_chat_keypad(buttons):
    rows = []
    for row in buttons:
        btns = []
        for b in row:
            btns.append({"id": b["id"], "type": "Simple", "button_text": b["text"]})
        rows.append({"buttons": btns})
    return {"rows": rows, "resize_keyboard": True, "one_time_keyboard": False}
