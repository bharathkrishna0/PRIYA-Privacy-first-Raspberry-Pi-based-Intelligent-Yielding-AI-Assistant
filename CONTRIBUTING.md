# Contributing to PRIYA

Thanks for helping. PRIYA is a small offline Hindi voice assistant for the
Raspberry Pi, so changes should keep it light, offline and easy to read.

## Development setup

You do not need a Raspberry Pi or a microphone for most work.

```bash
git clone https://github.com/bharathkrishna0/PRIYA-Privacy-first-Raspberry-Pi-based-Intelligent-Yielding-AI-Assistant.git priya
cd priya
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt     # no PyAudio needed for tests

python main.py --text --no-tts          # type transcripts instead of speaking
```

For the speech end-to-end test and the benchmark you also need the model and
espeak-ng:

```bash
sudo apt install espeak-ng
./scripts/download_model.sh
python -m pytest -m e2e -rs
python benchmarks/run_benchmark.py
```

For microphone mode install the full `requirements.txt` (needs
`sudo apt install portaudio19-dev python3-dev`).

## Checks

Run these before opening a pull request. CI runs the same commands on Python 3.9, 3.11 and 3.13.

```bash
ruff check .
ruff format --check .
python -m pytest -q
```

## Adding a voice command

1. Add example phrases to `INTENTS` in `intent_engine.py` (Devanagari, as Vosk
   outputs them). Check each word exists in the model vocabulary; words that
   are missing can never be recognised.
2. Add the reply in `execute_intent` in `actions.py`. If it runs a program,
   use a fixed argument list through the injected `runner` (no shell, never
   put transcript text in the command).
3. Add tests in `tests/test_intent_engine.py` and `tests/test_actions.py`.
4. Add a row to the command table in `README.md` and a line to `CHANGELOG.md`.

## Coding conventions

- Python 3.9+, formatted with `ruff format` (line length 100).
- Keep hardware imports (`pyaudio`, `vosk`) inside the functions that need them
  so the rest stays testable.
- Do not log transcripts above `DEBUG` level.
- No cloud APIs or heavyweight dependencies.

## Reporting bugs and proposing features

Use the issue templates. For security problems follow [SECURITY.md](SECURITY.md).

By contributing you agree that your contributions are licensed under the
[Apache License 2.0](LICENSE) and that you follow the
[Code of Conduct](CODE_OF_CONDUCT.md).
