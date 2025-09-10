import os
from dotenv import load_dotenv
import telebot
from telebot import types
import psycopg2
import psycopg2.extras

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMINS = [7717343429, 1900651840]
PAY_ADMIN = 7717343429  # bu siz berdi

bot = telebot.TeleBot(TOKEN)

# ======= Sovg'alar rasmi =======
photo_file_id = "AgACAgIAAxkBAAPlaL_8Zj819ujsWbOOHdpR193AlkoAArD1MRuYugABSngTwRZxBPimAQADAgADeQADNgQ"

# ======= Kanallar =======
MAJBURIY_CHANNELS = [
    {"id": "@ixtiyor_uc", "name": "Kanal 1"},
    {"id": "@ixtiyor_gaming", "name": "Kanal 2"},
]
OPTIONAL_CHANNELS = [
    {"name": "Kanal 3", "url": "https://t.me/+J60RmZvVVPUyNmJi"},
    {"name": "Instagram", "url": "https://www.instagram.com/ixtiyor_gaming"},
    {"name": "YouTube", "url": "https://youtube.com/@ixtiyorgaming?si=azcra7Wz-TQmUUrM"},
]

# ======= DB ulanish =======
if not DATABASE_URL:
    print("❌ DATABASE_URL env topilmadi. DB ishlamaydi.")
    conn = None
