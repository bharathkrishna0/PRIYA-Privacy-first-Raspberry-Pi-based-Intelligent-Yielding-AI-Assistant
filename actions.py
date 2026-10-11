"""Intent handlers: build the spoken reply and run allow-listed system commands.

Only fixed argument lists are ever executed (no shell, no text from the
transcript in a command line).
"""

from __future__ import annotations

import datetime
import logging
import random
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional

import psutil

from config import Config

logger = logging.getLogger(__name__)

Runner = Callable[..., "subprocess.CompletedProcess[bytes]"]

POWER_INTENTS = ("shutdown", "restart")

POWER_COMMANDS: Dict[str, List[str]] = {
    "shutdown": ["sudo", "-n", "shutdown", "-h", "now"],
    "restart": ["sudo", "-n", "reboot"],
}

UNKNOWN_REPLY = "माफ़ कीजिए, मैं समझ नहीं पाया।"

HINDI_DAYS = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
HINDI_MONTHS = [
    "जनवरी",
    "फ़रवरी",
    "मार्च",
    "अप्रैल",
    "मई",
    "जून",
    "जुलाई",
    "अगस्त",
    "सितंबर",
    "अक्टूबर",
    "नवंबर",
    "दिसंबर",
]

JOKES = [
    "प्रोग्रामर शादी क्यों नहीं करते? क्योंकि commit कर चुके होते हैं।",
    "Bug नहीं है, undocumented feature है।",
]


def hindi_date(now: datetime.datetime) -> str:
    return f"{now.day} {HINDI_MONTHS[now.month - 1]} {now.year}"


def hindi_day(now: datetime.datetime) -> str:
    return HINDI_DAYS[now.weekday()]


def _append_line(path: Path, text: str, now: datetime.datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{now.isoformat(timespec='seconds')}\t{text}\n")


def _run(command: List[str], runner: Runner) -> bool:
    try:
        result = runner(command, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (FileNotFoundError, OSError) as exc:
        logger.warning("Command %s unavailable: %s", command[0], exc)
        return False
    returncode = getattr(result, "returncode", 0)
    if returncode != 0:
        logger.warning("Command %s exited with %s", " ".join(command), returncode)
        return False
    return True


def change_volume(direction: str, config: Config, runner: Runner = subprocess.run) -> str:
    sign = "+" if direction == "up" else "-"
    command = ["amixer", "-q", "sset", config.mixer_control, f"{config.volume_step}%{sign}"]
    if not _run(command, runner):
        return "आवाज़ बदलने का कंट्रोल उपलब्ध नहीं है।"
    return "आवाज़ बढ़ा दी गई है।" if direction == "up" else "आवाज़ कम कर दी गई है।"


def power_action(intent: str, runner: Runner = subprocess.run) -> bool:
    """Run the shutdown/restart command. Callers must confirm with the user first."""
    if intent not in POWER_COMMANDS:
        raise ValueError(f"not a power intent: {intent}")
    return _run(POWER_COMMANDS[intent], runner)


def power_confirmation_prompt(intent: str) -> str:
    action = "बंद" if intent == "shutdown" else "रीस्टार्ट"
    return f"क्या आप सच में सिस्टम {action} करना चाहते हैं? हाँ या नहीं बोलिए।"


def power_started_reply(intent: str) -> str:
    return "सिस्टम बंद किया जा रहा है।" if intent == "shutdown" else "सिस्टम रीस्टार्ट हो रहा है।"


def execute_intent(
    intent: str,
    text: str = "",
    memory: Optional[dict] = None,
    *,
    payload: str = "",
    config: Optional[Config] = None,
    runner: Runner = subprocess.run,
    now: Optional[datetime.datetime] = None,
) -> str:
    """Return the Hindi reply for ``intent``.

    Shutdown/restart are never executed here; :mod:`assistant` asks for a
    spoken confirmation and then calls :func:`power_action`.
    """
    config = config or Config()
    now = now or datetime.datetime.now()

    if intent == "time":
        return "अभी समय है " + now.strftime("%H:%M")
    if intent == "date":
        return "आज की तारीख है " + hindi_date(now)
    if intent == "day":
        return "आज " + hindi_day(now) + " है"
    if intent == "cpu":
        return f"सीपीयू उपयोग {psutil.cpu_percent(interval=0.2)} प्रतिशत है"
    if intent == "memory":
        return f"मेमोरी उपयोग {psutil.virtual_memory().percent} प्रतिशत है"
    if intent == "disk":
        return f"डिस्क उपयोग {psutil.disk_usage('/').percent} प्रतिशत है"
    if intent == "battery":
        battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
        if battery:
            return f"बैटरी {round(battery.percent)} प्रतिशत है"
        return "बैटरी जानकारी उपलब्ध नहीं है"
    if intent == "system_info":
        return (
            f"सीपीयू {psutil.cpu_percent(interval=0.2)} प्रतिशत, "
            f"मेमोरी {psutil.virtual_memory().percent} प्रतिशत"
        )
    if intent in POWER_INTENTS:
        return power_confirmation_prompt(intent)
    if intent == "volume_up":
        return change_volume("up", config, runner)
    if intent == "volume_down":
        return change_volume("down", config, runner)
    if intent == "joke":
        return random.choice(JOKES)
    if intent == "motivation":
        return "कभी हार मत मानो। हर दिन एक नया अवसर है।"
    if intent in ("note", "reminder"):
        if not payload:
            return "क्या लिखना है? कृपया कमांड के साथ बोलिए।"
        filename = "notes.txt" if intent == "note" else "reminders.txt"
        _append_line(config.data_dir / filename, payload, now)
        return "नोट सेव कर दिया गया है" if intent == "note" else "रिमाइंडर सेव कर दिया गया है"
    if intent == "greeting":
        return "नमस्ते, मैं प्रिया हूँ।"
    if intent == "wellbeing":
        return "मैं बिल्कुल ठीक हूँ। आप कैसी हैं प्रिया जी?"
    if intent == "thanks":
        return "आपका स्वागत है। हमेशा मदद के लिए यहाँ हूँ।"
    if intent == "conversation":
        return "मैं आपकी आवाज़ इसी डिवाइस पर समझती हूँ, बिना इंटरनेट के।"
    return UNKNOWN_REPLY
