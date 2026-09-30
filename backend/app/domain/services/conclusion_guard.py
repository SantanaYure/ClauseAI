"""Deterministic check of the AI-written executive conclusion (P-EXECUTIVE-001, SPEC-009).

The model may only rephrase the facts it received. A conclusion is rejected when it
brings a percentage, an amount of money or any other number that is not in the facts,
or, in a conditioned decision, when it names a single policy as the winner.
"""

import re
from decimal import Decimal, InvalidOperation

from app.domain.services.text import normalize_text
from app.domain.value_objects import DecisionMode

_MULTIPLIERS = {
    "mil": Decimal(1_000),
    "mi": Decimal(1_000_000),
    "milhao": Decimal(1_000_000),
    "milhoes": Decimal(1_000_000),
    "bi": Decimal(1_000_000_000),
    "bilhao": Decimal(1_000_000_000),
    "bilhoes": Decimal(1_000_000_000),
}

# Works on normalized text (lowercase, no accents). Groups: number, multiplier, percent sign.
_QUANTITY = re.compile(
    r"(?<![\w.,])(\d+(?:[.,]\d+)*)"
    r"(?:\s?(" + "|".join(sorted(_MULTIPLIERS, key=len, reverse=True)) + r")\b)?"
    r"(\s?%)?"
)
# "Apólice 01" / "Apólice 02" are labels, not facts, also when joined:
# "Apólices 01 e 02", "Apólice 01 e a 02", "Apólice 01 ou a Apólice 02".
_POLICY_LABEL = re.compile(
    r"\bapolices?\s+0?[12]"
    r"(?:\s+(?:e|ou|x|vs\.?)\s+(?:a\s+)?(?:apolice\s+)?0?[12]\b(?![.,]?\d|\s?%|\s+(?:mil|mi|bi)))?"
    r"\b"
)

_POLICY = r"(?:a\s+)?apolice\s+(?:0?[12]|[ab])\b"
_SINGLE_WINNER = [
    re.compile(p)
    for p in (
        r"\b(?:vencedora|ganhadora|vence|ganha)\b",
        # "a melhor opção é a Apólice 01", but not "a melhor opção depende do perfil".
        r"\bmelhor\s+(?:opcao|escolha|alternativa|apolice)\s+(?:e|seria|sera)\s+"
        r"(?:a\s+)?(?:apolice\s+)?(?:0?[12]|[ab])\b",
        _POLICY + r"\s+(?:e|seria|sera|deve\s+ser)\s+(?:a\s+)?(?:melhor|mais\s+(?:indicada|"
        r"recomendada|vantajosa|adequada)|superior|preferivel|preferida|recomendada|"
        r"a\s+escolha)\b",
        r"\b(?:melhor|superior|mais\s+vantajosa)\s+(?:do\s+)?que\s+" + _POLICY,
        r"\b(?:recomend|indic|suger|sugir|aconselh)\w*(?:-se)?\s+" + _POLICY,
        r"\b(?:escolh|contrat|opt)\w*\s+(?:pela|a)\s+apolice\s+(?:0?[12]|[ab])\b",
    )
]


def _to_decimal(number: str) -> Decimal | None:
    """Brazilian notation: '1.000.000,00' and '1,5' are both understood."""

    if "," in number:
        number = number.replace(".", "").replace(",", ".")
    elif "." in number and all(len(group) == 3 for group in number.split(".")[1:]):
        number = number.replace(".", "")
    try:
        return Decimal(number)
    except InvalidOperation:
        return None


def _quantities(text: str) -> tuple[set[Decimal], set[Decimal]]:
    """Plain values (money included, multipliers applied) and percentages found in `text`."""

    values: set[Decimal] = set()
    percents: set[Decimal] = set()
    for number, multiplier, percent in _QUANTITY.findall(_POLICY_LABEL.sub(" ", text)):
        value = _to_decimal(number)
        if value is None:
            continue
        if percent:
            percents.add(value.normalize())
        else:
            values.add((value * _MULTIPLIERS.get(multiplier, Decimal(1))).normalize())
    return values, percents


def declares_single_winner(text: str) -> bool:
    normalized = normalize_text(text)
    return any(pattern.search(normalized) for pattern in _SINGLE_WINNER)


def is_grounded_conclusion(conclusion: str, facts_text: str, decision_mode: DecisionMode) -> bool:
    """True when the conclusion keeps to the facts; False means use the deterministic text."""

    if not conclusion.strip():
        return False
    fact_values, fact_percents = _quantities(normalize_text(facts_text))
    used_values, used_percents = _quantities(normalize_text(conclusion))
    if not used_percents <= fact_percents:
        return False
    if not used_values <= fact_values | fact_percents:
        return False
    return not (decision_mode == DecisionMode.CONDITIONED and declares_single_winner(conclusion))
