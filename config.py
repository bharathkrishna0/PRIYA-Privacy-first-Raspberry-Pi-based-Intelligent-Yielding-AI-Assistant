"""Runtime configuration for PRIYA.

Every setting has a default that matches the original hard-coded behaviour and
can be overridden with a ``PRIYA_*`` environment variable (see README).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent

# Vosk small-hi only emits Devanagari words from its vocabulary; "प्रियाजी" (one word)
# and Latin "priya ji" are not in it, so they could never be recognised.
DEFAULT_WAKE_WORDS: Tuple[str, ...] = ("प्रिया जी",)


def _get(environ: Mapping[str, str], name: str) -> Optional[str]:
    value = environ.get(name)
    if value is None or value.strip() == "":
        return None
    return value.strip()


def _int(environ: Mapping[str, str], name: str, default: Optional[int]) -> Optional[int]:
    value = _get(environ, name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc


def _float(environ: Mapping[str, str], name: str, default: float) -> float:
    value = _get(environ, name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {value!r}") from exc


def _bool(environ: Mapping[str, str], name: str, default: bool) -> bool:
    value = _get(environ, name)
    if value is None:
        return default
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true/false, got {value!r}")


@dataclass(frozen=True)
class Config:
    model_path: Path = PROJECT_ROOT / "model"
    input_device_index: Optional[int] = None
    sample_rate: int = 44100
    frames_per_buffer: int = 4096
    wake_words: Tuple[str, ...] = DEFAULT_WAKE_WORDS
    intent_threshold: float = 75.0
    use_grammar: bool = False
    listen_timeout_s: float = 10.0
    confirm_timeout_s: float = 15.0
    data_dir: Path = PROJECT_ROOT / "data"
    tts_voice: str = "hi"
    tts_speed: Optional[int] = None
    enable_power_commands: bool = True
    mixer_control: str = "Master"
    volume_step: int = 10
    log_level: str = "INFO"

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> Config:
        env = os.environ if environ is None else environ
        defaults = cls()
        wake = _get(env, "PRIYA_WAKE_WORDS")
        model_path = _get(env, "PRIYA_MODEL_PATH")
        data_dir = _get(env, "PRIYA_DATA_DIR")
        return cls(
            model_path=Path(model_path).expanduser() if model_path else defaults.model_path,
            input_device_index=_int(env, "PRIYA_INPUT_DEVICE", defaults.input_device_index),
            sample_rate=_int(env, "PRIYA_SAMPLE_RATE", defaults.sample_rate)
            or defaults.sample_rate,
            frames_per_buffer=_int(env, "PRIYA_FRAMES_PER_BUFFER", defaults.frames_per_buffer)
            or defaults.frames_per_buffer,
            wake_words=tuple(w.strip().lower() for w in wake.split(",") if w.strip())
            if wake
            else defaults.wake_words,
            intent_threshold=_float(env, "PRIYA_INTENT_THRESHOLD", defaults.intent_threshold),
            use_grammar=_bool(env, "PRIYA_USE_GRAMMAR", defaults.use_grammar),
            listen_timeout_s=_float(env, "PRIYA_LISTEN_TIMEOUT_S", defaults.listen_timeout_s),
            confirm_timeout_s=_float(env, "PRIYA_CONFIRM_TIMEOUT_S", defaults.confirm_timeout_s),
            data_dir=Path(data_dir).expanduser() if data_dir else defaults.data_dir,
            tts_voice=_get(env, "PRIYA_TTS_VOICE") or defaults.tts_voice,
            tts_speed=_int(env, "PRIYA_TTS_SPEED", defaults.tts_speed),
            enable_power_commands=_bool(
                env, "PRIYA_ENABLE_POWER_COMMANDS", defaults.enable_power_commands
            ),
            mixer_control=_get(env, "PRIYA_MIXER_CONTROL") or defaults.mixer_control,
            volume_step=_int(env, "PRIYA_VOLUME_STEP", defaults.volume_step)
            or defaults.volume_step,
            log_level=(_get(env, "PRIYA_LOG_LEVEL") or defaults.log_level).upper(),
        )
