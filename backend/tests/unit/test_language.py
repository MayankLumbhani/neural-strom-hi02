"""Tests for registry-driven script and language detection."""

from dataclasses import replace

import pytest

from grievance.nlp.language import detect_language
from grievance.nlp.languages import FALLBACK_LANGUAGE_CODES, LANGUAGES, SCRIPT_RANGES
from grievance.nlp.template_loader import load_templates


@pytest.mark.parametrize(
    ("text", "expected_code"),
    [
        ("Water supply is not working on my street.", "en"),
        ("मेरे घर में पानी नहीं है", "hi"),
        ("મારા વિસ્તારમાં પાણી આવતું નથી", "gu"),
        ("Mere ghar mein paani nahi aa raha hai", "hinglish"),
        ("माझ्या भागात पाणी नाही, कृपया मदत करा", "mr"),
        ("আমার এলাকায় জল নেই", "bn"),
        ("எங்கள் தெருவில் தண்ணீர் இல்லை", "ta"),
        ("మా వీధిలో నీరు రావడం లేదు", "te"),
        ("ನಮ್ಮ ಬೀದಿಯಲ್ಲಿ ನೀರು ಬರುತ್ತಿಲ್ಲ", "kn"),
        ("ഞങ്ങളുടെ തെരുവിൽ വെള്ളമില്ല", "ml"),
        ("ਸਾਡੀ ਗਲੀ ਵਿੱਚ ਪਾਣੀ ਨਹੀਂ ਆ ਰਿਹਾ", "pa"),
    ],
)
def test_detect_language_for_every_registry_entry(text: str, expected_code: str) -> None:
    """Detect every language registered for supported input scripts."""
    detection = detect_language(text)

    assert detection.language is not None
    assert detection.language.code == expected_code
    assert detection.reply_languages == (LANGUAGES[expected_code],)
    assert detection.script == LANGUAGES[expected_code].script


def test_devanagari_without_language_markers_defaults_to_hindi() -> None:
    """Use Hindi when Devanagari markers do not distinguish Hindi from Marathi."""
    detection = detect_language("नमस्ते पानी")

    assert detection.language is not None
    assert detection.language.code == "hi"


@pytest.mark.parametrize("text", ["", "مرحبا", "שלום", "helloo नमस्ते"])
def test_unknown_or_ambiguous_scripts_fall_back_to_english_and_hindi(text: str) -> None:
    """Return both configured fallback reply languages when input is unsupported."""
    detection = detect_language(text)

    assert detection.language is None
    assert tuple(language.code for language in detection.reply_languages) == FALLBACK_LANGUAGE_CODES


def test_registry_covers_supported_codes_and_tiers() -> None:
    """Keep the registry limited to the documented language tiers."""
    assert len(LANGUAGES) == 11
    assert {language.tier for language in LANGUAGES.values()} == {1, 2}
    assert all(language.verified == (language.tier == 1) for language in LANGUAGES.values())


def test_registry_contains_metadata_and_template_for_every_language() -> None:
    """Require complete script, font, and template metadata for all entries."""
    assert {language.script for language in LANGUAGES.values()} == set(SCRIPT_RANGES)
    assert all(
        language.code == code
        and language.name_en
        and language.name_native
        and language.script
        and language.font_family
        and language.template_file
        for code, language in LANGUAGES.items()
    )


def test_disabling_a_registry_language_uses_the_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Allow an experimental language to be disabled centrally."""
    monkeypatch.setitem(LANGUAGES, "bn", replace(LANGUAGES["bn"], enabled=False))

    detection = detect_language("আমার এলাকায় জল নেই")

    assert detection.language is None
    assert tuple(language.code for language in detection.reply_languages) == FALLBACK_LANGUAGE_CODES
    with pytest.raises(ValueError, match="disabled language code"):
        load_templates("bn")
