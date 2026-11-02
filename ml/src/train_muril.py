"""Fine-tune MuRIL for multilingual municipal department classification."""

import argparse
import importlib
import json
import os
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Protocol, TypedDict

from grievance.core.config import get_settings
from grievance.core.logging import configure_logging, logger
from grievance.nlp.languages import LANGUAGES
from grievance.seed import DEPARTMENTS
from ml.src.evaluate import (
    DEPARTMENT_CODES,
    DatasetRecord,
    Metrics,
    _calculate_metrics,
    _read_dataset,
)

MODEL_NAME: Final[str] = "google/muril-base-cased"
DEFAULT_MAX_LENGTH: Final[int] = 128
DEFAULT_EPOCHS: Final[int] = 4
DEFAULT_LEARNING_RATE: Final[float] = 3e-5
DEFAULT_BATCH_SIZE: Final[int] = 32
DEFAULT_SEED: Final[int] = 42
DEFAULT_TRAIN_PATH: Final[Path] = Path("ml/data/processed/train.csv")
DEFAULT_VALIDATION_PATH: Final[Path] = Path("ml/data/processed/validation.csv")
DEFAULT_EVALUATION_PATH: Final[Path] = Path("ml/data/eval_handwritten/eval.csv")
DEFAULT_OUTPUT_DIR: Final[Path] = Path("ml/artifacts/muril_model")
DEFAULT_METRICS_PATH: Final[Path] = Path("ml/artifacts/muril_metrics.json")
TIER1_EVALUATION_NOTE: Final[str] = (
    "AI-authored, short, parallel rows; accuracy may be an optimistic estimate."
)
TIER2_EVALUATION_NOTE: Final[str] = (
    "Unverified by native speakers; Tier 2 metrics are experimental."
)


class Tokenizer(Protocol):
    """Tokenizer interface needed to prepare padded Trainer examples."""

    def __call__(
        self, text: str, *, truncation: bool, max_length: int
    ) -> dict[str, Sequence[int]]: ...


class TokenizedDataset:
    """Map complaint text to token IDs and department label IDs."""

    def __init__(
        self,
        examples: list[DatasetRecord],
        tokenizer: Tokenizer,
        label2id: dict[str, int],
        max_length: int,
    ) -> None:
        self._rows: list[dict[str, list[int] | int]] = []
        for example in examples:
            encoded = tokenizer(
                example["text"],
                truncation=True,
                max_length=max_length,
            )
            row: dict[str, list[int] | int] = {key: list(values) for key, values in encoded.items()}
            row["labels"] = label2id[example["label"]]
            self._rows.append(row)

    def __len__(self) -> int:
        """Return the number of tokenized examples."""
        return len(self._rows)

    def __getitem__(self, index: int) -> dict[str, list[int] | int]:
        """Return one encoded example and its label."""
        return self._rows[index]


class LanguageMetrics(TypedDict):
    """Evaluation results tagged with the registry language tier."""

    tier: int
    unverified: bool
    metrics: Metrics


class TierMetrics(TypedDict):
    """Evaluation metrics grouped and labelled by language tier."""

    tier: int
    unverified: bool
    evaluation_note: str
    metrics: Metrics


class MuRILReport(TypedDict):
    """Metrics schema aligned with the baseline evaluation report."""

    model: str
    training_rows: int
    evaluation_rows: int
    best_checkpoint_validation_macro_f1: float
    overall: Metrics
    per_language: dict[str, LanguageMetrics]
    per_tier: dict[str, TierMetrics]


@dataclass(frozen=True)
class TrainingConfig:
    """Paths and hyperparameters for a MuRIL fine-tuning run."""

    train_path: Path
    validation_path: Path
    evaluation_path: Path
    output_dir: Path
    metrics_path: Path
    max_length: int
    epochs: int
    learning_rate: float
    batch_size: int
    seed: int
    push_to_hub: bool
    hub_model_id: str | None


def load_examples(path: Path, dataset_name: str) -> list[DatasetRecord]:
    """Read and validate a dataset against the department and language registries."""
    return _read_dataset(path, dataset_name)


def label_mappings() -> tuple[dict[str, int], dict[int, str]]:
    """Build deterministic department mappings from the repository seed list."""
    label2id = {department.code: index for index, department in enumerate(DEPARTMENTS)}
    id2label = {index: label for label, index in label2id.items()}
    if set(label2id) != set(DEPARTMENT_CODES) or len(label2id) != 9:
        raise ValueError("Department registry must define exactly nine unique labels")
    return label2id, id2label


