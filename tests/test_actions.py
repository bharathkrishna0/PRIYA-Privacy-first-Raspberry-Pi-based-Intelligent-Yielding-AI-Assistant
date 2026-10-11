import datetime
import subprocess
from collections import namedtuple

import pytest

import actions
from config import Config

NOW = datetime.datetime(2026, 3, 2, 9, 5, 0)  # a Monday


class Recorder:
    def __init__(self, returncode=0, exc=None):
        self.calls = []
        self.returncode = returncode
        self.exc = exc

    def __call__(self, command, **kwargs):
        self.calls.append(command)
        if self.exc:
            raise self.exc
        return subprocess.CompletedProcess(command, self.returncode)


@pytest.fixture
def config(tmp_path):
    return Config(data_dir=tmp_path / "data")


def run(intent, config, **kwargs):
    kwargs.setdefault("now", NOW)
    return actions.execute_intent(intent, config=config, **kwargs)


def test_time_date_day_in_hindi(config):
    assert run("time", config) == "अभी समय है 09:05"
    assert run("date", config) == "आज की तारीख है 2 मार्च 2026"
    assert run("day", config) == "आज सोमवार है"


def test_original_three_argument_call_signature_works(config):
    assert actions.execute_intent("time", "समय क्या है", {}, config=config, now=NOW)


@pytest.mark.parametrize("intent", ["cpu", "memory", "disk", "system_info"])
def test_system_stats_report_a_percentage(intent, config):
    assert "प्रतिशत" in run(intent, config)


def test_battery_missing(monkeypatch, config):
    monkeypatch.setattr(actions.psutil, "sensors_battery", lambda: None)
    assert run("battery", config) == "बैटरी जानकारी उपलब्ध नहीं है"


def test_battery_present(monkeypatch, config):
    Battery = namedtuple("Battery", "percent secsleft power_plugged")
    monkeypatch.setattr(actions.psutil, "sensors_battery", lambda: Battery(81.6, 0, True))
    assert run("battery", config) == "बैटरी 82 प्रतिशत है"


@pytest.mark.parametrize("intent", ["shutdown", "restart"])
def test_execute_intent_never_runs_power_commands(intent, config):
    runner = Recorder()
    reply = run(intent, config, runner=runner)
    assert "हाँ या नहीं" in reply
    assert runner.calls == []


def test_power_action_uses_fixed_noninteractive_sudo():
    runner = Recorder()
    assert actions.power_action("shutdown", runner)
    assert actions.power_action("restart", runner)
    assert runner.calls == [
        ["sudo", "-n", "shutdown", "-h", "now"],
        ["sudo", "-n", "reboot"],
    ]


def test_power_action_reports_failure():
    assert not actions.power_action("shutdown", Recorder(returncode=1))
    assert not actions.power_action("shutdown", Recorder(exc=FileNotFoundError()))


def test_power_action_rejects_other_intents():
    with pytest.raises(ValueError):
        actions.power_action("time", Recorder())


def test_volume_up_and_down(config):
    runner = Recorder()
    assert run("volume_up", config, runner=runner) == "आवाज़ बढ़ा दी गई है।"
    assert run("volume_down", config, runner=runner) == "आवाज़ कम कर दी गई है।"
    assert runner.calls == [
        ["amixer", "-q", "sset", "Master", "10%+"],
        ["amixer", "-q", "sset", "Master", "10%-"],
    ]


def test_volume_without_amixer(config):
    reply = run("volume_up", config, runner=Recorder(exc=FileNotFoundError()))
    assert reply == "आवाज़ बदलने का कंट्रोल उपलब्ध नहीं है।"


def test_note_is_saved_with_timestamp(config):
    assert run("note", config, payload="दूध लाना है") == "नोट सेव कर दिया गया है"
    content = (config.data_dir / "notes.txt").read_text(encoding="utf-8")
    assert content == "2026-03-02T09:05:00\tदूध लाना है\n"


def test_reminder_is_saved(config):
    run("reminder", config, payload="दवा लेनी है")
    assert "दवा लेनी है" in (config.data_dir / "reminders.txt").read_text(encoding="utf-8")


def test_empty_note_is_not_saved(config):
    assert "क्या लिखना है" in run("note", config, payload="")
    assert not (config.data_dir / "notes.txt").exists()


def test_unknown_intent(config):
    assert run("unknown", config) == actions.UNKNOWN_REPLY


def test_greeting_uses_priya_name(config):
    assert "प्रिया" in run("greeting", config)
