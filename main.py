from audio.microphone import auto_select_microphone, get_valid_sample_rate
from audio.recorder import record_voice_auto
from audio.stt_vosk import transcribe
from audio.tts import speak_kz
from ai.chat import chat


print("🤖 Jarvis v0.3 started")


auto_select_microphone()
MIC_RATE = get_valid_sample_rate()

while True:
    wav = record_voice_auto(MIC_RATE)
    if not wav:
        break

    text = transcribe(wav)
    if not text:
        continue

    if text.lower() in ["шығу", "exit", "stop"]:
        break

    reply = chat(text)
    print("Jarvis:", reply)
    speak_kz(reply)