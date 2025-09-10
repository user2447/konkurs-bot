import os
from dotenv import load_dotenv
import telebot
from telebot import types
import psycopg2

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = telebot.TeleBot(TOKEN)

# ================= DB bilan ulanish =================
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
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
except Exception as e:
    print(f"❌ DB xato: {e}")
    exit(1)

# ================= Sovg'alar rasmi =================
photo_file_id = "AgACAgIAAxkBAAPlaL_8Zj819ujsWbOOHdpR193AlkoAArD1MRuYugABSngTwRZxBPimAQADAgADeQADNgQ"

# ================= Majburiy kanallar =================
CHANNELS = [
    {"id": "@ixtiyor_uc", "name": "Kanal 1"},
    {"id": "@ixtiyor_gaming", "name": "Kanal 2"},
]

# ================= Foydalanuvchi funksiyalari =================
def add_user(user_id, phone, referrer=None):
    cursor.execute("""
        INSERT INTO users (user_id, phone, referrer, registered) 
        VALUES (%s, %s, %s, 1) ON CONFLICT (user_id) DO NOTHING
    """, (user_id, phone, referrer))
    conn.commit()

def add_ball(user_id, amount):
    cursor.execute("UPDATE users SET ball = ball + %s WHERE user_id = %s", (amount, user_id))
    conn.commit()

def get_ball(user_id):
    cursor.execute("SELECT ball FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def is_registered(user_id):
    cursor.execute("SELECT registered FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result and result[0] == 1

def get_referrer(user_id):
    cursor.execute("SELECT referrer FROM users WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

# ================= START handler =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
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
        reply_markup=markup
    )

# ================= CALLBACK handler =================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.from_user.id
    if call.data == "sub_done":
        if is_registered(chat_id):
            bot.answer_callback_query(call.id, "✅ Siz allaqachon ro'yxatdan o'tgansiz!")
            main_menu(chat_id)
            return
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        contact_button = types.KeyboardButton("📲 Raqamni yuborish", request_contact=True)
        markup.add(contact_button)
        bot.send_message(chat_id, "📲 Raqamingizni yuboring:", reply_markup=markup)
        bot.answer_callback_query(call.id)

# ================= Kontakt qabul qilish =================
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

# ================= Asosiy menyu =================
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

# ================= Tugmalar handleri =================
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
        "4 - o'rin 5 TA RP\n"
        "5 - o'rin 10 TA 120 UC\n"
        "6 - o'rin 20 TA 60 UC\n\n"
        "🔥 Konkurs 1 oy davom etadi.\n"
        "Boshlandi: 9 ~ Sentabr\n"
        "Tugashi: 9 ~ Oktabr\n\n"
        f"https://t.me/ixtiyor_rp_bot?start={chat_id}"
        )
    elif text == "🎁 Sovgalar":
        caption_text = (
            "Ixtiyor konkurs bot o'zining konkursiga start berdi\n"
            "Qatnashing va yutuqlarni qo'lga kiriting 😍\n\n"
            "1 - o'rin Lednik 6 AKK\n"
            "2 - o'rin LEDNIK 5 AKK\n"
            "3 - o'rin LEDNIK 4 AKK\n"
            "4 - o'rin 5 TA RP\n"
            "5 - o'rin 10 TA 120 UC\n"
            "6 - o'rin 20 TA 60 UC"
        )
        bot.send_photo(chat_id, photo_file_id, caption=caption_text)
    elif text == "👤 Ballarim":
        bot.send_message(chat_id, f"👤 Sizning ballaringiz: {get_ball(chat_id)}")
    elif text == "📊 Reyting":
        cursor.execute("SELECT user_id, ball FROM users ORDER BY ball DESC LIMIT 10")
        rows = cursor.fetchall()
        text_out = "📊 Top 10 Reyting:\n"
        for idx, row in enumerate(rows, 1):
            text_out += f"{idx}. {row[0]} - {row[1]} ball\n"
        bot.send_message(chat_id, text_out if rows else "Hozircha reyting mavjud emas.")
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
        link = f"https://t.me/ixtiyor_rp_bot?start={chat_id}"
        bot.send_message(chat_id, f"🔗 Sizning referral linkingiz:\n{link}")

# ================= Bot ishga tushurish =================
bot.infinity_polling()
