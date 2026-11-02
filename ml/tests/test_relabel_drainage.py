"""Offline tests for deterministic drainage-label normalization."""

import csv
from pathlib import Path

from relabel_drainage import relabel_department, relabel_splits


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    """Write a minimal processed-split fixture."""
    with path.open("w", encoding="utf-8", newline="") as dataset_file:
        writer = csv.DictWriter(dataset_file, fieldnames=("text", "label", "language"))
        writer.writeheader()
        writer.writerows(rows)


def test_drainage_health_row_is_relabelled() -> None:
    """Move a drainage issue from HEALTH to DRAINAGE."""
    assert relabel_department("drain water leaking on road", "HEALTH") == "DRAINAGE"


def test_drainage_with_mosquito_remains_health() -> None:
    """Keep disease-related complaints under HEALTH even when drainage is mentioned."""
    assert relabel_department("drain water with mosquitoes nearby", "HEALTH") == "HEALTH"


def test_non_drain_health_row_is_unchanged() -> None:
    """Leave a HEALTH row unchanged without a drainage keyword."""
    assert relabel_department("mosquitoes near the community ground", "HEALTH") == "HEALTH"


def test_other_labels_are_never_changed() -> None:
    """Never relabel a non-candidate department, even when it mentions a drain."""
    assert relabel_department("drain is blocked", "WATER") == "WATER"


def test_latin_disease_terms_use_word_boundaries() -> None:
    """Do not match disease keyword ill inside the words bill or drilling."""
    assert relabel_department("drain near the bill counter", "HEALTH") == "DRAINAGE"
    assert relabel_department("drilling work near the drainage", "SANITATION") == "DRAINAGE"


def test_hindi_drainage_and_disease_keywords_work() -> None:
    """Recognize Hindi drainage terms while preserving disease rows."""
    assert relabel_department("नाली का पानी सड़क पर बह रहा है", "HEALTH") == "DRAINAGE"
    assert relabel_department("नाला बंद है और मच्छर बढ़ रहे हैं", "HEALTH") == "HEALTH"


def test_gujarati_drainage_and_disease_keywords_work() -> None:
    """Recognize Gujarati drainage terms while preserving disease rows."""
    assert relabel_department("ગટરનું પાણી રસ્તા પર વહે છે", "SANITATION") == "DRAINAGE"
    assert relabel_department("ગટરમાં મચ્છર અને રોગચાળો", "HEALTH") == "HEALTH"


def test_relabeling_backs_up_audit_changes_and_is_idempotent(tmp_path: Path) -> None:
    """Back up both source files and leave all files untouched on a second run."""
    train_path = tmp_path / "train.csv"
    validation_path = tmp_path / "validation.csv"
    backup_dir = tmp_path / "backup"
    changes_path = tmp_path / "review" / "relabel_changes.csv"
    original_rows = [
        {"text": "drain leaking beside road", "label": "HEALTH", "language": "en"},
        {"text": "mosquitoes near wet ground", "label": "HEALTH", "language": "en"},
    ]
    _write_rows(train_path, original_rows)
    _write_rows(
        validation_path,
        [{"text": "ગટરનું પાણી રસ્તા પર છે", "label": "SANITATION", "language": "gu"}],
    )
    train_before = train_path.read_bytes()
    validation_before = validation_path.read_bytes()

    changes = relabel_splits(train_path, validation_path, backup_dir, changes_path)

    assert len(changes) == 2
    backups = list(backup_dir.iterdir())
    assert len(backups) == 2
    assert train_before in [path.read_bytes() for path in backups]
    assert validation_before in [path.read_bytes() for path in backups]
    with train_path.open(encoding="utf-8", newline="") as dataset_file:
        assert [row["label"] for row in csv.DictReader(dataset_file)] == [
            "DRAINAGE",
            "HEALTH",
        ]
    report_before = changes_path.read_bytes()
    train_after = train_path.read_bytes()
    validation_after = validation_path.read_bytes()

    assert relabel_splits(train_path, validation_path, backup_dir, changes_path) == []

    assert train_path.read_bytes() == train_after
    assert validation_path.read_bytes() == validation_after
    assert changes_path.read_bytes() == report_before
    assert len(list(backup_dir.iterdir())) == 2
