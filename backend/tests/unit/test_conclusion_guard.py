"""Deterministic check of the AI executive conclusion (P-EXECUTIVE-001)."""

import json

import pytest
from app.domain.services.conclusion_guard import declares_single_winner, is_grounded_conclusion
from app.domain.value_objects import DecisionMode

FACTS = json.dumps(
    {
        "decision_mode": "CONDITIONED",
        "score_aderencia_apolice_01": "82,5%",
        "score_aderencia_apolice_02": "79,0%",
        "maior_score": "A",
        "conclusao_deterministica": "A Apólice 01 tem o maior score de aderência (82,5%).",
        "vantagens_apolice_01": ["Limite máximo de garantia: R$ 10.000.000,00"],
        "vantagens_apolice_02": ["Prazo complementar: 36 meses"],
        "pontos_de_atencao": [],
    },
    ensure_ascii=False,
)

TECHNICAL = DecisionMode.TECHNICAL
CONDITIONED = DecisionMode.CONDITIONED


@pytest.mark.parametrize(
    "conclusion",
    [
        "A Apólice 01 tem 82,5% de aderência e a Apólice 02, 79%.",
        "A Apólice 01 oferece limite de R$ 10.000.000,00.",
        "A Apólice 01 oferece limite de R$ 10 milhões.",
        "A Apólice 01 oferece limite de 10 mi.",
        "A Apólice 02 tem prazo complementar de 36 meses.",
        "A Apólice 01 tem o maior score, mas as duas apólices seguem como alternativas "
        "conforme o perfil de risco do segurado.",
        "As Apólices 01 e 02 seguem como alternativas conforme o perfil de risco.",
        "Entre a Apólice 01 e a 02 a diferença de score é pequena.",
        "A melhor opção depende do perfil de risco; considere as duas apólices.",
    ],
)
def test_conclusion_grounded_in_the_facts_is_accepted(conclusion: str) -> None:
    assert is_grounded_conclusion(conclusion, FACTS, CONDITIONED)


@pytest.mark.parametrize(
    "conclusion",
    [
        "A Apólice 01 tem 90% de aderência.",  # invented percentage
        "A Apólice 01 oferece limite de R$ 5.000.000,00.",  # invented money
        "A Apólice 01 oferece limite de R$ 20 milhões.",
        "A Apólice 01 oferece limite de 1,5 mi.",
        "A Apólice 02 tem prazo complementar de 60 meses.",  # invented count
        "A Apólice 01 vence em 4 dos 7 conceitos críticos.",
        "A Apólice 01 e 2 milhões a mais de limite.",  # a number disguised as a label
        "As Apólices 01 e 2% de franquia.",
        "",
    ],
)
def test_conclusion_with_invented_numbers_is_rejected(conclusion: str) -> None:
    assert not is_grounded_conclusion(conclusion, FACTS, TECHNICAL)


@pytest.mark.parametrize(
    "conclusion",
    [
        "A Apólice 01 é a melhor opção para o segurado.",
        "A Apólice 02 é a vencedora.",
        "Recomenda-se a Apólice 01.",
        "Recomendamos a Apólice 02 pelo limite maior.",
        "A Apólice 01 é superior à Apólice 02.",
        "O segurado deve optar pela Apólice 01.",
        "A Apólice 01 é mais vantajosa do que a Apólice 02.",
        "A melhor opção é a Apólice 02.",
        "Sugerimos a Apólice 01 ao segurado.",
        "Indica-se a Apólice 02.",
        "A Apólice 01 deve ser preferida.",
    ],
)
def test_single_winner_is_rejected_only_in_a_conditioned_decision(conclusion: str) -> None:
    assert declares_single_winner(conclusion)
    assert not is_grounded_conclusion(conclusion, FACTS, CONDITIONED)
    assert is_grounded_conclusion(conclusion, FACTS, TECHNICAL)


def test_policy_labels_are_not_counted_as_facts() -> None:
    facts = json.dumps({"score_aderencia_apolice_01": "70,0%"}, ensure_ascii=False)

    assert is_grounded_conclusion("A Apólice 02 empata com a Apólice 01.", facts, TECHNICAL)
