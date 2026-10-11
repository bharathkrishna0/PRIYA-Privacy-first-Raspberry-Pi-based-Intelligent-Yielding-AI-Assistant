# Benchmarks and evaluation

All numbers here were measured by running the commands below. **None were
measured on a Raspberry Pi yet**: the Raspberry Pi results table is empty
until someone runs the procedure on real hardware.

## Procedure

```bash
sudo apt install espeak-ng
./scripts/download_model.sh
python benchmarks/run_benchmark.py --output benchmarks/results/<machine>-open.json
python benchmarks/run_benchmark.py --grammar --output benchmarks/results/<machine>-grammar.json
```

`benchmarks/run_benchmark.py`:

1. loads `vosk-model-small-hi-0.22` and records load time and the process RSS growth;
2. synthesises each phrase in `benchmarks/phrases.tsv` (22 phrases, one per
   command, plus the wake phrase, "हाँ" and "नहीं") with `espeak-ng -v hi`;
3. transcribes each WAV with Vosk (open vocabulary, or `--grammar` for the
   restricted command grammar) and runs the intent engine on the transcript;
4. reports real-time factor (decode time / audio length; below 1 is faster
   than real time), intent latency and intent accuracy.

**Limits:** espeak-ng speech is robotic and nothing like a human speaker, a
room or a cheap USB microphone. Accuracy from this script is a pipeline smoke
test and a way to compare settings, not a word error rate. A meaningful
accuracy figure needs recordings of real speakers (see "Still missing").

## Results: x86 development VM

Machine: Intel Xeon Platinum 8375C @ 2.90 GHz, 8 vCPU (shared cloud VM),
Ubuntu 22.04, Python 3.10, vosk 0.3.45, rapidfuzz 3.14, intent threshold 75.

| Mode | Model load | Model RSS | Mean RTF | Intent accuracy (espeak-ng) |
|---|---|---|---|---|
| Open vocabulary (default) | 0.95–1.13 s | ~161 MB | 1.54–1.66 | 12/22 |
| Restricted grammar (`PRIYA_USE_GRAMMAR=true`) | 1.06 s | ~161 MB | 0.047 | 20/22 |

Intent matching (RapidFuzz over ~40 phrases) takes well under 1 ms per transcript.

Observations:

- With the open vocabulary, decoding a 1–2 s utterance took about as long as
  the utterance on this VM (RTF ~1.5). Creating the recognizer took ~0.13 s and
  the final result ~0.1 s, so the time is in decoding against the large
  lookahead graph. On a Raspberry Pi this needs measuring: if RTF stays above 1
  the assistant will fall behind the microphone.
- Restricted grammar was ~30x faster here and recognised 20 of 22 synthetic
  phrases, against 12 of 22 for open vocabulary. The trade-off: in grammar mode
  only the listed phrases can be recognised, so free-text notes and reminders
  do not work.
- The wake phrase "प्रिया जी" was transcribed as just "जी" in both modes with
  espeak-ng's voice. Both words are in the model vocabulary, so this may be
  espeak-ng's pronunciation; it must be checked with a human speaker.
- Raw per-phrase transcripts are written to the `--output` JSON.

## Intent threshold

The original threshold was 60. On a small hand-written set (20 in-scope
variants, 12 out-of-scope requests) in-scope variants scored 80–100, while
out-of-scope requests scored up to 76: for example "मौसम कैसा है" (weather) → `time`
at 70 and "बत्ती बंद करो" (lights off) → `shutdown` at 67. The default is now 75
(`PRIYA_INTENT_THRESHOLD`). The set is small and self-made, so treat 75 as a
starting point to re-tune with real transcripts.

## Results: Raspberry Pi

| Board / RAM | OS | Python | Mode | Model load | Model RSS | Mean RTF | Accuracy |
|---|---|---|---|---|---|---|---|
| _not measured yet_ | | | | | | | |

## Still missing

- The table above, on the author's Raspberry Pi (Raspberry Pi OS 64-bit).
- End-to-end latency from end of speech to start of reply in microphone mode.
- CPU usage while idle-listening (`top -p $(pgrep -f main.py)`).
- Recognition accuracy on real speakers: record each phrase in
  `benchmarks/phrases.tsv` from several speakers as 16-bit mono WAV, then run
  `python main.py --wav recordings/*.wav --no-tts`. Do not commit recordings of
  other people without their consent.
