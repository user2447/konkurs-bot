import os
import telebot
from telebot import types

# ================= ENV =================
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

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

# ================= Adminlar =================
ADMINS = [7717343429, 1900651840]
PAY_ADMIN = 7717343429  # faqat shu admin /pay ishlatadi

# ================= Xotira =================
users = {}  # {user_id: {"phone": str, "ball": int, "registered": bool, "referrer": int}}

# ================= START handler =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    args = message.text.split()

    if chat_id not in users:
        users[chat_id] = {"phone": None, "ball": 0, "registered": False, "referrer": None}

    if len(args) > 1:
        referrer_id = int(args[1])
        if referrer_id != chat_id and not users[chat_id]["registered"]:
            users[chat_id]["referrer"] = referrer_id

    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in MAJBURIY_CHANNELS:
        markup.add(types.InlineKeyboardButton(ch["name"], url=f"https://t.me/{ch['id'].replace('@','')}"))
    for ch in OPTIONAL_CHANNELS:
        markup.add(types.InlineKeyboardButton(ch["name"], url=ch["url"]))
    markup.add(types.InlineKeyboardButton("Obuna bo'ldim ✅", callback_data="sub_done"))

    bot.send_message(chat_id,
        "🚀 Konkursda ishtirok etish uchun quyidagi majburiy kanallarga obuna bo‘ling va 'Obuna bo'ldim ✅' tugmasini bosing",
        reply_markup=markup
    )

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

        if not users[chat_id]["registered"]:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(types.KeyboardButton("📲 Raqamni yuborish", request_contact=True))
            bot.send_message(chat_id, "📲 Raqamingizni yuboring:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "✅ Siz allaqachon ro‘yxatdan o‘tib bo‘lgansiz.")
        bot.answer_callback_query(call.id)

# ================= Kontakt qabul qilish =================
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number

    if users[chat_id]["registered"]:
        bot.send_message(chat_id, "❌ Siz allaqachon ro‘yxatdan o‘tib bo‘lgansiz.")
        return

    users[chat_id]["phone"] = phone
    users[chat_id]["registered"] = True

    referrer_id = users[chat_id].get("referrer")
    if referrer_id and referrer_id in users:
        users[referrer_id]["ball"] += 10
        bot.send_message(referrer_id, f"🎉 Sizga yangi do‘st qo‘shildi!\n+10 ball qo‘shildi.\nJami: {users[referrer_id]['ball']}")

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

# ================= Tugmalar handler =================
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    chat_id = message.chat.id
    text = message.text
    sorted_users = sorted(users.items(), key=lambda x: x[1]["ball"], reverse=True)

    if text == "👤 Ballarim":
        ball = users.get(chat_id, {}).get("ball", 0)
        bot.send_message(chat_id, f"👤 Sizning ballaringiz: {ball}")
    elif text == "📊 Reyting":
        if chat_id in ADMINS:
            text_out = "📊 To‘liq Reyting (Adminlar uchun):\n"
            for idx, (uid, udata) in enumerate(sorted_users, 1):
                username = f"@{bot.get_chat(uid).username}" if bot.get_chat(uid).username else "❌ username yo'q"
                text_out += f"{idx}. {uid} {username} - {udata['ball']} ball\n"
            bot.send_message(chat_id, text_out if sorted_users else "Hozircha reyting mavjud emas.")
        else:
            text_out = "📊 Top 10 Reyting:\n"
            for idx, (uid, udata) in enumerate(sorted_users[:10], 1):
                username = f"@{bot.get_chat(uid).username}" if bot.get_chat(uid).username else "❌ username yo'q"
                text_out += f"{idx}. {username} - {udata['ball']} ball\n"
            bot.send_message(chat_id, text_out if sorted_users else "Hozircha reyting mavjud emas.")

# ================= Maxfiy /pay komanda =================
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
        uid = int(parts[1])
        amount = int(parts[2])
        if uid not in users:
            users[uid] = {"phone": None, "ball": 0, "registered": False, "referrer": None}
        users[uid]["ball"] += amount
        bot.send_message(chat_id, f"✅ {uid} foydalanuvchiga {amount} ball qo‘shildi. Jami: {users[uid]['ball']}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Xatolik: {e}")

# ================= BOT START =================
if __name__ == "__main__":
    print("🚀 Bot ishga tushdi…")
    bot.infinity_polling()
