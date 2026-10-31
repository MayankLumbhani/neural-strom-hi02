"""Select a reproducible Tier 1 sample for manual dataset review."""

import csv
import random
from pathlib import Path
from typing import Final, TypedDict

from grievance.core.config import get_settings
from grievance.core.logging import configure_logging, logger
from grievance.nlp.languages import LANGUAGES

REVIEW_SAMPLE_SIZE: Final[int] = 50
REVIEW_SAMPLE_SEED: Final[int] = 20261031
SOURCE_COLUMNS: Final[frozenset[str]] = frozenset({"text", "label", "language"})
REVIEW_COLUMNS: Final[tuple[str, ...]] = ("text", "label", "language", "verdict", "notes")
TIER1_LANGUAGES: Final[tuple[str, ...]] = tuple(
    code for code, language in LANGUAGES.items() if language.enabled and language.tier == 1
)


class ReviewRow(TypedDict):
    """One selected training example with fields for a human review."""

    text: str
    label: str
    language: str
    verdict: str
    notes: str


def make_review_sample(
    training_path: Path = Path("ml/data/processed/train.csv"),
    output_path: Path = Path("ml/data/review/review_sample.csv"),
) -> Path:
    """Write 50 seeded random training rows for every enabled Tier 1 language."""
    rows_by_language: dict[str, list[tuple[str, str, str]]] = {
        language: [] for language in TIER1_LANGUAGES
    }

    with training_path.open(encoding="utf-8-sig", newline="") as training_file:
        reader = csv.DictReader(training_file)
        if reader.fieldnames is None or not SOURCE_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(
                f"Training data must include these columns: {', '.join(sorted(SOURCE_COLUMNS))}"
            )

        for row in reader:
            language = row.get("language")
            if language not in rows_by_language:
                continue
            text = row.get("text")
            label = row.get("label")
            if not text or not label:
                raise ValueError(
                    f"Training rows for Tier 1 language {language} need non-empty text and label"
                )
            rows_by_language[language].append((text, label, language))

    random_source = random.Random(REVIEW_SAMPLE_SEED)
    review_rows: list[ReviewRow] = []
    for language, language_rows in rows_by_language.items():
        if len(language_rows) < REVIEW_SAMPLE_SIZE:
            raise ValueError(
                f"Training data has {len(language_rows)} rows for {language}; "
                f"at least {REVIEW_SAMPLE_SIZE} are required"
            )
        for text, label, row_language in random_source.sample(language_rows, REVIEW_SAMPLE_SIZE):
            review_rows.append(
                {
                    "text": text,
                    "label": label,
                    "language": row_language,
                    "verdict": "",
                    "notes": "",
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(review_rows)
    return output_path


def main() -> None:
    """Generate the default review sample and log its destination."""
    settings = get_settings()
    configure_logging(settings.log_level)
    output_path = make_review_sample()
    logger.info(
        "ml.review_sample.generated rows=%d output_path=%s",
        len(TIER1_LANGUAGES) * REVIEW_SAMPLE_SIZE,
        output_path,
    )


if __name__ == "__main__":
    main()
