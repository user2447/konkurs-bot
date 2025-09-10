import os
from dotenv import load_dotenv
import telebot
from telebot import types
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
DATABASE_URL = os.getenv("DATABASE_URL")

# ================= Adminlar =================
ADMINS = [7717343429, 1900651840]
PAY_ADMIN = 7717343429  # faqat shu odam /pay ishlatadi

# ================= Sovg'alar rasmi =================
photo_file_id = "AgACAgIAAxkBAAPlaL_8Zj819ujsWbOOHdpR193AlkoAArD1MRuYugABSngTwRZxBPimAQADAgADeQADNgQ"

# ================= Majburiy kanallar =================
MAJBURIY_CHANNELS = [
    {"id": "@ixtiyor_uc", "name": "Kanal 1"},
    {"id": "@ixtiyor_gaming", "name": "Kanal 2"},
]

# ================= Qo‘shimcha kanallar =================
OPTIONAL_CHANNELS = [
    {"name": "Kanal 3", "url": "https://t.me/+J60RmZvVVPUyNmJi"},
    {"name": "Instagram", "url": "https://www.instagram.com/ixtiyor_gaming"},
    {"name": "YouTube", "url": "https://youtube.com/@ixtiyorgaming?si=azcra7Wz-TQmUUrM"},
]

# ================= DB ulanish =================
conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id BIGINT PRIMARY KEY,
    phone TEXT,
    ball INT DEFAULT 0,
    registered BOOLEAN DEFAULT FALSE,
    referrer BIGINT
)
""")
conn.commit()

# ================= Helper funksiyalar =================
def get_user(chat_id):
    cur.execute("SELECT * FROM users WHERE chat_id=%s", (chat_id,))
    return cur.fetchone()

def add_or_update_user(chat_id, phone=None, registered=False, referrer=None, ball_increment=0):
    user = get_user(chat_id)
    if user:
        cur.execute("""
            UPDATE users
            SET phone = COALESCE(%s, phone),
                registered = %s,
                referrer = COALESCE(%s, referrer),
                ball = ball + %s
            WHERE chat_id = %s
        """, (phone, registered, referrer, ball_increment, chat_id))
    else:
        cur.execute("""
            INSERT INTO users (chat_id, phone, ball, registered, referrer)
            VALUES (%s, %s, %s, %s, %s)
        """, (chat_id, phone, ball_increment, registered, referrer))
    conn.commit()

# ================= START handler =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    args = message.text.split()

    user = get_user(chat_id)
    if not user:
        add_or_update_user(chat_id)

    referrer_id = int(args[1]) if len(args) > 1 else None
    if referrer_id and referrer_id != chat_id:
        add_or_update_user(chat_id, referrer=referrer_id)

    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in MAJBURIY_CHANNELS:
        markup.add(types.InlineKeyboardButton(ch["name"], url=f"https://t.me/{ch['id'].replace('@','')}"))
    for ch in OPTIONAL_CHANNELS:
        markup.add(types.InlineKeyboardButton(ch["name"], url=ch["url"]))
    markup.add(types.InlineKeyboardButton("Obuna bo'ldim ✅", callback_data="sub_done"))

    bot.send_message(chat_id, "🚀 Konkursda ishtirok etish uchun majburiy kanallarga obuna bo‘ling va tugmani bosing", reply_markup=markup)

# ================= CALLBACK handler =================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.from_user.id
    if call.data == "sub_done":
        not_subscribed = []
        for ch in MAJBURIY_CHANNELS:
            try:
                member = bot.get_chat_member(ch["id"], chat_id)
                if member.status not in ["member", "administrator", "creator"]:
                    not_subscribed.append(ch["name"])
            except Exception as e:
                bot.send_message(chat_id, f"⚠️ Bot '{ch['name']}' kanalida admin emas yoki kira olmayapti!\nXato: {e}")
                not_subscribed.append(ch["name"])
        if not_subscribed:
            bot.answer_callback_query(call.id, "❌ Siz barcha majburiy kanallarga obuna bo‘lmadingiz!")
            bot.send_message(chat_id, "⛔️ Quyidagi kanallarga obuna bo‘ling:\n" + "\n".join(not_subscribed))
            return

        user = get_user(chat_id)
        if not user['registered']:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            contact_button = types.KeyboardButton("📲 Raqamni yuborish", request_contact=True)
            markup.add(contact_button)
            bot.send_message(chat_id, "📲 Raqamingizni yuboring:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "✅ Siz allaqachon ro‘yxatdan o‘tib bo‘lgansiz.")
        bot.answer_callback_query(call.id)

# ================= Kontakt qabul qilish =================
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number
    user = get_user(chat_id)
    if user and user['registered']:
        bot.send_message(chat_id, "❌ Siz allaqachon ro‘yxatdan o‘tib bo‘lgansiz.")
        return
    add_or_update_user(chat_id, phone=phone, registered=True)
    referrer_id = get_user(chat_id)['referrer']
    if referrer_id:
        add_or_update_user(referrer_id, ball_increment=10)
        bot.send_message(referrer_id, f"🎉 Sizga yangi do‘st qo‘shildi! +10 ball")
    bot.send_message(chat_id, "🎉 Tabriklaymiz! Siz Konkursda to'liq ro'yxatdan o'tdingiz!")
    main_menu(chat_id)

# ================= Asosiy menyu =================
def main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🔴 Konkursda qatnashish"),
        types.KeyboardButton("🟢 Refeal link"),
        types.KeyboardButton("🎁 Sovgalar"),
        types.KeyboardButton("👤 Ballarim"),
        types.KeyboardButton("📊 Reyting"),
        types.KeyboardButton("💡 Shartlar")
    )
    bot.send_message(chat_id, "Asosiy menyu:", reply_markup=markup)

# ================= Tugmalar handleri =================
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    chat_id = message.chat.id
    text = message.text
    user = get_user(chat_id)

    if text == "🔴 Konkursda qatnashish":
        bot.send_message(chat_id, "Ixtiyor konkurs bot start berdi...")

    elif text == "🎁 Sovgalar":
        caption_text = "Sovgalar ro‘yxati..."
        bot.send_photo(chat_id, photo_file_id, caption=caption_text)

    elif text == "👤 Ballarim":
        ball = user['ball'] if user else 0
        bot.send_message(chat_id, f"👤 Sizning ballaringiz: {ball}")

    elif text == "📊 Reyting":
        cur.execute("SELECT * FROM users ORDER BY ball DESC")
        users_list = cur.fetchall()
        if chat_id in ADMINS:
            text_out = "📊 To‘liq Reyting (Adminlar uchun):\n"
            for idx, u in enumerate(users_list, 1):
                text_out += f"{idx}. {u['chat_id']} - {u['ball']} ball\n"
        else:
            text_out = "📊 Top 10 Reyting:\n"
            for idx, u in enumerate(users_list[:10], 1):
                text_out += f"{idx}. {u['chat_id']} - {u['ball']} ball\n"
        bot.send_message(chat_id, text_out if users_list else "Hozircha reyting mavjud emas.")

    elif text == "💡 Shartlar":
        bot.send_message(chat_id, "Tanlov shartlari ...")

    elif text == "🟢 Refeal link":
        link = f"https://t.me/ixtiyor_rp_bot?start={chat_id}"
        bot.send_message(chat_id, f"🔗 Sizning referral linkingiz:\n{link}")

# ================= Maxfiy /pay komanda =================
@bot.message_handler(commands=['pay'])
def pay_handler(message):
    chat_id = message.chat.id
    if chat_id != PAY_ADMIN:
        return
