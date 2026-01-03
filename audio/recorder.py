import time, wave, tempfile
import numpy as np
import sounddevice as sd
from scipy.signal import resample




def record_voice_auto(fs, silence_threshold=500, silence_limit=1.2, max_wait=10):
    recording = []
    chunk_duration = 0.1
    chunk_size = int(fs * chunk_duration)


    silent_time = 0
    started = False
    start_time = time.time()


    while True:
        chunk = sd.rec(chunk_size, samplerate=fs, channels=1, dtype=np.int16)
        sd.wait()
        amp = abs(chunk).mean()


        if not started:
            if amp > silence_threshold:
                started = True
                recording.append(chunk)
        elif time.time() - start_time > max_wait:
            return None
        else:
            recording.append(chunk)
            silent_time = silent_time + chunk_duration if amp < silence_threshold else 0
            if silent_time >= silence_limit:
                break


    audio = np.concatenate(recording)
    if fs != 16000:
        audio = resample(audio, int(len(audio) * 16000 / fs)).astype(np.int16)
        fs = 16000


    filename = tempfile.mktemp(suffix=".wav")
    with wave.open(filename, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(fs)
        f.writeframes(audio.tobytes())


    return filename