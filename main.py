import os
from dotenv import load_dotenv
import telebot
from telebot import types

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# ================= Sovg'alar rasmi =================
photo_file_id = "AgACAgIAAxkBAAPlaL_8Zj819ujsWbOOHdpR193AlkoAArD1MRuYugABSngTwRZxBPimAQADAgADeQADNgQ"

# ================= Majburiy kanallar =================
MAJBURIY_CHANNELS = [
    {"id": "@ixtiyor_uc", "name": "Kanal 1"},
    {"id": "@ixtiyor_gaming", "name": "Kanal 2"},
]

# ================= Qo‘shimcha kanallar (tekshirilmaydi) =================
OPTIONAL_CHANNELS = [
    {"name": "Kanal 3", "url": "https://t.me/+J60RmZvVVPUyNmJi"},
    {"name": "Instagram", "url": "https://www.instagram.com/ixtiyor_gaming"},
    {"name": "YouTube", "url": "https://youtube.com/@ixtiyorgaming?si=azcra7Wz-TQmUUrM"},
]

# ================= Adminlar =================
ADMINS = [7717343429, 1900651840]
PAY_ADMIN = 7717343429  # faqat shu odam /pay ishlatadi

# ================= Xotirada saqlash =================
users = {}  # {user_id: {"phone": str, "ball": int, "registered": bool, "referrer": int}}

# ================= START handler (referal bilan) =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    args = message.text.split()

    # Agar user ro‘yxatda bo‘lmasa, yaratamiz
    if chat_id not in users:
        users[chat_id] = {"phone": None, "ball": 0, "registered": False, "referrer": None}

    # Referral orqali kirgan bo‘lsa
    if len(args) > 1:
        referrer_id = int(args[1])
        if referrer_id != chat_id and not users[chat_id]["registered"]:
            users[chat_id]["referrer"] = referrer_id

    markup = types.InlineKeyboardMarkup(row_width=1)

    # Majburiy kanallar
    for ch in MAJBURIY_CHANNELS:
        markup.add(types.InlineKeyboardButton(ch["name"], url=f"https://t.me/{ch['id'].replace('@','')}"))

    # Ixtiyoriy kanallar
    for ch in OPTIONAL_CHANNELS:
        markup.add(types.InlineKeyboardButton(ch["name"], url=ch["url"]))

    markup.add(types.InlineKeyboardButton("Obuna bo'ldim ✅", callback_data="sub_done"))

    bot.send_message(
        chat_id,
        "🚀 Konkursda ishtirok etish uchun quyidagi majburiy kanallarga obuna bo‘ling va 'Obuna bo'ldim ✅' tugmasini bosing",
        reply_markup=markup
    )

# ================= CALLBACK handler =================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.from_user.id
    if call.data == "sub_done":
        # Faqat majburiylarni tekshiramiz
        not_subscribed = []
        for ch in MAJBURIY_CHANNELS:
            try:
                member = bot.get_chat_member(ch["id"], chat_id)
                if member.status not in ["member", "administrator", "creator"]:
                    not_subscribed.append(ch["name"])
            except:
                not_subscribed.append(ch["name"])

        if not_subscribed:
            bot.answer_callback_query(call.id, "❌ Siz barcha majburiy kanallarga obuna bo‘lmadingiz!")
            bot.send_message(chat_id, "⛔️ Quyidagi kanallarga obuna bo‘ling:\n" + "\n".join(not_subscribed))
            return

        # Agar oldin ro‘yxatdan o‘tmagan bo‘lsa, raqamni so‘raymiz
        if not users[chat_id]["registered"]:
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

    if users[chat_id]["registered"]:
        bot.send_message(chat_id, "❌ Siz allaqachon ro‘yxatdan o‘tib bo‘lgansiz.")
        return

    users[chat_id]["phone"] = phone
    users[chat_id]["registered"] = True

    # Referrenga ball qo‘shamiz (faqat yangi ro‘yxatdan o‘tganda)
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
        ball = users.get(chat_id, {}).get("ball", 0)
        bot.send_message(chat_id, f"👤 Sizning ballaringiz: {ball}")

    elif text == "📊 Reyting":
        sorted_users = sorted(users.items(), key=lambda x: x[1]["ball"], reverse=True)

        if chat_id in ADMINS:
            # Adminlarga Top 38
            text_out = "📊 Top 38 Reyting (Adminlar uchun):\n"
            for idx, (uid, udata) in enumerate(sorted_users[:38], 1):
                username = f"@{bot.get_chat(uid).username}" if bot.get_chat(uid).username else "❌ username yo'q"
                text_out += f"{idx}. {uid} {username} - {udata['ball']} ball\n"
            bot.send_message(chat_id, text_out if sorted_users else "Hozircha reyting mavjud emas.")
        else:
            # Oddiy userlarga Top 10
            text_out = "📊 Top 10 Reyting:\n"
            for idx, (uid, udata) in enumerate(sorted_users[:10], 1):
                text_out += f"{idx}. {uid} - {udata['ball']} ball\n"
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
        link = f"https://t.me/ixtiyor_rp_bot?start={chat_id}"
        bot.send_message(chat_id, f"🔗 Sizning referral linkingiz:\n{link}\n\nDo'stlaringizga yuboring!")

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

# ================= Botni ishga tushurish =================
bot.infinity_polling()
