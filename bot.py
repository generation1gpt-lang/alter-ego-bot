import random
import os
import requests
from groq import Groq
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ── ВСТАВЬ СЮДА СВОИ КЛЮЧИ ──────────────────────────────
BOT_TOKEN       = "8736013835:AAFs6vQn2msbbLrGetETMbU_HR7z6E0W49w"
GROQ_KEY        = "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"
ELEVEN_KEY      = "sk_cca338852398764db67b71af1b427cd9e733f3113e3f5e1a"
ELEVEN_VOICE_ID = "hpsx71m2z77a1un8xcL2"
# ────────────────────────────────────────────────────────

TRIGGER_WORDS = ["даник", "даниил", "danik", "daniil", "данил"]
CASINO_WORDS  = ["казино", "casino"]
VOICE_TRIGGERS = [
    "голосом", "голосовуху", "голосовое", "давай голос",
    "го голосовуху", "запиши", "скажи голосом", "войс",
    "voice", "запиши голосом", "давай войс"
]

MY_PROFILE = """
Ты — Даник, живой парень ~20 лет. Не бот, не ассистент — реальный чел в чате.

ГЛАВНОЕ ПРАВИЛО: всегда читай контекст и отвечай по ситуации. Не шпаришь скриптами — реагируешь на то что реально написали.

ХАРАКТЕР:
- Дерзкий, с юмором, не обижаешься на подколы — отвечаешь в ответ
- Если тебя оскорбили или подкалывают — подкалываешь обратно, можешь послать но по-дружески
- Если спрашивают по делу — отвечаешь по делу, но со своим стилем
- Умный, разбираешься в CS, бизнесе, ютубе, AI, блогинге
- Не обижаешься, не ноешь, не оправдываешься

СТИЛЬ:
- Скобочки вместо эмодзи: ) )) ))) — не больше трёх
- Коротко если простой вопрос, длиннее если тема серьёзная
- Сленг: "лол", "ну типа", "гатила", "шнеле", "пепе фаааа", "ну вообще то"
- Никаких настоящих эмодзи — только скобочки
- Никогда не начинаешь с "Конечно!", "Отличный вопрос!", "Я понимаю"

КОГДА ОТВЕЧАЕШЬ ГОЛОСОВЫМ — говори естественно, без скобочек, как будто реально записываешь войс. Живо, с интонацией, можешь мычать "ну типа", "короче", паузы.
"""

client = Groq(api_key=GROQ_KEY)
histories = {}
game_states = {}
message_counters = {}  # счётчик сообщений для каждого чата

# ── ГОЛОСОВОЕ СООБЩЕНИЕ ──────────────────────────────────

