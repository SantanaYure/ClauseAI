"""Content-based file type detection for uploads (SPEC-001).

The declared header and the extension are never trusted to accept a file. The
extension is used only to choose a clearer error message for broken Office files.
"""

import io
import zipfile
from enum import StrEnum

PDF_MIME = "application/pdf"
PNG_MIME = "image/png"
JPEG_MIME = "image/jpeg"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

_SIGNATURES = {
    b"%PDF": PDF_MIME,
    b"\x89PNG\r\n\x1a\n": PNG_MIME,
    b"\xff\xd8\xff": JPEG_MIME,
}
_ZIP_SIGNATURE = b"PK\x03\x04"
# Password-protected Office files (and legacy .doc) are OLE containers, not zips.
_OLE_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

_CONTENT_TYPES_PART = "[Content_Types].xml"
_DOCX_MAIN_PART = "word/document.xml"
# Excludes macro-enabled (.docm) and template (.dotx) main parts on purpose.
_DOCX_MAIN_CONTENT_TYPE = (
    b"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
)
_MAX_CONTENT_TYPES_BYTES = 1024 * 1024

FILE_EXTENSIONS = {PDF_MIME: "pdf", PNG_MIME: "png", JPEG_MIME: "jpg", DOCX_MIME: "docx"}

# Compressed DOCX text and XML shrink a lot; beyond this ratio it is a zip bomb.
DOCX_MAX_EXPANSION_RATIO = 20


class OfficeProblem(StrEnum):
    PROTECTED = "PROTECTED"
    CORRUPTED = "CORRUPTED"


def _open_zip(data: bytes) -> zipfile.ZipFile | None:
    try:
        return zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return None


def _is_docx(archive: zipfile.ZipFile) -> bool:
    names = set(archive.namelist())
    if _CONTENT_TYPES_PART not in names or _DOCX_MAIN_PART not in names:
        return False
    if archive.getinfo(_CONTENT_TYPES_PART).file_size > _MAX_CONTENT_TYPES_BYTES:
        return False
    try:
        declared = archive.read(_CONTENT_TYPES_PART)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError):
        return False
    return _DOCX_MAIN_CONTENT_TYPE in declared


def detect_content_type(data: bytes) -> str | None:
    """Detect the MIME type by content, not by the declared header (SPEC-001)."""

    head = data[:16].lstrip()
    for signature, mime in _SIGNATURES.items():
        if head.startswith(signature):
            return mime
    if data.startswith(_ZIP_SIGNATURE):
        archive = _open_zip(data)
        if archive is not None:
            with archive:
                return DOCX_MIME if _is_docx(archive) else None
    return None


def diagnose_office_problem(data: bytes, filename: str) -> OfficeProblem | None:
    """Explain why an undetected file is a protected or corrupted DOCX, when it is."""

    claims_docx = filename.lower().endswith((".docx", ".doc"))
    if data.startswith(_OLE_SIGNATURE):
        return OfficeProblem.PROTECTED if claims_docx else None
    if not data.startswith(_ZIP_SIGNATURE):
        return None
    archive = _open_zip(data)
    if archive is None:
        return OfficeProblem.CORRUPTED if claims_docx else None
    with archive:
        if any(info.flag_bits & 0x1 for info in archive.infolist()):
            return OfficeProblem.PROTECTED
        if _CONTENT_TYPES_PART in archive.namelist() and _DOCX_MAIN_PART not in archive.namelist():
            return OfficeProblem.CORRUPTED if claims_docx else None
    return None


def docx_expanded_size(data: bytes) -> int:
    """Total uncompressed size of the archive entries (0 when it is not a readable zip)."""

    archive = _open_zip(data)
    if archive is None:
        return 0
    with archive:
        return sum(info.file_size for info in archive.infolist())
