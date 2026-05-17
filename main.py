import os
import asyncio
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
import google.generativeai as genai
from gtts import gTTS
from duckduckgo_search import DDGS

# API Keys - Render Environment Variables mathi
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
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
                    title = r.get('title', '')
                    body = r.get('body', '')[:150]
                    output.append(f"• {title}: {body}")
                return "\n".join(output)
    except:
        pass
    return None

async def speak_voice(text, update):
    try:
        clean_text = text[:250]
        tts = gTTS(text=clean_text, lang='gu', slow=False, tld='co.in')
        audio_fp = BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        await update.message.reply_voice(voice=audio_fp, filename="voice.ogg")
    except:
        await update.message.reply_text(text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_memory[user_id] = []
    await update.message.reply_text("Chikku")
    await speak_voice("Kem cho? Hu Chikku, taro digital madadgar.", update)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in chat_memory:
        chat_memory[user_id] = []
    
    if update.message.voice:
        user_text = "Tame voice moklyu, hu samjyo."
    elif update.message.photo:
        user_text = "Tame photo moklyu, hu joi lidhu."
    else:
        user_text = update.message.text
    
    text_lower = user_text.lower()
    
    if any(word in text_lower for word in ['taru name', 'taro name', 'chiku', 'chikku', 'kon chu']):
        bot_text = "Haan bhai, maru name Chikku che 😊 Hu taro digital madadgar chu."
    elif any(word in text_lower for word in ['havaman', 'weather', 'stock', 'market', 'news', 'samachar', 'rate', 'bhav', 'aaj na', 'aaj nu']):
        search_result = duckduckgo_search(user_text + " India")
        if search_result:
            prompt = f"User: {user_text}\n\nLive data from web:\n{search_result}\n\nAnswer in Gujarati, short, friendly, 2-3 lines."
        else:
            prompt = f"User: {user_text}\n\nAnswer in Gujarati. If you can't find data, say to check Google."
    else:
        prompt = f"User: {user_text}\n\nAnswer in Gujarati, short, friendly, 2-3 lines."
    
    if 'bot_text' not in locals():
        try:
            response = await asyncio.to_thread(model.generate_content, prompt)
            bot_text = response.text
        except Exception as e:
            if "429" in str(e):
                bot_text = duckduckgo_search(user_text + " India") or "Thodi vaar pachi puch bhai, Google ni limit puri thai."
            else:
                bot_text = "Error aavyo, pachi try kar."
    
    chat_memory[user_id].append({"user": user_text, "bot": bot_text})
    await speak_voice(bot_text, update)

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    print("Chikku bot is running...")
    await app.run_polling()  # <- aa `await` must che

if __name__ == '__main__':
    asyncio.run(main())
  git add main.py
  git commit -m "Fix async main" 
  git push origin main
