"""Native PDF text reading (ADR-019)."""

import io

from pypdf import PdfReader
from pypdf.errors import DependencyError, PdfReadError

from app.domain.interfaces.ports import PdfText


class PypdfTextReader:
    """Extracts the text layer per page (1-based).

    Flags a PDF that needs a password (`encrypted`) or cannot be parsed
    (`unreadable`) instead of pretending it is a scanned document.
    """

    def read(self, data: bytes) -> PdfText:
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted and not reader.decrypt(""):
                return PdfText(page_count=0, page_texts={}, encrypted=True)
            texts = {
                index: (page.extract_text() or "").strip()
                for index, page in enumerate(reader.pages, start=1)
            }
            return PdfText(page_count=len(reader.pages), page_texts=texts)
        except DependencyError:  # e.g. AES encryption without the optional decryptor
            return PdfText(page_count=0, page_texts={}, encrypted=True)
        except (PdfReadError, ValueError, KeyError, TypeError, RecursionError):
            return PdfText(page_count=0, page_texts={}, unreadable=True)


__all__ = ["PypdfTextReader"]