async def send_voice(update: Update, text: str):
    """Генерирует голосовое через ElevenLabs и отправляет в Telegram"""
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVEN_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.4,
                "similarity_boost": 0.85,
                "style": 0.3,
                "use_speaker_boost": True
            }
        }
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            audio_path = "/tmp/voice_reply.mp3"
            with open(audio_path, "wb") as f:
                f.write(response.content)
            with open(audio_path, "rb") as audio:
                await update.message.reply_voice(voice=audio)
            os.remove(audio_path)
            return True
        else:
            print(f"ElevenLabs error: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"Voice error: {e}")
        return False

def is_voice_request(text: str) -> bool:
    text_lower = text.lower()
    return any(trigger in text_lower for trigger in VOICE_TRIGGERS)

# ── КАЗИНО ───────────────────────────────────────────────

def casino_menu():
    keyboard = [
        [InlineKeyboardButton("🎰 Слоты", callback_data="game_slots")],
        [InlineKeyboardButton("🔴 Красное / Чёрное", callback_data="game_roulette")],
        [InlineKeyboardButton("🎯 Угадай число (1-10)", callback_data="game_number")],
        [InlineKeyboardButton("🃏 Больше или меньше", callback_data="game_cards")],
        [InlineKeyboardButton("🪙 Орёл или решка", callback_data="game_coin")],
    ]
    return InlineKeyboardMarkup(keyboard)

def slots_spin():
    symbols = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    line = " | ".join(result)
    if result[0] == result[1] == result[2]:
        if result[0] == "💎":
            return line, "ДЖЕКПОТ гатила!!! ты богач теперь))"
        elif result[0] == "7️⃣":
            return line, "777!! лол гатила выиграл серьёзно))"
        else:
            return line, "три одинаковых! повезло))"
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        return line, "два одинаковых, почти, ещё раз)"
    else:
        return line, "нихт гатила, попробуй ещё)"

async def handle_casino_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user.first_name or "гатила"

    if data == "game_slots":
        line, msg = slots_spin()
        await query.edit_message_text(
            f"🎰 крутим...\n\n[ {line} ]\n\n{msg}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎰 Ещё раз", callback_data="game_slots")],
                [InlineKeyboardButton("↩️ Меню", callback_data="casino_menu")],
            ])
        )
    elif data == "game_roulette":
        await query.edit_message_text(
            f"🎡 рулетка, {user}, ставь:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔴 Красное", callback_data="roulette_red"),
                 InlineKeyboardButton("⚫ Чёрное", callback_data="roulette_black")]
            ])
        )
    elif data in ["roulette_red", "roulette_black"]:
        colors = ["🔴"] * 18 + ["⚫"] * 18 + ["🟢"]
        result = random.choice(colors)
        chosen = "🔴" if data == "roulette_red" else "⚫"
        if result == chosen:
            msg = f"выпало {result} — угадал, красавчик))"
        elif result == "🟢":
            msg = f"выпало 🟢 зеро — казино wins лол))"
        else:
            msg = f"выпало {result} — мимо гатила)"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎡 Ещё раз", callback_data="game_roulette")],
            [InlineKeyboardButton("↩️ Меню", callback_data="casino_menu")],
        ]))
    elif data == "game_coin":
        await query.edit_message_text(
            f"🪙 монетка, {user}, выбирай:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🦅 Орёл", callback_data="coin_heads"),
                 InlineKeyboardButton("🪙 Решка", callback_data="coin_tails")]
            ])
        )
    elif data in ["coin_heads", "coin_tails"]:
        result = random.choice(["heads", "tails"])
        result_text = "🦅 Орёл" if result == "heads" else "🪙 Решка"
        chosen = "heads" if data == "coin_heads" else "tails"
        msg = f"выпал {result_text} — {'угадал)' if result == chosen else 'мимо гатила)'}"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🪙 Ещё раз", callback_data="game_coin")],
            [InlineKeyboardButton("↩️ Меню", callback_data="casino_menu")],
        ]))
    elif data == "game_number":
        secret = random.randint(1, 10)
        game_states[query.from_user.id] = secret
        buttons = [
            [InlineKeyboardButton(str(i), callback_data=f"number_{i}") for i in range(1, 6)],
            [InlineKeyboardButton(str(i), callback_data=f"number_{i}") for i in range(6, 11)]
        ]
        await query.edit_message_text(
            f"🎯 загадал число 1-10, {user}, угадывай:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data.startswith("number_"):
        guess = int(data.split("_")[1])
        secret = game_states.get(query.from_user.id, random.randint(1, 10))
        if guess == secret:
            msg = f"🎯 УГАДАЛ!! было {secret}, красавчик гатила))"
        else:
            msg = f"🎯 мимо) было {secret}, ты поставил {guess}"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎯 Ещё раз", callback_data="game_number")],
            [InlineKeyboardButton("↩️ Меню", callback_data="casino_menu")],
        ]))
    elif data == "game_cards":
        first = random.randint(1, 10)
        await query.edit_message_text(
            f"🃏 твоя карта: *{first}*\nследующая больше или меньше?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬆️ Больше", callback_data=f"cards_higher_{first}"),
                 InlineKeyboardButton("⬇️ Меньше", callback_data=f"cards_lower_{first}")]
            ])
        )
    elif data.startswith("cards_"):
        parts = data.split("_")
        direction, prev = parts[1], int(parts[2])
        nxt = random.randint(1, 10)
        win = (direction == "higher" and nxt > prev) or (direction == "lower" and nxt < prev)
        if nxt == prev:
            msg = f"🃏 выпало {nxt} — ничья гатила)"
        elif win:
            msg = f"🃏 выпало {nxt} — угадал красавчик))"
        else:
            msg = f"🃏 выпало {nxt} — мимо, не повезло)"
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🃏 Ещё раз", callback_data="game_cards")],
            [InlineKeyboardButton("↩️ Меню", callback_data="casino_menu")],
        ]))
    elif data == "casino_menu":
        await query.edit_message_text(
            "казино открыто гатила) выбирай:",
            reply_markup=casino_menu()
        )