def build_report(
    evaluation: list[DatasetRecord],
    predictions: list[str],
    training_rows: int,
    validation_macro_f1: float,
) -> MuRILReport:
    """Build baseline-compatible overall, per-language, and tiered metrics."""
    if len(evaluation) != len(predictions):
        raise ValueError("Evaluation examples and predictions must have equal lengths")
    if not evaluation:
        raise ValueError("Evaluation CSV has no data rows")

    expected = [example["label"] for example in evaluation]
    overall = _calculate_metrics(expected, predictions, DEPARTMENT_CODES)
    language_indices: dict[str, list[int]] = defaultdict(list)
    tier_indices: dict[int, list[int]] = defaultdict(list)
    for index, example in enumerate(evaluation):
        language = LANGUAGES[example["language"]]
        language_indices[language.code].append(index)
        tier_indices[language.tier].append(index)
    if set(tier_indices) != {1, 2}:
        raise ValueError("Evaluation CSV must include rows from both language tiers")

    per_language: dict[str, LanguageMetrics] = {}
    for language_code, indexes in sorted(language_indices.items()):
        tier = LANGUAGES[language_code].tier
        per_language[language_code] = {
            "tier": tier,
            "unverified": tier == 2,
            "metrics": _calculate_metrics(
                [expected[index] for index in indexes],
                [predictions[index] for index in indexes],
                DEPARTMENT_CODES,
            ),
        }

    per_tier: dict[str, TierMetrics] = {}
    for tier in (1, 2):
        indexes = tier_indices[tier]
        per_tier[f"tier_{tier}"] = {
            "tier": tier,
            "unverified": tier == 2,
            "evaluation_note": TIER1_EVALUATION_NOTE if tier == 1 else TIER2_EVALUATION_NOTE,
            "metrics": _calculate_metrics(
                [expected[index] for index in indexes],
                [predictions[index] for index in indexes],
                DEPARTMENT_CODES,
            ),
        }

    return {
        "model": MODEL_NAME,
        "training_rows": training_rows,
        "evaluation_rows": len(evaluation),
        "best_checkpoint_validation_macro_f1": validation_macro_f1,
        "overall": overall,
        "per_language": per_language,
        "per_tier": per_tier,
    }


