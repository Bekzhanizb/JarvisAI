from audio.microphone import auto_select_microphone, get_valid_sample_rate
from audio.recorder import record_voice_auto
from audio.stt_vosk import transcribe
from audio.tts import speak_kz

from ai.chat import chat
from intent.resolver import resolve_intent
from core.executor.launcher import launch_app

print("🤖 Jarvis v0.3 started")

# --- Audio init ---
auto_select_microphone()
MIC_RATE = get_valid_sample_rate()

# --- Main loop ---
while True:
    wav_path = record_voice_auto(MIC_RATE)

    # ⏳ auto-exit after silence
    if not wav_path:
        print("⏹ Jarvis stopped (silence timeout)")
        break

    text = transcribe(wav_path)
    if not text:
        continue

    print("🧍‍♂️ You:", text)

    # 🔚 exit commands
    if text.lower() in ["шығу", "exit", "stop"]:
        speak_kz("Жақсы, көріскенше!")
        break

    # 🎯 1. Intent resolving (ML + OpenAI later)
    intent = resolve_intent(text)

    # ⚙ 2. If it is executable command → run it
    if intent and intent.get("type") == "action":
        result = launch_app(intent)
        if result:
            speak_kz(result)
        continue

    # 💬 3. Otherwise → normal chat
    reply = chat(text)
    print("🤖 Jarvis:", reply)
    speak_kz(reply)
