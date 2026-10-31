"""Generate synthetic multilingual complaint data with the Gemini API."""

import argparse
import csv
import json
import math
import random
import re
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from hashlib import sha256
from pathlib import Path
from typing import Final, Protocol, TypedDict

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from grievance.core.config import Settings, get_settings
from grievance.core.logging import configure_logging, logger
from grievance.nlp.languages import LANGUAGES, SCRIPT_RANGES
from grievance.seed import DEPARTMENTS

BATCH_SIZE: Final[int] = 15
MIN_COMPLAINT_LENGTH: Final[int] = 12
MAX_COMPLAINT_LENGTH: Final[int] = 500
NEAR_DUPLICATE_THRESHOLD: Final[float] = 0.9
REQUEST_DELAY_SECONDS: Final[float] = 1.0
RETRY_BASE_DELAY_SECONDS: Final[float] = 1.0
RETRY_MAX_DELAY_SECONDS: Final[float] = 30.0
MAX_RETRIES: Final[int] = 5
VALIDATION_FRACTION: Final[float] = 0.2
DEPARTMENT_CODES: Final[tuple[str, ...]] = tuple(department.code for department in DEPARTMENTS)
DEPARTMENT_NAMES: Final[dict[str, str]] = {
    department.code: department.name_en for department in DEPARTMENTS
}
PHONE_LIKE_DIGITS: Final[re.Pattern[str]] = re.compile(r"\+?\d[\d\s().-]{5,}\d")
WORD_TOKENS: Final[re.Pattern[str]] = re.compile(r"\w+", re.UNICODE)
NORMALIZED_SEPARATORS: Final[re.Pattern[str]] = re.compile(r"[^\w]+", re.UNICODE)


class ComplaintClient(Protocol):
    """Generate raw text responses from an LLM."""

    def generate(self, prompt: str) -> str:
        """Return the raw text response for a prompt."""


class DatasetRow(TypedDict):
    """One synthetic complaint and its classification metadata."""

    text: str
    label: str
    language: str
    tier: int
    variation: str
    verified: bool
    source: str


@dataclass(frozen=True)
class GenerationConfig:
    """Reproducible dataset size, split, and randomness settings."""

    seed: int = 20261031
    validation_fraction: float = VALIDATION_FRACTION
    tier1_samples_per_class_language: int = 100
    tier2_samples_per_class_language: int = 30

    def __post_init__(self) -> None:
        """Validate dataset generation settings."""
        if not 0 < self.validation_fraction < 1:
            raise ValueError("validation_fraction must be between 0 and 1")
        if self.tier1_samples_per_class_language < 2:
            raise ValueError("tier1_samples_per_class_language must be at least 2")
        if self.tier2_samples_per_class_language < 2:
            raise ValueError("tier2_samples_per_class_language must be at least 2")


@dataclass(frozen=True)
class DatasetSplit:
    """Stratified training and validation rows."""

    train: list[DatasetRow]
    validation: list[DatasetRow]


class _RequestRunner:
    """Apply retry backoff and spacing to Gemini API calls."""

    def __init__(self, client: ComplaintClient) -> None:
        """Initialize a runner for one generation operation."""
        self.client = client
        self.last_request_at: float | None = None

    def generate(self, prompt: str) -> str:
        """Call the LLM with bounded retries for rate limits and server errors."""
        if self.last_request_at is not None:
            delay = REQUEST_DELAY_SECONDS - (time.monotonic() - self.last_request_at)
            if delay > 0:
                time.sleep(delay)

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self.client.generate(prompt)
            except errors.APIError as exc:
                self.last_request_at = time.monotonic()
                if not _is_retryable(exc) or attempt == MAX_RETRIES:
                    raise
                retry_delay = min(
                    RETRY_BASE_DELAY_SECONDS * (2**attempt),
                    RETRY_MAX_DELAY_SECONDS,
                )
                time.sleep(retry_delay)
            else:
                self.last_request_at = time.monotonic()
                return response

        raise RuntimeError("Gemini request retries ended unexpectedly")


class GeminiComplaintClient:
    """Use the official Google Gen AI SDK to request complaint text."""

    def __init__(self, api_key: str, model: str, timeout_seconds: float) -> None:
        """Create a Gemini client without exposing its key in logs."""
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000)),
        )
        self._model = model

    def generate(self, prompt: str) -> str:
        """Request JSON-formatted text from the configured Gemini model."""
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        if response.text is None:
            raise ValueError("Gemini returned an empty text response")
        return response.text


