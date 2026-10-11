import io

import main


def test_text_mode_runs_without_microphone_or_model(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("PRIYA_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO("प्रिया जी सिस्टम बंद करो\nहाँ\nप्रिया जी आवाज़ बढ़ाओ\n"),
    )
    assert main.main(["--text", "--no-tts"]) == 0
    out = capsys.readouterr().out
    assert "[dry-run] would run: sudo -n shutdown -h now" in out
    assert "[dry-run] would run: amixer -q sset Master 10%+" in out


def test_missing_model_is_a_clean_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("PRIYA_MODEL_PATH", str(tmp_path / "missing"))
    assert main.main(["--wav", "x.wav", "--no-tts"]) == 1


def test_bad_config_exit_code(monkeypatch):
    monkeypatch.setenv("PRIYA_SAMPLE_RATE", "fast")
    assert main.main(["--text"]) == 2
