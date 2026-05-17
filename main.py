import os
import asyncio
from io import BytesIO

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import google.generativeai as genai
from gtts import gTTS
from duckduckgo_search import DDGS

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash-latest')

# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Kem cho!\nHu Chikku AI Bot chu 🤖\nGujarati ma vaat karo."
    )

# =========================
# GOOGLE SEARCH
# =========================

def search_web(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))

        if not results:
            return "Koi result malyo nathi."

        text = ""

        for r in results:
            text += f"\n🔹 {r['title']}\n{r['body']}\n"

        return text

    except Exception as e:
        return f"Search error: {e}"

# =========================
# TEXT MESSAGE
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_text = update.message.text

    try:
        web_result = search_web(user_text)

        prompt = f"""
        User question:
        {user_text}

        Web data:
        {web_result}

        Gujarati ma short ane useful jawab aapo.
        """

        response = model.generate_content(prompt)

        answer = response.text

        await update.message.reply_text(answer)

        # Voice Reply
        tts = gTTS(answer, lang="gu")

        audio_file = BytesIO()
        tts.write_to_fp(audio_file)

        audio_file.seek(0)

        await update.message.reply_voice(voice=audio_file)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# =========================
# MAIN FUNCTION
# =========================

async def main():

    print("🤖 Chikku bot is running...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    await app.initialize()

    await app.start()

    await app.updater.start_polling()

    while True:
        await asyncio.sleep(1)

# =========================
# RUN BOT
# =========================

if __name__ == "__main__":
    asyncio.run(main())

