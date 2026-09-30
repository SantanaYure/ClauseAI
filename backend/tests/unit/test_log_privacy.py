"""LGPD in logs: no token, uid, file name, insurer, extracted text or raw error message."""

import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
from app.shared.logging import owner_ref
from app.shared.logging.structured import StructuredJsonFormatter
from fastapi.testclient import TestClient

from tests.fakes import PDF_BYTES, FakeExtractor, auth_headers, build_test_app
from tests.integration.test_api_flow import wait_for

UID = "uidsecreto123"
FILENAME = "cpf-12345678900-joao.pdf"
INSURER = "Seguradora Sigilosa"
EXTRACTED = "trecho sigiloso extraído da apólice"


class _Capture(logging.Handler):
    """Formats at emit time, so the structured context (owner_ref, stack...) is kept."""

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.setFormatter(StructuredJsonFormatter())
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


@pytest.fixture
def captured() -> Iterator[_Capture]:
    handler = _Capture()
    root = logging.getLogger()
    previous = root.level
    root.addHandler(handler)
    root.setLevel(logging.DEBUG)
    yield handler
    root.removeHandler(handler)
    root.setLevel(previous)


class _LeakyExtractor(FakeExtractor):
    async def extract(self, content, knowledge_base):  # type: ignore[no-untyped-def]
        raise RuntimeError(f"{EXTRACTED} em {content.document.filename}")


def test_processing_failure_logs_no_personal_data(
    tmp_path: Path, captured: _Capture, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    with TestClient(build_test_app(tmp_path, _LeakyExtractor()), headers=auth_headers(UID)) as c:
        created = c.post(
            "/api/v1/policies",
            data={"document_types": ["POLICY"], "insurer": INSURER},
            files=[("files", (FILENAME, PDF_BYTES, "application/pdf"))],
        )
        assert created.status_code == 202
        wait_for(c, f"/api/v1/policies/{created.json()['policy_id']}", {"FAILED", "ATTENTION"})
        c.get("/api/v1/policies/pol_inexistente")

    everything = "\n".join(captured.lines) + caplog.text
    for secret in (UID, f"dev-{UID}", "Bearer", FILENAME, INSURER, EXTRACTED):
        assert secret not in everything, secret
    assert owner_ref(UID) in everything
    assert any('"error_type": "RuntimeError"' in line for line in captured.lines)


def test_owner_ref_is_a_short_stable_hash() -> None:
    assert owner_ref("abc") == owner_ref("abc")
    assert owner_ref("abc") != owner_ref("abd")
    assert len(owner_ref("abc")) == 12 and "abc" not in owner_ref("abc")


def test_formatter_drops_exception_messages() -> None:
    try:
        raise ValueError(EXTRACTED)
    except ValueError:
        record = logging.getLogger("t").makeRecord(
            "t", logging.ERROR, __file__, 1, "falhou", None, exc_info=__import__("sys").exc_info()
        )
    line = StructuredJsonFormatter().format(record)
    assert EXTRACTED not in line
    assert '"error_type": "ValueError"' in line
