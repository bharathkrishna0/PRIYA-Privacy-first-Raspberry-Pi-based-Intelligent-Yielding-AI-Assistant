"""Offline text-to-speech through the ``espeak-ng`` command-line tool."""

from __future__ import annotations

import logging
import shutil
import subprocess
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

_missing_warned = False


def build_command(text: str, voice: str = "hi", speed: Optional[int] = None) -> List[str]:
    command = ["espeak-ng", "-v", voice]
    if speed:
        command += ["-s", str(speed)]
    command.append(text)
    return command


def is_available() -> bool:
    return shutil.which("espeak-ng") is not None


def speak(
    text: str,
    voice: str = "hi",
    speed: Optional[int] = None,
    runner: Callable[..., object] = subprocess.run,
) -> bool:
    """Print and speak ``text``. Returns False if speech could not be produced.

    The text is passed as a single argument (no shell), so quotes or shell
    metacharacters in a response cannot run commands.
    """
    global _missing_warned
    print("PRIYA:", text, flush=True)
    if not text:
        return False
    try:
        runner(
            build_command(text, voice, speed),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        if not _missing_warned:
            logger.warning(
                "espeak-ng not found; replies are printed only (sudo apt install espeak-ng)"
            )
            _missing_warned = True
        return False
    except OSError as exc:
        logger.warning("espeak-ng failed: %s", exc)
        return False
    return True
