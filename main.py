import telebot
import os
import sqlite3
from telebot import types
from dotenv import load_dotenv

load_dotenv()  # .env dan o'qiydi

TOKEN = os.getenv("BOT_TOKEN")  # Railway Environment Variable dan oladi
bot = telebot.TeleBot(TOKEN)

# Railway ephemeral filesystem: har safar deploy bo‘lganda users.db yo‘q bo‘lishi mumkin
# Agar saqlash kerak bo‘lsa, PostgreSQL yoki boshqa DB ishlatish tavsiya qilinadi
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    phone TEXT,
    ball INTEGER DEFAULT 0,
    registered INTEGER DEFAULT 0,
    referrer INTEGER
)
""")
conn.commit()

# Foydalanuvchi qo‘shish
def add_user(user_id, phone, referrer=None):
    cursor.execute("""
    INSERT OR REPLACE INTO users (user_id, phone, ball, registered, referrer)
    VALUES (?, ?, COALESCE((SELECT ball FROM users WHERE user_id = ?), 0), 1, ?)
    """, (user_id, phone, user_id, referrer))
    conn.commit()

# Ball qo‘shish
def add_ball(user_id, amount):
    cursor.execute("UPDATE users SET ball = ball + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

# Ball olish
def get_ball(user_id):
    cursor.execute("SELECT ball FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

# Reyting olish
def get_top_users(limit=10):
    cursor.execute("SELECT user_id, ball FROM users ORDER BY ball DESC LIMIT ?", (limit,))
    return cursor.fetchall()

# Foydalanuvchi tekshirish
def is_registered(user_id):
    cursor.execute("SELECT registered FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result and result[0] == 1

# Referrer olish
def get_referrer(user_id):
    cursor.execute("SELECT referrer FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

# Sovg'alar rasmi uchun file_id
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

# START komandasi
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    args = message.text.split()

    # Referral logika
    ref_id = None
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id == chat_id:
                ref_id = None  # o‘zi-o‘zini refer qila olmaydi
        except:
            ref_id = None

    # Agar foydalanuvchi ro‘yxatdan o‘tgan bo‘lsa → menyu
    if is_registered(chat_id):
        main_menu(chat_id)
        return

    # Referrer ID ni vaqtincha DB ga saqlab qo‘yamiz
    cursor.execute("INSERT OR IGNORE INTO users (user_id, referrer) VALUES (?, ?)", (chat_id, ref_id))
    conn.commit()

    # Inline tugmalar
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

bot.send_message(
    chat_id,
    "🚀 Konkursda ishtirok etish uchun quyidagi kanallarga obuna bo‘ling ✅",
    reply_markup=markup,
    parse_mode="Markdown"
)


# CALLBACK handler
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

# Kontakt qabul qilish
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number

    # Foydalanuvchini ro‘yxatdan o‘tkazamiz
    referrer = get_referrer(chat_id)
    add_user(chat_id, phone, referrer)

    # Agar referer mavjud bo‘lsa, ball qo‘shamiz
    if referrer:
        add_ball(referrer, 10)
        bot.send_message(referrer, f"🎉 Sizga +10 ball qo'shildi! Jami: {get_ball(referrer)}")

    bot.send_message(chat_id, "🎉 Tabriklaymiz! Siz Konkursda to'liq ro'yxatdan o'tdingiz va boshlangʼich 0 ballga ega bo'ldingiz!")
    main_menu(chat_id)

# Asosiy menyu
def main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    konkurs = types.KeyboardButton("🔴 Konkursda qatnashish")
    referral = types.KeyboardButton("🟢 Refeal link")
    sovgalar = types.KeyboardButton("🎁 Sovgalar")
    ballarim = types.KeyboardButton("👤 Ballarim")
    reyting = types.KeyboardButton("📊 Reyting")
    shartlar = types.KeyboardButton("💡 Shartlar")
    markup.add(konkurs, referral)
    markup.add(sovgalar, ballarim)
    markup.add(reyting, shartlar)
    bot.send_message(chat_id, "Asosiy menyu:", reply_markup=markup)

# Tugmalar handleri
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
        "Konkursda qatnashish uchun:\n\n"
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
        score = get_ball(chat_id)
        bot.send_message(chat_id, f"👤 Sizning ballaringiz: {score}")

    elif text == "📊 Reyting":
        top_users = get_top_users()
        text_msg = "📊 Top 10 Reyting:\n"
        for i, (uid, ball) in enumerate(top_users, start=1):
            text_msg += f"{i}. {uid} - {ball} ball\n"
        bot.send_message(chat_id, text_msg)

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
        bot.send_message(chat_id, f"🔗 Sizning referral linkingiz:\n{link}\n\nDo'stlaringizga yuboring!")

bot.infinity_polling()
