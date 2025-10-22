import os
import json
import wave
import tempfile
import numpy as np
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from gtts import gTTS
from openai import OpenAI
from dotenv import load_dotenv
import psycopg2

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

# ====== Initializing ======
client = OpenAI(api_key=OPENAI_API_KEY)
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS dialog_history (
    id SERIAL PRIMARY KEY,
    role TEXT,
    content TEXT
);
""")
conn.commit()

# ====== Kazakh Speech Model (Vosk) ======
MODEL_PATH = "vosk-model-small-kz-0.42"
print("🔄 Vosk моделін жүктеу...")
model = Model(MODEL_PATH)
print("✅ Қазақ тілі моделі сәтті жүктелді!")

# ====== DB functions ======
def save_message(role, content):
    cursor.execute("INSERT INTO dialog_history (role, content) VALUES (%s, %s)", (role, content))
    conn.commit()

# ====== Recording ======
def record_voice(duration=5, fs=44100):
    print("🎙️ Дыбыс жазылуда...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
    sd.wait()
    filename = tempfile.mktemp(prefix="voice_", suffix=".wav")
    with wave.open(filename, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(fs)
        f.writeframes(audio.tobytes())
    return filename

# ====== Transcribing (Vosk) ======
def transcribe_audio_vosk(filename):
    wf = wave.open(filename, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())

    text_result = ""
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text_result += result.get("text", "") + " "
    final = json.loads(rec.FinalResult())
    text_result += final.get("text", "")
    return text_result.strip()

# ====== Voice the text ======
def speak_kz(text):
    print("🔊 Jarvis сөйлеп жатыр (OpenAI TTS)...")
    speech = tempfile.mktemp(suffix=".wav")
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    ) as response:
        response.stream_to_file(speech)

    os.system(f"mpg123 {speech}")


# ====== Jarvis replying ======
def chat_with_jarvis(prompt):
    save_message("user", prompt)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Сен Jarvis есімді қазақ тілінде сөйлейтін жасанды интеллектісің. Пайдаланушыға тек қазақша жауап бер. Егер сұрақ ағылшынша болса, оны қазақша аударып түсіндір."},
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content
    save_message("assistant", answer)
    return answer

# ====== Main loop ======
print("🤖 Jarvis v0.2 (Қазақша) іске қосылды!")
print("Айтқыңыз келгенді айтыңыз (немесе 'шығу' деп аяқтаңыз).")

while True:
    filename = record_voice(duration=5)
    text = transcribe_audio_vosk(filename)

    if not text:
        print("❌ Сөз танылмады, қайтадан айтыңыз.")
        continue

    if text.lower() in ["шығу", "exit", "stop"]:
        print("Jarvis: Көріскенше сау бол! 👋")
        break

    print("🧍‍♂️ Сіз:", text)
    reply = chat_with_jarvis(text)
    print("🤖 Jarvis:", reply)
    speak_kz(reply)