else:
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        conn.autocommit = True
        cur = conn.cursor()
        # jadval
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            phone TEXT,
            ball INTEGER DEFAULT 0,
            registered BOOLEAN DEFAULT FALSE,
            referrer BIGINT
        );
        """)
        print("✅ PostgreSQL: jadval tayyor.")
    except Exception as e:
        print("❌ PostgreSQL ga ulanishda xato:", e)
        conn = None

# ======= Yordamchi DB funksiyalar =======
def db_get_user(user_id):
    if not conn: return None
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as c:
        c.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        r = c.fetchone()
        return dict(r) if r else None

def db_ensure_user(user_id):
    if not conn: return
    with conn.cursor() as c:
        c.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))

def db_set_referrer(user_id, referrer_id):
    if not conn: return
    with conn.cursor() as c:
        c.execute("UPDATE users SET referrer = %s WHERE user_id = %s AND (referrer IS NULL OR referrer = '')", (referrer_id, user_id))

def db_register_user(user_id, phone):
    if not conn: return
    with conn.cursor() as c:
        c.execute("INSERT INTO users (user_id, phone, registered) VALUES (%s, %s, TRUE) ON CONFLICT (user_id) DO UPDATE SET phone = EXCLUDED.phone, registered = TRUE", (user_id, phone))

def db_add_ball(user_id, amount):
    if not conn: return
    with conn.cursor() as c:
        c.execute("UPDATE users SET ball = ball + %s WHERE user_id = %s", (amount, user_id))

def db_get_ball(user_id):
    if not conn: return 0
    with conn.cursor() as c:
        c.execute("SELECT ball FROM users WHERE user_id = %s", (user_id,))
        r = c.fetchone()
        return r[0] if r else 0

def db_get_top(limit=None):
    if not conn: return []
    with conn.cursor() as c:
        if limit:
            c.execute("SELECT user_id, ball FROM users ORDER BY ball DESC LIMIT %s", (limit,))
        else:
            c.execute("SELECT user_id, ball FROM users ORDER BY ball DESC")
        return c.fetchall()

# ======= /sync - admin uchun (xotiradagi users -> db) =======
# Bu deploy qilishdan OLDIN hozirgi running bot (eski)ga qo'shilib, admin tomonidan yuborilsa,
# xotiradagi 'users' dictni DBga yozadi. Agar hozirki running botda users dict bo'lmasa, bu bo'sh ishlaydi.
@bot.message_handler(commands=['sync'])
def sync_handler(message):
    chat_id = message.chat.id
    if chat_id not in ADMINS:
        return
    if not conn:
        bot.send_message(chat_id, "❌ DB mavjud emas, sync imkoni yo'q.")
        return
    # Bu yerda biz `users` dict bo'lsa uni DBga yozamiz.
    # Agar eski botda users dict boshqa nomda bo'lsa, o'zgartiring.
    try:
        # attempt to read in-memory users if present
        mem = globals().get("users", {})
        count = 0
        for uid, u in mem.items():
            db_ensure_user(uid)
            if u.get("phone"):
                db_register_user(uid, u.get("phone"))
            if u.get("referrer"):
                db_set_referrer(uid, u.get("referrer"))
            if u.get("ball"):
                # set ball to existing + that ball
                with conn.cursor() as c:
                    c.execute("UPDATE users SET ball = %s WHERE user_id = %s", (u.get("ball",0), uid))
            count += 1
        bot.send_message(chat_id, f"✅ Sync tugadi. {count} foydalanuvchi DB ga yozildi.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Sync xato: {e}")

# ======= Xotirada — fallback (agar DB yo'q bo'lsa ishlaydi) =======
# eski koddagi users dict bilan moslashuv uchun:
if conn is None:
    users = {}  # memory fallback
else:
    users = {}  # hamma funktsiyalar DB orqali ishlaydi, lekin memory ham saqlaymiz opsional ravishda

# ======= START handler (referal) =======
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    args = message.text.split()

    # DB user yaratish/ensure
    if conn:
        db_ensure_user(chat_id)
    else:
        if chat_id not in users:
            users[chat_id] = {"phone": None, "ball": 0, "registered": False, "referrer": None}

    # referral
    if len(args) > 1:
        try:
            ref_id = int(args[1])
        except:
            ref_id = None
        if ref_id and ref_id != chat_id:
            if conn:
                # set only if user not registered
                user = db_get_user(chat_id)
                if user and not user.get("registered"):
                    db_set_referrer(chat_id, ref_id)
            else:
                if not users[chat_id]["registered"]:
                    users[chat_id]["referrer"] = ref_id

    # Reply markup
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in MAJBURIY_CHANNELS:
        # build t.me link from id
        tlink = f"https://t.me/{ch['id'].replace('@','')}"
        markup.add(types.InlineKeyboardButton(ch["name"], url=tlink))
    for ch in OPTIONAL_CHANNELS:
        markup.add(types.InlineKeyboardButton(ch["name"], url=ch["url"]))
    markup.add(types.InlineKeyboardButton("Obuna bo'ldim ✅", callback_data="sub_done"))

    bot.send_message(chat_id,
                     "🚀 Konkursda ishtirok etish uchun quyidagi majburiy kanallarga obuna bo‘ling va 'Obuna bo'ldim ✅' tugmasini bosing",
                     reply_markup=markup)

# ======= CALLBACK handler =======
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.from_user.id
    if call.data != "sub_done":
        return

    # tekshiruv — faqat MAJBURIY_CHANNELS
    not_subscribed = []
    for ch in MAJBURIY_CHANNELS:
        try:
            member = bot.get_chat_member(ch["id"], chat_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_subscribed.append(ch["name"])
        except Exception as e:
            # agar bot admin emas yoki member list ga kira olmasa — treat as not subscribed (va log)
            not_subscribed.append(ch["name"])
            print(f"⚠️ Kanal tekshirish xato ({ch['id']}): {e}")

    if not_subscribed:
        bot.answer_callback_query(call.id, "❌ Siz barcha majburiy kanallarga obuna bo‘lmadingiz!")
        bot.send_message(chat_id, "⛔️ Quyidagi kanallarga obuna bo‘ling:\n" + "\n".join(not_subscribed))
        return

    # agar ro'yxatdan o'tmagan bo'lsa, raqam so'ramiz
    if conn:
        user = db_get_user(chat_id)
        registered = user.get("registered") if user else False
    else:
        registered = users.get(chat_id, {}).get("registered", False)

    if not registered:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        contact_button = types.KeyboardButton("📲 Raqamni yuborish", request_contact=True)
        markup.add(contact_button)
        bot.send_message(chat_id, "📲 Raqamingizni yuboring:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "✅ Siz allaqachon ro‘yxatdan o‘tib bo‘lgansiz.")
    bot.answer_callback_query(call.id)

# ======= Kontakt qabul qilish =======
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number

    if conn:
        user = db_get_user(chat_id)
        if user and user.get("registered"):
            bot.send_message(chat_id, "❌ Siz allaqachon ro‘yxatdan o‘tib bo‘lgansiz.")
            return
        db_register_user(chat_id, phone)
        # referrer kimligini tekshirib, ball berish
        user = db_get_user(chat_id)
        ref = user.get("referrer")
        if ref:
            # faqat agar ref mavjud bo'lsa va ref user oldindan mavjud bo'lsa
            ref_user = db_get_user(ref)
            if ref_user is not None:
                db_add_ball(ref, 10)
                # notify referrer
                try:
                    bot.send_message(ref, f"🎉 Sizga yangi do‘st qo‘shildi!\n+10 ball qo‘shildi.\nJami: {db_get_ball(ref)}")
                except Exception:
                    pass
    else:
        # memory fallback
        if users[chat_id]["registered"]:
            bot.send_message(chat_id, "❌ Siz allaqachon ro‘yxatdan o‘tib bo‘lgansiz.")
            return
        users[chat_id]["phone"] = phone
        users[chat_id]["registered"] = True
        ref = users[chat_id].get("referrer")
        if ref and ref in users:
            users[ref]["ball"] += 10
            try:
                bot.send_message(ref, f"🎉 Sizga yangi do‘st qo‘shildi!\n+10 ball qo‘shildi.\nJami: {users[ref]['ball']}")
            except Exception:
                pass

    bot.send_message(chat_id, "🎉 Tabriklaymiz! Siz Konkursda to'liq ro'yxatdan o'tdingiz!")
    main_menu(chat_id)

# ======= Menyu && Tekshiruvlar =======
def main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("🔴 Konkursda qatnashish"), types.KeyboardButton("🟢 Refeal link"))
    markup.add(types.KeyboardButton("🎁 Sovgalar"), types.KeyboardButton("👤 Ballarim"))
    markup.add(types.KeyboardButton("📊 Reyting"), types.KeyboardButton("💡 Shartlar"))
    bot.send_message(chat_id, "Asosiy menyu:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def text_handler(message):
    chat_id = message.chat.id
    text = message.text

    if text == "🔴 Konkursda qatnashish":
        bot.send_message(chat_id,
                         "Ixtiyor konkurs bot o'zining konkursiga start berdi\n"
                         "Qatnashing va sovgalarni qo'lga kiriting 😍\n\n"
                         "1 - o'rin Lednik 6 AKK\n"
                         "2 - o'rin LEDNIK 5 AKK\n"
                         "3 - o'rin LEDNIK 4 AKK\n"
                         "4-5-6-7-8 o'rin RP\n"
                         "9……19 120 UC\n"
                         "20……40  60 UC\n\n"
                         f"https://t.me/ixtiyor_rp_bot?start={chat_id}"
                         )

    elif text == "🎁 Sovgalar":
        caption_text = (
            "Ixtiyor konkurs bot o'zining konkursiga start berdi\n"
            "Qatnashing va yutuqlarni qo'lga kiriting 😍\n\n"
            "1 - o'rin Lednik 6 AKK\n"
            "2 - o'rin LEDNIK 5 AKK\n"
            "3 - o'rin LEDNIK 4 AKK\n"
            "4-5-6-7-8 o'rin RP\n"
            "9……19 120 UC\n"
            "20……40  60 UC"
        )
        bot.send_photo(chat_id, photo_file_id, caption=caption_text)

    elif text == "👤 Ballarim":
        if conn:
            bot.send_message(chat_id, f"👤 Sizning ballaringiz: {db_get_ball(chat_id)}")
        else:
            bot.send_message(chat_id, f"👤 Sizning ballaringiz: {users.get(chat_id,{}).get('ball',0)}")

    elif text == "📊 Reyting":
        if conn:
            # Adminlarga barcha (to'liq) reyting, oddiylarga top10
            rows = db_get_top(None)  # all users ordered
            if chat_id in ADMINS:
                text_out = "📊 To‘liq Reyting (Adminlar uchun):\n"
                for idx, (uid, ball) in enumerate(rows, 1):
                    # username olamiz — ehtimol public username yo'q bo'lishi mumkin
                    try:
                        chat = bot.get_chat(uid)
                        username = f"@{chat.username}" if getattr(chat, "username", None) else "❌ username yo'q"
                    except Exception:
                        username = "❌ username yo'q"
                    text_out += f"{idx}. {uid} {username} - {ball} ball\n"
                bot.send_message(chat_id, text_out if rows else "Hozircha reyting mavjud emas.")
            else:
                text_out = "📊 Top 10 Reyting:\n"
                for idx, (uid, ball) in enumerate(rows[:10], 1):
                    text_out += f"{idx}. {uid} - {ball} ball\n"
                bot.send_message(chat_id, text_out if rows else "Hozircha reyting mavjud emas.")
        else:
            # memory fallback
            sorted_users = sorted(users.items(), key=lambda x: x[1].get("ball",0), reverse=True)
            if chat_id in ADMINS:
                text_out = "📊 To‘liq Reyting (Adminlar uchun):\n"
                for idx, (uid, udata) in enumerate(sorted_users,1):
                    text_out += f"{idx}. {uid} - {udata.get('ball',0)} ball\n"
                bot.send_message(chat_id, text_out if sorted_users else "Hozircha reyting mavjud emas.")
            else:
                text_out = "📊 Top 10 Reyting:\n"
                for idx, (uid, udata) in enumerate(sorted_users[:10],1):
                    text_out += f"{idx}. {uid} - {udata.get('ball',0)} ball\n"
                bot.send_message(chat_id, text_out if sorted_users else "Hozircha reyting mavjud emas.")

    elif text == "💡 Shartlar":
        bot.send_message(chat_id,
                         "TANLOV ShARTLARI ✅\n\n"
                         "❗️ Ushbu tanlovda g'oliblar random orqali emas, balki to'plagan ballariga qarab aniqlanadi.\n\n"
                         "Ballar qanday to'planadi?\n"
                         "BOT sizga maxsus referral link beradi.\n"
                         "O'sha link orqali kirgan har bir do'stingiz uchun 10 balldan qo'shiladi.\n\n"
                         "⏳ Tanlov 9 ~ Oktabr kuni 20:00 da yakunlanadi.\n"
                         "❗️ Diqqat! Nakrutka qilganlar Ban bo‘ladi.\n"
                         "🙂 Faol bo'ling, mukofotlarni qo'lga kiriting.\n"
                         "‼️‼️ Tanlov g'oliblari hamma majburiy kanallarga a'zo bo'lishi shart❌"
                         )

    elif text == "🟢 Refeal link":
        bot.send_message(chat_id, f"🔗 Sizning referral linkingiz:\nhttps://t.me/{bot.get_me().username}?start={chat_id}\n\nDo'stlaringizga yuboring!")

# ======= /pay =======
@bot.message_handler(commands=['pay'])
def pay_handler(message):
    chat_id = message.chat.id
    if chat_id != PAY_ADMIN:
        return
    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(chat_id, "❌ To‘g‘ri format: /pay <user_id> <miqdor>")
            return
        uid = int(parts[1]); amount = int(parts[2])
        if conn:
            db_ensure_user(uid)
            db_add_ball(uid, amount)
            bot.send_message(chat_id, f"✅ {uid} foydalanuvchiga {amount} ball qo‘shildi. Jami: {db_get_ball(uid)}")
        else:
            if uid not in users:
                users[uid] = {"phone": None, "ball": 0, "registered": False, "referrer": None}
            users[uid]["ball"] += amount
            bot.send_message(chat_id, f"✅ {uid} foydalanuvchiga {amount} ball qo‘shildi. Jami: {users[uid]['ball']}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Xatolik: {e}")

# ======= Ishga tushurish =======
print("Bot ishga tushmoqda...")
bot.infinity_polling()
