# Security Policy

PRIYA runs on a local device and can execute a small, fixed set of system
commands (shutdown, reboot, volume). Bugs that let speech or text trigger other
commands, or that leak transcripts or notes, are treated as security issues.

## Supported versions

Only the latest commit on `main` is supported.

## Reporting a vulnerability

Please do **not** open a public issue. Instead, use GitHub's private reporting:
**Security → Report a vulnerability** on this repository
(https://github.com/bharathkrishna0/PRIYA-Privacy-first-Raspberry-Pi-based-Intelligent-Yielding-AI-Assistant/security/advisories/new).

Include the steps to reproduce, the affected file/function, and the impact.
You should get a reply within 7 days. Fixes are released on `main` and noted in
`CHANGELOG.md`.

## Design notes for reviewers

- System commands are fixed argument lists in `actions.py`
  (`POWER_COMMANDS`, `change_volume`), run with `subprocess` and no shell.
  Text from the transcript never becomes part of a command line.
- Shutdown and restart need a spoken "हाँ" within `PRIYA_CONFIRM_TIMEOUT_S`
  and use `sudo -n`, so they fail instead of prompting when sudo needs a password.
  Set `PRIYA_ENABLE_POWER_COMMANDS=false` to disable them entirely.
- `espeak-ng` receives the reply as a single argument (no shell).
- Notes and reminders are stored unencrypted in `PRIYA_DATA_DIR` (default `./data`).
