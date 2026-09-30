"""Gera as apólices D&O fictícias de `Policy/` (PDF e DOCX com o mesmo conteúdo).

Uso, a partir de `backend/` (requer o extra opcional `samples`):

    pip install -e ".[dev,samples]"
    python scripts/generate_sample_policies.py [--output-dir ../Policy] [--only 03]

Todas as empresas, números de apólice, processos SUSEP e pessoas são fictícios. A geração é
determinística: rodar duas vezes produz arquivos com o mesmo conteúdo.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sample_policies.builder import build_document  # noqa: E402
from sample_policies.catalog import SPECS  # noqa: E402
from sample_policies.model import Spec  # noqa: E402
from sample_policies.render_docx import render_docx  # noqa: E402
from sample_policies.render_pdf import render_pdf  # noqa: E402

DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "Policy"


def generate(output_dir: Path, only: str | None = None) -> list[Path]:
    """Escreve PDF e DOCX de cada apólice e devolve os caminhos gerados."""

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    specs: Sequence[Spec] = [s for s in SPECS if only is None or s.stem.startswith(only)]
    for spec in specs:
        blocks = build_document(spec)
        pdf = output_dir / f"{spec.stem}.pdf"
        docx = output_dir / f"{spec.stem}.docx"
        render_pdf(spec, blocks, pdf)
        render_docx(spec, blocks, docx)
        written += [pdf, docx]
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])  # type: ignore[union-attr]
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--only", help="Prefixo do arquivo (ex.: 01) para gerar uma só apólice.")
    arguments = parser.parse_args()
    for path in generate(arguments.output_dir, arguments.only):
        print(path)


if __name__ == "__main__":
    main()
