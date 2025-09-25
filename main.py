import os

import openai
import psycopg2
import sounddevice as sd
import numpy as np
import tempfile
import wave
from openai import OpenAI
from dotenv import load_dotenv
import soundfile as sf
from gtts import gTTS
import re

# ====== Parameters ======
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


DB_CONFIG = {
    "dbname": "shyraq_db",
    "user": "postgres",
    "password": "1234",
    "host": "localhost",
    "port": 5432
}

# ====== Connection ======
client = OpenAI(api_key=OPENAI_API_KEY)

conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Table to save conversations
cursor.execute("""
CREATE TABLE IF NOT EXISTS dialog_history (
    id SERIAL PRIMARY KEY,
    role TEXT,
    content TEXT
);
""")
conn.commit()

# ====== DB Functions ======
def save_message(role, content):
    cursor.execute("INSERT INTO dialog_history (role, content) VALUES (%s, %s)", (role, content))
    conn.commit()

# ====== Audio Functions =====
def record_voice(duration=5, fs=44100):
    print("Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
    sd.wait()
    filename = tempfile.mktemp(prefix="voice_", suffix=".wav")
    with wave.open(filename, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(fs)
        f.writeframes(audio.tobytes())
    return filename

def transcribe_audio(filename):
    with open(filename, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f,
        )
    return transcription.text

def speak(text):
    lang = detect_lang(text)
    if lang == "ru":
        # Russian speech with gTTS
        tts = gTTS(text=text, lang="ru")
        speech = tempfile.mktemp(suffix=".mp3")
        tts.save(speech)
        os.system(f"mpg123 {speech}")  # или sounddevice
    else:
        # The English speech
        speech = tempfile.mktemp(suffix=".wav")
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text
        ) as response:
            response.stream_to_file(speech)
        os.system(f"mpg123 {speech}")


# ====== Detect Language =====

def detect_lang(text):
    if re.search(r'[а-яА-Я]', text):
        return "ru"
    else:
        return "en"

# ====== Chat ======
def chat_with_jarvis(prompt):
    save_message("user", prompt)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "You are AI Jarvis. Always respond in the same language as the user (English or Russian). Be clear and friendly."},
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content
    save_message("assistant", answer)
    return answer

# ====== Main loops ======
print("🤖 Jarvis v0.1 started! Write something to get answer (or 'exit' to quit).")

while True:

    filename = record_voice(duration=5)
    text = transcribe_audio(filename)

    if text.lower() in ["exit", "quit"]:
        print("Jarvis: Goodbye, sir 👋")
        break

    print("You: ", text)
    reply = chat_with_jarvis(text)
    print("Jarvis:", reply)
    speak(reply)
