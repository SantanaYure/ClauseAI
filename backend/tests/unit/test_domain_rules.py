from app.application.use_cases.policies import detect_content_type
from app.domain.entities import AssessmentDecision, ConceptAssessment, Policy
from app.domain.services.guardrails import enforce_contract_rule, sanitize_decision
from app.domain.services.policy_aggregation import merge_occurrences
from app.domain.services.scoring import (
    ScoringParameters,
    build_items,
    build_pairs,
    build_profiles,
    build_summary,
)
from app.domain.services.text import resolve_concept
from app.domain.value_objects import (
    ContractStatus,
    DecisionMode,
    DocumentType,
    RiskProfile,
    Verdict,
)
from app.infrastructure.knowledge_base import JsonConceptCatalog

from tests.fakes import occurrence

KB = JsonConceptCatalog().load()


def policy(policy_id: str, occurrences: list) -> Policy:  # type: ignore[type-arg]
    return Policy(
        id=policy_id, insurer=policy_id, name=policy_id, occurrences=occurrences, correlation_id="c"
    )


def test_knowledge_base_matches_the_weight_matrix() -> None:
    assert len(KB.concepts) == 44
    assert len(KB.weighted) == 31
    assert sum(c.weight or 0 for c in KB.weighted) == 207
    assert KB.get("DO-005").related == ["DO-006"]  # type: ignore[union-attr]
    assert KB.get("DO-036").importance == "CRITICAL"  # type: ignore[union-attr]


def test_general_conditions_never_prove_contracting() -> None:
    found = occurrence("DO-002", ContractStatus.CONTRACTED)
    result = enforce_contract_rule(found, DocumentType.GENERAL_CONDITIONS)
    assert result.contract_status == ContractStatus.NOT_PROVEN
    assert enforce_contract_rule(found, DocumentType.SPECIFICATION).contract_status == "CONTRACTED"


def test_ai_decisions_are_clamped_to_scales_and_evidence() -> None:
    mention = sanitize_decision(
        AssessmentDecision(base_result=1.0, adjustment_factor=0.93), ContractStatus.NOT_PROVEN
    )
    assert (mention.base_result, mention.adjustment_factor) == (0.25, 0.9)
    assert mention.justification  # reductions always carry a justification
    excluded = sanitize_decision(
        AssessmentDecision(base_result=1.0, adjustment_factor=1.0), ContractStatus.EXCLUDED
    )
    assert (excluded.base_result, excluded.adjustment_factor) == (0.0, 0.0)


def test_contracted_and_excluded_in_different_documents_become_divergent() -> None:
    merged = merge_occurrences(
        [
            occurrence("DO-042", ContractStatus.CONTRACTED, "spec"),
            occurrence("DO-042", ContractStatus.EXCLUDED, "cg"),
        ]
    )
    assert merged[0].contract_status == ContractStatus.DIVERGENT
    assert len(merged[0].evidence) == 2


def _assess(pairs: list, decisions: dict[str, tuple[float, float]]) -> dict[str, ConceptAssessment]:  # type: ignore[type-arg]
    result = {}
    for pair in pairs:
        base_a, base_b = decisions.get(pair.concept.id, (1.0, 1.0))
        result[pair.concept.id] = ConceptAssessment(
            concept_id=pair.concept.id,
            a=AssessmentDecision(base_result=base_a, adjustment_factor=1.0, justification="x"),
            b=AssessmentDecision(base_result=base_b, adjustment_factor=1.0, justification="x"),
            main_difference="",
        )
    return result


def test_scoring_rules() -> None:
    contracted = {c.id: occurrence(c.id, ContractStatus.CONTRACTED) for c in KB.weighted}
    a_occurrences = dict(contracted)
    a_occurrences["DO-036"] = occurrence(
        "DO-036", ContractStatus.CONTRACTED, amount="R$ 50.000.000,00", limit_basis="AGGREGATE"
    )
    a_occurrences["DO-042"] = occurrence("DO-042", ContractStatus.EXCLUDED)
    b_occurrences = dict(contracted)
    b_occurrences["DO-036"] = occurrence(
        "DO-036",
        ContractStatus.CONTRACTED,
        amount="R$ 10.000.000,00",
        limit_basis="PER_CLAIM_AND_AGGREGATE",
    )
    del b_occurrences["DO-040"]

    pairs = build_pairs(
        KB, policy("a", list(a_occurrences.values())), policy("b", list(b_occurrences.values()))
    )
    params = ScoringParameters()
    items = {i.concept_id: i for i in build_items(pairs, _assess(pairs, {}), params)}

    assert items["DO-042"].a.points == 0  # express exclusion scores zero
    assert items["DO-036"].verdict == Verdict.INCONCLUSIVE  # different limit bases
    assert items["DO-040"].verdict == Verdict.FAVORS_A  # contracted vs not found
    assert items["DO-040"].guidance

    profiles = build_profiles(list(items.values()), params)
    base = next(p for p in profiles if p.profile == RiskProfile.BASE)
    financial = next(p for p in profiles if p.profile == RiskProfile.FINANCIAL)
    assert base.a.max == 207
    assert financial.a.max == 207 + 4 * 10 * 0.5
    summary = build_summary(list(items.values()), base, params)
    assert summary.decision_mode == DecisionMode.CONDITIONED  # critical concept inconclusive
    assert summary.score_vs_qualitative  # raw LMG favors A while the score favors B


def test_concept_resolution_by_variants() -> None:
    assert resolve_concept("Quais apólices cobrem multas?", KB.concepts).id == "DO-015"  # type: ignore[union-attr]
    assert resolve_concept("segurado contra segurado", KB.concepts).id == "DO-034"  # type: ignore[union-attr]
    assert resolve_concept("Qual é o LMG?", KB.concepts).id == "DO-036"  # type: ignore[union-attr]
    assert resolve_concept("previsão do tempo", KB.concepts) is None


def test_content_type_is_detected_by_signature() -> None:
    assert detect_content_type(b"%PDF-1.7 ...") == "application/pdf"
    assert detect_content_type(b"\x89PNG\r\n\x1a\n....") == "image/png"
    assert detect_content_type(b"\xff\xd8\xff\xe0...") == "image/jpeg"
    assert detect_content_type(b"PK\x03\x04 planilha") is None
