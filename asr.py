import pyaudio
import numpy as np
import json
from vosk import Model, KaldiRecognizer

class HindiASR:
    def __init__(self, model_path="model", device_index=None):
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, 16000)

        self.p = pyaudio.PyAudio()
        self.device_index = device_index

        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=4096
        )

    def listen(self):
        data = self.stream.read(4096, exception_on_overflow=False)

        audio = np.frombuffer(data, dtype=np.int16)
        audio = audio[::3] # downsample 44100 → ~16000
        audio_bytes = audio.tobytes()

        if self.recognizer.AcceptWaveform(audio_bytes):
            result = json.loads(self.recognizer.Result())
            return result.get("text", "")

        return ""
