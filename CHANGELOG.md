# Changelog

All notable changes are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- Crash on the first command after the wake phrase: `main.py` called
  `execute_intent()` with three arguments but it accepted two.
- Audio was decimated from 44.1 kHz by keeping every third sample (14.7 kHz,
  no low-pass filter) but labelled 16 kHz. The real capture rate is now passed
  to Vosk, which resamples internally.
- The committed `model/` folder was incomplete (no `graph/HCLr.fst`, `Gr.fst`
  or `ivector/`) and failed to load. It is removed; `scripts/download_model.sh`
  fetches the full model.
- PRIYA no longer hears and transcribes her own voice: capture pauses while speaking.
- Small talk ("कैसे हो", "धन्यवाद") no longer answers without the wake phrase.
- Dates and weekdays are spoken with Hindi names instead of English ones.
- The assistant introduced itself as "Astraeus"; it now says PRIYA.

### Security
- Shutdown and restart need a spoken "हाँ" confirmation and use `sudo -n`;
  `PRIYA_ENABLE_POWER_COMMANDS=false` disables them.
- `espeak-ng` and system commands run via `subprocess` with argument lists
  instead of `os.system` with an interpolated string.
- Transcripts are logged only at `DEBUG` level.

### Added
- Terminal demo recording (GIF + MP4) and screenshots in `docs/media/`, shown in the README Demo section.
- `config.py`: all settings in one place, overridable with `PRIYA_*` variables.
- `assistant.py`: hardware-free conversation state machine (wake, command,
  confirmation, follow-up "और", timeouts).
- Wake phrase and command in one utterance ("प्रिया जी समय क्या है").
- Volume up/down through `amixer`.
- Notes/reminders: trigger phrase at start or end; only the content is saved,
  with a timestamp, in `PRIYA_DATA_DIR`.
- Optional Vosk restricted-grammar mode (`PRIYA_USE_GRAMMAR=true`).
- `main.py --text`, `--wav`, `--list-devices`, `--no-tts`, `--dry-run`.
- Clear errors for a missing model or microphone.
- pytest suite, espeak-ng → Vosk end-to-end test, benchmark script, GitHub
  Actions CI, ruff config.
- Apache-2.0 license, contributing guide, code of conduct, security policy,
  issue and PR templates.

### Changed
- Default intent threshold raised from 60 to 75 after out-of-scope phrases such as "मौसम कैसा है" matched `time` (details in `docs/BENCHMARKS.md`).
- Default wake words reduced to "प्रिया जी": "प्रियाजी" and "priya ji" are not in the Vosk vocabulary.
- Unimplemented intents (`math`, `open`, `close`) removed from matching and
  listed as planned. `pyttsx3` and `numpy` dependencies removed (unused).
- Certificate moved to `docs/`.
