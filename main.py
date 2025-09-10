import os
from flask import Flask, request
import telebot
from telebot import types
from dotenv import load_dotenv
import psycopg2

# .env faylidan o'qish
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMINS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",")]

bot = telebot.TeleBot(TOKEN)

# PostgreSQL bilan ulanish
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Jadval yaratish (agar yo'q bo'lsa)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    phone TEXT,
    ball INTEGER DEFAULT 0,
    registered INTEGER DEFAULT 0,
    referrer BIGINT
)
""")
conn.commit()

# Foydalanuvchi qo'shish/yangilash
def add_user(user_id, phone, referrer=None):
    cursor.execute("""
    INSERT INTO users (user_id, phone, ball, registered, referrer)
    VALUES (%s, %s, COALESCE((SELECT ball FROM users WHERE user_id = %s), 0), 1, %s)
    ON CONFLICT (user_id) DO UPDATE SET phone = EXCLUDED.phone
    """, (user_id, phone, user_id, referrer))
    conn.commit()

# Ball qo'shish
def add_ball(user_id, amount):
    cursor.execute("UPDATE users SET ball = ball + %s WHERE user_id = %s", (amount, user_id))
    conn.commit()

# Ball olish
def get_ball(user_id):
    cursor.execute("SELECT ball FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

# Ro‘yxatdan o'tganligini tekshirish
def is_registered(user_id):
    cursor.execute("SELECT registered FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result and result[0] == 1

# Referrer olish
def get_referrer(user_id):
    cursor.execute("SELECT referrer FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

# Sovg'alar rasmi
photo_file_id = "AgACAgIAAxkBAAPlaL_8Zj819ujsWbOOHdpR193AlkoAArD1MRuYugABSngTwRZxBPimAQADAgADeQADNgQ"

# Majburiy kanallar
CHANNELS = [
    {"id": "@ixtiyor_uc", "name": "Kanal 1"},
    {"id": "@ixtiyor_gaming", "name": "Kanal 2"},
]

# Obuna tekshirish
def check_subscription(user_id):
    not_subscribed = []
    for ch in CHANNELS:
        try:
            status = bot.get_chat_member(ch["id"], user_id).status
            if status in ["left", "kicked"]:
                not_subscribed.append(ch["name"])
        except:
            not_subscribed.append(ch["name"])
    return not_subscribed

# Asosiy menyu
def main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton("🔴 Konkursda qatnashish"),
        types.KeyboardButton("🟢 Refeal link")
    )
    markup.add(
        types.KeyboardButton("🎁 Sovgalar"),
        types.KeyboardButton("👤 Ballarim")
    )
    markup.add(
        types.KeyboardButton("📊 Reyting"),
        types.KeyboardButton("💡 Shartlar")
    )
    bot.send_message(chat_id, "Asosiy menyu:", reply_markup=markup)

# Flask server yaratish (Railway uchun)
server = Flask(__name__)

@server.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

# /start handler
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    args = message.text.split()
    ref_id = None
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id == chat_id:
                ref_id = None
        except:
            ref_id = None

    if is_registered(chat_id):
        main_menu(chat_id)
        return

    cursor.execute("INSERT INTO users (user_id, referrer) VALUES (%s, %s) ON CONFLICT DO NOTHING", (chat_id, ref_id))
    conn.commit()

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Kanal 1", url="https://t.me/ixtiyor_uc"),
        types.InlineKeyboardButton("Kanal 2", url="https://t.me/ixtiyor_gaming"),
    )
    markup.add(
        types.InlineKeyboardButton("Instagram", url="https://www.instagram.com/ixtiyor_gaming"),
        types.InlineKeyboardButton("YouTube", url="https://youtube.com/@ixtiyorgaming?si=azcra7Wz-TQmUUrM"),
    )
    markup.add(types.InlineKeyboardButton("Obuna bo'ldim ✅", callback_data="sub_done"))

    bot.send_message(chat_id,
        "🚀 Konkursda ishtirok etish uchun quyidagi kanallarga obuna bo‘ling va “Obuna bo'ldim ✅” tugmasini bosing.",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# Kontakt handler
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number
    referrer = get_referrer(chat_id)
    add_user(chat_id, phone, referrer)

    if referrer:
        add_ball(referrer, 10)
        bot.send_message(referrer, f"🎉 Sizga +10 ball qo'shildi! Jami: {get_ball(referrer)}")

    bot.send_message(chat_id, "🎉 Tabriklaymiz! Siz Konkursda to'liq ro'yxatdan o'tdingiz!")
    main_menu(chat_id)

# Callback handler
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.from_user.id
    if call.data == "sub_done":
        not_subscribed = check_subscription(chat_id)
        if not_subscribed:
            bot.answer_callback_query(call.id,
                f"❌ Siz quyidagi kanallarga obuna bo‘lmadingiz: {', '.join(not_subscribed)}",
                show_alert=True
            )
            return
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        contact_button = types.KeyboardButton("📲 Raqamni yuborish", request_contact=True)
        markup.add(contact_button)
        bot.send_message(chat_id, "📲 Raqamni yuborish tugmasini bosgan holda raqamingizni yuboring!", reply_markup=markup)

# Text handler
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    chat_id = message.chat.id
    text = message.text

    if text == "🔴 Konkursda qatnashish":
        bot.send_message(chat_id, "Konkurs haqida ma’lumot...")
    elif text == "🎁 Sovgalar":
        bot.send_photo(chat_id, photo_file_id, caption="Sovgalar ro'yxati...")
    elif text == "👤 Ballarim":
        bot.send_message(chat_id, f"👤 Sizning ballaringiz: {get_ball(chat_id)}")
    elif text == "🟢 Refeal link":
        link = f"https://t.me/ixtiyor_rp_bot?start={chat_id}"
        bot.send_message(chat_id, f"🔗 Sizning referral linkingiz:\n{link}")

# Webhookni set qilish (Railway deployda bitta marta bajariladi)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # masalan: https://your-app.up.railway.app
bot.remove_webhook()
bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
