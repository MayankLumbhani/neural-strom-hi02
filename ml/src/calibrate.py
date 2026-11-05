"""Calibrate classifier auto-accept thresholds on validation rows only."""

import argparse
import json
from pathlib import Path
from typing import Final, TypedDict

from sklearn.pipeline import Pipeline

from grievance.nlp.classifier import train_baseline_model
from grievance.nlp.languages import LANGUAGES
from ml.src.evaluate import DatasetRecord, _read_dataset

TIER1_LANGUAGES: Final[tuple[str, ...]] = ("en", "hi", "gu", "hinglish")
CANDIDATE_GRID: Final[tuple[tuple[float, float, float], ...]] = (
    (0.25, 0.10, 0.0),
    (0.30, 0.15, 0.25),
    (0.35, 0.12, 0.25),
    (0.40, 0.12, 0.25),
    (0.45, 0.18, 0.25),
)


class Thresholds(TypedDict):
    """Auto-accept rule thresholds."""

    accept: float
    margin: float
    margin_min_confidence: float


class PredictionRow(TypedDict):
    """One validation or evaluation row with its ranked prediction."""

    text: str
    label: str
    language: str
    predicted: str
    top1: float
    top2_label: str
    top2: float


class RuleMetrics(TypedDict):
    """Acceptance metrics for one subset of rows."""

    rows: int
    accepted: int
    coverage: float
    correct: int
    incorrect: int
    precision: float


class LanguageMetrics(TypedDict):
    """Top-1 and rule metrics for one language."""

    rows: int
    top1_accuracy: float
    accepted: int
    coverage: float
    correct: int
    incorrect: int
    precision: float


class DatasetReport(TypedDict):
    """Rule metrics and per-language detail for one dataset."""

    tier_1: RuleMetrics
    all: RuleMetrics
    per_language: dict[str, LanguageMetrics]


class CalibrationReport(TypedDict):
    """Stable JSON report for the classifier calibration."""

    model: str
    tuning_dataset: str
    tuning_note: str
    training_rows: int
    validation_rows: int
    evaluation_rows: int
    thresholds: Thresholds
    candidate_grid: list[dict[str, object]]
    validation: DatasetReport
    evaluation: DatasetReport
    eval_examples: list[dict[str, object]]


def _thresholds(accept: float, margin: float, margin_min_confidence: float) -> Thresholds:
    """Build a typed threshold bundle."""
    return Thresholds(
        accept=accept,
        margin=margin,
        margin_min_confidence=margin_min_confidence,
    )


def _predict_rows(records: list[DatasetRecord], model: Pipeline) -> list[PredictionRow]:
    """Rank class probabilities for every record."""
    rows: list[PredictionRow] = []
    for record in records:
        probabilities = model.predict_proba([record["text"]])[0]
        classifier = model[-1]
        class_labels = classifier.classes_
        ranked = sorted(
            (
                (str(class_labels[index]), float(probability))
                for index, probability in enumerate(probabilities)
            ),
            key=lambda result: result[1],
            reverse=True,
        )
        rows.append(
            PredictionRow(
                text=record["text"],
                label=record["label"],
                language=record["language"],
                predicted=ranked[0][0],
                top1=ranked[0][1],
                top2_label=ranked[1][0],
                top2=ranked[1][1],
            )
        )
    return rows


def _accepts(row: PredictionRow, thresholds: Thresholds) -> bool:
    """Apply the absolute-confidence or large-margin acceptance rule."""
    top1 = row["top1"]
    margin = top1 - row["top2"]
    return top1 >= thresholds["accept"] or (
        top1 >= thresholds["margin_min_confidence"] and margin >= thresholds["margin"]
    )


def _rule_metrics(
    rows: list[PredictionRow],
    thresholds: Thresholds,
    tier1_only: bool,
) -> RuleMetrics:
    """Calculate accepted coverage and precision for rows in scope."""
    selected = [row for row in rows if not tier1_only or LANGUAGES[row["language"]].tier == 1]
    accepted = [row for row in selected if _accepts(row, thresholds)]
    correct = sum(row["label"] == row["predicted"] for row in accepted)
    return RuleMetrics(
        rows=len(selected),
        accepted=len(accepted),
        coverage=len(accepted) / len(selected) if selected else 0.0,
        correct=correct,
        incorrect=len(accepted) - correct,
        precision=correct / len(accepted) if accepted else 0.0,
    )


def _top1_accuracy(rows: list[PredictionRow]) -> float:
    """Return raw top-1 accuracy for a set of rows."""
    return sum(row["label"] == row["predicted"] for row in rows) / len(rows)


def _language_metrics(
    rows: list[PredictionRow],
    thresholds: Thresholds,
) -> dict[str, LanguageMetrics]:
    """Report raw accuracy and accepted coverage for Tier 1 languages."""
    metrics: dict[str, LanguageMetrics] = {}
    for language_code in TIER1_LANGUAGES:
        language_rows = [row for row in rows if row["language"] == language_code]
        rule = _rule_metrics(language_rows, thresholds, tier1_only=True)
        metrics[language_code] = LanguageMetrics(
            rows=len(language_rows),
            top1_accuracy=_top1_accuracy(language_rows),
            accepted=rule["accepted"],
            coverage=rule["coverage"],
            correct=rule["correct"],
            incorrect=rule["incorrect"],
            precision=rule["precision"],
        )
    return metrics


