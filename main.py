import os
import asyncio
from io import BytesIO
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

import google.generativeai as genai
from gtts import gTTS
from duckduckgo_search import DDGS

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY missing")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

chat_memory = {}


def duckduckgo_search(query):

    try:

        with DDGS() as ddgs:

            results = list(ddgs.text(query, max_results=3))

            if results:

                output = []

                for r in results:

                    title = r.get("title", "")
                    body = str(r.get("body", ""))[:150]

                    output.append(f"• {title}: {body}")

                return "\n".join(output)

    except Exception as e:

        print(e)

    return None


async def speak_voice(text, update):

    try:

        clean_text = text[:250]

        tts = gTTS(
            text=clean_text,
            lang="gu",
            slow=False,
            tld="co.in"
        )

        audio_fp = BytesIO()

        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)

        await update.message.reply_audio(
            audio=audio_fp,
            filename="voice.mp3",
            title="Chikku Voice Reply"
        )

    except Exception as e:

        print(e)

        await update.message.reply_text(text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    chat_memory[user_id] = []

    await update.message.reply_text("Chikku")

    await speak_voice(
        "Kem cho? Hu Chikku, taro digital madadgar.",
        update
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in chat_memory:

        chat_memory[user_id] = []

    if update.message.voice:

        user_text = "Tame voice moklyu."

    elif update.message.photo:

        user_text = "Tame photo moklyu."

    else:

        user_text = update.message.text if update.message.text else ""

    text_lower = user_text.lower()

    if any(word in text_lower for word in [
        "taru name",
        "taro name",
        "chiku",
        "chikku",
        "kon chu"
    ]):

        bot_text = "Haan bhai, maru name Chikku che 😊"

    elif any(word in text_lower for word in [
        "weather",
        "news",
        "market",
        "bhav",
        "samachar"
    ]):

        search_result = duckduckgo_search(user_text + " India")

        if search_result:

            prompt = f"""
User: {user_text}

Live data:
{search_result}

Answer in Gujarati.
"""

        else:

            prompt = f"""
User: {user_text}

Answer in Gujarati.
"""

    else:

        prompt = f"""
User: {user_text}

Answer in Gujarati, friendly and short.
"""

    if 'bot_text' not in locals():

        try:

            response = await asyncio.to_thread(
                model.generate_content,
                prompt
            )

            bot_text = (
                response.text.strip()
                if hasattr(response, "text") and response.text
                else "Mane jawab malyo nathi."
            )

        except Exception as e:

            print(e)

            bot_text = "Error aavyo bhai."

    chat_memory[user_id].append({
        "user": user_text,
        "bot": bot_text
    })

    await speak_voice(bot_text, update)


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            (
                filters.TEXT |
                filters.VOICE |
                filters.PHOTO
            ) & ~filters.COMMAND,
            handle_message
        )
    )

    print("Chikku bot is running...")

    app.run_polling()


if __name__ == "__main__":

    main()
