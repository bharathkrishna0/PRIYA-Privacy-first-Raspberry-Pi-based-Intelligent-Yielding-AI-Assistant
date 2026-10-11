from pathlib import Path

import pytest

import tts
from config import Config


def test_defaults_match_original_behaviour():
    config = Config.from_env({})
    assert config.sample_rate == 44100
    assert config.input_device_index is None
    assert config.model_path.name == "model"
    assert "प्रिया जी" in config.wake_words
    assert config.enable_power_commands


def test_env_overrides():
    config = Config.from_env(
        {
            "PRIYA_MODEL_PATH": "/opt/vosk",
            "PRIYA_INPUT_DEVICE": "2",
            "PRIYA_SAMPLE_RATE": "48000",
            "PRIYA_WAKE_WORDS": "प्रिया जी, Hey Priya",
            "PRIYA_INTENT_THRESHOLD": "80",
            "PRIYA_ENABLE_POWER_COMMANDS": "false",
            "PRIYA_USE_GRAMMAR": "1",
            "PRIYA_LOG_LEVEL": "debug",
        }
    )
    assert config.model_path == Path("/opt/vosk")
    assert config.input_device_index == 2
    assert config.sample_rate == 48000
    assert config.wake_words == ("प्रिया जी", "hey priya")
    assert config.intent_threshold == 80
    assert not config.enable_power_commands
    assert config.use_grammar
    assert config.log_level == "DEBUG"


@pytest.mark.parametrize(
    "name,value", [("PRIYA_INPUT_DEVICE", "usb"), ("PRIYA_USE_GRAMMAR", "maybe")]
)
def test_invalid_values_raise(name, value):
    with pytest.raises(ValueError, match=name):
        Config.from_env({name: value})


def test_speak_passes_text_as_single_argument(capsys):
    calls = []
    text = 'नमस्ते"; rm -rf ~; echo "'
    assert tts.speak(text, runner=lambda cmd, **kw: calls.append(cmd))
    assert calls == [["espeak-ng", "-v", "hi", text]]
    assert "PRIYA:" in capsys.readouterr().out


def test_speak_with_speed():
    assert tts.build_command("नमस्ते", "hi", 140) == ["espeak-ng", "-v", "hi", "-s", "140", "नमस्ते"]


def test_speak_without_espeak_does_not_crash():
    def missing(cmd, **kw):
        raise FileNotFoundError

    assert tts.speak("नमस्ते", runner=missing) is False
