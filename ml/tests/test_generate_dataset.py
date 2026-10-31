"""Tests for balanced synthetic complaint dataset generation."""

import csv
from collections import Counter
from pathlib import Path

import pytest
from generate_dataset import (
    DEPARTMENT_CODES,
    GenerationConfig,
    generate_dataset,
    write_dataset,
)

from grievance.nlp.languages import LANGUAGES


def test_generated_dataset_is_balanced_and_stratified() -> None:
    """Balance labels within each language and retain a reproducible tier split."""
    split = generate_dataset()
    train_counts = Counter((row["language"], row["label"]) for row in split.train)
    validation_counts = Counter((row["language"], row["label"]) for row in split.validation)

    assert len(train_counts) == len(LANGUAGES) * len(DEPARTMENT_CODES)
    assert len(validation_counts) == len(LANGUAGES) * len(DEPARTMENT_CODES)
    assert set(train_counts.values()) == {40, 8}
    assert set(validation_counts.values()) == {10, 2}
    assert all(
        row["tier"] == LANGUAGES[row["language"]].tier for row in split.train + split.validation
    )
    assert all(not row["verified"] for row in split.train + split.validation)


def test_generated_dataset_includes_all_required_variations() -> None:
    """Generate typos, slang, code-mixing, missing locations, and ambiguity."""
    split = generate_dataset()

    assert {row["variation"] for row in split.train + split.validation} == {
        "clean",
        "typo",
        "slang",
        "code_mixed",
        "missing_location",
        "ambiguous",
    }


def test_splits_have_no_duplicate_text_at_large_sample_sizes() -> None:
    """Prevent identical synthetic complaints from leaking between the splits."""
    split = generate_dataset(
        GenerationConfig(
            tier1_samples_per_class_language=100,
            tier2_samples_per_class_language=10,
        )
    )
    train_texts = [row["text"] for row in split.train]
    validation_texts = [row["text"] for row in split.validation]

    assert len(train_texts) == len(set(train_texts))
    assert len(validation_texts) == len(set(validation_texts))
    assert set(train_texts).isdisjoint(validation_texts)


def test_generator_is_deterministic_for_a_fixed_seed() -> None:
    """Return identical rows when invoked with the same generation seed."""
    config = GenerationConfig(seed=13, tier1_samples_per_class_language=12)

    assert generate_dataset(config) == generate_dataset(config)


def test_generated_csvs_have_the_required_split_and_tier_column(tmp_path: Path) -> None:
    """Write readable CSV files with labels, language tiers, and review state."""
    split = generate_dataset(
        GenerationConfig(
            seed=5,
            tier1_samples_per_class_language=6,
            tier2_samples_per_class_language=4,
        )
    )
    train_path, validation_path = write_dataset(tmp_path, split)

    with train_path.open(encoding="utf-8-sig", newline="") as train_file:
        train_rows = list(csv.DictReader(train_file))
    with validation_path.open(encoding="utf-8-sig", newline="") as validation_file:
        validation_rows = list(csv.DictReader(validation_file))

    assert {"text", "label", "language", "tier", "variation", "verified"} == set(train_rows[0])
    assert len(train_rows) == len(split.train)
    assert len(validation_rows) == len(split.validation)
    assert {row["tier"] for row in train_rows + validation_rows} == {"1", "2"}
    assert {row["verified"] for row in train_rows + validation_rows} == {"false"}


@pytest.mark.parametrize(
    "settings",
    [
        {"validation_fraction": 0},
        {"validation_fraction": 1},
        {"tier1_samples_per_class_language": 1},
        {"tier2_samples_per_class_language": 1},
    ],
)
def test_generation_settings_reject_invalid_values(settings: dict[str, float | int]) -> None:
    """Reject invalid split fractions or sample counts."""
    with pytest.raises(ValueError):
        GenerationConfig(**settings)
