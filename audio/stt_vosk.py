import json, wave
from vosk import Model, KaldiRecognizer

model = Model("vosk-model-kz-0.42")

def transcribe(filename):
    wf = wave.open(filename, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())
    text = ""


    while True:
        data = wf.readframes(8000)
        if not data:
            break
        if rec.AcceptWaveform(data):
            text += json.loads(rec.Result()).get("text", "") + " "


    text += json.loads(rec.FinalResult()).get("text", "")
    return text.strip()