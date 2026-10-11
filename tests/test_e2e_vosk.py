"""End-to-end: espeak-ng audio -> Vosk -> intent. Skipped without model/espeak-ng.

espeak-ng speech is synthetic; these phrases were chosen because the small
Hindi model transcribes them reliably. They prove the pipeline is wired up,
not that recognition is accurate for human speakers.
"""

import shutil
import subprocess

import pytest

from asr import load_model, missing_model_files, transcribe_wav
from config import Config
from intent_engine import detect_intent

CONFIG = Config()

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        bool(missing_model_files(CONFIG.model_path)) or shutil.which("espeak-ng") is None,
        reason="needs ./model (scripts/download_model.sh) and espeak-ng",
    ),
]


@pytest.fixture(scope="module")
def model():
    return load_model(CONFIG.model_path)


def synth(tmp_path, text):
    path = tmp_path / "speech.wav"
    subprocess.run(["espeak-ng", "-v", "hi", "-w", str(path), text], check=True)
    return path


@pytest.mark.parametrize(
    "phrase,intent",
    [
        ("समय क्या है", "time"),
        ("आज की तारीख क्या है", "date"),
        ("सीपीयू उपयोग", "cpu"),
        ("मेमोरी उपयोग", "memory"),
        ("बैटरी स्थिति", "battery"),
    ],
)
def test_spoken_command_reaches_intent(model, tmp_path, phrase, intent):
    transcript = transcribe_wav(synth(tmp_path, phrase), model)
    assert detect_intent(transcript) == intent, transcript


def test_rejects_stereo_wav(model, tmp_path):
    import wave

    path = tmp_path / "stereo.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00" * 3200)
    with pytest.raises(ValueError):
        transcribe_wav(path, model)
