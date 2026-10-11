"""Reproducible speech-pipeline benchmark.

Synthesises each phrase in phrases.tsv with espeak-ng, runs it through Vosk
and the intent engine, and records model load time, peak memory, real-time
factor and intent accuracy. espeak-ng speech is robotic, so accuracy here is
a smoke test of the pipeline, not a measure of accuracy on human speech.

    python benchmarks/run_benchmark.py [--grammar] [--output results/x.json]
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from asr import load_model, transcribe_wav  # noqa: E402
from config import Config  # noqa: E402
from intent_engine import grammar_phrases, is_affirmative, is_negative, match_intent  # noqa: E402


def load_phrases(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            expected, phrase = line.split("\t", 1)
            yield expected, phrase


def classify(expected: str, transcript: str, config: Config) -> str:
    if expected == "wake":
        return "wake" if any(w in transcript for w in config.wake_words) else "missed"
    if expected == "yes":
        return "yes" if is_affirmative(transcript) else "other"
    if expected == "no":
        return "no" if is_negative(transcript) else "other"
    return match_intent(transcript, config.intent_threshold).intent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grammar", action="store_true", help="use Vosk restricted grammar")
    parser.add_argument("--phrases", type=Path, default=ROOT / "benchmarks" / "phrases.tsv")
    parser.add_argument("--voice", default="hi")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    config = Config.from_env()
    process = psutil.Process()
    rss_before = process.memory_info().rss
    start = time.perf_counter()
    model = load_model(config.model_path)
    load_s = time.perf_counter() - start
    rss_after_load = process.memory_info().rss
    grammar = grammar_phrases(config.wake_words) if args.grammar else None

    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, (expected, phrase) in enumerate(load_phrases(args.phrases)):
            wav_path = Path(tmp) / f"{i}.wav"
            subprocess.run(["espeak-ng", "-v", args.voice, "-w", str(wav_path), phrase], check=True)
            with wave.open(str(wav_path)) as wav:
                audio_s = wav.getnframes() / wav.getframerate()
            t0 = time.perf_counter()
            transcript = transcribe_wav(wav_path, model, grammar)
            asr_s = time.perf_counter() - t0
            t1 = time.perf_counter()
            predicted = classify(expected, transcript, config)
            intent_ms = (time.perf_counter() - t1) * 1000
            rows.append(
                {
                    "phrase": phrase,
                    "expected": expected,
                    "transcript": transcript,
                    "predicted": predicted,
                    "correct": predicted == expected,
                    "audio_s": round(audio_s, 3),
                    "asr_s": round(asr_s, 3),
                    "rtf": round(asr_s / audio_s, 3),
                    "intent_ms": round(intent_ms, 3),
                }
            )

    correct = sum(r["correct"] for r in rows)
    summary = {
        "machine": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "total_ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
        },
        "model": str(config.model_path.name),
        "grammar": bool(args.grammar),
        "intent_threshold": config.intent_threshold,
        "model_load_s": round(load_s, 2),
        "rss_model_mb": round((rss_after_load - rss_before) / 2**20, 1),
        "peak_rss_mb": round(process.memory_info().rss / 2**20, 1),
        "mean_rtf": round(sum(r["rtf"] for r in rows) / len(rows), 3),
        "mean_intent_ms": round(sum(r["intent_ms"] for r in rows) / len(rows), 3),
        "accuracy": f"{correct}/{len(rows)}",
        "rows": rows,
    }

    print(f"{'expected':12} {'ok':3} {'rtf':>5}  transcript")
    for r in rows:
        mark = "yes" if r["correct"] else "no"
        print(f"{r['expected']:12} {mark:3} {r['rtf']:5.2f}  {r['transcript']}")
    print(
        f"\nload {summary['model_load_s']} s | model RSS {summary['rss_model_mb']} MB | "
        f"mean RTF {summary['mean_rtf']} | accuracy {summary['accuracy']}"
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
