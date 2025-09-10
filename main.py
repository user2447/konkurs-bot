., [9/10/2025 10:53 PM]
# ================= Kontakt qabul qilish =================
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = str(message.chat.id)
    phone = message.contact.phone_number

    if users[chat_id]["registered"]:
        bot.send_message(chat_id, "❌ Siz allaqachon ro‘yxatdan o‘tib bo‘lgansiz.")
        return

    users[chat_id]["phone"] = phone
    users[chat_id]["registered"] = True
    save_users()

    referrer_id = users[chat_id].get("referrer")
    if referrer_id and referrer_id in users:
        users[referrer_id]["ball"] += 10
        save_users()
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

# ================= Tugmalar handleri =================
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    chat_id = str(message.chat.id)
    text = message.text

    if text == "🔴 Konkursda qatnashish":
        bot.send_message(chat_id,
        "Ixtiyor konkurs bot o'zining konkursiga start berdi\n"
        "Qatnashing va sovgalarni qo'lga kiriting 😍\n\n"
        "1 - o'rin: Lednik 6 AKK\n"
        "2 - o'rin: Lednik 5 AKK\n"
        "3 - o'rin: Lednik 4 AKK\n"
        "4-8 o'rin: RP\n"
        "9-19 o'rin: 120 UC\n"
        "20-40 o'rin: 60 UC\n\n"
        "🔥 Konkurs 1 oy davom etadi.\n"
        "Boshlandi: 9 Sentabr\n"
        "Tugashi: 9 Oktabr\n\n"
        f"Sizning ishtirok linkingiz: https://t.me/ixtiyor_rp_bot?start={chat_id}"
        )

    elif text == "🎁 Sovgalar":
        caption_text = (
            "🎁 Konkurs Sovgalari:\n\n"
            "🥇 1-o‘rin: Lednik 6 AKK\n"
            "🥈 2-o‘rin: Lednik 5 AKK\n"
            "🥉 3-o‘rin: Lednik 4 AKK\n"
            "4-8 o‘rin: RP\n"
            "9-19 o‘rin: 120 UC\n"
            "20-40 o‘rin: 60 UC\n"
        )
        bot.send_photo(chat_id, photo_file_id, caption=caption_text)

    elif text == "🟢 Refeal link":
        link = f"https://t.me/ixtiyor_rp_bot?start={chat_id}"
        bot.send_message(chat_id, f"🔗 Sizning referral linkingiz:\n{link}\n\nDo'stlaringizga yuboring!")

    elif text == "👤 Ballarim":
        ball = users.get(chat_id, {}).get("ball", 0)
        bot.send_message(chat_id, f"👤 Sizning ballaringiz: {ball}")

    elif text == "📊 Reyting":
        sorted_users = sorted(users.items(), key=lambda x: x[1]["ball"], reverse=True)
        if chat_id in [str(a) for a in ADMINS]:
            text_out = "📊 To‘liq Reyting (Adminlar uchun):\n"
            for idx, (uid, udata) in enumerate(sorted_users, 1):
                try:
                    username = f"@{bot.get_chat(int(uid)).username}" if bot.get_chat(int(uid)).username else "❌ username yo'q"
                except:
                    username = "❌ username yo'q"
                text_out += f"{idx}. {uid} {username} - {udata['ball']} ball\n"

            for chunk in [text_out[i:i+4000] for i in range(0, len(text_out), 4000)]:
                bot.send_message(chat_id, chunk)

        else:
            text_out = "📊 Top 10 Reyting:\n"
            for idx, (uid, udata) in enumerate(sorted_users[:10], 1):
                try:

., [9/10/2025 10:53 PM]
username = f"@{bot.get_chat(int(uid)).username}" if bot.get_chat(int(uid)).username else "❌ username yo'q"
                except:
                    username = "❌ username yo'q"
                text_out += f"{idx}. {username} - {udata['ball']} ball\n"
            bot.send_message(chat_id, text_out if sorted_users else "Hozircha reyting mavjud emas.")

    elif text == "💡 Shartlar":
        bot.send_message(chat_id,
        "💡 Konkurs Shartlari:\n\n"
        "❗ G'oliblar random emas, to'plagan ballariga qarab aniqlanadi.\n"
        "❗ Har bir referral orqali kirgan do'stlaringiz uchun 10 ball qo'shiladi.\n"
        "⏳ Konkurs 9 Oktabr 20:00 da tugaydi.\n"
        "❗ Nakrutka qilganlar ban bo'ladi.\n"
        "✅ Majburiy kanallarga a'zo bo'lish sharti mavjud.\n"
        "🙂 Faol bo'ling, mukofotlarni qo'lga kiriting."
        )

# ================= Maxfiy /pay komanda =================
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