def require_gemini_model(settings: Settings) -> str:
    """Return the configured model or fail clearly before making an API call."""
    if settings.gemini_model is None or not settings.gemini_model.strip():
        raise RuntimeError("GEMINI_MODEL must be configured before generating a dataset")
    return settings.gemini_model.strip()


def require_gemini_api_key(settings: Settings) -> str:
    """Return the configured API key or fail without revealing its value."""
    if settings.gemini_api_key is None or not settings.gemini_api_key.get_secret_value().strip():
        raise RuntimeError("GEMINI_API_KEY must be configured before generating a dataset")
    return settings.gemini_api_key.get_secret_value()


def parse_batch_response(response: str) -> list[str]:
    """Parse a strict JSON list of complaint strings."""
    try:
        parsed = json.loads(response)
    except json.JSONDecodeError as exc:
        raise ValueError("Gemini response must be a strict JSON list of strings") from exc
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError("Gemini response must be a strict JSON list of strings")
    return [item.strip() for item in parsed]


def validate_complaint(text: str, script: str) -> tuple[str | None, str | None]:
    """Clean a complaint or return the reason it is rejected."""
    cleaned = text.strip()
    if not MIN_COMPLAINT_LENGTH <= len(cleaned) <= MAX_COMPLAINT_LENGTH:
        return None, "length"
    if not _matches_script(cleaned, script):
        return None, "script"
    if _has_repeated_adjacent_words(cleaned):
        return None, "repeated_words"
    if _contains_phone_like_digits(cleaned):
        return None, "phone_number"
    return cleaned, None


def _matches_script(text: str, script: str) -> bool:
    """Check that all letters in a complaint belong to the registry script."""
    ranges = SCRIPT_RANGES.get(script)
    letters = [character for character in text if character.isalpha()]
    if ranges is None or not letters:
        return False
    return all(
        any(start <= ord(character) <= end for start, end in ranges) for character in letters
    )


def _has_repeated_adjacent_words(text: str) -> bool:
    """Detect repeated adjacent words regardless of case or punctuation."""
    words = [word.casefold() for word in WORD_TOKENS.findall(text)]
    return any(first == second for first, second in zip(words, words[1:], strict=False))


def _contains_phone_like_digits(text: str) -> bool:
    """Reject likely phone numbers while permitting short ward numbers."""
    for match in PHONE_LIKE_DIGITS.finditer(text):
        if sum(character.isdigit() for character in match.group()) >= 7:
            return True
    return False


