"""QA: testes que descrevem falhas conhecidas no envio e no processamento de apólices.

Cada teste falha hoje e deve passar depois da correção (ver relatório do QA).
"""

import asyncio
import io
from pathlib import Path

import pypdf
from app.application.commands import CreatePolicyCommand, UploadedFile
from app.application.use_cases import PolicyService
from app.domain.value_objects import DocumentStatus, DocumentType, PolicyStatus
from app.infrastructure.pdf import PypdfTextReader
from fastapi.testclient import TestClient

from tests.fakes import OWNER, FakeExtractor, auth_headers, build_test_app, make_docx

DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _docx_bytes() -> bytes:
    return make_docx()


def _post(client: TestClient, name: str, data: bytes, content_type: str):  # type: ignore[no-untyped-def]
    return client.post(
        "/api/v1/policies",
        data={"document_types": "POLICY"},
        files=[("files", (name, data, content_type))],
    )


def test_docx_upload_is_accepted(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path), headers=auth_headers()) as client:
        response = _post(client, "apolice.docx", _docx_bytes(), DOCX_CT)
        assert response.status_code == 202, response.text


def test_encrypted_pdf_is_rejected_at_upload_with_clear_message(tmp_path: Path) -> None:
    writer = pypdf.PdfWriter()
    writer.add_blank_page(200, 200)
    writer.encrypt("segredo")
    buffer = io.BytesIO()
    writer.write(buffer)
    with TestClient(build_test_app(tmp_path), headers=auth_headers()) as client:
        response = _post(client, "protegido.pdf", buffer.getvalue(), "application/pdf")
        assert response.status_code == 422, response.text
        assert "senha" in response.text.lower()


def test_corrupt_pdf_is_rejected_at_upload_with_clear_message(tmp_path: Path) -> None:
    with TestClient(build_test_app(tmp_path), headers=auth_headers()) as client:
        response = _post(client, "quebrado.pdf", b"%PDF-1.4\nlixo sem estrutura", "application/pdf")
        assert response.status_code == 422, response.text


def test_pypdf_reader_flags_encrypted_pdf() -> None:
    writer = pypdf.PdfWriter()
    writer.add_blank_page(200, 200)
    writer.encrypt("segredo")
    buffer = io.BytesIO()
    writer.write(buffer)
    result = PypdfTextReader().read(buffer.getvalue())
    assert getattr(result, "encrypted", False) is True


async def test_cancelling_a_policy_does_not_kill_the_queue_worker(tmp_path: Path) -> None:
    """Cancelar chama task.cancel() na task do worker da fila (asyncio.current_task());
    o worker morre (CancelledError e BaseException) e nada mais é processado."""

    started = asyncio.Event()

    class SlowExtractor(FakeExtractor):
        async def extract(self, content, knowledge_base):  # type: ignore[no-untyped-def]
            started.set()
            await asyncio.sleep(30)
            return await super().extract(content, knowledge_base)

    app = build_test_app(tmp_path, SlowExtractor())
    services = app.state.services
    async with app.router.lifespan_context(app):
        service: PolicyService = services.policies
        first = await service.create_policy(
            CreatePolicyCommand(
                owner_id=OWNER,
                insurer=None,
                name=None,
                correlation_id="c1",
                files=[
                    UploadedFile("a.pdf", "application/pdf", b"%PDF-1.4\n", DocumentType.POLICY)
                ],
            )
        )
        await asyncio.wait_for(started.wait(), 5)
        await service.cancel_policy(OWNER, first.id)
        await asyncio.sleep(0.2)

        service._extractor = FakeExtractor()  # type: ignore[assignment]
        second = await service.create_policy(
            CreatePolicyCommand(
                owner_id=OWNER,
                insurer=None,
                name=None,
                correlation_id="c2",
                files=[
                    UploadedFile("b.pdf", "application/pdf", b"%PDF-1.4\n", DocumentType.POLICY)
                ],
            )
        )
        for _ in range(60):
            current = await service.get_policy(OWNER, second.id)
            if current.status != PolicyStatus.PROCESSING:
                break
            await asyncio.sleep(0.05)
        assert current.status != PolicyStatus.PROCESSING, "worker morreu após o cancelamento"
        assert current.documents[0].status == DocumentStatus.COMPLETED
