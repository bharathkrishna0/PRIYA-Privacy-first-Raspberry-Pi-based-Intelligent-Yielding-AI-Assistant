import datetime
import subprocess

import pytest

from assistant import CANCELLED_REPLY, POWER_DISABLED_REPLY, WAKE_REPLY, Assistant
from config import Config


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append(command)
        return subprocess.CompletedProcess(command, 0)


@pytest.fixture
def env(tmp_path):
    clock = FakeClock()
    runner = Recorder()
    assistant = Assistant(
        Config(data_dir=tmp_path),
        runner=runner,
        clock=clock,
        now=lambda: datetime.datetime(2026, 3, 2, 9, 5),
    )
    return assistant, clock, runner


def test_ignores_commands_without_wake_phrase(env):
    assistant, _, _ = env
    assert assistant.handle("समय क्या है") is None
    assert assistant.handle("धन्यवाद") is None


def test_ignores_empty_transcripts(env):
    assistant, _, _ = env
    assert assistant.handle("") is None
    assert assistant.handle("   ") is None


def test_wake_then_command(env):
    assistant, _, _ = env
    assert assistant.handle("प्रिया जी").text == WAKE_REPLY
    reply = assistant.handle("समय क्या है")
    assert (reply.intent, reply.text) == ("time", "अभी समय है 09:05")


def test_one_command_per_wake(env):
    assistant, _, _ = env
    assistant.handle("प्रिया जी")
    assistant.handle("समय क्या है")
    assert assistant.handle("आज कौन सा दिन है") is None


def test_wake_and_command_in_one_utterance(env):
    assistant, _, _ = env
    assert assistant.handle("प्रिया जी आज कौन सा दिन है").intent == "day"


def test_listening_times_out(env):
    assistant, clock, _ = env
    assistant.handle("प्रिया जी")
    clock.t += assistant.config.listen_timeout_s + 1
    assert assistant.handle("समय क्या है") is None


def test_follow_up_repeats_last_intent(env):
    assistant, _, _ = env
    assistant.handle("प्रिया जी आज कौन सा दिन है")
    assert assistant.handle("प्रिया जी और").intent == "day"


def test_unknown_command_is_answered_but_not_remembered(env):
    assistant, _, _ = env
    assert assistant.handle("प्रिया जी गाना बजाओ").intent == "unknown"
    assert assistant.memory["last_intent"] is None


def test_shutdown_requires_confirmation(env):
    assistant, _, runner = env
    prompt = assistant.handle("प्रिया जी सिस्टम बंद करो")
    assert "हाँ या नहीं" in prompt.text
    assert prompt.after_speech is None
    reply = assistant.handle("हाँ")
    assert runner.calls == []  # only runs after the reply has been spoken
    reply.after_speech()
    assert runner.calls == [["sudo", "-n", "shutdown", "-h", "now"]]


@pytest.mark.parametrize("answer", ["नहीं", "समय क्या है", "हाँ नहीं"])
def test_anything_but_yes_cancels(env, answer):
    assistant, _, runner = env
    assistant.handle("प्रिया जी सिस्टम रीस्टार्ट करो")
    reply = assistant.handle(answer)
    assert reply.text == CANCELLED_REPLY
    assert reply.after_speech is None
    assert runner.calls == []


def test_confirmation_expires(env):
    assistant, clock, runner = env
    assistant.handle("प्रिया जी सिस्टम बंद करो")
    clock.t += assistant.config.confirm_timeout_s + 1
    assert assistant.handle("हाँ") is None
    assert runner.calls == []


def test_power_commands_can_be_disabled(tmp_path):
    runner = Recorder()
    assistant = Assistant(Config(data_dir=tmp_path, enable_power_commands=False), runner=runner)
    assert assistant.handle("प्रिया जी सिस्टम बंद करो").text == POWER_DISABLED_REPLY
    assert assistant.handle("हाँ") is None
    assert runner.calls == []


def test_note_via_voice_flow(env, tmp_path):
    assistant, _, _ = env
    assistant.handle("प्रिया जी नोट सेव करो दूध लाना है")
    assert "दूध लाना है" in (tmp_path / "notes.txt").read_text(encoding="utf-8")


def test_small_talk_needs_wake_phrase(env):
    assistant, _, _ = env
    assert assistant.handle("कैसे हो") is None
    assert assistant.handle("प्रिया जी कैसे हो").intent == "wellbeing"
