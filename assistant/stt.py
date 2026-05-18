import json
import queue
import threading
import time

import pyaudio
from vosk import Model, KaldiRecognizer


class SpeechRecognizer:
    RATE = 16000
    CHUNK = 4000
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    SILENCE_DURATION = 2.5
    MAX_DURATION = 15.0

    def __init__(self, model_path):
        self.model = Model(model_path)

    def listen(self, timeout=MAX_DURATION):
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )
        stream.start_stream()

        rec = KaldiRecognizer(self.model, self.RATE)

        text = ""
        silence_start = None
        start_time = time.time()
        has_speech = False

        try:
            while time.time() - start_time < timeout:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    partial = result.get("text", "").strip()
                    if partial:
                        text = partial
                        has_speech = True
                        silence_start = None
                else:
                    partial_result = json.loads(rec.PartialResult())
                    partial = partial_result.get("partial", "").strip()
                    if partial:
                        has_speech = True
                        silence_start = None
                    elif has_speech:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= self.SILENCE_DURATION:
                            break
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

        if not text and has_speech:
            final = json.loads(rec.FinalResult())
            text = final.get("text", "").strip()

        return text