def _eval_examples(
    rows: list[PredictionRow],
    thresholds: Thresholds,
) -> list[dict[str, object]]:
    """Select three distinct departments per Tier 1 language from eval rows."""
    selected: dict[str, list[PredictionRow]] = {language: [] for language in TIER1_LANGUAGES}
    seen_labels: dict[str, set[str]] = {language: set() for language in TIER1_LANGUAGES}
    for row in rows:
        language_code = row["language"]
        if language_code not in selected or len(selected[language_code]) >= 3:
            continue
        if row["label"] in seen_labels[language_code]:
            continue
        selected[language_code].append(row)
        seen_labels[language_code].add(row["label"])

    examples: list[dict[str, object]] = []
    for language_code in TIER1_LANGUAGES:
        for row in selected[language_code]:
            examples.append(
                {
                    "language": language_code,
                    "text": row["text"],
                    "expected": row["label"],
                    "predicted": row["predicted"],
                    "top1": round(row["top1"], 4),
                    "top2_label": row["top2_label"],
                    "top2": round(row["top2"], 4),
                    "margin": round(row["top1"] - row["top2"], 4),
                    "accepted": _accepts(row, thresholds),
                }
            )
    return examples


def _candidate_grid(
    validation_rows: list[PredictionRow],
    evaluation_rows: list[PredictionRow],
) -> list[dict[str, object]]:
    """Report validation and held-out metrics for nearby candidate rules."""
    grid: list[dict[str, object]] = []
    for accept, margin, floor in CANDIDATE_GRID:
        thresholds = _thresholds(accept, margin, floor)
        grid.append(
            {
                "thresholds": thresholds,
                "validation_tier1": _rule_metrics(validation_rows, thresholds, tier1_only=True),
                "evaluation_tier1": _rule_metrics(evaluation_rows, thresholds, tier1_only=True),
            }
        )
    return grid


def build_calibration_report(
    training_path: Path,
    validation_path: Path,
    evaluation_path: Path,
    thresholds: Thresholds,
) -> CalibrationReport:
    """Fit the baseline and measure the acceptance rule on validation and eval."""
    training = _read_dataset(training_path, "Training")
    validation = _read_dataset(validation_path, "Validation")
    evaluation = _read_dataset(evaluation_path, "Evaluation")
    model = train_baseline_model(training_path)
    validation_rows = _predict_rows(validation, model)
    evaluation_rows = _predict_rows(evaluation, model)

    return CalibrationReport(
        model="char_tfidf_logistic_regression",
        tuning_dataset="validation",
        tuning_note=(
            "Thresholds were selected using validation Tier 1 coverage and precision only; "
            "the handwritten evaluation rows are held out."
        ),
        training_rows=len(training),
        validation_rows=len(validation),
        evaluation_rows=len(evaluation),
        thresholds=thresholds,
        candidate_grid=_candidate_grid(validation_rows, evaluation_rows),
        validation=DatasetReport(
            tier_1=_rule_metrics(validation_rows, thresholds, tier1_only=True),
            all=_rule_metrics(validation_rows, thresholds, tier1_only=False),
            per_language=_language_metrics(validation_rows, thresholds),
        ),
        evaluation=DatasetReport(
            tier_1=_rule_metrics(evaluation_rows, thresholds, tier1_only=True),
            all=_rule_metrics(evaluation_rows, thresholds, tier1_only=False),
            per_language=_language_metrics(evaluation_rows, thresholds),
        ),
        eval_examples=_eval_examples(evaluation_rows, thresholds),
    )


def write_report(report: CalibrationReport, output_path: Path) -> Path:
    """Write the calibration report as UTF-8 JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as report_file:
        json.dump(report, report_file, indent=2, ensure_ascii=False)
        report_file.write("\n")
    return output_path


def _parse_args() -> argparse.Namespace:
    """Parse calibration inputs and threshold overrides."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--training",
        type=Path,
        default=Path("ml/data/processed/train.csv"),
        help="training CSV used to fit the baseline",
    )
    parser.add_argument(
        "--validation",
        type=Path,
        default=Path("ml/data/processed/validation.csv"),
        help="validation CSV used only for threshold selection",
    )
    parser.add_argument(
        "--evaluation",
        type=Path,
        default=Path("ml/data/eval_handwritten/eval.csv"),
        help="held-out handwritten evaluation CSV",
    )
    parser.add_argument("--accept-threshold", type=float, default=0.35)
    parser.add_argument("--margin-threshold", type=float, default=0.12)
    parser.add_argument("--margin-min-confidence", type=float, default=0.25)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/reports/confidence_calibration.json"),
        help="JSON report output",
    )
    return parser.parse_args()


def main() -> None:
    """Calibrate, evaluate, and save the confidence threshold report."""
    args = _parse_args()
    thresholds = _thresholds(
        args.accept_threshold,
        args.margin_threshold,
        args.margin_min_confidence,
    )
    report = build_calibration_report(
        args.training,
        args.validation,
        args.evaluation,
        thresholds,
    )
    output_path = write_report(report, args.output)
    validation_tier1 = report["validation"]["tier_1"]
    evaluation_tier1 = report["evaluation"]["tier_1"]
    print(
        f"wrote {output_path} "
        f"validation_tier1_coverage={validation_tier1['coverage']:.4f} "
        f"validation_tier1_precision={validation_tier1['precision']:.4f} "
        f"evaluation_tier1_coverage={evaluation_tier1['coverage']:.4f} "
        f"evaluation_tier1_precision={evaluation_tier1['precision']:.4f}"
    )


if __name__ == "__main__":
    main()
