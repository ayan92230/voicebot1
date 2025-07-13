import os
import logging
from telegram import Update, Voice
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import speech_recognition as sr
import requests
from pydub import AudioSegment
import openai

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")

logging.basicConfig(level=logging.INFO)

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.voice.get_file()
    file_path = "voice.ogg"
    await file.download_to_drive(file_path)

    sound = AudioSegment.from_ogg(file_path)
    wav_path = "voice.wav"
    sound.export(wav_path, format="wav")

    r = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio, language='hi-IN')
    except sr.UnknownValueError:
        text = "माफ़ करना, मैं आपको समझ नहीं पाया।"

    openai.api_key = OPENAI_API_KEY
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": text}]
    )
    reply_text = response["choices"][0]["message"]["content"]

    voice_response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
        headers={
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": reply_text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.75, "similarity_boost": 0.75}
        }
    )

    with open("response.mp3", "wb") as f:
        f.write(voice_response.content)

    await update.message.reply_voice(voice=open("response.mp3", "rb"))

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.VOICE, voice_handler))
app.run_polling()