def _normalize_text(text: str) -> str:
    """Normalize text for exact and near-duplicate comparisons."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(NORMALIZED_SEPARATORS.sub(" ", normalized).split())


def _is_near_duplicate(candidate: str, accepted: list[str]) -> bool:
    """Compare normalized text against earlier complaints for the language."""
    return any(
        SequenceMatcher(None, candidate, previous).ratio() >= NEAR_DUPLICATE_THRESHOLD
        for previous in accepted
    )


def _build_prompt(language_code: str, department_code: str, count: int) -> str:
    """Build the language- and department-specific synthetic data prompt."""
    language = LANGUAGES[language_code]
    language_instruction = (
        "Use natural Hindi written only with Latin letters (romanized Hindi), not Devanagari."
        if language_code == "hinglish"
        else f"Write naturally in {language.name_en} using its {language.script} script."
    )
    other_instruction = (
        "For OTHER, distribute examples across three genuinely different types: "
        "vague or ambiguous complaints with no clear department, general municipal "
        "questions, and issues that fit none of the other departments. Include "
        "multiple distinct examples of each type; do not reuse one generic sentence."
        if department_code == "OTHER"
        else f"Every complaint must clearly concern {DEPARTMENT_NAMES[department_code]}."
    )
    return (
        f"Create exactly {count} distinct, fictional municipal complaint messages "
        f"for the {DEPARTMENT_NAMES[department_code]} department. "
        f"Language: {language.name_en} ({language.code}); script: {language.script}. "
        f"{language_instruction} {other_instruction}\n"
        "Return only a valid JSON array of strings, with no markdown or surrounding text. "
        "Do not repeat or closely paraphrase any phrasing within this batch. "
        "Vary tone (polite, angry, brief, detailed), length, spoken style, occasional "
        "realistic typos, concrete fictional details, and how long the issue has lasted. "
        "About 25% of messages must contain no location; vary the rest using only "
        "fictional ward numbers, fictional areas, invented street names, and invented "
        "landmarks. Never name real people or real places, and never include a phone "
        "number or a full street address. Avoid unrelated code-mixing; use another "
        "language only when naturally required by the specified Hinglish style."
    )


def _is_retryable(error: errors.APIError) -> bool:
    """Return whether an API error is a retryable rate limit or server failure."""
    status_code = getattr(error, "code", None)
    return isinstance(status_code, int) and (status_code == 429 or 500 <= status_code <= 599)


def _cache_path(cache_dir: Path, model: str, language: str, label: str, index: int) -> Path:
    """Return a model-specific deterministic path for one raw batch response."""
    model_key = sha256(model.encode("utf-8")).hexdigest()[:12]
    return cache_dir / f"{model_key}_{language}_{label}_{index:03d}.json"


def _read_or_generate_batch(
    runner: _RequestRunner,
    prompt: str,
    cache_path: Path,
) -> tuple[list[str], bool]:
    """Load a cached raw response or generate and persist a new batch."""
    if cache_path.exists():
        response = cache_path.read_text(encoding="utf-8")
        return parse_batch_response(response), True

    response = runner.generate(prompt)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(response, encoding="utf-8")
    return parse_batch_response(response), False


def _generation_config(settings: Settings) -> GenerationConfig:
    """Build generation sizes and seed from validated application settings."""
    return GenerationConfig(
        seed=settings.dataset_seed,
        tier1_samples_per_class_language=settings.dataset_tier1_samples_per_class_language,
        tier2_samples_per_class_language=settings.dataset_tier2_samples_per_class_language,
    )


def generate_dataset(
    client: ComplaintClient,
    config: GenerationConfig,
    cache_dir: Path,
    model: str,
    batch_limit: int | None = None,
) -> DatasetSplit:
    """Generate, validate, deduplicate, and stratify synthetic complaint rows."""
    if batch_limit is not None and batch_limit < 1:
        raise ValueError("batch_limit must be at least 1")

    runner = _RequestRunner(client)
    exact_texts: set[str] = set()
    near_texts_by_language: dict[str, list[str]] = defaultdict(list)
    rows_by_stratum: dict[tuple[str, str], list[DatasetRow]] = defaultdict(list)
    dropped_by_stratum: Counter[tuple[str, str]] = Counter()
    processed_batches = 0
    reached_batch_limit = False

    for language_code, language in LANGUAGES.items():
        if not language.enabled:
            continue
        target_count = (
            config.tier1_samples_per_class_language
            if language.tier == 1
            else config.tier2_samples_per_class_language
        )
        max_batches = math.ceil(target_count / BATCH_SIZE) * 2
        for department_code in DEPARTMENT_CODES:
            stratum = (language_code, department_code)
            batch_index = 0
            while len(rows_by_stratum[stratum]) < target_count:
                if batch_limit is not None and processed_batches >= batch_limit:
                    reached_batch_limit = True
                    break
                if batch_index >= max_batches:
                    raise RuntimeError(
                        f"Only {len(rows_by_stratum[stratum])} valid complaints were "
                        f"produced for {language_code}/{department_code}; "
                        f"expected {target_count} after {max_batches} batches"
                    )
                cache_path = _cache_path(
                    cache_dir, model, language_code, department_code, batch_index
                )
                prompt = _build_prompt(language_code, department_code, BATCH_SIZE)
                batch, was_cached = _read_or_generate_batch(runner, prompt, cache_path)
                processed_batches += 1
                batch_index += 1

                for text in batch:
                    complaint, rejection_reason = validate_complaint(text, language.script)
                    if rejection_reason is not None:
                        dropped_by_stratum[stratum] += 1
                        continue
                    if complaint is None:
                        raise RuntimeError("Complaint validation returned an invalid state")
                    normalized = _normalize_text(complaint)
                    if normalized in exact_texts:
                        dropped_by_stratum[stratum] += 1
                        continue
                    if _is_near_duplicate(normalized, near_texts_by_language[language_code]):
                        dropped_by_stratum[stratum] += 1
                        continue

                    exact_texts.add(normalized)
                    near_texts_by_language[language_code].append(normalized)
                    rows_by_stratum[stratum].append(
                        {
                            "text": complaint,
                            "label": department_code,
                            "language": language_code,
                            "tier": language.tier,
                            "variation": "llm_generated",
                            "verified": False,
                            "source": "llm",
                        }
                    )
                    if len(rows_by_stratum[stratum]) == target_count:
                        break

                logger.info(
                    "ml.dataset.batch language=%s department=%s cached=%s kept=%d dropped=%d",
                    language_code,
                    department_code,
                    was_cached,
                    len(rows_by_stratum[stratum]),
                    dropped_by_stratum[stratum],
                )
            if reached_batch_limit:
                break
        if reached_batch_limit:
            break

    for language_code, language in LANGUAGES.items():
        if not language.enabled:
            continue
        for department_code in DEPARTMENT_CODES:
            stratum = (language_code, department_code)
            logger.info(
                "ml.dataset.stratum language=%s department=%s kept=%d dropped=%d",
                language_code,
                department_code,
                len(rows_by_stratum[stratum]),
                dropped_by_stratum[stratum],
            )

    all_rows = [row for rows in rows_by_stratum.values() for row in rows]
    return _stratified_split(all_rows, config)


def _stratified_split(rows: list[DatasetRow], config: GenerationConfig) -> DatasetSplit:
    """Split rows by language and department without text overlap."""
    strata: dict[tuple[str, str], list[DatasetRow]] = defaultdict(list)
    for row in rows:
        strata[(row["language"], row["label"])].append(row)

    random_source = random.Random(config.seed)
    train_rows: list[DatasetRow] = []
    validation_rows: list[DatasetRow] = []
    for stratum_rows in strata.values():
        random_source.shuffle(stratum_rows)
        if len(stratum_rows) < 2:
            train_rows.extend(stratum_rows)
            continue
        validation_count = max(1, round(len(stratum_rows) * config.validation_fraction))
        validation_rows.extend(stratum_rows[:validation_count])
        train_rows.extend(stratum_rows[validation_count:])

    random_source.shuffle(train_rows)
    random_source.shuffle(validation_rows)
    train_texts = {_normalize_text(row["text"]) for row in train_rows}
    validation_texts = {_normalize_text(row["text"]) for row in validation_rows}
    if not train_texts.isdisjoint(validation_texts):
        raise RuntimeError("Train and validation splits contain overlapping complaint text")
    return DatasetSplit(train=train_rows, validation=validation_rows)


def write_split(path: Path, rows: list[DatasetRow]) -> None:
    """Write one dataset split as UTF-8 CSV with a stable column order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = (
        "text",
        "label",
        "language",
        "tier",
        "variation",
        "verified",
        "source",
    )
    with path.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({**row, "verified": str(row["verified"]).lower()} for row in rows)


