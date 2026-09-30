"""Garante que o gerador de apólices de exemplo roda e que os arquivos passam pelo backend."""

import importlib.util
import time
from pathlib import Path
from types import ModuleType

import pytest
from app.application.file_types import DOCX_MIME, PDF_MIME, detect_content_type
from app.infrastructure.pdf import PypdfTextReader
from app.infrastructure.word import PythonDocxTextReader
from fastapi.testclient import TestClient

from tests import fakes

pytest.importorskip("reportlab", reason="extra opcional 'samples' não instalado")

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "generate_sample_policies.py"


def _load_generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("generate_sample_policies", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> list[Path]:
    output = tmp_path_factory.mktemp("policies")
    return _load_generator().generate(output)  # type: ignore[no-any-return]


def test_generates_pdf_and_docx_for_five_policies(generated: list[Path]) -> None:
    assert sorted(p.suffix for p in generated) == [".docx"] * 5 + [".pdf"] * 5
    assert len({p.stem for p in generated}) == 5


def test_files_are_accepted_by_content_type_detector(generated: list[Path]) -> None:
    for path in generated:
        expected = PDF_MIME if path.suffix == ".pdf" else DOCX_MIME
        assert detect_content_type(path.read_bytes()) == expected, path.name


def test_pdfs_have_text_layer_with_clauses_and_page_footer(generated: list[Path]) -> None:
    for path in (p for p in generated if p.suffix == ".pdf"):
        pages = PypdfTextReader().read(path.read_bytes()).page_texts
        text = "\n".join(pages.values())
        assert len(pages) >= 10, path.name
        for expected in ("CLÁUSULA 1 – OBJETO", "CLÁUSULA 9 – EXCLUSÕES", "Processo SUSEP"):
            assert expected in text, (path.name, expected)
        assert f"Página 1 de {len(pages)}" in text


def test_docx_have_headings_tables_header_and_footer(generated: list[Path]) -> None:
    for path in (p for p in generated if p.suffix == ".docx"):
        pages = PythonDocxTextReader().read(path.read_bytes()).page_texts
        text = "\n".join(pages.values())
        assert "## CLÁUSULA 1 – OBJETO" in text, path.name
        assert "[Tabela]" in text and "[Cabeçalho]" in text and "[Rodapé]" in text


def test_policies_differ_where_the_comparison_needs_it(generated: list[Path]) -> None:
    texts = {
        p.stem[:2]: "\n".join(PythonDocxTextReader().read(p.read_bytes()).page_texts.values())
        for p in generated
        if p.suffix == ".docx"
    }
    assert "Retroatividade ilimitada" in texts["01"] and "Retroatividade ilimitada" in texts["05"]
    assert "Retroatividade datada" in texts["02"] and "Retroatividade datada" in texts["04"]
    assert "Período de retroatividade" in texts["03"]
    assert "run-off" in texts["05"] and "run-off" in texts["04"]
    assert "de, baseada em, atribuível a" in texts["02"]  # exclusão ampla de poluição
    assert len({text for text in texts.values()}) == 5


@pytest.mark.parametrize("suffix", [".pdf", ".docx"])
def test_upload_smoke_with_fakes(
    generated: list[Path], tmp_path: Path, suffix: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # O stub de PDF dos fakes não lê PDFs reais; aqui o leitor nativo confirma a camada de texto.
    monkeypatch.setattr(fakes, "FakePdfReader", PypdfTextReader)
    path = next(p for p in generated if p.suffix == suffix)
    mime = PDF_MIME if suffix == ".pdf" else DOCX_MIME
    with TestClient(fakes.build_test_app(tmp_path), headers=fakes.auth_headers()) as client:
        response = client.post(
            "/api/v1/policies",
            data={"document_types": ["POLICY"], "insurer": "Seguradora Fictícia"},
            files=[("files", (path.name, path.read_bytes(), mime))],
        )
        assert response.status_code == 202, response.text
        url = f"/api/v1/policies/{response.json()['policy_id']}"
        deadline = time.monotonic() + 10
        body = client.get(url).json()
        while (
            body["status"] not in {"READY", "ATTENTION", "FAILED"} and time.monotonic() < deadline
        ):
            time.sleep(0.05)
            body = client.get(url).json()
        assert body["status"] in {"READY", "ATTENTION"}, body
        assert body["documents"][0]["status"] == "COMPLETED"
