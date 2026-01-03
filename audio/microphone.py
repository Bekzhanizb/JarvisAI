import sounddevice as sd


def auto_select_microphone():
    for i, dev in enumerate(sd.query_devices()):
        if dev['max_input_channels'] > 0:
            sd.default.device = i
            print(f"🎤 Microphone selected: {dev['name']}")
            return
    raise RuntimeError("No microphone found")




def get_valid_sample_rate():
    for rate in [16000, 32000, 44100, 48000]:
        try:
            sd.check_input_settings(samplerate=rate, channels=1)
            return rate
        except:
            continue
    raise RuntimeError("No valid sample rate")