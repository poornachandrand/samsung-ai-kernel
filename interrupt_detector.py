from dataclasses import dataclass, field
from typing import Dict, Optional
import re


@dataclass
class InterruptionResult:
    interrupted: bool
    interruption_type: str
    new_goal: Optional[str] = None
    slots: Dict[str, str] = field(default_factory=dict)
    changed_slots: Dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0
    reason: str = ""

    def to_dict(self):
        return {
            "interrupted": self.interrupted,
            "interruption_type": self.interruption_type,
            "new_goal": self.new_goal,
            "slots": self.slots,
            "changed_slots": self.changed_slots,
            "confidence": self.confidence,
            "reason": self.reason,
        }


class InterruptDetector:

    CORRECTION_WORDS = [
        "actually",
        "wait",
        "no",
        "nope",
        "sorry",
        "instead",
        "rather",
        "change that",
        "make that",
        "make it",
        "i meant",
        "i mean",
        "correction",
        "hold on",
        "hang on",
        "never mind",
    ]

    CONSTRAINT_WORDS = [
        "also",
        "additionally",
        "plus",
        "as well",
        "too",
    ]

    CITIES = [
        "bangalore",
        "bengaluru",
        "mumbai",
        "delhi",
        "new delhi",
        "hyderabad",
        "chennai",
        "kolkata",
        "pune",
        "ahmedabad",
        "jaipur",
        "goa",
        "kochi",
        "lucknow",
        "indore",
        "bhopal",
        "nagpur",
        "surat",
        "patna",
        "varanasi",
        "chandigarh",
        "dubai",
        "london",
        "paris",
        "singapore",
        "new york",
        "los angeles",
    ]

    DATE_WORDS = [
        "day after tomorrow",
        "next week",
        "next month",
        "today",
        "tomorrow",
        "tonight",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    def classify_interruption(
        self,
        previous_text: str,
        current_text: str,
    ) -> InterruptionResult:

        current = self._clean(current_text)
        previous = self._clean(previous_text)

        if not current:
            return InterruptionResult(
                interrupted=False,
                interruption_type="none",
                confidence=1.0,
                reason="Empty current utterance.",
            )

        current_slots = self.extract_slots(current)
        previous_slots = self.extract_slots(previous)

        correction_signal = self._has_correction_signal(current)

        changed_slots = {}

        for key, value in current_slots.items():
            if key not in previous_slots:
                changed_slots[key] = value
            elif previous_slots[key] != value:
                changed_slots[key] = value

        # Explicit correction always takes priority.
        if correction_signal:
            return InterruptionResult(
                interrupted=True,
                interruption_type="correction",
                new_goal=self.parse_new_goal(current),
                slots=current_slots,
                changed_slots=changed_slots,
                confidence=0.95,
                reason="Correction/interruption language detected.",
            )

        # "Also", "plus", etc. means the user is adding information,
        # not replacing the existing task.
        if self._has_constraint_signal(current):
            return InterruptionResult(
                interrupted=False,
                interruption_type="constraint",
                new_goal=None,
                slots=current_slots,
                changed_slots={},
                confidence=0.85,
                reason="Additional constraint detected rather than replacement.",
            )

        # If an existing slot changed without explicit correction words,
        # treat it as an interruption.
        if changed_slots and previous_slots:
            return InterruptionResult(
                interrupted=True,
                interruption_type="correction",
                new_goal=self.parse_new_goal(current),
                slots=current_slots,
                changed_slots=changed_slots,
                confidence=0.85,
                reason="Existing intent slot changed.",
            )

        return InterruptionResult(
            interrupted=False,
            interruption_type="none",
            new_goal=None,
            slots=current_slots,
            changed_slots={},
            confidence=0.80,
            reason="No clear interruption detected.",
        )

    def extract_slots(self, text: str) -> Dict[str, str]:

        text = self._clean(text)
        slots = {}

        # Example:
        # from Bangalore to Delhi
        match = re.search(
            r"\bfrom\s+(.+?)\s+to\s+(.+?)(?:\s+(?:on|for|tomorrow|today|next|this)\b|$)",
            text,
            re.IGNORECASE,
        )

        if match:
            origin = self._normalise_city(match.group(1))
            destination = self._normalise_city(match.group(2))

            if origin:
                slots["origin"] = origin

            if destination:
                slots["destination"] = destination

        # Example:
        # make that Mumbai
        # make it Mumbai
        # instead Mumbai
        correction_destination = re.search(
            r"\b(?:make\s+(?:that|it)|instead(?:\s+of)?|to)\s+"
            r"([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\b",
            text,
            re.IGNORECASE,
        )

        if correction_destination:
            possible_city = self._normalise_city(
                correction_destination.group(1)
            )

            if possible_city:
                slots["destination"] = possible_city

        # Explicit "to Mumbai"
        if "destination" not in slots:
            match = re.search(
                r"\bto\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)\b",
                text,
                re.IGNORECASE,
            )

            if match:
                possible_city = self._normalise_city(
                    match.group(1)
                )

                if possible_city:
                    slots["destination"] = possible_city

        # Date
        date = self._extract_date(text)

        if date:
            slots["date"] = date

        # Trip type
        if re.search(
            r"\breturn\b|\bround trip\b",
            text,
            re.IGNORECASE,
        ):
            slots["trip_type"] = "return"

        elif re.search(
            r"\bone way\b|\bone-way\b",
            text,
            re.IGNORECASE,
        ):
            slots["trip_type"] = "one_way"

        # Time
        # Examples:
        # 2 PM
        # 2:30 PM
        # 10 AM
        # 10:30 AM
        time_match = re.search(
            r"\b\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)\b",
            text,
            re.IGNORECASE,
        )

        if time_match:
            slots["time"] = time_match.group(0).upper()

        return slots

    def parse_new_goal(self, text: str) -> str:

        text = self._clean(text)

        patterns = [
            r"^\s*actually\s+",
            r"^\s*wait\s+",
            r"^\s*wait,\s*",
            r"^\s*no\s+",
            r"^\s*no,\s*",
            r"^\s*sorry\s+",
            r"^\s*hold on\s+",
            r"^\s*hang on\s+",
            r"^\s*i mean\s+",
            r"^\s*i meant\s+",
            r"^\s*correction\s*:\s*",
        ]

        cleaned = text

        for pattern in patterns:
            cleaned = re.sub(
                pattern,
                "",
                cleaned,
                flags=re.IGNORECASE,
            )

        cleaned = re.sub(
            r"^\s*(?:make\s+(?:that|it)|instead)\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned

    def _extract_date(self, text: str) -> Optional[str]:

        text = self._clean(text)

        for date_word in sorted(
            self.DATE_WORDS,
            key=len,
            reverse=True,
        ):
            if re.search(
                rf"\b{re.escape(date_word)}\b",
                text,
                re.IGNORECASE,
            ):
                return date_word

        numeric_date = re.search(
            r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b",
            text,
        )

        if numeric_date:
            return numeric_date.group(0)

        return None

    def _has_correction_signal(self, text: str) -> bool:

        text = self._clean(text)

        for phrase in self.CORRECTION_WORDS:
            if re.search(
                rf"\b{re.escape(phrase)}\b",
                text,
                re.IGNORECASE,
            ):
                return True

        return False

    def _has_constraint_signal(self, text: str) -> bool:

        text = self._clean(text)

        for phrase in self.CONSTRAINT_WORDS:
            if re.search(
                rf"\b{re.escape(phrase)}\b",
                text,
                re.IGNORECASE,
            ):
                return True

        return False

    def _normalise_city(self, value: str) -> Optional[str]:

        value = value.strip().lower()

        value = re.sub(r"[,.!?]", "", value)
        value = re.sub(r"\s+", " ", value).strip()

        for city in sorted(
            self.CITIES,
            key=len,
            reverse=True,
        ):
            if city == value:

                if city in ("bangalore", "bengaluru"):
                    return "Bangalore"

                if city == "new delhi":
                    return "New Delhi"

                return city.title()

        return None

    @staticmethod
    def _clean(text: str) -> str:

        if text is None:
            return ""

        text = str(text).strip()
        text = re.sub(r"\s+", " ", text)

        return text