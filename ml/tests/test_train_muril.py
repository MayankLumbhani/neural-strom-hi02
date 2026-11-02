"""Offline tests for MuRIL dataset loading and report metrics."""

import csv
from pathlib import Path

import pytest
from train_muril import (
    build_report,
    label_mappings,
    load_examples,
)

from grievance.seed import DEPARTMENTS


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    """Write fixture data with the baseline-compatible CSV schema."""
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=("text", "label", "language"))
        writer.writeheader()
        writer.writerows(rows)


def test_load_examples_uses_department_and_language_registries(tmp_path: Path) -> None:
    """Load valid examples and reject unknown label or language values."""
    path = tmp_path / "train.csv"
    _write_csv(
        path,
        [
            {"text": "water issue one", "label": "WATER", "language": "en"},
            {"text": "પાણીની સમસ્યા", "label": "WATER", "language": "gu"},
        ],
    )

    examples = load_examples(path, "Training")

    assert [example["language"] for example in examples] == ["en", "gu"]
    _write_csv(
        path,
        [{"text": "invalid department", "label": "NOT_A_DEPARTMENT", "language": "en"}],
    )
    with pytest.raises(ValueError, match="unknown department"):
        load_examples(path, "Training")
    _write_csv(path, [{"text": "invalid language", "label": "WATER", "language": "xx"}])
    with pytest.raises(ValueError, match="unknown language"):
        load_examples(path, "Training")


def test_label_mapping_comes_from_department_seed_registry() -> None:
    """Keep model output indices aligned with the canonical department seed."""
    label2id, id2label = label_mappings()

    assert list(label2id) == [department.code for department in DEPARTMENTS]
    assert len(label2id) == 9
    assert {index: label for label, index in label2id.items()} == id2label


def test_build_report_has_baseline_shape_and_tiered_language_metrics() -> None:
    """Report evaluation scores by all labels, language, and separate tiers."""
    evaluation = [
        {"text": "water english", "label": "WATER", "language": "en"},
        {"text": "road hindi", "label": "ROADS", "language": "hi"},
        {"text": "நீர் தமிழ்", "label": "WATER", "language": "ta"},
        {"text": "சாலை தமிழ்", "label": "ROADS", "language": "ta"},
    ]

    report = build_report(evaluation, ["WATER", "ROADS", "WATER", "ROADS"], 12, 0.75)

    assert report["training_rows"] == 12
    assert report["evaluation_rows"] == 4
    assert report["best_checkpoint_validation_macro_f1"] == 0.75
    assert report["overall"]["accuracy"] == 1
    assert report["overall"]["confusion_matrix"]["labels"] == [
        department.code for department in DEPARTMENTS
    ]
    assert report["per_language"]["en"]["metrics"]["accuracy"] == 1
    assert report["per_language"]["ta"]["metrics"]["macro_f1"] == pytest.approx(2 / 9)
    assert report["per_language"]["ta"]["tier"] == 2
    assert report["per_language"]["ta"]["unverified"] is True
    assert report["per_tier"]["tier_1"]["tier"] == 1
    assert report["per_tier"]["tier_2"]["unverified"] is True


def test_build_report_rejects_mismatched_predictions() -> None:
    """Avoid silently truncating evaluation results when lengths differ."""
    evaluation = [{"text": "water", "label": "WATER", "language": "en"}]

    with pytest.raises(ValueError, match="equal lengths"):
        build_report(evaluation, [], 1, 0.5)
