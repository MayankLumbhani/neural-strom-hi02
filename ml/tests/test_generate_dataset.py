"""Tests for LLM-generated synthetic complaint data."""

import csv
import json
from pathlib import Path

import pytest
from generate_dataset import (
    GenerationConfig,
    _build_prompt,
    generate_dataset,
    parse_batch_response,
    require_gemini_model,
    validate_complaint,
    write_dataset,
)

from grievance.core.config import Settings


class FakeClient:
    """Return queued JSON responses without making network calls."""

    def __init__(self, responses: list[str]) -> None:
        """Store fake responses and initialize the call count."""
        self.responses = responses
        self.calls = 0
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        """Return the next response from the local queue."""
        self.prompts.append(prompt)
        response = self.responses[self.calls]
        self.calls += 1
        return response


def _config(count: int = 2) -> GenerationConfig:
    """Use tiny dataset strata for fast offline tests."""
    return GenerationConfig(
        seed=17,
        tier1_samples_per_class_language=count,
        tier2_samples_per_class_language=count,
    )


def _valid_english_complaints() -> list[str]:
    """Return distinct fictional English examples that pass validation."""
    return [
        "Water pipe leaking near fictional Ward 8 since Monday morning",
        "Please inspect the fictional canal road after three rainy days",
        "The invented street light has stayed dark since last Thursday",
        "Fictional Ward 4 has overflowing bins for nearly two weeks",
        "A made-up road near the Clockless Park has a deep pothole",
        "Could someone check the invented drain after yesterday's storm",
        "The fictional power line has flickered every evening this week",
        "Mosquitoes have gathered near the imaginary garden for four days",
        "My fictional property bill lists an incorrect amount this month",
        "Water pressure dropped along the invented Crescent Lane yesterday",
        "The imaginary market road has loose stones after recent repairs",
        "Uncollected rubbish has piled up beside fictional Ward 12 today",
        "A dark lamp near the made-up library needs attention this week",
        "The invented sewer has backed up for two nights in a row",
        "Please review the fictional service issue reported last weekend",
    ]


@pytest.mark.parametrize(
    "response",
    [
        '```json\n["complaint"]\n```',
        '{"complaint": "not a list"}',
        '["valid", 4]',
        "['single quotes are not JSON']",
    ],
)
def test_batch_parser_rejects_non_strict_json(response: str) -> None:
    """Reject prose, wrong shapes, non-string items, and invalid JSON."""
    with pytest.raises(ValueError, match="strict JSON list"):
        parse_batch_response(response)


def test_batch_parser_accepts_only_a_json_list_of_strings() -> None:
    """Trim complaint strings while preserving the strict JSON list shape."""
    assert parse_batch_response('["  fictional complaint  ", "another complaint"]') == [
        "fictional complaint",
        "another complaint",
    ]


@pytest.mark.parametrize(
    ("text", "script", "reason"),
    [
        ("The The water is not flowing near a fictional ward", "Latin", "repeated_words"),
        ("There is water trouble in fictional Ward 8; call 123 456 7890", "Latin", "phone_number"),
        ("पानी नहीं आ रहा है और समस्या कई दिनों से जारी है", "Latin", "script"),
        ("Water supply has failed across fictional Ward 8", "Devanagari", "script"),
    ],
)
def test_validation_drops_invalid_script_repeats_and_phone_numbers(
    text: str,
    script: str,
    reason: str,
) -> None:
    """Drop complaints with wrong scripts, repeated adjacent words, or phone-like digits."""
    complaint, rejection = validate_complaint(text, script)

    assert complaint is None
    assert rejection == reason


def test_validation_strips_and_keeps_a_valid_complaint() -> None:
    """Retain a length-valid complaint written in the configured script."""
    complaint, rejection = validate_complaint(
        "  Water is unavailable near fictional Ward 8 since yesterday  ",
        "Latin",
    )

    assert complaint == "Water is unavailable near fictional Ward 8 since yesterday"
    assert rejection is None


def test_generation_deduplicates_exact_and_near_duplicate_text(tmp_path: Path) -> None:
    """Drop normalized repeats and near copies before filling each stratum."""
    first = "Water pipe leaking beside fictional Ward 8 since Monday morning"
    near = "Water pipe leaking beside the fictional Ward 8 since Monday morning"
    distinct = "The invented pump has stopped working since early Tuesday morning"
    responses = [json.dumps([first, first.lower(), near, distinct])]
    client = FakeClient(responses)

    split = generate_dataset(client, _config(), tmp_path, "test-model", batch_limit=1)
    generated = split.train + split.validation

    assert len(generated) == 2
    assert len({row["text"].casefold() for row in generated}) == 2
    assert near not in {row["text"] for row in generated}
    assert distinct in {row["text"] for row in generated}
    assert client.calls == 1


