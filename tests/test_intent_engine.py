import pytest

from intent_engine import (
    INTENTS,
    UNKNOWN,
    detect_intent,
    grammar_phrases,
    is_affirmative,
    is_negative,
    match_intent,
    normalize,
)


@pytest.mark.parametrize(
    "intent,phrase",
    [(intent, phrase) for intent, phrases in INTENTS.items() for phrase in phrases],
)
def test_every_example_phrase_maps_to_its_intent(intent, phrase):
    assert detect_intent(phrase) == intent


@pytest.mark.parametrize(
    "text,expected",
    [
        ("अभी समय क्या है", "time"),
        ("कौन सा दिन है", "day"),
        ("सीपीयू का उपयोग", "cpu"),
        ("सिस्टम की जानकारी", "system_info"),
        ("मजाक सुनाओ ना", "joke"),
    ],
)
def test_close_variants_match(text, expected):
    assert detect_intent(text) == expected


@pytest.mark.parametrize("text", ["मौसम कैसा है", "बत्ती बंद करो", "गाना बजाओ", "दरवाजा बंद करो"])
def test_out_of_scope_requests_are_unknown(text):
    assert detect_intent(text) == UNKNOWN


def test_empty_text_is_unknown():
    assert match_intent("   ").intent == UNKNOWN


def test_normalize_strips_punctuation_and_case():
    assert normalize("  Priya   Ji, समय क्या है।  ") == "priya ji समय क्या है"


def test_note_prefix_returns_payload():
    match = match_intent("नोट सेव करो दूध लाना है")
    assert (match.intent, match.payload) == ("note", "दूध लाना है")


def test_note_suffix_returns_payload():
    match = match_intent("कल बैंक जाना है लिख लो")
    assert (match.intent, match.payload) == ("note", "कल बैंक जाना है")


def test_reminder_prefix():
    match = match_intent("रिमाइंडर सेट करो दवा लेनी है")
    assert (match.intent, match.payload) == ("reminder", "दवा लेनी है")


def test_threshold_is_respected():
    assert match_intent("समय क्या", threshold=99).intent == UNKNOWN


@pytest.mark.parametrize("text", ["हाँ", "हां", "जी हाँ", "हाँ जी बिल्कुल"])
def test_affirmative(text):
    assert is_affirmative(text)


@pytest.mark.parametrize("text", ["नहीं", "हाँ नहीं", "रद्द करो", "पता नहीं"])
def test_not_affirmative(text):
    assert not is_affirmative(text)
    assert is_negative(text)


def test_affirmative_needs_whole_word():
    assert not is_affirmative("यहाँ")


def test_grammar_contains_wake_word_and_commands():
    phrases = grammar_phrases(["प्रिया जी"])
    assert "प्रिया जी" in phrases
    assert "समय क्या है" in phrases
    assert "हाँ" in phrases
    assert len(phrases) == len(set(phrases))
