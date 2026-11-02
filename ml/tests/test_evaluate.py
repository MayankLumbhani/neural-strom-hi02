"""Tests for the baseline evaluation report."""

import csv
import json
from pathlib import Path

import pytest
from evaluate import DEPARTMENT_CODES, _calculate_metrics, evaluate_baseline, write_report


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    """Write a small CSV fixture using the evaluator input columns."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=("text", "label", "language"))
        writer.writeheader()
        writer.writerows(rows)


def test_metrics_include_per_class_scores_and_confusion_matrix() -> None:
    """Return all required metrics with a stable nine-class matrix."""
    expected = ["WATER", "ROADS", "WATER"]
    metrics = _calculate_metrics(expected, expected, DEPARTMENT_CODES)

    assert metrics["accuracy"] == 1
    assert metrics["macro_f1"] == pytest.approx(1 / len(DEPARTMENT_CODES) * 2)
    class_metrics = metrics["per_class"]
    assert class_metrics["WATER"] == {
        "precision": 1,
        "recall": 1,
        "f1": 1,
        "support": 2,
    }
    matrix = metrics["confusion_matrix"]
    assert matrix["labels"] == list(DEPARTMENT_CODES)
    assert len(matrix["rows_actual_columns_predicted"]) == len(DEPARTMENT_CODES)
    assert (
        matrix["rows_actual_columns_predicted"][DEPARTMENT_CODES.index("WATER")][
            DEPARTMENT_CODES.index("WATER")
        ]
        == 2
    )


def test_evaluator_reports_language_tier_and_writes_json(tmp_path: Path) -> None:
    """Fit only on training rows and write separate tier and language metrics."""
    training_path = tmp_path / "train.csv"
    evaluation_path = tmp_path / "eval.csv"
    output_path = tmp_path / "reports" / "baseline_metrics.json"
    training_rows = [
        {"text": "water pipe leaking complaint training", "label": "WATER", "language": "en"},
        {"text": "road pothole broken street training", "label": "ROADS", "language": "en"},
        {"text": "புதிய நீர் குழாய் புகார் பயிற்சி", "label": "WATER", "language": "ta"},
        {"text": "புதிய சாலை பள்ளம் புகார் பயிற்சி", "label": "ROADS", "language": "ta"},
    ]
    evaluation_rows = [
        {
            "text": "water pipe leaking complaint evaluation",
            "label": "WATER",
            "language": "en",
        },
        {"text": "road pothole broken street evaluation", "label": "ROADS", "language": "en"},
        {"text": "நீர் குழாய் புகார் மதிப்பீடு", "label": "WATER", "language": "ta"},
        {"text": "சாலை பள்ளம் புகார் மதிப்பீடு", "label": "ROADS", "language": "ta"},
    ]
    _write_rows(training_path, training_rows)
    _write_rows(evaluation_path, evaluation_rows)

    report = evaluate_baseline(training_path, evaluation_path)
    write_report(report, output_path)

    loaded = json.loads(output_path.read_text(encoding="utf-8"))
    assert loaded == report
    assert report["training_rows"] == 4
    assert report["evaluation_rows"] == 4
    assert set(report["per_language"]) == {"en", "ta"}
    assert report["per_language"]["en"]["tier"] == 1
    assert report["per_language"]["ta"]["tier"] == 2
    assert report["per_language"]["ta"]["unverified"] is True
    assert report["per_tier"]["tier_1"]["tier"] == 1
    assert report["per_tier"]["tier_2"]["unverified"] is True
    assert report["overall"]["confusion_matrix"]["labels"] == list(DEPARTMENT_CODES)


def test_evaluator_rejects_training_evaluation_text_overlap(tmp_path: Path) -> None:
    """Prevent reporting metrics when held-out text occurs in training."""
    training_path = tmp_path / "train.csv"
    evaluation_path = tmp_path / "eval.csv"
    shared = {"text": "same text", "label": "WATER", "language": "en"}
    _write_rows(training_path, [shared, {"text": "other", "label": "ROADS", "language": "en"}])
    _write_rows(evaluation_path, [shared])

    with pytest.raises(ValueError, match="share 1 complaint texts"):
        evaluate_baseline(training_path, evaluation_path)
