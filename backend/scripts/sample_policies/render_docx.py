"""Renderiza os blocos em DOCX com estilos de título, tabelas reais, cabeçalho e rodapé."""

import io
import zipfile
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

from .model import Block, Spec
from .model import Table as TableModel

FIXED_DATE = datetime(2026, 9, 29, 12, 0, 0)
ACCENT = RGBColor(0x3B, 0x4A, 0x5A)
CONTENT_WIDTH_CM = 17.0


def _field(paragraph: Paragraph, instruction: str) -> None:
    """Insere um campo (PAGE, NUMPAGES) com um resultado provisório."""

    run = paragraph.add_run()
    for kind, text in (("begin", None), (None, instruction), ("separate", None), (None, "1")):
        if kind:
            element = OxmlElement("w:fldChar")
            element.set(qn("w:fldCharType"), kind)
        elif text == instruction:
            element = OxmlElement("w:instrText")
            element.set(qn("xml:space"), "preserve")
            element.text = f" {instruction} "
        else:
            element = OxmlElement("w:t")
            element.text = text
        run._r.append(element)
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(end)


def _shade(cell: object, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()  # type: ignore[attr-defined]
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:fill"), fill)
    properties.append(shading)


def _setup_styles(document: DocxDocument) -> None:
    normal = document.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(9.5)
    normal.paragraph_format.space_after = Pt(4)
    for name, size in (("Title", 17), ("Heading 1", 14), ("Heading 2", 11)):
        style = document.styles[name]
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = ACCENT
    document.styles["Heading 2"].paragraph_format.space_before = Pt(12)


def _setup_page(document: DocxDocument, spec: Spec) -> None:
    section = document.sections[0]
    section.page_width, section.page_height = Cm(21.0), Cm(29.7)
    section.left_margin = section.right_margin = Cm(2.0)
    section.top_margin, section.bottom_margin = Cm(2.4), Cm(2.2)
    header = section.header.paragraphs[0]
    header.text = f"{spec.insurer.upper()} · Seguro D&O · Apólice nº {spec.apolice}"
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run(f"{spec.insurer} · Apólice nº {spec.apolice} · Documento fictício · Página ")
    _field(footer, "PAGE")
    footer.add_run(" de ")
    _field(footer, "NUMPAGES")
    for paragraph in (header, footer):
        for run in paragraph.runs:
            run.font.size = Pt(8)


def _add_table(document: DocxDocument, model: TableModel) -> None:
    if model.caption:
        caption = document.add_paragraph()
        caption.paragraph_format.keep_with_next = True
        caption.paragraph_format.space_before = Pt(8)
        run = caption.add_run(model.caption)
        run.bold = True
        run.font.color.rgb = ACCENT
    table = document.add_table(rows=1, cols=len(model.header))
    table.style = "Table Grid"
    table.autofit = False
    widths = [Cm(CONTENT_WIDTH_CM * share) for share in model.widths] if model.widths else []
    for index, title in enumerate(model.header):
        cell = table.rows[0].cells[index]
        cell.text = ""
        cell.paragraphs[0].add_run(title).bold = True
        _shade(cell, "E6EAEE")
    header_row = table.rows[0]._tr.get_or_add_trPr()
    header_row.append(OxmlElement("w:tblHeader"))
    for values in model.rows:
        row = table.add_row()
        cant_split = OxmlElement("w:cantSplit")
        row._tr.get_or_add_trPr().append(cant_split)
        for index, value in enumerate(values):
            row.cells[index].text = value
    for row in table.rows:
        for index, cell in enumerate(row.cells):
            if widths:
                cell.width = widths[index]
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(1)
                for run in paragraph.runs:
                    run.font.size = Pt(8.5)
    document.add_paragraph().paragraph_format.space_after = Pt(2)


def _add_block(document: DocxDocument, block: Block) -> None:
    kind = block.kind
    if kind == "title":
        document.add_paragraph(block.text, style="Title")
    elif kind in ("h1", "h2", "h3"):
        document.add_heading(block.text, level=int(kind[1]))
    elif kind == "subtitle":
        document.add_paragraph().add_run(block.text).bold = True
    elif kind == "table" and block.table is not None:
        _add_table(document, block.table)
    elif kind == "pagebreak":
        document.add_page_break()
    elif kind == "item":
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.left_indent = Cm(1.1)
        paragraph.paragraph_format.first_line_indent = Cm(-1.1)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        paragraph.add_run(f"{block.number}  ").bold = True
        paragraph.add_run(block.text)
    elif kind == "bullet":
        paragraph = document.add_paragraph(block.text)
        paragraph.paragraph_format.left_indent = Cm(1.6)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif kind == "note":
        run = document.add_paragraph().add_run(block.text)
        run.font.size = Pt(8)
        run.font.color.rgb = ACCENT
    else:
        paragraph = document.add_paragraph(block.text)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def _normalized(data: bytes) -> bytes:
    """Regrava o zip com datas fixas: mesma entrada gera o mesmo arquivo."""

    source = zipfile.ZipFile(io.BytesIO(data))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target:
        for name in source.namelist():
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 29, 12, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(info, source.read(name))
    return out.getvalue()


def _drop_legacy_styles(document: DocxDocument) -> None:
    """Remove a parte `stylesWithEffects` do modelo padrão (legado do Word 2010, 430 KB).

    Ela quase dobra o tamanho descompactado e aproxima o arquivo do limite de expansão
    aceito no upload, sem função para a leitura do texto.
    """

    relationships = document.part.rels
    for rel_id in [i for i, r in relationships.items() if r.reltype.endswith("stylesWithEffects")]:
        relationships.pop(rel_id)


def render_docx(spec: Spec, blocks: list[Block], path: Path) -> None:
    document = Document()
    _drop_legacy_styles(document)
    _setup_styles(document)
    _setup_page(document, spec)
    properties = document.core_properties
    properties.title = f"Apólice D&O {spec.apolice}"
    properties.author = spec.insurer
    properties.subject = "Seguro de Responsabilidade Civil de Administradores e Diretores (D&O)"
    properties.created = properties.modified = FIXED_DATE
    properties.last_modified_by = spec.insurer
    for block in blocks:
        _add_block(document, block)
    stream = io.BytesIO()
    document.save(stream)
    path.write_bytes(_normalized(stream.getvalue()))
