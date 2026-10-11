"""PRIYA entry point.

python main.py                 # microphone mode (Raspberry Pi)
python main.py --text          # type transcripts instead of speaking
python main.py --wav a.wav ... # feed WAV files through Vosk
python main.py --list-devices  # show microphone indices
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from typing import Callable, List, Optional, Sequence

import tts
from assistant import Assistant, Reply
from config import Config
from intent_engine import grammar_phrases

logger = logging.getLogger("priya")

BANNER = """
===================================
 PRIYA - offline Hindi voice assistant
 Wake phrase: "प्रिया जी" (Priya Ji)
===================================
"""
STARTUP_GREETING = "नमस्ते प्रिया जी। मैं तैयार हूँ।"


def dry_run_runner(command: Sequence[str], **_: object) -> subprocess.CompletedProcess:
    print("[dry-run] would run:", " ".join(command), flush=True)
    return subprocess.CompletedProcess(list(command), 0)


def deliver(reply: Optional[Reply], say: Callable[[str], object]) -> None:
    if reply is None:
        return
    say(reply.text)
    if reply.after_speech is not None:
        reply.after_speech()


def make_speaker(config: Config, enabled: bool) -> Callable[[str], object]:
    if not enabled:
        return lambda text: print("PRIYA:", text, flush=True)
    return lambda text: tts.speak(text, config.tts_voice, config.tts_speed)


def run_text(assistant: Assistant, say: Callable[[str], object]) -> int:
    print('Type what you would say, e.g. "प्रिया जी समय क्या है". Ctrl+D to quit.')
    for line in sys.stdin:
        deliver(assistant.handle(line), say)
    return 0


def run_wav(paths: List[str], config: Config, assistant: Assistant, say) -> int:
    from asr import load_model, transcribe_wav

    model = load_model(config.model_path)
    grammar = grammar_phrases(config.wake_words) if config.use_grammar else None
    for path in paths:
        transcript = transcribe_wav(path, model, grammar)
        print(f"[{path}] transcript: {transcript!r}", flush=True)
        deliver(assistant.handle(transcript), say)
    return 0


def run_microphone(config: Config, assistant: Assistant, say) -> int:
    from asr import HindiASR

    print("Loading Vosk Hindi model...")
    grammar = grammar_phrases(config.wake_words) if config.use_grammar else None
    asr = HindiASR(config, grammar=grammar)
    say(STARTUP_GREETING)
    print("System ready. Say 'प्रिया जी' to activate.\n")
    try:
        while True:
            reply = assistant.handle(asr.listen())
            if reply is None:
                continue
            asr.pause()
            try:
                deliver(reply, say)
            finally:
                asr.resume()
    except KeyboardInterrupt:
        print("\nStopping.")
        return 0
    finally:
        asr.close()


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PRIYA offline Hindi voice assistant")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--text", action="store_true", help="read transcripts from stdin")
    mode.add_argument("--wav", nargs="+", metavar="FILE", help="transcribe WAV files with Vosk")
    mode.add_argument("--list-devices", action="store_true", help="list audio input devices")
    parser.add_argument("--no-tts", action="store_true", help="print replies instead of speaking")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print shutdown/restart/volume commands instead of running them "
        "(always on in --text and --wav modes)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        config = Config.from_env()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    logging.basicConfig(level=config.log_level, format="%(levelname)s %(name)s: %(message)s")

    if args.list_devices:
        from asr import list_input_devices

        for index, name, channels, rate in list_input_devices():
            print(f"{index:3d}  {name}  (inputs={channels}, default rate={rate} Hz)")
        return 0

    simulated = bool(args.text or args.wav)
    runner = dry_run_runner if (args.dry_run or simulated) else subprocess.run
    assistant = Assistant(config, runner=runner)
    say = make_speaker(config, enabled=not args.no_tts)

    print(BANNER)
    from asr import MicrophoneError, ModelError

    try:
        if args.text:
            return run_text(assistant, say)
        if args.wav:
            return run_wav(args.wav, config, assistant, say)
        return run_microphone(config, assistant, say)
    except (ModelError, MicrophoneError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
