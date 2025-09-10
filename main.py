import os
from dotenv import load_dotenv
import telebot
from telebot import types

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))  # .env: ADMIN_IDS="id1,id2"
OWNER_ID = 7717343429  # faqat egaga /pay ishlaydi

bot = telebot.TeleBot(TOKEN)

# ================= Sovg'alar rasmi =================
photo_file_id = "AgACAgIAAxkBAAPlaL_8Zj819ujsWbOOHdpR193AlkoAArD1MRuYugABSngTwRZxBPimAQADAgADeQADNgQ"

# ================= Kanallar =================
CHANNELS = [
    {"id": "@ixtiyor_uc", "name": "Kanal 1"},
    {"id": "@ixtiyor_gaming", "name": "Kanal 2"},
]
OPTIONAL_CHANNEL = {"id": "https://t.me/+J60RmZvVVPUyNmJi", "name": "3-Kanal (ixtiyoriy)"}

# ================= Xotirada saqlash =================
users = {}  # {user_id: {"phone": str, "ball": int, "registered": bool, "username": str}}

# ================= START handler =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    username = message.from_user.username or ""
    if chat_id not in users:
        users[chat_id] = {"phone": None, "ball": 0, "registered": False, "username": username}

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Kanal 1", url="https://t.me/ixtiyor_uc"),
        types.InlineKeyboardButton("Kanal 2", url="https://t.me/ixtiyor_gaming"),
        types.InlineKeyboardButton("3-Kanal (ixtiyoriy)", url=OPTIONAL_CHANNEL["id"]),
    )
    markup.add(
        types.InlineKeyboardButton("Instagram", url="https://www.instagram.com/ixtiyor_gaming"),
        types.InlineKeyboardButton("YouTube", url="https://youtube.com/@ixtiyorgaming?si=azcra7Wz-TQmUUrM"),
    )
    markup.add(types.InlineKeyboardButton("Obuna bo'ldim ✅", callback_data="sub_done"))

    bot.send_message(chat_id,
        "🚀 Konkursda qatnashish uchun 1 va 2-kanallarga obuna bo‘ling.\n"
        "3-kanalga obuna bo‘lish majburiy emas.",
        reply_markup=markup
    )

# ================= CALLBACK handler =================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.from_user.id
    if call.data == "sub_done":
        if users.get(chat_id, {}).get("registered"):
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
    users[chat_id]["phone"] = phone
    users[chat_id]["registered"] = True
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
        "Ixtiyor konkurs bot konkursini boshladi!\n"
        "Qatnashing va sovgalarni qo‘lga kiriting 😍\n\n"
        "1 - o‘rin: Lednik 6 AKK\n"
        "2 - o‘rin: LEDNIK 5 AKK\n"
        "3 - o‘rin: LEDNIK 4 AKK\n"
        "4 - o‘rin: 5 TA RP\n"
        "5 - o‘rin: 10 TA 120 UC\n"
        "6 - o‘rin: 20 TA 60 UC\n\n"
        "🔥 Konkurs 1 oy davom etadi.\n"
        "Boshlandi: 9 ~ Sentabr\n"
        "Tugashi: 9 ~ Oktabr\n\n"
        f"https://t.me/ixtiyor_rp_bot?start={chat_id}"
        )

    elif text == "🎁 Sovgalar":
        caption_text = (
            "🎁 Sovg‘alar ro‘yxati:\n\n"
            "1 - o‘rin: Lednik 6 AKK\n"
            "2 - o‘rin: LEDNIK 5 AKK\n"
            "3 - o‘rin: LEDNIK 4 AKK\n"
            "4 - o‘rin: 5 TA RP\n"
            "5 - o‘rin: 10 TA 120 UC\n"
            "6 - o‘rin: 20 TA 60 UC"
        )
        bot.send_photo(chat_id, photo_file_id, caption=caption_text)

    elif text == "👤 Ballarim":
        ball = users.get(chat_id, {}).get("ball", 0)
        bot.send_message(chat_id, f"👤 Sizning ballaringiz: {ball}")

    elif text == "📊 Reyting":
        sorted_users = sorted(users.items(), key=lambda x: x[1]["ball"], reverse=True)
        if chat_id in ADMIN_IDS:
            limit = 38
            text_out = "📊 Top 38 Reyting (Admin uchun):\n"
            for idx, (uid, udata) in enumerate(sorted_users[:limit], 1):
                uname = f"@{udata['username']}" if udata['username'] else "No username"
                text_out += f"{idx}. {uid} ({uname}) - {udata['ball']} ball\n"
        else:
            limit = 10
            text_out = "📊 Top 10 Reyting:\n"
            for idx, (uid, udata) in enumerate(sorted_users[:limit], 1):
                text_out += f"{idx}. {udata['ball']} ball\n"
        bot.send_message(chat_id, text_out if sorted_users else "Hozircha reyting mavjud emas.")

    elif text == "💡 Shartlar":
        bot.send_message(chat_id,
        "📌 TANLOV ShARTLARI:\n\n"
        "❗️ G‘oliblar random emas, ballariga qarab aniqlanadi.\n"
        "Har bir referal = 10 ball.\n"
        "⏳ Tanlov 9 ~ Oktabr kuni 20:00 da yakunlanadi.\n"
        "❌ Nakrutka qilganlar ban qilinadi."
        )

    elif text == "🟢 Refeal link":
        link = f"https://t.me/ixtiyor_rp_bot?start={chat_id}"
        bot.send_message(chat_id, f"🔗 Sizning referral linkingiz:\n{link}\n\nDo‘stlaringizga yuboring!")

# ================= Admin komandalar =================
@bot.message_handler(commands=['top'])
def admin_top(message):
    chat_id = message.chat.id
    if chat_id not in ADMIN_IDS:
        return
    sorted_users = sorted(users.items(), key=lambda x: x[1]["ball"], reverse=True)
    text_out = "📊 Full Top 38:\n"
    for idx, (uid, udata) in enumerate(sorted_users[:38], 1):
        uname = f"@{udata['username']}" if udata['username'] else "No username"
        text_out += f"{idx}. {uid} ({uname}) - {udata['ball']} ball\n"
    bot.send_message(chat_id, text_out if sorted_users else "Hozircha reyting mavjud emas.")

@bot.message_handler(commands=['pay'])
def pay_command(message):
    chat_id = message.chat.id
    if chat_id != OWNER_ID:
        return
    try:
        _, uid, amount = message.text.split()
        uid = int(uid)
        amount = int(amount)
        if uid in users:
            users[uid]["ball"] += amount
            bot.send_message(chat_id, f"✅ {uid} foydalanuvchiga {amount} ball qo‘shildi.")
            bot.send_message(uid, f"🎉 Sizga +{amount} ball qo‘shildi!")
        else:
            bot.send_message(chat_id, "❌ Foydalanuvchi topilmadi.")
    except:
        bot.send_message(chat_id, "❌ Foydalanish: /pay <id> <miqdor>")

# ================= Botni ishga tushurish =================
bot.infinity_polling()
