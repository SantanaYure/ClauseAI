"""Reads a DOCX in document order into stable logical pages.

Evidence origin: DOCX has no fixed pages, so a logical page (1-based, like a PDF
page) starts at an explicit page break, at a section break that begins a new
page, or when the current block reaches `MAX_CHARS_PER_PAGE`. The split happens
only between paragraphs or tables, so the numbering is deterministic and a quote
never straddles two pages.

Known limits: automatic list/clause numbers, footnotes and text boxes are not
part of the paragraph text stored in the file and are not extracted.
"""

import io
import re
import zipfile
from collections.abc import Iterator

from docx import Document as open_document
from docx.document import Document
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.section import Section, _Footer, _Header
from docx.table import Table, _Cell
from docx.text.hyperlink import Hyperlink
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from lxml.etree import XMLSyntaxError  # type: ignore[import-untyped]

from app.domain.interfaces.ports import DocumentUnreadableError, DocxText

MAX_CHARS_PER_PAGE = 3500
_HEADING = re.compile(r"^Heading (\d)$")


class _Pages:
    """Accumulates blocks and closes a logical page on a break or size cap."""

    def __init__(self, max_chars: int) -> None:
        self._max_chars = max_chars
        self._pages: list[list[str]] = [[]]
        self._chars = 0

    def add(self, text: str) -> None:
        if not text:
            return
        if self._chars and self._chars + len(text) > self._max_chars:
            self.break_page()
        self._pages[-1].append(text)
        self._chars += len(text)

    def break_page(self) -> None:
        if self._pages[-1]:  # consecutive breaks never create empty pages
            self._pages.append([])
            self._chars = 0

    def result(self) -> dict[int, str]:
        blocks = (page for page in self._pages if page)
        return {number: "\n".join(page) for number, page in enumerate(blocks, start=1)}


def _is_page_break(run: Run) -> bool:
    """Explicit break only: `Run.contains_page_break` reports Word's rendered guess."""

    return bool(run._r.xpath('./w:br[@w:type="page"]'))


def _has_page_break(paragraph: Paragraph) -> bool:
    return any(_is_page_break(run) for run in paragraph.runs)


def _list_depth(paragraph: Paragraph) -> int | None:
    properties = paragraph._p.pPr
    if properties is not None and properties.numPr is not None:
        levels = properties.xpath("./w:numPr/w:ilvl/@w:val")
        return int(levels[0]) if levels else 0
    style = paragraph.style
    return 0 if style is not None and (style.name or "").startswith("List") else None


def _paragraph_text(paragraph: Paragraph) -> str:
    return _format(paragraph, paragraph.text)


def _format(paragraph: Paragraph, raw_text: str) -> str:
    """Render `raw_text` with the heading or list marker of its paragraph."""

    text = raw_text.strip()
    if not text:
        return ""
    style = (paragraph.style.name if paragraph.style is not None else "") or ""
    if style == "Title":
        return f"# {text}"
    heading = _HEADING.match(style)
    if heading:
        return f"{'#' * int(heading.group(1))} {text}"
    depth = _list_depth(paragraph)
    return f"{'  ' * depth}- {text}" if depth is not None else text


def _cell_text(cell: _Cell) -> str:
    parts = [p.text.strip() for p in cell.paragraphs if p.text.strip()]
    parts.extend(_table_inline(nested) for nested in cell.tables)
    return " / ".join(part for part in parts if part)


def _table_rows(table: Table) -> Iterator[str]:
    seen: set[object] = set()  # merged cells repeat: keep them at their first column
    for row_number, row in enumerate(table.rows, start=1):
        cells: list[str] = []
        for column, cell in enumerate(row.cells, start=1):
            if cell._tc in seen:
                continue
            seen.add(cell._tc)
            text = _cell_text(cell)
            if text:
                cells.append(f"[Coluna {column}] {text}")
        if cells:
            yield f"Linha {row_number}: " + " | ".join(cells)


def _table_inline(table: Table) -> str:
    return " ; ".join(_table_rows(table))


def _table_text(table: Table) -> str:
    rows = list(_table_rows(table))
    return "[Tabela]\n" + "\n".join(rows) if rows else ""


def _header_footer_text(part: _Header | _Footer) -> str:
    if part.is_linked_to_previous:
        return ""  # inherits the previous section's text, already extracted
    lines = [_paragraph_text(p) for p in part.paragraphs]
    lines.extend(_table_text(t) for t in part.tables)
    return "\n".join(line for line in lines if line)


def _section_parts(section: Section, label: str, attribute: str) -> list[str]:
    parts = [getattr(section, attribute)]
    if section.different_first_page_header_footer:
        parts.append(getattr(section, f"first_page_{attribute}"))
    texts = dict.fromkeys(_header_footer_text(part) for part in parts)
    return [f"[{label}] {text}" for text in texts if text]


class PythonDocxTextReader:
    def __init__(self, max_chars_per_page: int = MAX_CHARS_PER_PAGE) -> None:
        self._max_chars = max_chars_per_page

    def read(self, data: bytes) -> DocxText:
        try:
            document = open_document(io.BytesIO(data))
            return DocxText(page_texts=self._paginate(document))
        except (zipfile.BadZipFile, XMLSyntaxError, KeyError, ValueError, AttributeError) as exc:
            raise DocumentUnreadableError("DOCX could not be parsed") from exc

    def _paginate(self, document: Document) -> dict[int, str]:
        sections = list(document.sections)
        pages = _Pages(self._max_chars)
        section_index = 0
        for header in _section_parts(sections[0], "Cabeçalho", "header"):
            pages.add(header)

        for child in document.element.body.iterchildren():
            if child.tag == qn("w:tbl"):
                pages.add(_table_text(Table(child, document)))
            elif child.tag == qn("w:p"):
                paragraph = Paragraph(child, document)
                properties = paragraph._p.pPr
                if properties is not None and properties.pageBreakBefore_val:
                    pages.break_page()
                if _has_page_break(paragraph):
                    self._add_split_paragraph(pages, paragraph)
                else:
                    pages.add(_paragraph_text(paragraph))
                if properties is not None and properties.sectPr is not None:
                    section_index = self._close_section(pages, sections, section_index)

        for footer in _section_parts(sections[section_index], "Rodapé", "footer"):
            pages.add(footer)
        return pages.result()

    @staticmethod
    def _add_split_paragraph(pages: _Pages, paragraph: Paragraph) -> None:
        """Keep the text before and after an in-paragraph page break on their own pages."""

        buffer: list[str] = []

        def flush() -> None:
            pages.add(_format(paragraph, "".join(buffer)))
            buffer.clear()

        for item in paragraph.iter_inner_content():
            buffer.append(item.text)
            if not isinstance(item, Hyperlink) and _is_page_break(item):
                flush()
                pages.break_page()
        flush()

    @staticmethod
    def _close_section(pages: _Pages, all_sections: list[Section], index: int) -> int:
        for footer in _section_parts(all_sections[index], "Rodapé", "footer"):
            pages.add(footer)
        following = index + 1
        if following >= len(all_sections):
            return index
        if all_sections[following].start_type != WD_SECTION.CONTINUOUS:
            pages.break_page()
        for header in _section_parts(all_sections[following], "Cabeçalho", "header"):
            pages.add(header)
        return following
