import os
import json
from dotenv import load_dotenv
import telebot
from telebot import types

# ================= Env =================
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

ADMINS = [7717343429, 1900651840]
PAY_ADMIN = 7717343429

# ================= Fayl va saqlash =================
USERS_FILE = "/mnt/data/users.json"

if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
else:
    users = {}

def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# ================= Sovg'alar =================
photo_file_id = "AgACAgIAAxkBAAPlaL_8Zj819ujsWbOOHdpR193AlkoAArD1MRuYugABSngTwRZxBPimAQADAgADeQADNgQ"

# ================= Kanallar =================
MAJBURIY_CHANNELS = [
    {"id": "@ixtiyor_uc", "name": "Kanal 1"},
    {"id": "@ixtiyor_gaming", "name": "Kanal 2"},
]

OPTIONAL_CHANNELS = [
    {"name": "Kanal 3", "url": "https://t.me/+J60RmZvVVPUyNmJi"},
    {"name": "Instagram", "url": "https://www.instagram.com/ixtiyor_gaming"},
    {"name": "YouTube", "url": "https://youtube.com/@ixtiyorgaming?si=azcra7Wz-TQmUUrM"},
]

# ================= START =================
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = str(message.chat.id)
    args = message.text.split()

    if chat_id not in users:
        users[chat_id] = {"phone": None, "ball": 0, "registered": False, "referrer": None}
        save_users()

    if len(args) > 1:
        try:
            referrer_id = str(int(args[1]))
            if referrer_id != chat_id and not users[chat_id]["registered"]:
                users[chat_id]["referrer"] = referrer_id
                save_users()
        except:
            pass

    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in MAJBURIY_CHANNELS:
        markup.add(types.InlineKeyboardButton(ch["name"], url=f"https://t.me/{ch['id'].replace('@','')}"))
    for ch in OPTIONAL_CHANNELS:
        markup.add(types.InlineKeyboardButton(ch["name"], url=ch["url"]))

    markup.add(types.InlineKeyboardButton("Obuna bo'ldim ✅", callback_data="sub_done"))

    bot.send_message(chat_id,
                     "🚀 Konkursda ishtirok etish uchun quyidagi majburiy kanallarga obuna bo‘ling va 'Obuna bo'ldim ✅' tugmasini bosing",
                     reply_markup=markup)

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = str(call.from_user.id)
    if call.data == "sub_done":
        not_subscribed = []
        for ch in MAJBURIY_CHANNELS:
            try:
                member = bot.get_chat_member(ch["id"], int(chat_id))
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
            contact_button = types.KeyboardButton("📲 Raqamni yuborish", request_contact=True)
            markup.add(contact_button)
            bot.send_message(chat_id, "📲 Raqamingizni yuboring:", reply_markup=markup)
        else:
            bot.send_message(chat_id, "✅ Siz allaqachon ro‘yxatdan o‘tib bo‘lgansiz.")
            main_menu(chat_id)
        bot.answer_callback_query(call.id)

# ================= Kontakt =================
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = str(message.chat.id)
    phone = message.contact.phone_number

    if users[chat_id]["registered"]:
        bot.send_message(chat_id, "❌ Siz allaqachon ro‘yxatdan o‘tib bo‘lgansiz.")
        main_menu(chat_id)
        return

    users[chat_id]["phone"] = phone
    users[chat_id]["registered"] = True

    referrer_id = users[chat_id].get("referrer")
    if referrer_id and referrer_id in users:
        users[referrer_id]["ball"] += 10
        bot.send_message(referrer_id, f"🎉 Sizga yangi do‘st qo‘shildi! +10 ball\nJami: {users[referrer_id]['ball']}")

    save_users()
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

# ================= Text handler =================
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    chat_id = str(message.chat.id)
    text = message.text

    if text == "🔴 Konkursda qatnashish":
        bot.send_message(chat_id,
                         "🎉 Konkursga qatnashish:\n"
                         "1️⃣ Majburiy kanallarga obuna bo‘lishingiz kerak.\n"
                         "2️⃣ ‘Obuna bo'ldim ✅’ tugmasini bosing.\n"
                         "3️⃣ Ro‘yxatdan o‘tish uchun telefon raqamingizni yuboring.\n\n"
                         "Konkurs davomiyligi: 1 oy\n"
                         "Boshlandi: 9 Sentabr\n"
                         "Tugadi: 9 Oktabr"
                         )

    elif text == "🟢 Refeal link":
        bot.send_message(chat_id,
                         f"🔗 Sizning refeal linkingiz: https://t.me/ixtiyor_rp_bot?start={chat_id}\n"
                         "Do‘stlaringiz ushbu havola orqali ro‘yxatdan o‘tsa, siz ball olasiz!"
                         )

    elif text == "🎁 Sovgalar":
        caption = (
            "🎁 Sovgalar:\n"
            "1 - o'rin: Lednik 6 AKK\n"
            "2 - o'rin: LEDNIK 5 AKK\n"
            "3 - o'rin: LEDNIK 4 AKK\n"
            "4-8 o'rin: RP\n"
            "9-19 o'rin: 120 UC\n"
            "20-40 o'rin: 60 UC\n\n"
            "🔥 Konkurs 1 oy davom etadi\n"
            "Boshlandi: 9 Sentabr\n"
            "Tugadi: 9 Oktabr"
        )
        bot.send_photo(chat_id, photo_file_id, caption=caption)

    elif text == "👤 Ballarim":
        bot.send_message(chat_id, f"👤 Sizning ballaringiz: {users.get(chat_id, {}).get('ball', 0)}")

    elif text == "📊 Reyting":
        sorted_users = sorted(users.items(), key=lambda x: x[1]["ball"], reverse=True)
        text_out = "📊 Reyting (hamma foydalanuvchilar):\n"
        count = 0
        for uid, udata in sorted_users:
            try:
                username = f"@{bot.get_chat(int(uid)).username}" if bot.get_chat(int(uid)).username else "❌ username yo'q"
            except:
                username = "❌ username yo'q"
            text_out += f"{count+1}. {username} - {udata['ball']} ball\n"
            count += 1

        for chunk in [text_out[i:i + 4000] for i in range(0, len(text_out), 4000)]:
            bot.send_message(chat_id, chunk)

    elif text == "💡 Shartlar":
        bot.send_message(chat_id,
                         "TANLOV ShARTLARI ✅\n"
                         "❗️ Ballar referral orqali to‘planadi.\n"
                         "⏳ Yakun: 9 Oktabr 20:00\n"
                         "‼️ Nakrutka qilganlar Ban bo‘ladi."
                         )
    else:
        bot.send_message(chat_id, "❌ Noma’lum buyruq")

# ================= /pay =================
@bot.message_handler(commands=['pay'])
def pay_handler(message):
    chat_id = str(message.chat.id)
    if chat_id != str(PAY_ADMIN):
        return

    try:
        parts = message.text.split()
        if len(parts) != 3:
            bot.send_message(chat_id, "❌ To‘g‘ri format: /pay <user_id> <miqdor>")
            return
        uid = str(int(parts[1]))
        amount = int(parts[2])

        if uid not in users:
            users[uid] = {"phone": None, "ball": 0, "registered": False, "referrer": None}

        users[uid]["ball"] += amount
        save_users()
        bot.send_message(chat_id, f"✅ {uid} foydalanuvchiga {amount} ball qo‘shildi. Jami: {users[uid]['ball']}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Xatolik: {e}")

# ================= Botni ishga tushurish =================
bot.infinity_polling()
