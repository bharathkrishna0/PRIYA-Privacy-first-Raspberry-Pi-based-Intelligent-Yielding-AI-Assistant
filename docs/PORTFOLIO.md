# Project summary (for a resume or portfolio)

**PRIYA: offline Hindi voice assistant for Raspberry Pi** · Python · Vosk/Kaldi · RapidFuzz · espeak-ng

- Built a voice assistant that does Hindi speech recognition, intent matching
  and speech output on-device, without cloud APIs, as part of the Bharat
  AI-SoC Student Challenge (Arm Education and the Chips to Startup Programme, MeitY, Jan–Mar 2026).
- Designed a pipeline of microphone capture → Vosk speech-to-text → wake
  phrase → RapidFuzz fuzzy intent matching → allow-listed system actions → espeak-ng.
- Answers 20 command types: time, date, CPU/memory/disk/battery status,
  volume, notes, reminders, small talk, and shutdown/restart behind a spoken
  confirmation.
- Made the core testable without hardware (configurable runner, clock and
  audio source) and added 100+ pytest tests, a speech end-to-end test and CI.
- Measured that restricted-grammar decoding was ~30x faster than open
  vocabulary on a development VM (RTF 0.05 vs 1.5) with a reproducible benchmark.

Keep these lines in sync with the README. Add Raspberry Pi latency figures
only after measuring them (see docs/BENCHMARKS.md).