# ── ОСНОВНОЙ ОБРАБОТЧИК ──────────────────────────────────

def should_reply(update: Update, bot_username: str) -> bool:
    msg = update.message
    text = (msg.text or "").lower()
    chat_type = msg.chat.type

    if chat_type == "private":
        return True
    if msg.entities:
        for entity in msg.entities:
            if entity.type == "mention":
                mention = msg.text[entity.offset:entity.offset + entity.length].lower()
                if mention == f"@{bot_username.lower()}":
                    return True
    if msg.reply_to_message and msg.reply_to_message.from_user:
        if msg.reply_to_message.from_user.username == bot_username:
            return True
    for word in TRIGGER_WORDS + CASINO_WORDS + VOICE_TRIGGERS:
        if word in text:
            return True
    return False

async def get_ai_reply(chat_id: int, user_name: str, user_text: str, voice_mode: bool = False) -> str:
    if chat_id not in histories:
        histories[chat_id] = [{"role": "system", "content": MY_PROFILE}]

    prompt = user_text
    if voice_mode:
        prompt = f"{user_text}\n\n[Ответь как будто записываешь голосовое сообщение — разговорно, живо, без скобочек, можешь использовать 'короче', 'ну типа', паузы обозначай через '...']"

    histories[chat_id].append({
        "role": "user",
        "content": f"{user_name} пишет тебе: {prompt}"
    })

    if len(histories[chat_id]) > 21:
        histories[chat_id] = [histories[chat_id][0]] + histories[chat_id][-20:]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=histories[chat_id],
        max_tokens=400,
        temperature=0.95,
    )

    reply = response.choices[0].message.content
    histories[chat_id].append({"role": "assistant", "content": reply})
    return reply

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    bot_username = context.bot.username
    if not should_reply(update, bot_username):
        return

    chat_id = update.effective_chat.id
    user_text = update.message.text
    user_name = update.message.from_user.first_name or "гатила"

    # Казино
    if any(word in user_text.lower() for word in CASINO_WORDS):
        await update.message.reply_text(
            "казино открыто гатила) выбирай игру:",
            reply_markup=casino_menu()
        )
        return

    # Получаем AI ответ
    voice_requested = is_voice_request(user_text)

    # Считаем сообщения для авто-голосового каждые 7
    message_counters[chat_id] = message_counters.get(chat_id, 0) + 1
    auto_voice = (message_counters[chat_id] % 7 == 0)

    use_voice = voice_requested or auto_voice

    reply = await get_ai_reply(chat_id, user_name, user_text, voice_mode=use_voice)

    if use_voice:
        success = await send_voice(update, reply)
        if not success:
            # Если голосовое не получилось — отправляем текстом
            await update.message.reply_text(reply + "\n\n_(голосовое не удалось, вот текстом)_", parse_mode="Markdown")
    else:
        await update.message.reply_text(reply)

def main():
    print("✦ Alter Ego (Даник) запущен.")
    print(f"✦ Триггеры чат: {', '.join(TRIGGER_WORDS)}")
    print(f"✦ Триггеры голос: {', '.join(VOICE_TRIGGERS)}")
    print("✦ Авто-голосовое каждые 7 сообщений")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_casino_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
