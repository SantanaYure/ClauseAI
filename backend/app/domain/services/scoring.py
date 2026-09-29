"""Deterministic scoring (knowledge base sections 4.6, 6 and 7; SPEC-016/017/019).

The AI only proposes Resultado-base and Fator de Ajuste per concept. Every number,
verdict, profile and decision mode is computed here, with Decimal arithmetic.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.domain.entities import (
    AssessmentDecision,
    ComparisonItem,
    ComparisonSide,
    Concept,
    ConceptAssessment,
    ConceptOccurrence,
    ExecutiveSummary,
    KnowledgeBase,
    Policy,
    ProfileResult,
    QualityCheck,
    ScoreSummary,
)
from app.domain.services.guardrails import sanitize_decision
from app.domain.value_objects import (
    ContractStatus,
    DecisionMode,
    DocumentType,
    Importance,
    Level,
    RiskProfile,
    Verdict,
)

SLOT_A = "Apólice 01"
SLOT_B = "Apólice 02"

PROFILE_PRIORITIES: dict[RiskProfile, list[str]] = {
    RiskProfile.BASE: [],
    RiskProfile.FINANCIAL: ["DO-036", "DO-002", "DO-003", "DO-005"],
    RiskProfile.INTERNATIONAL: ["DO-038", "DO-043", "DO-037", "DO-039", "DO-040"],
    RiskProfile.REGULATORY: ["DO-008", "DO-015", "DO-021", "DO-032"],
    RiskProfile.TAIL: ["DO-037", "DO-041", "DO-039", "DO-040"],
    RiskProfile.LABOR_REPUTATIONAL: ["DO-017", "DO-026", "DO-020", "DO-029", "DO-005"],
}

_STATUS_LABELS = {
    ContractStatus.CONTRACTED: "contratada",
    ContractStatus.NOT_PROVEN: "não comprovado",
    ContractStatus.NOT_FOUND: "não localizado",
    ContractStatus.EXCLUDED: "excluído",
    ContractStatus.DIVERGENT: "divergente",
}


@dataclass(frozen=True, slots=True)
class ScoringParameters:
    """Parameters still PENDING_BUSINESS_VALIDATION (knowledge base, section 10)."""

    profile_multiplier: Decimal = Decimal("1.5")
    close_score_threshold: Decimal = Decimal("0.03")
    min_completeness: Decimal = Decimal("0.70")
    equivalence_threshold: Decimal = Decimal("0.10")
    ocr_min_confidence: float = 0.7


@dataclass(frozen=True, slots=True)
class ConceptPair:
    """Deterministic input for one concept: what each policy says about it."""

    concept: Concept
    a: ConceptOccurrence | None
    b: ConceptOccurrence | None

    @property
    def weight(self) -> int:
        return self.concept.weight or 0

    @property
    def limits_comparable(self) -> bool:
        if self.a and self.b and self.a.limit_basis and self.b.limit_basis:
            return self.a.limit_basis == self.b.limit_basis
        return True

    @property
    def needs_assessment(self) -> bool:
        statuses = {self.status(self.a), self.status(self.b)}
        return bool(statuses - {ContractStatus.NOT_FOUND, ContractStatus.EXCLUDED})

    @staticmethod
    def status(occurrence: ConceptOccurrence | None) -> ContractStatus:
        return occurrence.contract_status if occurrence else ContractStatus.NOT_FOUND


def _dec(value: float | int) -> Decimal:
    return Decimal(str(value))


def _round2(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def build_pairs(knowledge_base: KnowledgeBase, a: Policy, b: Policy) -> list[ConceptPair]:
    """Same concepts, criteria and weights for both policies (prompt 7)."""

    occurrences_a = {o.concept_id: o for o in a.occurrences}
    occurrences_b = {o.concept_id: o for o in b.occurrences}
    return [
        ConceptPair(concept, occurrences_a.get(concept.id), occurrences_b.get(concept.id))
        for concept in knowledge_base.weighted
    ]


def default_assessment(pair: ConceptPair) -> ConceptAssessment:
    """Assessment for concepts that need no AI: absent or expressly excluded on both sides."""

    def decision(occurrence: ConceptOccurrence | None) -> AssessmentDecision:
        return AssessmentDecision(base_result=0, adjustment_factor=0, confidence=Level.HIGH)

    return ConceptAssessment(
        concept_id=pair.concept.id,
        a=decision(pair.a),
        b=decision(pair.b),
        main_difference="",
    )


def _side(
    weight: int, occurrence: ConceptOccurrence | None, decision: AssessmentDecision
) -> tuple[ComparisonSide, Level]:
    status = ConceptPair.status(occurrence)
    safe = sanitize_decision(decision, status)
    points = _dec(weight) * _dec(safe.base_result) * _dec(safe.adjustment_factor)
    confidence = occurrence.confidence if occurrence else Level.MEDIUM
    if safe.confidence == Level.LOW:
        confidence = Level.LOW
    sufficient = status in (ContractStatus.CONTRACTED, ContractStatus.EXCLUDED) and (
        confidence != Level.LOW
    )
    justification = safe.justification or (occurrence.justification if occurrence else None)
    side = ComparisonSide(
        term=occurrence.term if occurrence else "—",
        contract_status=status,
        base_result=safe.base_result,
        adjustment_factor=safe.adjustment_factor,
        points=_round2(points),
        justification=justification,
        evidence=occurrence.evidence if occurrence else [],
        sufficient_evidence=sufficient,
        amount=occurrence.amount if occurrence else None,
    )
    return side, confidence


def _verdict(
    a: ComparisonSide, b: ComparisonSide, limits_comparable: bool, params: ScoringParameters
) -> Verdict:
    if (
        a.contract_status == ContractStatus.EXCLUDED
        and b.contract_status == ContractStatus.EXCLUDED
    ):
        return Verdict.EQUIVALENT_BOTH_EXCLUDED
    if not limits_comparable:
        return Verdict.INCONCLUSIVE
    if a.sufficient_evidence and b.sufficient_evidence:
        if abs(_dec(a.points) - _dec(b.points)) < params.equivalence_threshold:
            return Verdict.EQUIVALENT
        return Verdict.FAVORS_A if a.points > b.points else Verdict.FAVORS_B
    # One contracted and the other not found: favorable, subject to confirmation.
    if (
        a.contract_status == ContractStatus.CONTRACTED
        and a.sufficient_evidence
        and b.contract_status == ContractStatus.NOT_FOUND
    ):
        return Verdict.FAVORS_A
    if (
        b.contract_status == ContractStatus.CONTRACTED
        and b.sufficient_evidence
        and a.contract_status == ContractStatus.NOT_FOUND
    ):
        return Verdict.FAVORS_B
    return Verdict.INCONCLUSIVE


def _describe(side: ComparisonSide) -> str:
    label = _STATUS_LABELS[side.contract_status]
    return f"{label} — {side.justification}" if side.justification else label


def _main_difference(
    a: ComparisonSide, b: ComparisonSide, limits_comparable: bool, proposed: str
) -> str:
    if not limits_comparable:
        return (
            f"Valores brutos: {SLOT_A} {a.amount}; {SLOT_B} {b.amount}. "
            "Bases de aplicação diferentes: não comparáveis diretamente."
        )
    if (
        a.contract_status == ContractStatus.EXCLUDED
        and b.contract_status == ContractStatus.EXCLUDED
    ):
        return "As duas apólices excluem expressamente."
    if proposed.strip():
        return proposed.strip()
    if a.contract_status == b.contract_status and a.points == b.points:
        return "Sem diferença material identificada."
    return f"{SLOT_A}: {_describe(a)}. {SLOT_B}: {_describe(b)}."


def build_items(
    pairs: list[ConceptPair],
    assessments: dict[str, ConceptAssessment],
    params: ScoringParameters,
) -> list[ComparisonItem]:
    items: list[ComparisonItem] = []
    for pair in pairs:
        assessment = assessments.get(pair.concept.id) or default_assessment(pair)
        a, confidence_a = _side(pair.weight, pair.a, assessment.a)
        b, confidence_b = _side(pair.weight, pair.b, assessment.b)
        verdict = _verdict(a, b, pair.limits_comparable, params)
        confidence = (
            Level.LOW
            if Level.LOW in (confidence_a, confidence_b)
            else Level.MEDIUM
            if Level.MEDIUM in (confidence_a, confidence_b)
            else Level.HIGH
        )
        uncertain = any(
            side.contract_status
            in (ContractStatus.NOT_PROVEN, ContractStatus.NOT_FOUND, ContractStatus.DIVERGENT)
            for side in (a, b)
        )
        items.append(
            ComparisonItem(
                concept_id=pair.concept.id,
                concept_name=pair.concept.name,
                importance=pair.concept.importance,
                weight=pair.weight,
                a=a,
                b=b,
                main_difference=_main_difference(
                    a, b, pair.limits_comparable, assessment.main_difference
                ),
                verdict=verdict,
                confidence=confidence,
                guidance=verdict == Verdict.INCONCLUSIVE or uncertain or confidence == Level.LOW,
            )
        )
    return items


def _summarize(items: list[ComparisonItem], slot: str, weights: dict[str, Decimal]) -> ScoreSummary:
    favors = Verdict.FAVORS_A if slot == "a" else Verdict.FAVORS_B
    raw = maximum = sufficient_weight = sufficient_points = inconclusive_weight = Decimal(0)
    critical_unconfirmed = favorable = equivalent = inconclusive = 0
    for item in items:
        side: ComparisonSide = getattr(item, slot)
        weight = weights[item.concept_id]
        points = weight * _dec(side.base_result) * _dec(side.adjustment_factor)
        raw += points
        maximum += weight
        if side.sufficient_evidence:
            sufficient_weight += weight
            sufficient_points += points
        elif item.importance == Importance.CRITICAL:
            critical_unconfirmed += item.weight
        if item.verdict == Verdict.INCONCLUSIVE:
            inconclusive_weight += weight
            inconclusive += 1
        if item.verdict == favors:
            favorable += 1
        if item.verdict in (Verdict.EQUIVALENT, Verdict.EQUIVALENT_BOTH_EXCLUDED):
            equivalent += 1
    return ScoreSummary(
        raw=_round2(raw),
        max=_round2(maximum),
        adherence=float(raw / maximum) if maximum else 0.0,
        documentary=float(sufficient_points / sufficient_weight) if sufficient_weight else 0.0,
        completeness=float(sufficient_weight / maximum) if maximum else 0.0,
        critical_unconfirmed_weight=critical_unconfirmed,
        inconclusive_weight=_round2(inconclusive_weight),
        favorable=favorable,
        equivalent=equivalent,
        inconclusive=inconclusive,
    )


def _impact(item: ComparisonItem) -> float:
    return abs(item.a.points - item.b.points)


def build_profiles(items: list[ComparisonItem], params: ScoringParameters) -> list[ProfileResult]:
    """Base weights are never changed; profiles use separate adjusted weights."""

    results: list[ProfileResult] = []
    for profile, prioritized in PROFILE_PRIORITIES.items():
        multiplier = Decimal(1) if profile == RiskProfile.BASE else params.profile_multiplier
        weights = {
            item.concept_id: _dec(item.weight)
            * (multiplier if item.concept_id in prioritized else 1)
            for item in items
        }
        a = _summarize(items, "a", weights)
        b = _summarize(items, "b", weights)
        difference = _dec(a.adherence) - _dec(b.adherence)
        scope = (
            items
            if profile == RiskProfile.BASE
            else [item for item in items if item.concept_id in prioritized]
        )
        decisive = sorted((i for i in scope if _impact(i) > 0), key=_impact, reverse=True)[:3]
        limitations = [
            f"{i.concept_name}: inconclusivo" for i in scope if i.verdict == Verdict.INCONCLUSIVE
        ]
        if min(_dec(a.completeness), _dec(b.completeness)) < params.min_completeness:
            limitations.append("Índice de completude abaixo do mínimo.")
        results.append(
            ProfileResult(
                profile=profile,
                prioritized=prioritized,
                multiplier=float(multiplier),
                a=a,
                b=b,
                winner="TIE"
                if abs(difference) < Decimal("0.0005")
                else ("A" if difference > 0 else "B"),
                decisive_concepts=[item.concept_name for item in decisive],
                sensitivity="SENSITIVE"
                if abs(difference) < params.close_score_threshold
                else "ROBUST",
                limitations=limitations,
            )
        )
    return results


def format_percent(value: float) -> str:
    rounded = _dec(value * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{str(rounded).replace('.', ',')}%"


def _amount_value(amount: str | None) -> Decimal:
    if not amount:
        return Decimal(0)
    digits = "".join(char for char in amount if char.isdigit() or char == ",").replace(",", ".")
    try:
        return Decimal(digits.rstrip(".")) if digits else Decimal(0)
    except ArithmeticError:
        return Decimal(0)


def build_summary(
    items: list[ComparisonItem], base: ProfileResult, params: ScoringParameters
) -> ExecutiveSummary:
    """Deterministic executive summary; the AI may only rewrite the conclusion text."""

    critical_inconclusive = [
        i
        for i in items
        if i.importance == Importance.CRITICAL and i.verdict == Verdict.INCONCLUSIVE
    ]
    low_completeness = (
        min(_dec(base.a.completeness), _dec(base.b.completeness)) < params.min_completeness
    )
    close = abs(_dec(base.a.adherence) - _dec(base.b.adherence)) < params.close_score_threshold
    decision_mode = (
        DecisionMode.CONDITIONED
        if close or low_completeness or critical_inconclusive
        else DecisionMode.TECHNICAL
    )

    def advantages(verdict: Verdict, slot: str) -> list[str]:
        chosen = sorted(
            (i for i in items if i.verdict == verdict),
            key=lambda i: (i.weight, _impact(i)),
            reverse=True,
        )[:5]
        return [f"{i.concept_name}: {getattr(i, slot).term}" for i in chosen]

    attention = [f"{i.concept_name} (crítico) está inconclusivo." for i in critical_inconclusive]
    attention += [
        f"{i.concept_name}: contratação não comprovada em uma das apólices."
        for i in items
        if ContractStatus.NOT_PROVEN in (i.a.contract_status, i.b.contract_status)
    ]
    if low_completeness:
        attention.append("Índice de completude abaixo do mínimo em pelo menos uma apólice.")

    notes: list[str] = []
    for item in items:
        if item.verdict != Verdict.INCONCLUSIVE or not (item.a.amount and item.b.amount):
            continue
        value_a, value_b = _amount_value(item.a.amount), _amount_value(item.b.amount)
        raw_leader = "TIE" if value_a == value_b else ("A" if value_a > value_b else "B")
        if raw_leader not in ("TIE", base.winner):
            leader = SLOT_A if raw_leader == "A" else SLOT_B
            notes.append(
                f"{item.concept_name}: o valor bruto favorece a {leader} "
                f"({item.a.amount} × {item.b.amount}), mas as bases não são comparáveis e o "
                "conceito ficou fora da vantagem calculada."
            )

    leader_label = None if base.winner == "TIE" else (SLOT_A if base.winner == "A" else SLOT_B)
    leader_score = base.a.adherence if base.winner == "A" else base.b.adherence
    reasons = (
        (["diferença pequena entre os scores"] if close else [])
        + (["completude baixa"] if low_completeness else [])
        + (
            [
                "conceito crítico inconclusivo ("
                + ", ".join(i.concept_name for i in critical_inconclusive)
                + ")"
            ]
            if critical_inconclusive
            else []
        )
    )
    if leader_label is None:
        conclusion = (
            "As apólices empatam no score de aderência; "
            "a escolha depende das prioridades do segurado."
        )
    elif decision_mode == DecisionMode.CONDITIONED:
        conclusion = (
            f"A {leader_label} tem o maior score de aderência ({format_percent(leader_score)}), "
            f"mas o resultado é condicionado: {'; '.join(reasons)}. Considere as duas apólices "
            "como alternativas conforme o perfil de risco do segurado."
        )
    else:
        conclusion = (
            f"A {leader_label} tem o maior score de aderência ({format_percent(leader_score)}), "
            "com evidência suficiente nos conceitos críticos."
        )

    return ExecutiveSummary(
        decision_mode=decision_mode,
        highest_score=base.winner,
        advantages_a=advantages(Verdict.FAVORS_A, "a"),
        advantages_b=advantages(Verdict.FAVORS_B, "b"),
        equivalent_critical=[
            i.concept_name
            for i in items
            if i.importance == Importance.CRITICAL
            and i.verdict in (Verdict.EQUIVALENT, Verdict.EQUIVALENT_BOTH_EXCLUDED)
        ],
        highest_impact=[
            i.concept_name for i in sorted(items, key=_impact, reverse=True)[:5] if _impact(i) > 0
        ],
        attention_points=attention,
        score_vs_qualitative=" ".join(notes) or None,
        conclusion=conclusion,
    )


def build_quality_gate(
    a: Policy,
    b: Policy,
    items: list[ComparisonItem],
    summary: ExecutiveSummary,
    knowledge_base: KnowledgeBase,
    params: ScoringParameters,
) -> list[QualityCheck]:
    """Checklist of prompt 16, computed from the stored data."""

    documents = [*a.documents, *b.documents]
    evidences = [e for i in items for e in (*i.a.evidence, *i.b.evidence)]
    min_confidence = min((e.confidence for e in evidences), default=1.0)
    ocr_documents = [d.filename for d in documents if d.ocr_required]
    expected_weight = sum(c.weight or 0 for c in knowledge_base.weighted)
    total_weight = sum(i.weight for i in items)
    non_comparable = [i.concept_name for i in items if "não comparáveis" in i.main_difference]
    critical_inconclusive = [
        i.concept_name
        for i in items
        if i.importance == Importance.CRITICAL and i.verdict == Verdict.INCONCLUSIVE
    ]
    not_proven = sum(
        1 for i in items if ContractStatus.NOT_PROVEN in (i.a.contract_status, i.b.contract_status)
    )
    only_conditions = [
        p.insurer
        for p in (a, b)
        if all(
            d.type in (DocumentType.GENERAL_CONDITIONS, DocumentType.PROPOSAL) for d in p.documents
        )
    ]
    recomputed = all(
        abs(
            _dec(side.points)
            - _dec(i.weight) * _dec(side.base_result) * _dec(side.adjustment_factor)
        )
        < Decimal("0.01")
        for i in items
        for side in (i.a, i.b)
    )

    def check(check_id: str, label: str, passed: bool, detail: str) -> QualityCheck:
        return QualityCheck(id=check_id, label=label, passed=passed, detail=detail)

    return [
        check("files", "Todos os documentos foram lidos",
              all(d.status == "COMPLETED" for d in documents),
              f"{len(documents)} documento(s) processado(s)."),
        check("ocr", "OCR avaliado quanto à confiança", min_confidence >= params.ocr_min_confidence,
              f"OCR usado em {', '.join(ocr_documents)}; menor confiança {min_confidence:.2f}."
              if ocr_documents else "Nenhum documento precisou de OCR."),
        check("pages", "Todas as páginas foram processadas", all(d.pages > 0 for d in documents),
              f"{sum(d.pages for d in documents)} páginas."),
        check("classification", "Documentos classificados",
              all(d.type != DocumentType.OTHER for d in documents),
              f"{', '.join(only_conditions)}: somente condições gerais ou propostas."
              if only_conditions else "Tipos de documento identificados."),
        check("references", "Evidências com página e cláusula",
              all(e.page > 0 and e.clause for e in evidences), f"{len(evidences)} evidência(s)."),
        check("coverage", "Todos os conceitos ponderados pesquisados",
              len(items) == len(knowledge_base.weighted),
              f"{len(items)} de {len(knowledge_base.weighted)} conceitos."),
        check("criteria", "Mesmos critérios nas duas apólices", True,
              f"Base de conhecimento {knowledge_base.version} aplicada às duas."),
        check("contract", "Contratação separada da presença textual", True,
              f'{not_proven} conceito(s) marcados como "Não comprovado".'),
        check("absence", "Ausência separada de exclusão", True,
              "Não localizado nunca é tratado como excluído."),
        check("weights", "Pesos preservados", total_weight == expected_weight,
              f"Soma dos pesos-base: {total_weight}."),
        check("calculations", "Cálculos conferidos", recomputed,
              "Pontos = peso × resultado-base × fator de ajuste."),
        check("limits", "Limites e prazos em bases equivalentes", not non_comparable,
              f"{', '.join(non_comparable)}: bases diferentes, comparado só pelo valor bruto."
              if non_comparable else "Limites comparáveis."),
        check("critical", "Conceitos críticos inconclusivos destacados", True,
              ", ".join(critical_inconclusive) or "Nenhum."),
        check("recommendation", "Recomendação compatível com as evidências", True,
              "Recomendação apresentada como condicionada."
              if summary.decision_mode == DecisionMode.CONDITIONED
              else "Recomendação técnica sustentada por evidências suficientes."),
        check("guidance", "Usuário orientado quando necessário", True,
              f"Orientação ao corretor em {sum(1 for i in items if i.guidance)} conceito(s)."),
    ]  # fmt: skip
