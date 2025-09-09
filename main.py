import telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")  # hostingdan oladi
bot = telebot.TeleBot(TOKEN)

users = {}  # foydalanuvchi ma'lumotlari
referrals = {}  # referral tracking

# Sovg'alar rasmi uchun file_id (botdan rasm yuborib olgan file_id yoziladi)
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


# Rasm yuborganda file_id olish
@bot.message_handler(content_types=['photo'])
def get_file_id(message):
    file_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, f"📷 Siz yuborgan rasmning file_id si:\n{file_id}")


# Start komandasi
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    args = message.text.split()

    # Referral logika
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id in users and chat_id not in users:
                users[ref_id]["ball"] += 10
                bot.send_message(ref_id, f"🎉 Sizga +10 ball qo'shildi! Jami: {users[ref_id]['ball']}")
        except:
            pass

    # Agar foydalanuvchi ro'yxatdan o'tgan bo'lsa, menyuga qaytariladi
    if chat_id in users and users[chat_id].get("registered", False):
        main_menu(chat_id)
        return

    # Tugmalar
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
        "🚀 Konkursda ishtirok etish uchun quyidagi **1, 2- kanallarga** obuna bo‘ling va “Obuna bo‘ldim ✅” tugmasini bosing.\n\n"
        "⚠️ Instagram va YouTube ixtiyoriy.",
        reply_markup=markup
    )


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


# Kontakt qabul qilish
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number

    users[chat_id] = {
        "phone": phone,
        "ball": 0,
        "registered": True
    }
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
        score = users.get(chat_id, {}).get("ball", 0)
        bot.send_message(chat_id, f"👤 Sizning ballaringiz: {score}")

    elif text == "📊 Reyting":
        top_users = sorted(users.items(), key=lambda x: x[1].get("ball",0), reverse=True)[:10]
        text_msg = "📊 Top 10 Reyting:\n"
        for i, (uid, data) in enumerate(top_users, start=1):
            text_msg += f"{i}. {uid} - {data.get('ball',0)} ball\n"
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
