"""Normalize drainage-related HEALTH and SANITATION labels in generated splits."""

import argparse
import csv
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from grievance.seed import DEPARTMENTS

LATIN_DRAINAGE_KEYWORDS: Final[tuple[str, ...]] = (
    "drain",
    "drains",
    "drainage",
    "sewer",
    "sewers",
    "sewage",
    "manhole",
    "manholes",
    "gutter",
    "gutters",
    "nala",
    "naala",
    "nalla",
    "naale",
    "naali",
    "nali",
    "nalli",
)
HINDI_DRAINAGE_KEYWORDS: Final[tuple[str, ...]] = (
    "नाला",
    "नाले",
    "नाली",
    "सीवर",
    "ड्रेनेज",
    "मैनहोल",
    "गटर",
)
GUJARATI_DRAINAGE_KEYWORDS: Final[tuple[str, ...]] = (
    "ગટર",
    "નાળું",
    "નાળા",
    "ગરનાળ",
    "ડ્રેનેજ",
    "મેનહોલ",
)
LATIN_DISEASE_KEYWORDS: Final[tuple[str, ...]] = (
    "mosquito",
    "mosquitoes",
    "malaria",
    "dengue",
    "disease",
    "diseases",
    "infection",
    "infectious",
    "sick",
    "ill",
    "illness",
    "bimar",
    "bimari",
    "machhar",
    "fogging",
    "epidemic",
)
HINDI_DISEASE_KEYWORDS: Final[tuple[str, ...]] = (
    "मच्छर",
    "मलेरिया",
    "डेंगू",
    "बीमार",
    "बीमारी",
    "संक्रामक",
    "संक्रमण",
)
GUJARATI_DISEASE_KEYWORDS: Final[tuple[str, ...]] = (
    "મચ્છર",
    "મેલેરિયા",
    "ડેંગ્યુ",
    "બીમાર",
    "બીમારી",
    "રોગ",
    "રોગચાળો",
)

LATIN_DRAINAGE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(?:" + "|".join(re.escape(word) for word in LATIN_DRAINAGE_KEYWORDS) + r")\b",
    re.IGNORECASE,
)
LATIN_DISEASE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(?:" + "|".join(re.escape(word) for word in LATIN_DISEASE_KEYWORDS) + r")\b",
    re.IGNORECASE,
)
HEALTH_LABEL: Final[str] = "HEALTH"
SANITATION_LABEL: Final[str] = "SANITATION"
DRAINAGE_LABEL: Final[str] = "DRAINAGE"
RELABEL_SOURCE_LABELS: Final[frozenset[str]] = frozenset({HEALTH_LABEL, SANITATION_LABEL})
REQUIRED_COLUMNS: Final[frozenset[str]] = frozenset({"text", "label", "language"})
DEFAULT_TRAIN_PATH: Final[Path] = Path("ml/data/processed/train.csv")
DEFAULT_VALIDATION_PATH: Final[Path] = Path("ml/data/processed/validation.csv")
DEFAULT_BACKUP_DIR: Final[Path] = Path("ml/data/processed/backup")
DEFAULT_CHANGES_PATH: Final[Path] = Path("ml/data/review/relabel_changes.csv")


@dataclass(frozen=True)
class DatasetFile:
    """Parsed CSV and encoding metadata for one processed split."""

    path: Path
    fieldnames: list[str]
    rows: list[dict[str, str]]
    has_utf8_bom: bool


@dataclass(frozen=True)
class RelabelChange:
    """One applied department-label normalization."""

    text: str
    old_label: str
    new_label: str
    language: str
    file: str


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    """Check for any non-Latin keyword without altering the input text."""
    folded_text = text.casefold()
    return any(keyword.casefold() in folded_text for keyword in keywords)


def relabel_department(text: str, label: str) -> str:
    """Return DRAINAGE for drainage complaints currently labelled HEALTH or SANITATION."""
    if label not in RELABEL_SOURCE_LABELS:
        return label

    has_drainage_keyword = LATIN_DRAINAGE_PATTERN.search(text) is not None or any(
        _contains_any(text, keywords)
        for keywords in (HINDI_DRAINAGE_KEYWORDS, GUJARATI_DRAINAGE_KEYWORDS)
    )
    if not has_drainage_keyword:
        return label

    has_disease_keyword = LATIN_DISEASE_PATTERN.search(text) is not None or any(
        _contains_any(text, keywords)
        for keywords in (HINDI_DISEASE_KEYWORDS, GUJARATI_DISEASE_KEYWORDS)
    )
    return label if has_disease_keyword else DRAINAGE_LABEL


def _read_dataset(path: Path) -> DatasetFile:
    """Read a processed CSV and validate the columns required by this rule."""
    with path.open("rb") as dataset_file:
        has_utf8_bom = dataset_file.read(3) == b"\xef\xbb\xbf"
    with path.open(encoding="utf-8-sig", newline="") as dataset_file:
        reader = csv.DictReader(dataset_file)
        if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise ValueError(f"{path} must include text, label, and language columns")
        fieldnames = list(reader.fieldnames)
        rows: list[dict[str, str]] = []
        for line_number, raw_row in enumerate(reader, start=2):
            row: dict[str, str] = {}
            for fieldname in fieldnames:
                value = raw_row.get(fieldname)
                if not isinstance(value, str):
                    raise ValueError(f"{path} row {line_number} has an invalid CSV shape")
                row[fieldname] = value
            if not all(row[column] for column in REQUIRED_COLUMNS):
                raise ValueError(
                    f"{path} row {line_number} needs non-empty text, label, and language"
                )
            rows.append(row)
    return DatasetFile(path, fieldnames, rows, has_utf8_bom)


