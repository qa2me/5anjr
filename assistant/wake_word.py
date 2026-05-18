import json
import queue
import threading
import time

import pyaudio
from vosk import Model, KaldiRecognizer


class WakeWordDetector:
    RATE = 16000
    CHUNK = 4000
    FORMAT = pyaudio.paInt16
    CHANNELS = 1

    def __init__(self, model_path, keyphrase="hey linux"):
        self.model = Model(model_path)
        self.keyphrase = keyphrase.lower()
        self.audio_queue = queue.Queue()
        self.running = False
        self._on_wake = None
        self._stream = None
        self._pa = None

    def on_wake(self, callback):
        self._on_wake = callback

    def _audio_callback(self, in_data, frame_count, time_info, status):
        self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def _listen_loop(self):
        rec = KaldiRecognizer(self.model, self.RATE)

        while self.running:
            try:
                data = self.audio_queue.get(timeout=0.3)
            except queue.Empty:
                continue

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower().strip()
                if self.keyphrase in text:
                    if self._on_wake:
                        self._on_wake()
            else:
                partial = json.loads(rec.PartialResult())
                partial_text = partial.get("partial", "").lower().strip()
                if self.keyphrase in partial_text:
                    if self._on_wake:
                        self._on_wake()

    def start(self):
        if self.running:
            return
        self.running = True
        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
            stream_callback=self._audio_callback,
        )
        self._stream.start_stream()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.running = False
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._pa:
            self._pa.terminate()
        if hasattr(self, "_thread"):
            self._thread.join(timeout=2)
