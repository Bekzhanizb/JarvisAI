import os
import json
import wave
import tempfile
import numpy as np
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from scipy.signal import resample
from gtts import gTTS
from openai import OpenAI
from dotenv import load_dotenv
import time
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
MODEL_PATH = "vosk-model-kz-0.42"
print("🔄 Vosk моделін жүктеу...")
model = Model(MODEL_PATH)
print("✅ Қазақ тілі моделі сәтті жүктелді!")

# ====== DB functions ======
def save_message(role, content):
    cursor.execute("INSERT INTO dialog_history (role, content) VALUES (%s, %s)", (role, content))
    conn.commit()

# ===== Session memory =====

session_history = []

# ====== Auto Select Microphone ======

def auto_select_microphone():
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            sd.default.device = i
            print(f"Микрофон таңдалды: {dev['name']}")
            return
    raise Exception("Микрофон табылмады!")

# ===== Valid Sample Rate =====

def get_valid_sample_rate():
    device = sd.query_devices(sd.default.device, 'input')
    rates = [16000, 32000, 44100, 48000]

    for r in rates:
        try:
            sd.check_input_settings(samplerate=r, channels=1)
            print(f"🎚 Микрофон {r} Hz жиілігін қолдайды")
            return r
        except:
            continue

    raise Exception("❌ Микрофон үшін қолайлы sample rate табылмады.")


# ===== Main values =====

auto_select_microphone()  #Auto selecting Microphone

MIC_RATE = get_valid_sample_rate() #Microphone Rate(Hz)

# ====== Recording ======

def record_voice_auto(fs=MIC_RATE,
                      silence_threshold=500,
                      silence_limit=1.2,
                      max_wait_before_speech=10):
    print("🎙 Күту режимі: дауысты 10 секунд ішінде анықтау...")

    recording = []
    chunk_duration = 0.1
    chunk_size = int(fs * chunk_duration)

    silent_time = 0
    active_speech_detected = False
    start_wait = time.time()

    while True:
        chunk = sd.rec(chunk_size, samplerate=fs, channels=1, dtype=np.int16)
        sd.wait()
        amplitude = abs(chunk).mean()

        if not active_speech_detected:
            if amplitude > silence_threshold:
                print("🎤 Дауыc анықталды!")
                active_speech_detected = True
                recording.append(chunk)
            else:
                if time.time() - start_wait >= max_wait_before_speech:
                    print("⏳ 10 секунд ішінде дауыс болмады. Jarvis өшіріледі.")
                    return None
                continue
        else:
            recording.append(chunk)

            if amplitude < silence_threshold:
                silent_time += chunk_duration
            else:
                silent_time = 0

            if silent_time >= silence_limit:
                print("🔇 Тыныштық анықталды — жазу тоқтады.")
                break

    audio_data = np.concatenate(recording, axis=0)

    # --- Resampling 16kHz ---
    if fs != 16000:
        target_length = int(len(audio_data) * 16000 / fs)
        audio_data = resample(audio_data, target_length).astype(np.int16)
        fs = 16000

    filename = tempfile.mktemp(prefix="voice_", suffix=".wav")
    with wave.open(filename, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(fs)
        f.writeframes(audio_data.tobytes())

    return filename


# ====== Transcribing (Vosk) ======
def transcribe_audio_vosk(filename):
    wf = wave.open(filename, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())

    full_text = ""

    while True:
        data = wf.readframes(8000)
        if len(data) == 0:
            break

        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "")
            full_text += text + " "

    # Final result
    final = json.loads(rec.FinalResult())
    final_text = final.get("text", "")

    result_text = (full_text + " " + final_text).strip()
    return result_text



# ====== Voice the text ======

def speak_kz(text):
    print("🔊 Jarvis сөйлеп жатыр (Kazakh Male Adaptive Voice)...")
    speech_path = tempfile.mktemp(suffix=".wav")

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="onyx",  # Male Basic Voice
        input=text,
        extra_body={
            "format": "wav",

            # Adaptive Voice Parameters
            "speed": 1.0,            # the pace of speech will adjust itself.
            "pitch": "auto",            # the pitch of the voice adapts to the context
            "emotion": "auto",          # emotion depends on the text
            "intonation": "auto",       # automatic intonation
            "natural_pauses": True,     # natural pauses
            "emphasis": "balanced",     # a pleasant and soft accent
            "clarity": "high"           # voice clarity
        }
    ) as response:
        response.stream_to_file(speech_path)

    os.system(f"mpg123 {speech_path}")




# ====== Jarvis replying ======

def chat_with_jarvis(prompt):

    session_history.append({"role": "user", "content": prompt}) #Save user message in session

    save_message("user", prompt) #Save message to PostgreSQL

    messages = [{"role": "system",
                 "content": "Сен Jarvis есімді қазақ тілінде сөйлейтін жасанды интеллектісің. Пайдаланушыға тек қазақша жауап бер. Контекстті осы сеанста сақтау."}
                ] + session_history  #Build messages for the model

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    answer = response.choices[0].message.content

    session_history.append({"role": "assistant", "content": answer})
    save_message("assistant", answer) #Save assistant reply

    return answer

# ====== Main loop ======
print("🤖 Jarvis v0.2 (Қазақша) іске қосылды!")
print("Айтқыңыз келгенді айтыңыз (немесе 'шығу' деп аяқтаңыз).")

while True:
    filename = record_voice_auto()

    if filename is None:
        break  # auto-exit

    text = transcribe_audio_vosk(filename)

    if not text:
        print("Сөз танылмады, қайтадан айтыңыз.")
        continue

    if text.lower() in ["шығу", "exit", "stop"]:
        print("Jarvis: Көріскенше сау бол! 👋")
        break

    print("Сіз:", text)
    reply = chat_with_jarvis(text)
    print("🤖 Jarvis:", reply)
    speak_kz(reply)

