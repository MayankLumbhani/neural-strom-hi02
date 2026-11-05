"""Fit and save the baseline classifier artifact used by the production image."""

import argparse
from pathlib import Path

import joblib

from grievance.core.logging import configure_logging, logger
from grievance.nlp.classifier import (
    DEFAULT_BASELINE_ARTIFACT_PATH,
    DEFAULT_TRAINING_PATH,
    train_baseline_model,
)


def _parse_args() -> argparse.Namespace:
    """Parse the training CSV and artifact output paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, default=DEFAULT_TRAINING_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_BASELINE_ARTIFACT_PATH)
    return parser.parse_args()


def main() -> None:
    """Fit the baseline pipeline once and persist it with joblib."""
    configure_logging("INFO")
    args = _parse_args()
    model = train_baseline_model(args.training)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.output)
    logger.info(
        "ml.baseline.export.completed training_path=%s output_path=%s",
        args.training,
        args.output,
    )


if __name__ == "__main__":
    main()
