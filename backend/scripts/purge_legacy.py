"""Apaga do Firestore os registros anteriores ao isolamento por dono (LGPD).

Registros sem `owner_id` não aparecem para ninguém desde o isolamento anônimo por
navegador, mas continuam guardados. Este script os remove:

- `policies/{id}` sem `owner_id`, com a subcoleção `concept_occurrences`;
- `comparisons/{id}` sem `owner_id`.

Por padrão só conta (dry-run). Use `--apply` para apagar. Imprime apenas contagens,
nunca conteúdo. Usa as credenciais do backend (FIREBASE_CREDENTIALS_PATH no .env).

    cd backend
    python scripts/purge_legacy.py            # só conta
    python scripts/purge_legacy.py --apply    # apaga
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

POLICIES = "policies"
COMPARISONS = "comparisons"
OCCURRENCES = "concept_occurrences"


@dataclass(frozen=True, slots=True)
class PurgeReport:
    policies: int
    occurrences: int
    comparisons: int
    applied: bool


def _is_legacy(snapshot: Any) -> bool:
    return not (snapshot.to_dict() or {}).get("owner_id")


class LegacyPurger:
    """Finds (and optionally deletes) documents without an owner."""

    def __init__(self, client: Any) -> None:
        self._client = client

    def run(self, apply: bool) -> PurgeReport:
        policies = occurrences = 0
        for snapshot in self._legacy(POLICIES):
            children = list(snapshot.reference.collection(OCCURRENCES).list_documents())
            occurrences += len(children)
            policies += 1
            if apply:
                for child in children:
                    child.delete()
                snapshot.reference.delete()
        comparisons = 0
        for snapshot in self._legacy(COMPARISONS):
            comparisons += 1
            if apply:
                snapshot.reference.delete()
        return PurgeReport(policies, occurrences, comparisons, applied=apply)

    def _legacy(self, collection: str) -> list[Any]:
        # Projection: only the owner field travels, never the document content.
        query = self._client.collection(collection).select(["owner_id"])
        return [snapshot for snapshot in query.stream() if _is_legacy(snapshot)]


def _report_lines(report: PurgeReport) -> list[str]:
    verb = "Apagados" if report.applied else "Seriam apagados (dry-run)"
    lines = [
        f"{verb}:",
        f"  apólices sem dono: {report.policies}",
        f"  ocorrências dessas apólices: {report.occurrences}",
        f"  comparações sem dono: {report.comparisons}",
    ]
    if not report.applied:
        lines.append("Nada foi alterado. Rode com --apply para apagar.")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apaga registros sem owner_id do Firestore.")
    parser.add_argument("--apply", action="store_true", help="apaga de fato (padrão: dry-run)")
    args = parser.parse_args(argv)

    from app.infrastructure.firebase import firebase_app
    from app.shared.config.settings import get_settings
    from firebase_admin import firestore

    settings = get_settings()
    if not (settings.firebase_credentials_path or settings.firebase_project_id):
        print("Configure FIREBASE_CREDENTIALS_PATH no backend/.env.")
        return 2
    client = firestore.client(firebase_app(settings))
    for line in _report_lines(LegacyPurger(client).run(apply=args.apply)):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
