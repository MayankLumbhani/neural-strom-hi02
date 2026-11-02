"""Train and evaluate the TF-IDF plus Logistic Regression baseline."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Final, TypedDict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline

from grievance.core.config import get_settings
from grievance.core.logging import configure_logging, logger
from grievance.nlp.languages import LANGUAGES
from grievance.seed import DEPARTMENTS

DEPARTMENT_CODES: Final[tuple[str, ...]] = tuple(department.code for department in DEPARTMENTS)
REQUIRED_COLUMNS: Final[frozenset[str]] = frozenset({"text", "label", "language"})
TIER1_EVALUATION_NOTE: Final[str] = (
    "AI-authored, short, parallel rows; accuracy may be an optimistic estimate."
)
TIER2_EVALUATION_NOTE: Final[str] = (
    "Unverified by native speakers; Tier 2 metrics are experimental."
)


class DatasetRecord(TypedDict):
    """Fields required by baseline training and evaluation."""

    text: str
    label: str
    language: str


class ClassMetrics(TypedDict):
    """Metrics for one department label."""

    precision: float
    recall: float
    f1: float
    support: int


class ConfusionMatrix(TypedDict):
    """Confusion matrix with actual labels as rows and predictions as columns."""

    labels: list[str]
    rows_actual_columns_predicted: list[list[int]]


class Metrics(TypedDict):
    """Aggregate and per-class classification metrics."""

    accuracy: float
    macro_f1: float
    per_class: dict[str, ClassMetrics]
    confusion_matrix: ConfusionMatrix


class LanguageMetrics(TypedDict):
    """Evaluation results tagged with the language tier."""

    tier: int
    unverified: bool
    metrics: Metrics


class TierMetrics(TypedDict):
    """Evaluation results grouped by language tier."""

    tier: int
    unverified: bool
    evaluation_note: str
    metrics: Metrics


class BaselineReport(TypedDict):
    """Stable JSON report schema for the baseline evaluation."""

    model: str
    training_rows: int
    evaluation_rows: int
    overall: Metrics
    per_language: dict[str, LanguageMetrics]
    per_tier: dict[str, TierMetrics]


def _read_dataset(path: Path, dataset_name: str) -> list[DatasetRecord]:
    """Load and validate text, label, and language fields from a CSV."""
    with path.open(encoding="utf-8-sig", newline="") as dataset_file:
        reader = csv.DictReader(dataset_file)
        if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            required = ", ".join(sorted(REQUIRED_COLUMNS))
            raise ValueError(f"{dataset_name} CSV must include columns: {required}")
        records: list[DatasetRecord] = []
        for line_number, row in enumerate(reader, start=2):
            text = row.get("text")
            label = row.get("label")
            language = row.get("language")
            if not text or not label or not language:
                raise ValueError(
                    f"{dataset_name} CSV row {line_number} needs non-empty text, label, "
                    "and language"
                )
            if label not in DEPARTMENT_CODES:
                raise ValueError(
                    f"{dataset_name} CSV row {line_number} has unknown department {label!r}"
                )
            if language not in LANGUAGES:
                raise ValueError(
                    f"{dataset_name} CSV row {line_number} has unknown language {language!r}"
                )
            records.append({"text": text, "label": label, "language": language})
    if not records:
        raise ValueError(f"{dataset_name} CSV has no data rows: {path}")
    return records


def _calculate_metrics(
    expected: list[str],
    predicted: list[str],
    labels: tuple[str, ...],
) -> Metrics:
    """Calculate accuracy, macro-F1, per-class scores, and confusion matrix."""
    matrix = confusion_matrix(expected, predicted, labels=labels)
    class_metrics: dict[str, ClassMetrics] = {}
    for index, label in enumerate(labels):
        true_positive = int(matrix[index, index])
        false_positive = int(matrix[:, index].sum()) - true_positive
        false_negative = int(matrix[index, :].sum()) - true_positive
        precision = (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 0.0
        )
        recall = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        class_metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": int(matrix[index, :].sum()),
        }

    return {
        "accuracy": float(accuracy_score(expected, predicted)),
        "macro_f1": float(
            f1_score(expected, predicted, labels=labels, average="macro", zero_division=0)
        ),
        "per_class": class_metrics,
        "confusion_matrix": ConfusionMatrix(
            labels=list(labels),
            rows_actual_columns_predicted=[[int(value) for value in row] for row in matrix],
        ),
    }


def evaluate_baseline(training_path: Path, evaluation_path: Path) -> BaselineReport:
    """Fit the baseline on training data and report metrics on the held-out eval set."""
    training = _read_dataset(training_path, "Training")
    evaluation = _read_dataset(evaluation_path, "Evaluation")
    training_texts = [row["text"] for row in training]
    evaluation_texts = [row["text"] for row in evaluation]
    overlap = set(training_texts).intersection(evaluation_texts)
    if overlap:
        raise ValueError(f"Training and evaluation datasets share {len(overlap)} complaint texts")

    model = make_pipeline(
        TfidfVectorizer(analyzer="char", ngram_range=(2, 5)),
        LogisticRegression(max_iter=1000),
    )
    training_labels = [row["label"] for row in training]
    if len(set(training_labels)) < 2:
        raise ValueError("Training CSV must contain at least two department labels")
    model.fit(training_texts, training_labels)
    predictions = [str(label) for label in model.predict(evaluation_texts)]
    evaluation_labels = [row["label"] for row in evaluation]
    metrics = _calculate_metrics(evaluation_labels, predictions, DEPARTMENT_CODES)

    evaluation_by_language: dict[str, list[int]] = defaultdict(list)
    evaluation_by_tier: dict[int, list[int]] = defaultdict(list)
    for index, row in enumerate(evaluation):
        tier = LANGUAGES[row["language"]].tier
        evaluation_by_language[row["language"]].append(index)
        evaluation_by_tier[tier].append(index)
    if set(evaluation_by_tier) != {1, 2}:
        raise ValueError("Evaluation CSV must include rows from both language tiers")

    per_language: dict[str, LanguageMetrics] = {}
    for language_code, indexes in sorted(evaluation_by_language.items()):
        tier = LANGUAGES[language_code].tier
        per_language[language_code] = {
            "tier": tier,
            "unverified": tier == 2,
            "metrics": _calculate_metrics(
                [evaluation_labels[index] for index in indexes],
                [predictions[index] for index in indexes],
                DEPARTMENT_CODES,
            ),
        }

    per_tier: dict[str, TierMetrics] = {}
    for tier in (1, 2):
        indexes = evaluation_by_tier[tier]
        per_tier[f"tier_{tier}"] = {
            "tier": tier,
            "unverified": tier == 2,
            "evaluation_note": TIER1_EVALUATION_NOTE if tier == 1 else TIER2_EVALUATION_NOTE,
            "metrics": _calculate_metrics(
                [evaluation_labels[index] for index in indexes],
                [predictions[index] for index in indexes],
                DEPARTMENT_CODES,
            ),
        }

    return {
        "model": "char_tfidf_logistic_regression",
        "training_rows": len(training),
        "evaluation_rows": len(evaluation),
        "overall": metrics,
        "per_language": per_language,
        "per_tier": per_tier,
    }


def write_report(report: BaselineReport, output_path: Path) -> Path:
    """Write the baseline metrics report as UTF-8 JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as report_file:
        json.dump(report, report_file, indent=2, ensure_ascii=False)
        report_file.write("\n")
    return output_path


def _parse_args() -> argparse.Namespace:
    """Parse optional baseline input and report paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--training",
        type=Path,
        default=Path("ml/data/processed/train.csv"),
        help="training CSV (evaluation rows must not be included)",
    )
    parser.add_argument(
        "--evaluation",
        type=Path,
        default=Path("ml/data/eval_handwritten/eval.csv"),
        help="held-out evaluation CSV",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/reports/baseline_metrics.json"),
        help="JSON report output",
    )
    return parser.parse_args()


def main() -> None:
    """Train, evaluate, and save the baseline metrics report."""
    args = _parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    report = evaluate_baseline(args.training, args.evaluation)
    output_path = write_report(report, args.output)
    logger.info(
        "ml.baseline.evaluation.completed train_rows=%d evaluation_rows=%d "
        "output_path=%s overall_accuracy=%.4f overall_macro_f1=%.4f",
        report["training_rows"],
        report["evaluation_rows"],
        output_path,
        report["overall"]["accuracy"],
        report["overall"]["macro_f1"],
    )


if __name__ == "__main__":
    main()
