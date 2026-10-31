"""Tests for the deterministic Tier 1 manual-review sample."""

import csv
from collections import Counter
from pathlib import Path

import pytest
from make_review_sample import (
    REVIEW_COLUMNS,
    REVIEW_SAMPLE_SIZE,
    TIER1_LANGUAGES,
    make_review_sample,
)


def _write_training_data(path: Path, rows_per_language: int) -> None:
    """Write distinct synthetic training rows for each enabled Tier 1 language."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as training_file:
        writer = csv.DictWriter(
            training_file,
            fieldnames=("text", "label", "language", "tier", "variation", "verified"),
        )
        writer.writeheader()
        for language in TIER1_LANGUAGES:
            for index in range(rows_per_language):
                writer.writerow(
                    {
                        "text": f"{language} synthetic complaint {index}",
                        "label": "WATER",
                        "language": language,
                        "tier": 1,
                        "variation": "clean",
                        "verified": "false",
                    }
                )


def test_review_sample_has_fifty_rows_per_tier1_language_and_exact_columns(
    tmp_path: Path,
) -> None:
    """Select the configured count and leave reviewer fields blank."""
    training_path = tmp_path / "train.csv"
    output_path = tmp_path / "review" / "review_sample.csv"
    _write_training_data(training_path, rows_per_language=60)

    make_review_sample(training_path, output_path)

    with output_path.open(encoding="utf-8-sig", newline="") as sample_file:
        reader = csv.DictReader(sample_file)
        rows = list(reader)
        assert reader.fieldnames == list(REVIEW_COLUMNS)

    assert len(rows) == REVIEW_SAMPLE_SIZE * len(TIER1_LANGUAGES)
    assert Counter(row["language"] for row in rows) == {
        language: REVIEW_SAMPLE_SIZE for language in TIER1_LANGUAGES
    }
    assert all(row["verdict"] == "" and row["notes"] == "" for row in rows)
    assert all(row["text"].startswith(f"{row['language']} synthetic") for row in rows)


def test_review_sample_is_reproducible(tmp_path: Path) -> None:
    """Write identical sample contents when the fixed seed is reused."""
    training_path = tmp_path / "train.csv"
    first_output = tmp_path / "first.csv"
    second_output = tmp_path / "second.csv"
    _write_training_data(training_path, rows_per_language=60)

    make_review_sample(training_path, first_output)
    make_review_sample(training_path, second_output)

    assert first_output.read_bytes() == second_output.read_bytes()


def test_review_sample_rejects_insufficient_training_rows(tmp_path: Path) -> None:
    """Fail clearly rather than producing an incomplete review sample."""
    training_path = tmp_path / "train.csv"
    output_path = tmp_path / "review.csv"
    _write_training_data(training_path, rows_per_language=REVIEW_SAMPLE_SIZE - 1)

    with pytest.raises(ValueError, match="at least 50 are required"):
        make_review_sample(training_path, output_path)

    assert not output_path.exists()
