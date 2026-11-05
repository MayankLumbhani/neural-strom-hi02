"""Classifier interface and configured implementations."""

import csv
import importlib
import pickle
from pathlib import Path
from typing import Any, NewType, Protocol, cast

import joblib
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, make_pipeline

from grievance.core.config import Settings
from grievance.core.logging import logger
from grievance.seed import DEPARTMENTS

DepartmentCode = NewType("DepartmentCode", str)
DEPARTMENT_CODES = frozenset(department.code for department in DEPARTMENTS)
DEFAULT_TRAINING_PATH = Path("ml/data/processed/train.csv")
DEFAULT_BASELINE_ARTIFACT_PATH = Path("ml/artifacts/baseline.joblib")
MURIL_MAX_LENGTH = 128
TOP_K = 3


class Prediction(BaseModel):
    """Department prediction with confidence and ranked alternatives."""

    model_config = ConfigDict(frozen=True)

    label: DepartmentCode
    confidence: float = Field(ge=0, le=1)
    top_k: list[tuple[DepartmentCode, float]]

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str) -> DepartmentCode:
        """Require a department code from the canonical seed registry."""
        if value not in DEPARTMENT_CODES:
            raise ValueError(f"Unknown department code: {value}")
        return DepartmentCode(value)

    @field_validator("top_k")
    @classmethod
    def validate_top_k(
        cls, values: list[tuple[DepartmentCode, float]]
    ) -> list[tuple[DepartmentCode, float]]:
        """Require valid department codes and probabilities in the ranked results."""
        for label, probability in values:
            if label not in DEPARTMENT_CODES:
                raise ValueError(f"Unknown department code in top_k: {label}")
            if not 0 <= probability <= 1:
                raise ValueError("top_k probabilities must be between zero and one")
        return values

    @model_validator(mode="after")
    def validate_top_k_contains_prediction(self) -> "Prediction":
        """Require the predicted label to be the highest-ranked result."""
        if not self.top_k or self.top_k[0][0] != self.label:
            raise ValueError("top_k must be non-empty and start with the predicted label")
        return self


class Classifier(Protocol):
    """Common inference interface for department classifiers."""

    def predict(self, text: str) -> Prediction:
        """Return the predicted department and ranked confidence scores."""


class ClassifierLoadError(RuntimeError):
    """A configured classifier could not be initialized."""


def train_baseline_model(training_path: Path = DEFAULT_TRAINING_PATH) -> Pipeline:
    """Fit the baseline pipeline using validated synthetic training rows."""
    if not training_path.is_file():
        raise ClassifierLoadError(f"Baseline training CSV not found: {training_path}")

    texts: list[str] = []
    labels: list[str] = []
    with training_path.open(encoding="utf-8-sig", newline="") as training_file:
        reader = csv.DictReader(training_file)
        if reader.fieldnames is None or not {"text", "label"}.issubset(reader.fieldnames):
            raise ClassifierLoadError("Baseline training CSV must include text and label columns")
        for line_number, row in enumerate(reader, start=2):
            text = row.get("text")
            label = row.get("label")
            if not text or not label:
                raise ClassifierLoadError(
                    f"Baseline training CSV row {line_number} has empty text or label"
                )
            if label not in DEPARTMENT_CODES:
                raise ClassifierLoadError(
                    f"Baseline training CSV row {line_number} has unknown department"
                )
            texts.append(text)
            labels.append(label)

    if not texts:
        raise ClassifierLoadError("Baseline training CSV contains no data rows")
    if len(set(labels)) < 2:
        raise ClassifierLoadError("Baseline training CSV must contain at least two labels")

    model = make_pipeline(
        TfidfVectorizer(analyzer="char", ngram_range=(2, 5)),
        LogisticRegression(max_iter=1000),
    )
    model.fit(texts, labels)
    return model


