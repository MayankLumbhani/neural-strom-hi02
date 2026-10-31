"""Script-based language detection for supported complaint text."""

from collections import Counter
from dataclasses import dataclass
from unicodedata import category, normalize

from grievance.nlp.languages import (
    FALLBACK_LANGUAGE_CODES,
    LANGUAGES,
    SCRIPT_RANGES,
    Language,
)


@dataclass(frozen=True)
class LanguageDetection:
    """Detected language, script, and languages to use for a reply."""

    language: Language | None
    script: str | None
    reply_languages: tuple[Language, ...]


def _script_counts(text: str) -> Counter[str]:
    """Count supported-script characters represented in the registry."""
    counts: Counter[str] = Counter()
    for character in text:
        codepoint = ord(character)
        for script, ranges in SCRIPT_RANGES.items():
            if any(start <= codepoint <= end for start, end in ranges):
                counts[script] += 1
                break
    return counts


def _dominant_script(counts: Counter[str]) -> str | None:
    """Return a unique dominant script or None when no script is identifiable."""
    if not counts:
        return None
    largest_count = max(counts.values())
    dominant = [script for script, count in counts.items() if count == largest_count]
    return dominant[0] if len(dominant) == 1 else None


def _marker_count(text: str, language: Language) -> int:
    """Count whole-word language markers from the central registry."""
    words: Counter[str] = Counter()
    current_word: list[str] = []
    for character in normalize("NFC", text.casefold()):
        if category(character)[0] in {"L", "M", "N"}:
            current_word.append(character)
        elif current_word:
            words["".join(current_word)] += 1
            current_word.clear()
    if current_word:
        words["".join(current_word)] += 1
    return sum(words[marker.casefold()] for marker in language.detection_markers)


def _select_language(text: str, script: str) -> Language | None:
    """Select a registry language for a script using its configured markers."""
    candidates = [
        language
        for language in LANGUAGES.values()
        if language.enabled and language.script == script
    ]
    if not candidates:
        return None

    marker_scores = {language: _marker_count(text, language) for language in candidates}
    highest_score = max(marker_scores.values())
    if highest_score:
        winners = [language for language, score in marker_scores.items() if score == highest_score]
        if len(winners) == 1:
            return winners[0]

    return next(
        (language for language in candidates if language.default_for_script),
        None,
    )


def detect_language(text: str) -> LanguageDetection:
    """Detect a supported language or request an English-and-Hindi fallback reply."""
    script = _dominant_script(_script_counts(text))
    language = _select_language(text, script) if script is not None else None
    if language is not None:
        return LanguageDetection(language, script, (language,))

    fallback_languages = tuple(LANGUAGES[code] for code in FALLBACK_LANGUAGE_CODES)
    return LanguageDetection(None, script, fallback_languages)
