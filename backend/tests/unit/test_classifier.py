"""Tests for classifier implementations and backend selection."""

import csv
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import joblib
import pytest
from pydantic import ValidationError

from grievance.core.config import Settings
from grievance.nlp import classifier as classifier_module
from grievance.nlp.classifier import (
    BaselineClassifier,
    ClassifierLoadError,
    DepartmentCode,
    FakeClassifier,
    MurilClassifier,
    Prediction,
    build_classifier,
    train_baseline_model,
)
from grievance.seed import DEPARTMENTS


def _write_training_csv(path: Path) -> None:
    """Write a minimal two-class corpus for local baseline tests."""
    with path.open("w", encoding="utf-8", newline="") as training_file:
        writer = csv.DictWriter(training_file, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(
            [
                {"text": "water supply stopped", "label": "WATER"},
                {"text": "no water from tap", "label": "WATER"},
                {"text": "road pothole broken", "label": "ROADS"},
                {"text": "road is damaged", "label": "ROADS"},
            ]
        )


def test_prediction_rejects_unknown_departments() -> None:
    """Keep predictions constrained to canonical department codes."""
    with pytest.raises(ValidationError, match="Unknown department code"):
        Prediction(
            label=DepartmentCode("UNKNOWN"),
            confidence=0.8,
            top_k=[(DepartmentCode("UNKNOWN"), 0.8)],
        )


def test_fake_classifier_returns_a_stable_prediction() -> None:
    """Return the deterministic configured output for any complaint."""
    classifier = FakeClassifier("WATER")

    first = classifier.predict("no water in the lane")
    second = classifier.predict("streetlights are broken")

    assert first == second
    assert first.label == "WATER"
    assert first.confidence == 1.0
    assert first.top_k == [("WATER", 1.0)]


def test_baseline_classifier_fits_and_returns_ranked_probabilities(tmp_path: Path) -> None:
    """Train a small local baseline and validate its prediction shape."""
    training_path = tmp_path / "train.csv"
    _write_training_csv(training_path)

    prediction = BaselineClassifier(
        training_path,
        artifact_path=tmp_path / "missing.joblib",
    ).predict("water from tap is stopped")

    assert prediction.label == "WATER"
    assert prediction.confidence > 0.5
    assert prediction.top_k[0][0] == prediction.label
    assert all(0 <= score <= 1 for _, score in prediction.top_k)


def test_baseline_artifact_matches_freshly_fitted_model(tmp_path: Path) -> None:
    """Load the saved pipeline and produce identical predictions to a fresh fit."""
    training_path = tmp_path / "train.csv"
    artifact_path = tmp_path / "baseline.joblib"
    _write_training_csv(training_path)
    joblib.dump(train_baseline_model(training_path), artifact_path)

    loaded = BaselineClassifier(
        training_path=tmp_path / "missing.csv",
        artifact_path=artifact_path,
    )
    fresh = BaselineClassifier(
        training_path=training_path,
        artifact_path=tmp_path / "missing.joblib",
    )

    for text in ("water supply stopped", "road pothole broken", "tap has no water"):
        assert loaded.predict(text) == fresh.predict(text)


def test_baseline_artifact_load_error_is_reported(tmp_path: Path) -> None:
    """Reject a corrupt artifact instead of silently training from the CSV."""
    training_path = tmp_path / "train.csv"
    artifact_path = tmp_path / "baseline.joblib"
    _write_training_csv(training_path)
    artifact_path.write_bytes(b"not a joblib artifact")

    with pytest.raises(ClassifierLoadError, match="Baseline artifact could not be loaded"):
        BaselineClassifier(training_path, artifact_path=artifact_path)


def test_backend_factory_selects_baseline_from_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fit the configured baseline backend once from its training CSV."""
    training_path = tmp_path / "train.csv"
    _write_training_csv(training_path)
    monkeypatch.setattr(classifier_module, "DEFAULT_TRAINING_PATH", training_path)
    monkeypatch.setattr(
        classifier_module,
        "DEFAULT_BASELINE_ARTIFACT_PATH",
        tmp_path / "missing.joblib",
    )

    classifier = build_classifier(Settings(_env_file=None, classifier_backend="baseline"))

    assert isinstance(classifier, BaselineClassifier)
    assert classifier.predict("water from tap").label == "WATER"


def test_backend_factory_selects_fake_without_model_download() -> None:
    """Build the fake backend from application settings without network access."""
    classifier = build_classifier(Settings(_env_file=None, classifier_backend="fake"))

    assert isinstance(classifier, FakeClassifier)
    assert classifier.predict("test").label == "OTHER"


def test_backend_factory_reports_missing_muril_model_name() -> None:
    """Require the configured Hub or local model name for MuRIL."""
    settings = Settings(
        _env_file=None,
        classifier_backend="muril",
        model_name_or_path=None,
    )

    with pytest.raises(ClassifierLoadError, match="MODEL_NAME_OR_PATH must be configured"):
        build_classifier(settings)


def test_muril_classifier_loads_and_predicts_with_mocked_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exercise MuRIL loading and inference without model downloads."""

    class Tensor:
        def __getitem__(self, index: int) -> "Tensor":
            return self

        def tolist(self) -> list[float]:
            return [0.8, 0.1, 0.025, 0.02, 0.015, 0.01, 0.01, 0.01, 0.01]

    tokenizer = Mock(return_value={"input_ids": [1]})
    model = Mock()
    model.config.id2label = {index: department.code for index, department in enumerate(DEPARTMENTS)}
    model.return_value = SimpleNamespace(logits=Tensor())
    transformers = SimpleNamespace(
        AutoTokenizer=SimpleNamespace(from_pretrained=lambda *args, **kwargs: tokenizer),
        AutoModelForSequenceClassification=SimpleNamespace(
            from_pretrained=lambda *args, **kwargs: model
        ),
    )
    torch = SimpleNamespace(
        inference_mode=nullcontext,
        softmax=lambda logits, dim: logits,
    )

    def import_module(name: str) -> Any:
        """Return dependency doubles instead of importing or downloading packages."""
        return {"transformers": transformers, "torch": torch}[name]

    monkeypatch.setattr("grievance.nlp.classifier.importlib.import_module", import_module)
    classifier = MurilClassifier(
        Settings(
            _env_file=None,
            classifier_backend="muril",
            model_name_or_path="local-test-model",
        )
    )

    prediction = classifier.predict("test complaint")

    assert prediction.label == "WATER"
    assert prediction.confidence == 0.8
    assert prediction.top_k[0][0] == "WATER"