def write_dataset(output_dir: Path, split: DatasetSplit) -> tuple[Path, Path]:
    """Write training and validation CSV files under the requested directory."""
    train_path = output_dir / "train.csv"
    validation_path = output_dir / "validation.csv"
    write_split(train_path, split.train)
    write_split(validation_path, split.validation)
    return train_path, validation_path


def _check_gemini(runner: _RequestRunner) -> None:
    """Verify key, model access, and JSON response without writing dataset files."""
    response = runner.generate(
        'Return exactly this JSON array and nothing else: ["synthetic check complaint"]'
    )
    parse_batch_response(response)


def _parse_args() -> argparse.Namespace:
    """Parse check, quick-trial, and normal generation options."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify the Gemini key and model")
    mode.add_argument(
        "--limit",
        type=int,
        metavar="N",
        help="process at most N batches total for a quick trial",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("ml/data/processed"),
        help="directory for generated train.csv and validation.csv",
    )
    return parser.parse_args()


def main() -> None:
    """Run the configured check or generate and write both dataset splits."""
    args = _parse_args()
    try:
        settings = get_settings()
        model = require_gemini_model(settings)
        api_key = require_gemini_api_key(settings)
        configure_logging(settings.log_level)
        client = GeminiComplaintClient(api_key, model, settings.llm_timeout_seconds)
        if args.check:
            _check_gemini(_RequestRunner(client))
            sys.stdout.write(f"ok model={model}\n")
            return
        if args.limit is not None and args.limit < 1:
            raise ValueError("--limit must be at least 1")

        config = _generation_config(settings)
        cache_dir = Path("ml/data/raw/llm_batches")
        split = generate_dataset(client, config, cache_dir, model, args.limit)
        train_path, validation_path = write_dataset(args.output_dir, split)
        logger.info(
            "ml.dataset.generated model=%s train_rows=%d validation_rows=%d "
            "train_path=%s validation_path=%s",
            model,
            len(split.train),
            len(split.validation),
            train_path,
            validation_path,
        )
    except (RuntimeError, ValueError, ValidationError, errors.APIError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
