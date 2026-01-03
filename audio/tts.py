import os, tempfile
from openai import OpenAI
from core.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def speak_kz(text):
    path = tempfile.mktemp(suffix=".wav")
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="onyx",
        input=text,
        extra_body={
            "format": "wav",
            "emotion": "auto",
            "intonation": "auto",
            "speed": 1.0
        }
    ) as r:
        r.stream_to_file(path)

    os.system(f"mpg123 {path}")