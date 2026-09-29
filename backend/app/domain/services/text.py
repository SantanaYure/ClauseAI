"""Text normalization and concept resolution by variants (SPEC-018)."""

import re
import unicodedata

from app.domain.entities import Concept

_STOPWORDS = frozenset(
    {
        "a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "em", "no", "na", "para",
        "por", "com", "que", "qual", "quais", "cobre", "cobertura", "apolice", "apolices",
        "seguradora", "tem", "uma", "um", "sobre", "como",
    }
)  # fmt: skip


def normalize_text(value: str) -> str:
    """Lowercase, strip accents and collapse whitespace."""

    decomposed = unicodedata.normalize("NFD", value)
    without_accents = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", without_accents.lower()).strip()


def significant_words(value: str) -> set[str]:
    words = re.findall(r"[a-z0-9&]+", normalize_text(value))
    return {word for word in words if len(word) >= 3 and word not in _STOPWORDS}


def _score(concept: Concept, question: str) -> float:
    normalized = normalize_text(question)
    question_words = significant_words(question)
    best = 0.0
    for variant in (concept.name, *concept.variants):
        candidate = normalize_text(variant)
        if len(candidate) > 2 and re.search(rf"\b{re.escape(candidate)}\b", normalized):
            best = max(best, 1.0 + len(candidate) / 100)
            continue
        words = significant_words(variant)
        if words:
            overlap = len(words & question_words) / len(words)
            if overlap >= 0.5:
                best = max(best, overlap)
    return best


def resolve_concept(question: str, concepts: list[Concept]) -> Concept | None:
    """Pick the concept whose name or variants best match the question."""

    scored = [(concept, _score(concept, question)) for concept in concepts]
    scored = [item for item in scored if item[1] > 0]
    if not scored:
        return None
    return max(scored, key=lambda item: item[1])[0]
