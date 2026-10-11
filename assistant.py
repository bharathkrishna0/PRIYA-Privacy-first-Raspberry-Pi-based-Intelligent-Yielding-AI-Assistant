"""Conversation state machine: wake phrase, one command, confirmation, follow-up.

This module has no audio or hardware dependencies so it can be unit-tested
with plain strings.
"""

from __future__ import annotations

import datetime
import logging
import subprocess
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

import actions
from config import Config
from intent_engine import UNKNOWN, is_affirmative, match_intent, normalize

logger = logging.getLogger(__name__)

WAKE_REPLY = "जी प्रिया जी, बताइए।"
CANCELLED_REPLY = "ठीक है, रद्द कर दिया।"
POWER_DISABLED_REPLY = "यह कमांड इस डिवाइस पर बंद है।"
POWER_FAILED_REPLY = "माफ़ कीजिए, यह कमांड चल नहीं पाई।"
FOLLOW_UP_WORD = "और"


@dataclass
class Reply:
    text: str
    intent: Optional[str] = None
    after_speech: Optional[Callable[[], None]] = field(default=None, repr=False, compare=False)


class Assistant:
    """Turns final transcripts into replies.

    Flow: idle -> (wake phrase) -> listening -> (one command) -> idle.
    Shutdown/restart move to an extra confirmation state that needs "हाँ".
    """

    def __init__(
        self,
        config: Optional[Config] = None,
        *,
        runner: Callable[..., object] = subprocess.run,
        clock: Callable[[], float] = time.monotonic,
        now: Callable[[], datetime.datetime] = datetime.datetime.now,
    ) -> None:
        self.config = config or Config()
        self.runner = runner
        self.clock = clock
        self.now = now
        self.listening_since: Optional[float] = None
        self.pending_power: Optional[str] = None
        self.pending_since: float = 0.0
        self.memory: Dict[str, Optional[str]] = {
            "last_intent": None,
            "last_response": None,
        }

    @property
    def listening(self) -> bool:
        if self.listening_since is None:
            return False
        if self.clock() - self.listening_since > self.config.listen_timeout_s:
            self.listening_since = None
            return False
        return True

    def _strip_wake(self, text: str) -> Optional[str]:
        for wake in sorted(self.config.wake_words, key=len, reverse=True):
            index = text.find(wake)
            if index != -1:
                return normalize(text[:index] + " " + text[index + len(wake) :])
        return None

    def handle(self, transcript: str) -> Optional[Reply]:
        text = normalize(transcript)
        if not text:
            return None
        logger.debug("Transcript: %s", text)

        if self.pending_power is not None:
            return self._handle_confirmation(text)

        remainder = self._strip_wake(text)
        if remainder is not None:
            self.listening_since = self.clock()
            if not remainder:
                return Reply(WAKE_REPLY, intent="wake")
            text = remainder
        elif not self.listening:
            logger.debug("Ignored (no wake phrase)")
            return None

        self.listening_since = None
        return self._handle_command(text)

    def _handle_command(self, text: str) -> Reply:
        match = match_intent(text, self.config.intent_threshold)
        intent = match.intent
        if intent == UNKNOWN and FOLLOW_UP_WORD in text.split() and self.memory["last_intent"]:
            intent = self.memory["last_intent"]
            logger.info("Follow-up: repeating %s", intent)
        logger.info("Intent: %s (score %.0f)", intent, match.score)

        if intent in actions.POWER_INTENTS:
            if not self.config.enable_power_commands:
                return Reply(POWER_DISABLED_REPLY, intent=intent)
            self.pending_power = intent
            self.pending_since = self.clock()
            return Reply(actions.power_confirmation_prompt(intent), intent=intent)

        response = actions.execute_intent(
            intent,
            text,
            self.memory,
            payload=match.payload,
            config=self.config,
            runner=self.runner,
            now=self.now(),
        )
        if intent != UNKNOWN:
            self.memory["last_intent"] = intent
            self.memory["last_response"] = response
        return Reply(response, intent=intent)

    def _handle_confirmation(self, text: str) -> Optional[Reply]:
        intent = self.pending_power
        expired = self.clock() - self.pending_since > self.config.confirm_timeout_s
        self.pending_power = None
        if expired:
            logger.info("Confirmation for %s expired", intent)
            return self.handle(text)
        if not is_affirmative(text):
            return Reply(CANCELLED_REPLY, intent="cancel")

        def run_power() -> None:
            if not actions.power_action(intent, self.runner):
                logger.error("%s command failed (is passwordless sudo configured?)", intent)

        return Reply(actions.power_started_reply(intent), intent=intent, after_speech=run_power)