def _collect_changes(dataset: DatasetFile) -> list[RelabelChange]:
    """Collect all planned changes without modifying the loaded dataset."""
    changes: list[RelabelChange] = []
    for row in dataset.rows:
        old_label = row["label"]
        new_label = relabel_department(row["text"], old_label)
        if new_label != old_label:
            changes.append(
                RelabelChange(
                    text=row["text"],
                    old_label=old_label,
                    new_label=new_label,
                    language=row["language"],
                    file=dataset.path.name,
                )
            )
    return changes


def _apply_changes(dataset: DatasetFile) -> None:
    """Apply the deterministic label rule to the loaded dataset after backup."""
    for row in dataset.rows:
        row["label"] = relabel_department(row["text"], row["label"])


def _create_backups(datasets: list[DatasetFile], backup_dir: Path) -> list[Path]:
    """Create exclusive timestamped copies before changing any processed split."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    suffix = 0
    while True:
        tag = timestamp if suffix == 0 else f"{timestamp}_{suffix}"
        destinations = [
            backup_dir / f"{dataset.path.stem}_{tag}{dataset.path.suffix}" for dataset in datasets
        ]
        if not any(path.exists() for path in destinations):
            break
        suffix += 1

    for dataset, destination in zip(datasets, destinations, strict=True):
        with dataset.path.open("rb") as source, destination.open("xb") as backup:
            shutil.copyfileobj(source, backup)
    return destinations


def _write_dataset(dataset: DatasetFile) -> None:
    """Write a processed split with its original headers and BOM convention."""
    encoding = "utf-8-sig" if dataset.has_utf8_bom else "utf-8"
    with dataset.path.open("w", encoding=encoding, newline="") as dataset_file:
        writer = csv.DictWriter(dataset_file, fieldnames=dataset.fieldnames)
        writer.writeheader()
        writer.writerows(dataset.rows)


def _write_change_report(changes: list[RelabelChange], path: Path) -> None:
    """Write the requested row-level audit report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as report_file:
        writer = csv.DictWriter(
            report_file,
            fieldnames=("text", "old_label", "new_label", "language", "file"),
        )
        writer.writeheader()
        writer.writerows(
            {
                "text": change.text,
                "old_label": change.old_label,
                "new_label": change.new_label,
                "language": change.language,
                "file": change.file,
            }
            for change in changes
        )


def _print_summary(
    datasets: list[DatasetFile],
    changes: list[RelabelChange],
) -> None:
    """Print change counts and resulting train-label counts by language."""
    changed_by_file = Counter(change.file for change in changes)
    changed_by_language = Counter(change.language for change in changes)
    changed_by_pair = Counter((change.old_label, change.new_label) for change in changes)
    training = datasets[0]
    training_counts = Counter((row["language"], row["label"]) for row in training.rows)

    print("Rows changed per file:")
    for dataset in datasets:
        print(f"  {dataset.path.name}: {changed_by_file[dataset.path.name]}")
    print("Rows changed per language:")
    changed_languages = {row["language"] for dataset in datasets for row in dataset.rows}
    for language in sorted(changed_languages):
        print(f"  {language}: {changed_by_language[language]}")
    print("Rows changed per old-label to new-label pair:")
    for old_label, new_label in sorted(changed_by_pair):
        print(f"  {old_label} -> {new_label}: {changed_by_pair[(old_label, new_label)]}")
    if not changed_by_pair:
        print("  none")
    print("New train.csv label counts per language:")
    languages = sorted({row["language"] for row in training.rows})
    labels = [department.code for department in DEPARTMENTS]
    for language in languages:
        counts = ", ".join(f"{label}={training_counts[(language, label)]}" for label in labels)
        print(f"  {language}: {counts}")


def relabel_splits(
    train_path: Path = DEFAULT_TRAIN_PATH,
    validation_path: Path = DEFAULT_VALIDATION_PATH,
    backup_dir: Path = DEFAULT_BACKUP_DIR,
    changes_path: Path = DEFAULT_CHANGES_PATH,
) -> list[RelabelChange]:
    """Back up and relabel processed train/validation splits, leaving eval data untouched."""
    datasets = [_read_dataset(train_path), _read_dataset(validation_path)]
    changes = [change for dataset in datasets for change in _collect_changes(dataset)]
    if changes:
        _create_backups(datasets, backup_dir)
        changed_files = {change.file for change in changes}
        for dataset in datasets:
            if dataset.path.name in changed_files:
                _apply_changes(dataset)
                _write_dataset(dataset)
        _write_change_report(changes, changes_path)
    _print_summary(datasets, changes)
    return changes


def main() -> None:
    """Run the deterministic relabeling on the processed train and validation files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=DEFAULT_TRAIN_PATH)
    parser.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION_PATH)
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR)
    parser.add_argument("--changes", type=Path, default=DEFAULT_CHANGES_PATH)
    args = parser.parse_args()
    relabel_splits(args.train, args.validation, args.backup_dir, args.changes)


if __name__ == "__main__":
    main()