def write_report(report: MuRILReport, path: Path) -> None:
    """Write metrics JSON without including credentials or training data."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as report_file:
        json.dump(report, report_file, ensure_ascii=False, indent=2)
        report_file.write("\n")


def _validate_config(config: TrainingConfig) -> None:
    """Reject invalid hyperparameters and inconsistent Hub options."""
    if config.max_length < 1:
        raise ValueError("--max_length must be greater than zero")
    if config.epochs < 1:
        raise ValueError("--epochs must be greater than zero")
    if config.learning_rate <= 0:
        raise ValueError("--learning_rate must be greater than zero")
    if config.batch_size < 1:
        raise ValueError("--batch_size must be greater than zero")
    if config.push_to_hub and not config.hub_model_id:
        raise ValueError("--push_to_hub requires --hub_model_id")
    if config.hub_model_id and not config.push_to_hub:
        raise ValueError("--hub_model_id can only be used with --push_to_hub")


def _ensure_disjoint_texts(training: list[DatasetRecord], evaluation: list[DatasetRecord]) -> None:
    """Prevent any exact complaint text from crossing the train/evaluation boundary."""
    overlap = {row["text"] for row in training}.intersection(row["text"] for row in evaluation)
    if overlap:
        raise ValueError(f"Training and evaluation datasets share {len(overlap)} complaint texts")


def _write_label_mapping(output_dir: Path) -> None:
    """Persist the class order next to the saved model for inference loaders."""
    label2id, id2label = label_mappings()
    mapping = {
        "label2id": label2id,
        "id2label": {str(index): label for index, label in id2label.items()},
    }
    with (output_dir / "label_mapping.json").open(
        "w", encoding="utf-8", newline=""
    ) as mapping_file:
        json.dump(mapping, mapping_file, ensure_ascii=False, indent=2)
        mapping_file.write("\n")


def run_training(config: TrainingConfig) -> MuRILReport:
    """Fine-tune MuRIL, select by validation macro-F1, and evaluate the best model."""
    _validate_config(config)
    hub_token = os.environ.get("HF_TOKEN")
    if config.push_to_hub and not hub_token:
        raise ValueError("HF_TOKEN must be set in the environment when pushing to the Hub")
    training = load_examples(config.train_path, "Training")
    validation = load_examples(config.validation_path, "Validation")
    evaluation = load_examples(config.evaluation_path, "Evaluation")
    label2id, id2label = label_mappings()
    training_labels = {example["label"] for example in training}
    if training_labels != set(label2id):
        missing_labels = sorted(set(label2id).difference(training_labels))
        raise ValueError(f"Training CSV is missing department labels: {', '.join(missing_labels)}")
    _ensure_disjoint_texts(training, evaluation)

    transformers: Any = importlib.import_module("transformers")
    torch: Any = importlib.import_module("torch")
    tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_NAME)
    model = transformers.AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id,
    )
    transformers.set_seed(config.seed)

    training_dataset = TokenizedDataset(training, tokenizer, label2id, config.max_length)
    validation_dataset = TokenizedDataset(validation, tokenizer, label2id, config.max_length)
    evaluation_dataset = TokenizedDataset(evaluation, tokenizer, label2id, config.max_length)

    def compute_metrics(eval_prediction: Any) -> dict[str, float]:
        """Calculate validation metrics across all configured department labels."""
        logits = eval_prediction.predictions
        if isinstance(logits, tuple):
            logits = logits[0]
        predictions = logits.argmax(axis=-1).tolist()
        expected = eval_prediction.label_ids.tolist()
        return {
            "accuracy": float(
                sum(
                    actual == predicted
                    for actual, predicted in zip(expected, predictions, strict=True)
                )
                / len(expected)
            ),
            "macro_f1": _calculate_metrics(
                [id2label[int(index)] for index in expected],
                [id2label[int(index)] for index in predictions],
                DEPARTMENT_CODES,
            )["macro_f1"],
        }

    training_args = transformers.TrainingArguments(
        output_dir=str(config.output_dir),
        num_train_epochs=config.epochs,
        learning_rate=config.learning_rate,
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=config.batch_size,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_macro_f1",
        greater_is_better=True,
        save_total_limit=2,
        seed=config.seed,
        data_seed=config.seed,
        fp16=bool(torch.cuda.is_available()),
        report_to=[],
    )
    trainer = transformers.Trainer(
        model=model,
        args=training_args,
        train_dataset=training_dataset,
        eval_dataset=validation_dataset,
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
    )
    trainer.train()
    best_validation_macro_f1 = trainer.state.best_metric
    if best_validation_macro_f1 is None:
        raise RuntimeError("Training completed without a best validation macro-F1 checkpoint")
    trainer.save_model(str(config.output_dir))
    tokenizer.save_pretrained(str(config.output_dir))
    _write_label_mapping(config.output_dir)

    predictions_output = trainer.predict(evaluation_dataset)
    predicted_ids = predictions_output.predictions
    if isinstance(predicted_ids, tuple):
        predicted_ids = predicted_ids[0]
    predictions = [id2label[int(index)] for index in predicted_ids.argmax(axis=-1).tolist()]
    report = build_report(
        evaluation,
        predictions,
        len(training),
        float(best_validation_macro_f1),
    )
    write_report(report, config.metrics_path)

    if config.push_to_hub:
        trainer.model.push_to_hub(config.hub_model_id, token=hub_token)
        tokenizer.push_to_hub(config.hub_model_id, token=hub_token)
    return report


def _parse_args() -> TrainingConfig:
    """Parse training hyperparameters, dataset paths, and optional Hub settings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train_path", type=Path, default=DEFAULT_TRAIN_PATH)
    parser.add_argument("--validation_path", type=Path, default=DEFAULT_VALIDATION_PATH)
    parser.add_argument("--evaluation_path", type=Path, default=DEFAULT_EVALUATION_PATH)
    parser.add_argument("--output_dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--metrics_path", type=Path, default=DEFAULT_METRICS_PATH)
    parser.add_argument("--max_length", type=int, default=DEFAULT_MAX_LENGTH)
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--learning_rate", type=float, default=DEFAULT_LEARNING_RATE)
    parser.add_argument("--batch_size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--push_to_hub", action="store_true")
    parser.add_argument("--hub_model_id")
    args = parser.parse_args()
    return TrainingConfig(
        train_path=args.train_path,
        validation_path=args.validation_path,
        evaluation_path=args.evaluation_path,
        output_dir=args.output_dir,
        metrics_path=args.metrics_path,
        max_length=args.max_length,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        seed=args.seed,
        push_to_hub=args.push_to_hub,
        hub_model_id=args.hub_model_id,
    )


def main() -> None:
    """Run MuRIL fine-tuning and log a concise metrics-file location."""
    config = _parse_args()
    settings = get_settings()
    configure_logging(settings.log_level)
    report = run_training(config)
    logger.info(
        "ml.muril.training.completed train_rows=%d evaluation_rows=%d "
        "best_validation_macro_f1=%.4f metrics_path=%s",
        report["training_rows"],
        report["evaluation_rows"],
        report["best_checkpoint_validation_macro_f1"],
        config.metrics_path,
    )


if __name__ == "__main__":
    main()
