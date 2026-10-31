"""Tests for LLM-generated synthetic complaint data."""

import csv
import json
from pathlib import Path

import generate_dataset as dataset_generator
import httpx
import pytest
from generate_dataset import (
    DEPARTMENT_CODES,
    GenerationConfig,
    _build_prompt,
    _limit_repeated_openers,
    generate_dataset,
    parse_batch_response,
    require_gemini_model,
    validate_complaint,
    write_dataset,
)

from grievance.core.config import Settings
from grievance.nlp.languages import LANGUAGES as LANGUAGE_REGISTRY


class FakeClient:
    """Return queued JSON responses without making network calls."""

    def __init__(self, responses: list[str | Exception]) -> None:
        """Store fake responses and initialize the call count."""
        self.responses = responses
        self.calls = 0
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        """Return the next response from the local queue."""
        self.prompts.append(prompt)
        response = self.responses[self.calls]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response


def _config(count: int = 2, minimum_fraction: float = 0.9) -> GenerationConfig:
    """Use tiny dataset strata for fast offline tests."""
    return GenerationConfig(
        seed=17,
        tier1_samples_per_class_language=count,
        tier2_samples_per_class_language=count,
        minimum_stratum_fraction=minimum_fraction,
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


def _valid_water_complaints(count: int) -> list[str]:
    """Return distinct synthetic English water complaints for shortfall tests."""
    templates = (
        "Water pipe stopped flowing near fictional Ward {ward} since Monday morning",
        "A broken pump has reduced supply in fictional Ward {ward} since yesterday",
        "Residents near fictional Ward {ward} found muddy water in their taps today",
        "The public tap in fictional Ward {ward} has leaked continuously since dawn",
        "Water pressure dropped across fictional Ward {ward} during the afternoon",
        "A supply valve near fictional Ward {ward} is spraying water onto the road",
        "The reservoir feeding fictional Ward {ward} has supplied no water since Tuesday",
        "Several homes in fictional Ward {ward} received discolored water this morning",
        "A damaged pipeline near fictional Ward {ward} is flooding the footpath",
        "The pump serving fictional Ward {ward} makes a loud noise and stops",
    )
    return [templates[index].format(ward=index + 1) for index in range(count)]


def _capture_generator_logs(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Capture formatted generator log records independently of global handlers."""
    messages: list[str] = []

    def record(message: str, *args: object) -> None:
        """Store a formatted log message."""
        messages.append(message % args if args else message)

    monkeypatch.setattr(dataset_generator.logger, "info", record)
    monkeypatch.setattr(dataset_generator.logger, "warning", record)
    return messages


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
    ("text", "language_code", "department_code", "reason"),
    [
        (
            "The The water is not flowing near a fictional ward",
            "en",
            "WATER",
            "repeated_words",
        ),
        (
            "पानी पानी नहीं आ रहा है और समस्या कई दिनों से जारी है",
            "hi",
            "WATER",
            "repeated_words",
        ),
        (
            "There is water trouble in fictional Ward 8; call 123 456 7890",
            "en",
            "WATER",
            "phone_number",
        ),
        ("पानी नहीं आ रहा है और समस्या कई दिनों से जारी है", "en", "WATER", "language"),
        ("Water supply has failed across fictional Ward 8", "hi", "WATER", "language"),
        (
            "Paani nahi aa raha near fictional Ward 8 since yesterday",
            "en",
            "WATER",
            "language",
        ),
        (
            "Water supply is absent near fictional Ward 8 since yesterday",
            "hinglish",
            "WATER",
            "language",
        ),
        (
            "जल आपूर्ति बंद है water supply issue reported near fictional ward",
            "hi",
            "WATER",
            "language",
        ),
        (
            "My water bill shows a large overcharge this month in fictional Ward 8",
            "en",
            "WATER",
            "billing_scope",
        ),
        (
            "Water pressure failed near Oakwood Lane since yesterday",
            "en",
            "WATER",
            "western_place_name",
        ),
    ],
)
def test_validation_drops_invalid_script_repeats_and_phone_numbers(
    text: str,
    language_code: str,
    department_code: str,
    reason: str,
) -> None:
    """Drop text that violates language, department, location, or safety rules."""
    complaint, rejection = validate_complaint(text, language_code, department_code)

    assert complaint is None
    assert rejection == reason


def test_validation_strips_and_keeps_a_valid_complaint() -> None:
    """Retain a length-valid complaint written in the configured script."""
    complaint, rejection = validate_complaint(
        "  Water is unavailable near fictional Ward 8 since yesterday  ",
        "en",
        "WATER",
    )

    assert complaint == "Water is unavailable near fictional Ward 8 since yesterday"
    assert rejection is None


def test_validation_accepts_hinglish_and_limited_english_loanwords() -> None:
    """Require a Hinglish marker and permit a few English words in native script."""
    hinglish, hinglish_rejection = validate_complaint(
        "Paani supply nahi aa rahi near fictional Ward 8 since yesterday",
        "hinglish",
        "WATER",
    )
    hindi, hindi_rejection = validate_complaint(
        "जल आपूर्ति बंद है और pump कई घंटों से काम नहीं कर रहा",
        "hi",
        "WATER",
    )

    assert hinglish is not None
    assert hinglish_rejection is None
    assert hindi is not None
    assert hindi_rejection is None


def test_hindi_combining_marks_do_not_create_false_repeated_words() -> None:
    """Keep combining vowel signs attached so normal Hindi words pass validation."""
    complaint, rejection = validate_complaint(
        "पिछले चार दिन से हमारे इलाके में पानी की आपूर्ति पूरी तरह से ठप है।",
        "hi",
        "WATER",
    )

    assert complaint is not None
    assert rejection is None


def test_generation_revalidates_raw_cached_batch_without_network_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Revalidate cached raw JSON without making a network call or sleeping."""
    cached_rows = [
        "पिछले चार दिन से हमारे इलाके में पानी की आपूर्ति पूरी तरह से ठप है।",
        "आज सुबह से नल में पानी बहुत धीमी धार से आ रहा है, कृपया जांच करें।",
    ]
    response = json.dumps(cached_rows, ensure_ascii=False)
    cache_path = dataset_generator._cache_path(tmp_path, "test-model", "hi", "WATER", 0)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(response, encoding="utf-8")
    monkeypatch.setattr(dataset_generator, "LANGUAGES", {"hi": LANGUAGE_REGISTRY["hi"]})
    monkeypatch.setattr(dataset_generator, "DEPARTMENT_CODES", ("WATER",))
    monkeypatch.setattr(
        dataset_generator.time,
        "sleep",
        lambda _: pytest.fail("cached batch replay must not sleep"),
    )
    client = FakeClient([])

    split = generate_dataset(client, _config(), tmp_path, "test-model", batch_limit=1)

    assert client.calls == 0
    assert cache_path.read_text(encoding="utf-8") == response
    assert {row["text"] for row in split.train + split.validation} == set(cached_rows)


@pytest.mark.parametrize(
    "error",
    [
        httpx.ReadTimeout("simulated read timeout"),
        httpx.ConnectTimeout("simulated connect timeout"),
        httpx.ConnectError("simulated connection failure"),
    ],
)
def test_request_runner_retries_httpx_transport_errors_with_backoff(
    error: httpx.TransportError,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retry transient HTTPX transport errors with exponential backoff."""
    client = FakeClient([error, '["response"]'])
    sleeps: list[float] = []
    monkeypatch.setattr(dataset_generator, "MAX_RETRIES", 1)
    monkeypatch.setattr(dataset_generator, "REQUEST_DELAY_SECONDS", 0)
    monkeypatch.setattr(dataset_generator.time, "sleep", sleeps.append)

    response = dataset_generator._RequestRunner(client).generate("prompt")

    assert response == '["response"]'
    assert client.calls == 2
    assert sleeps == [dataset_generator.RETRY_BASE_DELAY_SECONDS]


def test_main_stops_cleanly_after_transport_retries_and_keeps_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Report a resumable error without traceback after all network retries fail."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(dataset_generator, "LANGUAGES", {"en": LANGUAGE_REGISTRY["en"]})
    monkeypatch.setattr(dataset_generator, "DEPARTMENT_CODES", ("WATER",))
    monkeypatch.setattr(dataset_generator, "MAX_RETRIES", 2)
    monkeypatch.setattr(dataset_generator, "REQUEST_DELAY_SECONDS", 0)
    monkeypatch.setattr(dataset_generator.time, "sleep", lambda _: None)
    cache_dir = tmp_path / "ml" / "data" / "raw" / "llm_batches"
    cached_response = json.dumps(_valid_english_complaints())
    cache_path = dataset_generator._cache_path(cache_dir, "test-model", "en", "WATER", 0)
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(cached_response, encoding="utf-8")
    client = FakeClient([httpx.ReadTimeout("simulated timeout")] * 3)
    settings = Settings(
        _env_file=None,
        gemini_api_key="test-key",
        gemini_model="test-model",
    )
    monkeypatch.setattr(dataset_generator, "get_settings", lambda: settings)
    monkeypatch.setattr(dataset_generator, "configure_logging", lambda _: None)
    monkeypatch.setattr(
        dataset_generator,
        "_parse_args",
        lambda: dataset_generator.argparse.Namespace(
            check=False,
            limit=2,
            output_dir=tmp_path / "processed",
        ),
    )
    monkeypatch.setattr(
        dataset_generator,
        "GeminiComplaintClient",
        lambda api_key, model, timeout_seconds: client,
    )

    with pytest.raises(SystemExit) as exit_error:
        dataset_generator.main()

    error_output = capsys.readouterr().err
    assert exit_error.value.code == 1
    assert client.calls == 3
    assert "Any completed batches remain cached" in error_output
    assert "run the same command again to resume" in error_output
    assert "Traceback" not in error_output
    assert cache_path.read_text(encoding="utf-8") == cached_response


def test_fake_client_generation_drops_language_billing_and_place_violations(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Apply new content filters to untrusted fake-client batch output."""
    log_messages = _capture_generator_logs(monkeypatch)
    valid = [
        "Water pipe leaking near fictional Ward 8 since Monday morning",
        "Fictional Ward 9 has low water pressure since yesterday afternoon",
        "A broken pump stopped supply near fictional Ward 10 this morning",
    ]
    client = FakeClient(
        [
            json.dumps(
                [
                    "Paani nahi aa raha near fictional Ward 7 since yesterday",
                    "My water bill has a meter reading overcharge in fictional Ward 6",
                    "Water is leaking beside Oakwood Lane since yesterday morning",
                    *valid,
                ]
            )
        ]
    )

    split = generate_dataset(client, _config(3), tmp_path, "test-model", batch_limit=1)
    generated = split.train + split.validation

    assert {row["text"] for row in generated} == set(valid)
    assert client.calls == 1
    assert any(
        "drop_reasons=billing_scope:1,language:1,western_place_name:1" in message
        for message in log_messages
    )


def test_tax_is_the_only_department_allowed_to_keep_billing_complaints() -> None:
    """Allow bills and meter-reading disputes only under the TAX department."""
    complaint = "My water bill has a meter reading overcharge in fictional Ward 8"

    assert validate_complaint(complaint, "en", "TAX") == (complaint, None)


def test_batch_limiter_drops_repeated_named_openers() -> None:
    """Keep each named opener within ten percent of a fifteen-row batch."""
    batch = [
        "Hey, water is unavailable near fictional Ward 8",
        "Hey, a pipe has leaked in fictional Ward 9 since yesterday",
        "Excuse me, pressure dropped in fictional Ward 10 since Monday",
        "Excuse me, a tap is leaking near fictional Ward 11 since Monday",
        "Urgent: a pipe burst in fictional Ward 12 this morning",
        "Urgent: water is flowing onto the road near fictional Ward 13",
        *[
            f"Water supply failed in fictional Ward {ward} since yesterday morning"
            for ward in range(14, 23)
        ],
    ]

    accepted, dropped = _limit_repeated_openers(batch)

    assert dropped == 3
    assert len(accepted) == 12
    assert sum(text.startswith("Hey") for text in accepted) == 1
    assert sum(text.startswith("Excuse me") for text in accepted) == 1
    assert sum(text.startswith("Urgent:") for text in accepted) == 1


def test_generation_accepts_and_reports_ninety_percent_stratum_shortfall(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Keep a 90% stratum and emit per-stratum warning and final summary."""
    log_messages = _capture_generator_logs(monkeypatch)
    monkeypatch.setattr(dataset_generator, "LANGUAGES", {"en": LANGUAGE_REGISTRY["en"]})
    monkeypatch.setattr(dataset_generator, "DEPARTMENT_CODES", ("WATER",))
    client = FakeClient(
        [
            json.dumps(_valid_water_complaints(9)),
            json.dumps([]),
        ]
    )

    split = generate_dataset(client, _config(10), tmp_path, "test-model")

    assert len(split.train) + len(split.validation) == 9
    assert any("ml.dataset.stratum.shortfall" in message for message in log_messages)
    assert any("ml.dataset.shortfalls summary=en/WATER:9/10" in message for message in log_messages)


def test_generation_aborts_below_configured_shortfall_threshold(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Fail clearly when a fully attempted stratum is below 90% of its target."""
    monkeypatch.setattr(dataset_generator, "LANGUAGES", {"en": LANGUAGE_REGISTRY["en"]})
    monkeypatch.setattr(dataset_generator, "DEPARTMENT_CODES", ("WATER",))
    client = FakeClient(
        [
            json.dumps(_valid_water_complaints(8)),
            json.dumps([]),
        ]
    )

    with pytest.raises(RuntimeError, match="8/10.*below the configured 90% minimum"):
        generate_dataset(client, _config(10), tmp_path, "test-model")


def test_generation_config_rejects_invalid_minimum_fraction() -> None:
    """Require the configured minimum shortfall fraction to be within (0, 1]."""
    for fraction in (0, 1.01):
        with pytest.raises(ValueError, match="minimum_stratum_fraction"):
            _config(minimum_fraction=fraction)


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


def test_department_prompts_reserve_all_billing_issues_for_tax() -> None:
    """Explicitly prohibit financial and bill complaints in every non-TAX prompt."""
    for department_code in DEPARTMENT_CODES:
        prompt = _build_prompt("en", department_code, 15)
        if department_code == "TAX":
            assert "Only create Property Tax and Billing complaints" in prompt
            assert "water and electricity bill" in prompt
        else:
            assert "Never include billing, payment, overcharge, or" in prompt
            assert "water and electricity bills" in prompt
            assert "belong only to TAX" in prompt


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
    assert "plain English only" in _build_prompt("en", "WATER", 15)
    assert "no greeting or formula" in hinglish_prompt
    assert "lowercase, missing punctuation" in hinglish_prompt
    assert "multi-sentence stories" in hinglish_prompt
    assert "nagar, society, chowk" in hinglish_prompt
    assert "Oakwood Lane" in hinglish_prompt


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