def test_generation_resumes_from_cached_batch_without_network_call(tmp_path: Path) -> None:
    """Reuse the raw cached batch when the same model and stratum are requested."""
    responses = [json.dumps(_valid_english_complaints())]
    first_client = FakeClient(responses)
    first_split = generate_dataset(first_client, _config(), tmp_path, "test-model", batch_limit=1)

    resumed_client = FakeClient([])
    resumed_split = generate_dataset(
        resumed_client, _config(), tmp_path, "test-model", batch_limit=1
    )

    assert first_client.calls == 1
    assert resumed_client.calls == 0
    assert first_split == resumed_split
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_split_is_stratified_and_has_no_text_overlap(tmp_path: Path) -> None:
    """Split each processed language/label stratum and prevent cross-split leakage."""
    client = FakeClient(
        [json.dumps(_valid_english_complaints()), json.dumps(_valid_english_complaints()[2:])]
    )
    split = generate_dataset(client, _config(), tmp_path, "test-model", batch_limit=2)

    train_texts = {row["text"].casefold() for row in split.train}
    validation_texts = {row["text"].casefold() for row in split.validation}
    train_strata = {(row["language"], row["label"]) for row in split.train}
    validation_strata = {(row["language"], row["label"]) for row in split.validation}

    assert train_texts.isdisjoint(validation_texts)
    assert train_strata == validation_strata
    assert len(train_strata) == 2
    assert client.calls == 2
    assert all(row["source"] == "llm" for row in split.train + split.validation)


def test_other_prompt_requires_varied_ambiguous_municipal_complaints() -> None:
    """Prompt OTHER examples to cover vague, general, and uncategorized issues."""
    prompt = _build_prompt("en", "OTHER", 15)

    assert "vague or ambiguous complaints" in prompt
    assert "general municipal questions" in prompt
    assert "fit none of the other departments" in prompt
    assert "multiple distinct examples of each type" in prompt
    assert "Do not repeat or closely paraphrase" in prompt
    assert "About 25%" in prompt


def test_prompt_uses_registry_scripts_and_romanized_hinglish() -> None:
    """Use registry scripts for native-script languages and Latin for Hinglish."""
    hindi_prompt = _build_prompt("hi", "WATER", 15)
    gujarati_prompt = _build_prompt("gu", "WATER", 15)
    bengali_prompt = _build_prompt("bn", "WATER", 15)
    hinglish_prompt = _build_prompt("hinglish", "WATER", 15)

    assert "Devanagari script" in hindi_prompt
    assert "Gujarati script" in gujarati_prompt
    assert "Bengali script" in bengali_prompt
    assert "romanized Hindi" in hinglish_prompt


def test_write_dataset_preserves_columns_and_adds_llm_source(tmp_path: Path) -> None:
    """Write the established schema with tier and LLM provenance metadata."""
    client = FakeClient([json.dumps(_valid_english_complaints())])
    split = generate_dataset(client, _config(), tmp_path / "cache", "test-model", batch_limit=1)
    train_path, validation_path = write_dataset(tmp_path / "processed", split)

    with train_path.open(encoding="utf-8-sig", newline="") as train_file:
        train_rows = list(csv.DictReader(train_file))
    with validation_path.open(encoding="utf-8-sig", newline="") as validation_file:
        validation_rows = list(csv.DictReader(validation_file))

    expected_columns = {
        "text",
        "label",
        "language",
        "tier",
        "variation",
        "verified",
        "source",
    }
    assert set(train_rows[0]) == expected_columns
    assert all(row["tier"] == "1" for row in train_rows + validation_rows)
    assert all(row["source"] == "llm" for row in train_rows + validation_rows)
    assert all(row["verified"] == "false" for row in train_rows + validation_rows)


def test_unset_gemini_model_fails_with_clear_configuration_error() -> None:
    """Fail before any request when GEMINI_MODEL is absent."""
    with pytest.raises(RuntimeError, match="GEMINI_MODEL must be configured"):
        require_gemini_model(Settings(_env_file=None, gemini_model=None))
