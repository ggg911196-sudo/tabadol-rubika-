import aiosqlite
import json
import os
DB_PATH = os.getenv("DB_PATH", "tabadol_rubika.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS banners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            photo_file_id TEXT
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS exchanges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id TEXT,
            partner_username TEXT,
            partner_channel TEXT,
            partner_banner_text TEXT,
            proof_chat_id TEXT,
            owner_message_ids TEXT,
            expire_at TEXT
        )''')
        await db.execute('''CREATE TABLE IF NOT EXISTS states (
            user_id TEXT PRIMARY KEY,
            state TEXT,
            data TEXT
        )''')
        await db.commit()

async def add_banner(text, photo=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO banners (text, photo_file_id) VALUES (?,?)", (text, photo))
        await db.commit()

async def get_banners():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, text, photo_file_id FROM banners") as cur:
            rows = await cur.fetchall()
            return [{"id":r[0],"text":r[1],"photo":r[2]} for r in rows]

async def clear_banners():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM banners")
        await db.commit()

async def set_user_state(user_id, state, data=None):
    import json
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO states (user_id, state, data) VALUES (?,?,?)",
                         (str(user_id), state, json.dumps(data or {})))
        await db.commit()

async def get_user_state(user_id):
    import json
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT state, data FROM states WHERE user_id=?", (str(user_id),)) as cur:
            row = await cur.fetchone()
            if row:
                return row[0], json.loads(row[1])
            return None, {}

async def clear_user_state(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM states WHERE user_id=?", (str(user_id),))
        await db.commit()

async def add_exchange(partner_id, username, channel, banner_text, proof_chat_id, owner_msg_ids, expire_at):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO exchanges (partner_id, partner_username, partner_channel, partner_banner_text, proof_chat_id, owner_message_ids, expire_at) VALUES (?,?,?,?,?,?,?)",
                         (str(partner_id), username, channel, banner_text, str(proof_chat_id), json.dumps(owner_msg_ids), str(expire_at)))
        await db.commit()

async def get_active_exchanges():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, owner_message_ids, expire_at FROM exchanges") as cur:
            return await cur.fetchall()

async def delete_exchange(eid):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM exchanges WHERE id=?", (eid,))
        await db.commit()
