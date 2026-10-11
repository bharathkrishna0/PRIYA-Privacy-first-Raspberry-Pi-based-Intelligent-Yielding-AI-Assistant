"""Offline Hindi speech recognition with Vosk (Kaldi).

``pyaudio`` and ``vosk`` are imported lazily so the rest of the project (and
its tests) works on machines without a microphone or the speech model.
"""

from __future__ import annotations

import json
import logging
import wave
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from config import Config

logger = logging.getLogger(__name__)

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip"
REQUIRED_MODEL_FILES = ("am/final.mdl", "conf/mfcc.conf", "conf/model.conf")


class ModelError(RuntimeError):
    """The Vosk model directory is missing or incomplete."""


class MicrophoneError(RuntimeError):
    """The audio input device could not be opened or read."""


def missing_model_files(model_path: Path) -> List[str]:
    model_path = Path(model_path)
    if not model_path.is_dir():
        return [str(model_path)]
    missing = [name for name in REQUIRED_MODEL_FILES if not (model_path / name).is_file()]
    graph = model_path / "graph"
    has_static_graph = (graph / "HCLG.fst").is_file()
    has_lookahead_graph = (graph / "HCLr.fst").is_file() and (graph / "Gr.fst").is_file()
    if not (has_static_graph or has_lookahead_graph):
        missing.append("graph/HCLG.fst or graph/HCLr.fst + graph/Gr.fst")
    return missing


def load_model(model_path: Path):
    missing = missing_model_files(model_path)
    if missing:
        raise ModelError(
            f"Vosk model at '{model_path}' is missing: {', '.join(missing)}. "
            f"Run scripts/download_model.sh (downloads {MODEL_URL})."
        )
    from vosk import Model, SetLogLevel

    SetLogLevel(-1)
    return Model(str(model_path))


def make_recognizer(model, sample_rate: int, grammar: Optional[Sequence[str]] = None):
    from vosk import KaldiRecognizer

    if grammar:
        phrases = list(grammar) + ["[unk]"]
        return KaldiRecognizer(model, float(sample_rate), json.dumps(phrases, ensure_ascii=False))
    return KaldiRecognizer(model, float(sample_rate))


def list_input_devices() -> List[Tuple[int, str, int, int]]:
    """Return (index, name, input channels, default sample rate) for each input device."""
    import pyaudio

    pa = pyaudio.PyAudio()
    try:
        devices = []
        for index in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(index)
            channels = int(info.get("maxInputChannels", 0))
            if channels > 0:
                devices.append((index, str(info["name"]), channels, int(info["defaultSampleRate"])))
        return devices
    finally:
        pa.terminate()


class HindiASR:
    """Streams microphone audio into a Vosk recognizer.

    The microphone is opened at ``config.sample_rate`` and the same rate is
    given to Vosk, which resamples internally to the model's 16 kHz.
    """

    def __init__(self, config: Config, model=None, grammar: Optional[Sequence[str]] = None) -> None:
        self.config = config
        self.model = model if model is not None else load_model(config.model_path)
        self.recognizer = make_recognizer(self.model, config.sample_rate, grammar)

        import pyaudio

        self._pa = pyaudio.PyAudio()
        try:
            self.stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=config.sample_rate,
                input=True,
                input_device_index=config.input_device_index,
                frames_per_buffer=config.frames_per_buffer,
            )
        except (OSError, ValueError) as exc:
            self._pa.terminate()
            raise MicrophoneError(
                f"Could not open microphone (device={config.input_device_index}, "
                f"rate={config.sample_rate} Hz): {exc}. "
                "Run `python main.py --list-devices`, then set PRIYA_INPUT_DEVICE "
                "and PRIYA_SAMPLE_RATE."
            ) from exc

    def listen(self) -> str:
        """Read one buffer; return a finished utterance or an empty string."""
        try:
            data = self.stream.read(self.config.frames_per_buffer, exception_on_overflow=False)
        except OSError as exc:
            raise MicrophoneError(f"Microphone read failed: {exc}") from exc
        if self.recognizer.AcceptWaveform(data):
            return json.loads(self.recognizer.Result()).get("text", "")
        return ""

    def pause(self) -> None:
        """Stop capturing so PRIYA does not transcribe her own voice."""
        self.stream.stop_stream()

    def resume(self) -> None:
        self.recognizer.Reset()
        self.stream.start_stream()

    def close(self) -> None:
        try:
            self.stream.stop_stream()
            self.stream.close()
        finally:
            self._pa.terminate()


def transcribe_wav(path: Path, model, grammar: Optional[Iterable[str]] = None) -> str:
    """Transcribe a mono 16-bit PCM WAV file (any sample rate)."""
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
            raise ValueError(f"{path}: expected mono 16-bit PCM WAV")
        recognizer = make_recognizer(model, wav.getframerate(), list(grammar) if grammar else None)
        parts = []
        while True:
            data = wav.readframes(4000)
            if not data:
                break
            if recognizer.AcceptWaveform(data):
                parts.append(json.loads(recognizer.Result()).get("text", ""))
        parts.append(json.loads(recognizer.FinalResult()).get("text", ""))
    return " ".join(part for part in parts if part)
