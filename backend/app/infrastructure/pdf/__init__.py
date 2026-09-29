"""Native PDF text reading (ADR-019)."""

import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.domain.interfaces.ports import PdfText


class PypdfTextReader:
    """Extracts the text layer per page (1-based); empty result on failure."""

    def read(self, data: bytes) -> PdfText:
        try:
            reader = PdfReader(io.BytesIO(data))
            texts = {
                index: (page.extract_text() or "").strip()
                for index, page in enumerate(reader.pages, start=1)
            }
            return PdfText(page_count=len(reader.pages), page_texts=texts)
        except (PdfReadError, ValueError, KeyError):
            return PdfText(page_count=0, page_texts={})


__all__ = ["PypdfTextReader"]
