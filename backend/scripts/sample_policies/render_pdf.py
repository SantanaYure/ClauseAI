"""Renderiza os blocos em PDF com camada de texto (reportlab, fontes padrão Type 1)."""

from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .model import Block, Spec
from .model import Table as TableModel

MARGIN = 20 * mm
INK = colors.HexColor("#1f2933")
ACCENT = colors.HexColor("#3b4a5a")
HEAD_BG = colors.HexColor("#e6eaee")
GRID = colors.HexColor("#9aa5b1")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]
    body = ParagraphStyle(
        "Body", parent=base, fontName="Helvetica", fontSize=9.2, leading=12.4,
        textColor=INK, alignment=TA_JUSTIFY, spaceAfter=4,
    )  # fmt: skip
    return {
        "title": ParagraphStyle(
            "Title",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            alignment=0,
            spaceAfter=8,
            textColor=ACCENT,
        ),
        "subtitle": ParagraphStyle(
            "Sub",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            alignment=0,
            spaceAfter=4,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            alignment=0,
            spaceBefore=6,
            spaceAfter=8,
            textColor=ACCENT,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            alignment=0,
            spaceBefore=10,
            spaceAfter=4,
            textColor=ACCENT,
            keepWithNext=1,
        ),
        "p": body,
        "item": ParagraphStyle("Item", parent=body, leftIndent=26, firstLineIndent=-26),
        "bullet": ParagraphStyle("Bullet", parent=body, leftIndent=40, firstLineIndent=-12),
        "note": ParagraphStyle(
            "Note", parent=body, fontSize=8, leading=10.5, textColor=ACCENT, spaceBefore=6
        ),
        "cell": ParagraphStyle(
            "Cell", parent=body, fontSize=8.2, leading=10.4, alignment=0, spaceAfter=0
        ),
        "cellhead": ParagraphStyle(
            "CellHead",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=8.2,
            leading=10.4,
            alignment=0,
            spaceAfter=0,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=body,
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            alignment=0,
            spaceBefore=8,
            spaceAfter=3,
            textColor=ACCENT,
            keepWithNext=1,
        ),
    }


class _NumberedCanvas(Canvas):
    """Canvas que conhece o total de páginas, para o rodapé “Página X de Y”."""

    def __init__(self, *args: Any, footer: str = "", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._footer = footer
        self._saved: list[dict[str, Any]] = []

    def showPage(self) -> None:  # noqa: N802 (nome da API do reportlab)
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self._draw_footer(total)
            super().showPage()
        super().save()

    def _draw_footer(self, total: int) -> None:
        width, _ = A4
        self.setStrokeColor(GRID)
        self.setLineWidth(0.4)
        self.line(MARGIN, 15 * mm, width - MARGIN, 15 * mm)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(INK)
        self.drawString(MARGIN, 10.5 * mm, self._footer)
        self.drawRightString(width - MARGIN, 10.5 * mm, f"Página {self._pageNumber} de {total}")


def _cell(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text), style)


def _table(model: TableModel, styles: dict[str, ParagraphStyle], width: float) -> list[Any]:
    data = [[_cell(h, styles["cellhead"]) for h in model.header]]
    data += [[_cell(v, styles["cell"]) for v in row] for row in model.rows]
    widths = [width * share for share in model.widths] if model.widths else None
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
                ("GRID", (0, 0), (-1, -1), 0.4, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    flow: list[Any] = []
    if model.caption:
        flow.append(Paragraph(escape(model.caption), styles["caption"]))
    flow.append(table)
    flow.append(Spacer(1, 6))
    return flow


def _flowables(blocks: list[Block], width: float) -> list[Any]:
    styles = _styles()
    story: list[Any] = []
    for block in blocks:
        text = escape(block.text)
        if block.kind == "pagebreak":
            story.append(PageBreak())
        elif block.kind == "table" and block.table is not None:
            story.extend(_table(block.table, styles, width))
        elif block.kind == "item":
            story.append(Paragraph(f"<b>{block.number}</b>&nbsp;&nbsp;{text}", styles["item"]))
        elif block.kind in styles:
            story.append(Paragraph(text, styles[block.kind]))
    return story


def render_pdf(spec: Spec, blocks: list[Block], path: Path) -> None:
    footer = (
        f"{spec.insurer} · Apólice nº {spec.apolice} · Documento fictício, sem valor contratual"
    )
    document = BaseDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=22 * mm,
        bottomMargin=20 * mm,
        title=f"Apólice D&O {spec.apolice}",
        author=spec.insurer,
        subject="Seguro de Responsabilidade Civil de Administradores e Diretores (D&O)",
        invariant=True,  # datas e IDs fixos: mesma entrada gera o mesmo arquivo
    )
    frame = Frame(MARGIN, 20 * mm, A4[0] - 2 * MARGIN, A4[1] - 42 * mm, id="body")

    def header(canvas: Canvas, _doc: BaseDocTemplate) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(ACCENT)
        canvas.drawString(MARGIN, A4[1] - 14 * mm, spec.insurer.upper())
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(
            A4[0] - MARGIN, A4[1] - 14 * mm, f"Seguro D&O · Apólice nº {spec.apolice}"
        )
        canvas.setStrokeColor(GRID)
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN, A4[1] - 16 * mm, A4[0] - MARGIN, A4[1] - 16 * mm)
        canvas.restoreState()

    document.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=header)])
    story = _flowables(blocks, frame._width)
    story = [KeepTogether(item) if isinstance(item, list) else item for item in story]
    document.build(story, canvasmaker=lambda *a, **k: _NumberedCanvas(*a, footer=footer, **k))
