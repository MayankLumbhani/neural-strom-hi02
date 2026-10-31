"""Tests for the localized fixed-message templates."""

import re
from importlib.resources import files

from grievance.nlp.languages import LANGUAGES
from grievance.nlp.template_loader import (
    REQUIRED_TEMPLATE_KEYS,
    load_templates,
    template_keys,
)


def test_every_registered_language_has_identical_template_keys() -> None:
    """Ensure every language template provides the full architecture-defined key set."""
    key_sets = {template_keys(load_templates(language_code)) for language_code in LANGUAGES}

    assert key_sets == {REQUIRED_TEMPLATE_KEYS}


def test_tier_two_templates_are_marked_machine_translated() -> None:
    """Label experimental templates as machine-translated and unverified."""
    for language in LANGUAGES.values():
        if language.tier == 2:
            header = (
                files("grievance.nlp.templates")
                .joinpath(language.template_file)
                .read_text(encoding="utf-8")
                .splitlines()[0]
            )
            assert "Machine-translated" in header
            assert "not verified by native speakers" in header


def test_ticket_messages_have_consistent_format_placeholders() -> None:
    """Keep message interpolation fields aligned across localized templates."""
    placeholders_by_language: dict[str, set[str]] = {}
    for language_code in LANGUAGES:
        templates = load_templates(language_code)
        placeholders_by_language[language_code] = set(
            re.findall(r"{([^}]+)}", templates.ticket_created)
        ) | set(re.findall(r"{([^}]+)}", templates.status_reply))

    assert set().union(*placeholders_by_language.values()) == {
        "ticket_id",
        "department",
        "status",
    }
    assert all(
        placeholders == {"ticket_id", "department", "status"}
        for placeholders in placeholders_by_language.values()
    )
