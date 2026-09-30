"""scripts/purge_legacy.py: dry-run by default, deletes only records without owner."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from tests.firestore_fake import FakeFirestoreClient

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "purge_legacy.py"
SECRET = "Seguradora Sigilosa"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("purge_legacy", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _client() -> FakeFirestoreClient:
    client = FakeFirestoreClient()
    client.store.update(
        {
            "policies/legacy": {"insurer": SECRET},
            "policies/legacy/concept_occurrences/DO-001": {"term": SECRET},
            "policies/legacy/concept_occurrences/DO-002": {"term": SECRET},
            "policies/empty_owner": {"owner_id": "", "insurer": SECRET},
            "policies/owned": {"owner_id": "alice", "insurer": SECRET},
            "policies/owned/concept_occurrences/DO-001": {"owner_id": "alice"},
            "comparisons/legacy": {"policy_a": SECRET},
            "comparisons/owned": {"owner_id": "alice"},
        }
    )
    return client


def test_dry_run_counts_without_deleting() -> None:
    client = _client()
    before = dict(client.store)

    report = _load().LegacyPurger(client).run(apply=False)

    assert (report.policies, report.occurrences, report.comparisons) == (2, 2, 1)
    assert client.store == before


def test_apply_deletes_only_records_without_owner() -> None:
    client = _client()

    report = _load().LegacyPurger(client).run(apply=True)

    assert report.applied
    assert sorted(client.store) == [
        "comparisons/owned",
        "policies/owned",
        "policies/owned/concept_occurrences/DO-001",
    ]
    assert _load().LegacyPurger(client).run(apply=True).policies == 0


def test_report_prints_counts_only(capsys: pytest.CaptureFixture[str]) -> None:
    module = _load()
    report = module.LegacyPurger(_client()).run(apply=False)
    for line in module._report_lines(report):
        print(line)

    output = capsys.readouterr().out
    assert SECRET not in output and "legacy" not in output
    assert "dry-run" in output and "--apply" in output