class BaselineClassifier:
    """Character n-gram TF-IDF and Logistic Regression classifier."""

    def __init__(
        self,
        training_path: Path = DEFAULT_TRAINING_PATH,
        artifact_path: Path = DEFAULT_BASELINE_ARTIFACT_PATH,
    ) -> None:
        self._model: Pipeline = self._load_model(training_path, artifact_path)

    @staticmethod
    def _load_model(training_path: Path, artifact_path: Path) -> Pipeline:
        """Load the saved artifact when present, otherwise fit from the CSV."""
        if artifact_path.is_file():
            try:
                model = joblib.load(artifact_path)
            except (
                OSError,
                ValueError,
                EOFError,
                ImportError,
                AttributeError,
                KeyError,
                pickle.UnpicklingError,
            ) as error:
                raise ClassifierLoadError(
                    f"Baseline artifact could not be loaded: {artifact_path}"
                ) from error
            if not isinstance(model, Pipeline):
                raise ClassifierLoadError(
                    f"Baseline artifact is not a scikit-learn pipeline: {artifact_path}"
                )
            logger.info("classifier.baseline.loaded source=artifact path=%s", artifact_path)
            return cast(Pipeline, model)
        logger.info("classifier.baseline.loaded source=csv path=%s", training_path)
        return train_baseline_model(training_path)

    def predict(self, text: str) -> Prediction:
        """Predict a department with the baseline model's class probabilities."""
        probabilities = self._model.predict_proba([text])[0]
        classifier = self._model[-1]
        class_labels = classifier.classes_
        ranked = sorted(
            (
                (DepartmentCode(str(class_labels[index])), float(probability))
                for index, probability in enumerate(probabilities)
            ),
            key=lambda result: result[1],
            reverse=True,
        )[:TOP_K]
        return Prediction(
            label=ranked[0][0],
            confidence=ranked[0][1],
            top_k=ranked,
        )


class MurilClassifier:
    """Fine-tuned MuRIL inference backend loaded from the configured model path."""

    def __init__(self, settings: Settings) -> None:
        if not settings.model_name_or_path:
            raise ClassifierLoadError("MODEL_NAME_OR_PATH must be configured for the MuRIL backend")

        transformers = importlib.import_module("transformers")
        self._torch: Any = importlib.import_module("torch")
        token = settings.hf_token.get_secret_value() if settings.hf_token else None
        self._tokenizer: Any = transformers.AutoTokenizer.from_pretrained(
            settings.model_name_or_path,
            token=token,
        )
        self._model: Any = transformers.AutoModelForSequenceClassification.from_pretrained(
            settings.model_name_or_path,
            token=token,
        )
        self._labels = self._read_labels(self._model.config.id2label)
        self._model.eval()

    @staticmethod
    def _read_labels(raw_labels: dict[int | str, str]) -> dict[int, DepartmentCode]:
        """Validate and normalize model-config label mappings."""
        labels = {int(index): DepartmentCode(label) for index, label in raw_labels.items()}
        if set(labels) != set(range(len(DEPARTMENT_CODES))):
            raise ClassifierLoadError("MuRIL model must define mappings for all nine classes")
        if {str(label) for label in labels.values()} != DEPARTMENT_CODES:
            raise ClassifierLoadError("MuRIL model label mapping does not match department codes")
        return labels

    def predict(self, text: str) -> Prediction:
        """Predict a department using the loaded MuRIL model."""
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=MURIL_MAX_LENGTH,
        )
        with self._torch.inference_mode():
            logits = self._model(**inputs).logits[0]
            probabilities = self._torch.softmax(logits, dim=-1).tolist()

        ranked = sorted(
            (
                (self._labels[index], float(probability))
                for index, probability in enumerate(probabilities)
            ),
            key=lambda result: result[1],
            reverse=True,
        )[:TOP_K]
        return Prediction(
            label=ranked[0][0],
            confidence=ranked[0][1],
            top_k=ranked,
        )


class FakeClassifier:
    """Deterministic classifier for offline tests."""

    def __init__(
        self,
        label: str = "OTHER",
        confidence: float = 1.0,
        top_k: list[tuple[str, float]] | None = None,
    ) -> None:
        """Configure a repeatable department prediction and ranked confidence scores."""
        ranked = top_k or [(label, confidence)]
        if ranked[0][0] != label:
            raise ValueError("top_k must start with the configured label")
        self._prediction = Prediction(
            label=DepartmentCode(label),
            confidence=ranked[0][1],
            top_k=[(DepartmentCode(code), score) for code, score in ranked],
        )

    def predict(self, text: str) -> Prediction:
        """Return the same configured prediction for every input."""
        return self._prediction


def build_classifier(settings: Settings) -> Classifier:
    """Build the runtime classifier selected by settings."""
    try:
        if settings.classifier_backend == "baseline":
            return BaselineClassifier()
        if settings.classifier_backend == "muril":
            return MurilClassifier(settings)
        if settings.classifier_backend == "fake":
            return FakeClassifier()
    except ClassifierLoadError:
        raise
    except (ImportError, OSError, RuntimeError, TypeError, ValueError) as error:
        raise ClassifierLoadError(
            f"Unable to load the {settings.classifier_backend} classifier backend"
        ) from error
    raise ClassifierLoadError(f"Unsupported classifier backend: {settings.classifier_backend}")
