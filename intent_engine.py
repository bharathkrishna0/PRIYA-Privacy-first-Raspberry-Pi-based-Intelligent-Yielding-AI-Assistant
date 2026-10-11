"""Fuzzy intent matching for Hindi transcripts produced by Vosk.

Matching uses RapidFuzz ``ratio`` against short example phrases, so a
transcript has to be close to a whole phrase. Note and reminder commands are
matched by a trigger phrase at the start or end, and the rest of the
transcript is returned as the payload to save.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from rapidfuzz import fuzz

DEFAULT_THRESHOLD = 75.0
UNKNOWN = "unknown"

INTENTS: Dict[str, List[str]] = {
    "time": ["समय क्या है", "अभी कितने बजे हैं", "समय बताओ"],
    "date": ["आज की तारीख क्या है", "तारीख बताओ"],
    "day": ["आज कौन सा दिन है"],
    "cpu": ["सीपीयू उपयोग", "सिस्टम लोड"],
    "memory": ["मेमोरी उपयोग", "रैम उपयोग"],
    "disk": ["डिस्क उपयोग", "स्टोरेज कितना है"],
    "battery": ["बैटरी स्थिति", "बैटरी कितनी है"],
    "system_info": ["सिस्टम जानकारी"],
    "shutdown": ["सिस्टम बंद करो"],
    "restart": ["सिस्टम रीस्टार्ट करो"],
    "volume_up": ["आवाज़ बढ़ाओ", "आवाज बढ़ाओ", "वॉल्यूम बढ़ाओ"],
    "volume_down": ["आवाज़ कम करो", "आवाज कम करो", "वॉल्यूम कम करो"],
    "joke": ["मजाक सुनाओ", "मज़ाक सुनाओ", "जोक सुनाओ"],
    "motivation": ["प्रेरणा दो", "मोटिवेशन दो"],
    "greeting": ["नमस्ते", "हेलो"],
    "wellbeing": ["कैसे हो", "आप कैसे हो"],
    "thanks": ["धन्यवाद", "शुक्रिया"],
    "conversation": ["बात करो"],
}

# Commands whose trigger phrase is followed (or preceded) by free text to save.
PREFIX_INTENTS: Dict[str, Tuple[str, ...]] = {
    "note": ("नोट सेव करो", "नोट लिखो", "लिख लो"),
    "reminder": ("रिमाइंडर सेट करो",),
}

# Backwards-compatible alias for the original module-level name.
intents = INTENTS

AFFIRMATIVE = ("हाँ", "हां", "जी हाँ", "हाँ जी", "बिल्कुल", "ठीक है")
NEGATIVE = ("नहीं", "ना", "मत करो", "रद्द करो", "रद्द")

_PUNCTUATION = re.compile(r"[।,.!?\"']+")
_SPACES = re.compile(r"\s+")


@dataclass(frozen=True)
class IntentMatch:
    intent: str
    score: float
    phrase: Optional[str] = None
    payload: str = ""


def normalize(text: str) -> str:
    text = _PUNCTUATION.sub(" ", text or "").lower()
    return _SPACES.sub(" ", text).strip()


def _match_prefix(text: str) -> Optional[IntentMatch]:
    for intent, triggers in PREFIX_INTENTS.items():
        for trigger in triggers:
            if text == trigger or text.startswith(trigger + " "):
                return IntentMatch(intent, 100.0, trigger, text[len(trigger) :].strip())
            if text.endswith(" " + trigger):
                return IntentMatch(intent, 100.0, trigger, text[: -len(trigger)].strip())
    return None


def match_intent(text: str, threshold: float = DEFAULT_THRESHOLD) -> IntentMatch:
    """Return the best intent for ``text`` or ``UNKNOWN`` below ``threshold``."""
    text = normalize(text)
    if not text:
        return IntentMatch(UNKNOWN, 0.0)

    prefix = _match_prefix(text)
    if prefix:
        return prefix

    best = IntentMatch(UNKNOWN, 0.0)
    for intent, phrases in INTENTS.items():
        for phrase in phrases:
            score = fuzz.ratio(text, phrase)
            if score > best.score:
                best = IntentMatch(intent, score, phrase)

    if best.score > threshold:
        return best
    return IntentMatch(UNKNOWN, best.score, best.phrase)


def detect_intent(text: str, threshold: float = DEFAULT_THRESHOLD) -> str:
    return match_intent(text, threshold).intent


def _contains_phrase(text: str, phrases: Iterable[str]) -> bool:
    padded = f" {normalize(text)} "
    return any(f" {phrase} " in padded for phrase in phrases)


def is_affirmative(text: str) -> bool:
    return _contains_phrase(text, AFFIRMATIVE) and not is_negative(text)


def is_negative(text: str) -> bool:
    return _contains_phrase(text, NEGATIVE)


_DEVANAGARI_PHRASE = re.compile(r"^[\u0900-\u097F ]+$")


def grammar_phrases(wake_words: Iterable[str] = ()) -> List[str]:
    """All phrases PRIYA understands, for Vosk's restricted-grammar mode.

    Non-Devanagari wake words are dropped because the Hindi model cannot emit them.
    """
    phrases = [w for w in wake_words if _DEVANAGARI_PHRASE.match(w)]
    for examples in INTENTS.values():
        phrases.extend(examples)
    for triggers in PREFIX_INTENTS.values():
        phrases.extend(triggers)
    phrases.extend(AFFIRMATIVE)
    phrases.extend(NEGATIVE)
    phrases.append("और")
    return sorted(set(phrases))
