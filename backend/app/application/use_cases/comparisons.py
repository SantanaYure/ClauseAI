"""Comparison use cases (SPEC-007 to SPEC-009, SPEC-016, SPEC-017, SPEC-019).

A comparison belongs to the owner of both policies and expires with the earliest of
them. Someone else's comparison, or an expired one, answers exactly like a missing one.
"""

from uuid import uuid4

from app.application.commands import CreateComparisonCommand
from app.application.errors import conflict, invalid, not_found
from app.application.quotas import QuotaGuard
from app.domain.entities import (
    Comparison,
    ConceptOccurrence,
    ExecutiveSummary,
    Failure,
    Policy,
    PolicyRef,
    utc_now,
)
from app.domain.interfaces.events import Event, EventBus
from app.domain.interfaces.ports import (
    AssessmentRequest,
    ComparisonRepository,
    ConceptAssessor,
    ConceptCatalog,
    PolicyRepository,
    SummaryWriter,
)
from app.domain.services.scoring import (
    ConceptPair,
    ScoringParameters,
    build_items,
    build_pairs,
    build_profiles,
    build_quality_gate,
    build_summary,
    format_percent,
    unassessed_assessment,
)
from app.domain.value_objects import (
    COMPARABLE_POLICY_STATUSES,
    FINAL_COMPARISON_STATUSES,
    ComparisonStatus,
    RiskProfile,
)
from app.shared.exceptions import ApplicationError
from app.shared.logging import error_fields, get_logger, log_context, owner_ref

COMPARISON_REQUESTED = "ComparisonRequested"
# Keeps each assessment request small enough for free-tier token limits.
MAX_EVIDENCE_PER_SIDE = 2
MAX_EVIDENCE_CHARS = 400

logger = get_logger(__name__)


def _side_payload(occurrence: ConceptOccurrence | None) -> dict[str, object]:
    """Only the facts the assessor may use (P-ASSESS-001)."""

    if occurrence is None:
        return {"contract_status": "NOT_FOUND"}
    return {
        "contract_status": occurrence.contract_status,
        "term": occurrence.term,
        "note": occurrence.justification,
        "limit_basis": occurrence.limit_basis,
        "amount": occurrence.amount,
        "evidence": [
            {"text": e.text[:MAX_EVIDENCE_CHARS], "clause": e.clause, "page": e.page}
            for e in occurrence.evidence[:MAX_EVIDENCE_PER_SIDE]
        ],
    }


def _ref(policy: Policy) -> PolicyRef:
    return PolicyRef(id=policy.id, insurer=policy.insurer, name=policy.name)


class _ComparisonGone(Exception):
    """The comparison was deleted while it was running."""


def _comparison_not_found() -> ApplicationError:
    return not_found("COMPARISON_NOT_FOUND", "Comparação não encontrada.")


def _failure(exc: ApplicationError, prefix: str) -> Failure:
    return Failure(
        code=exc.code,
        message=prefix + exc.message,
        retryable=bool((exc.details or {}).get("retryable")),
    )


class ComparisonService:
    def __init__(
        self,
        comparisons: ComparisonRepository,
        policies: PolicyRepository,
        catalog: ConceptCatalog,
        assessor: ConceptAssessor,
        summary_writer: SummaryWriter,
        event_bus: EventBus,
        parameters: ScoringParameters,
        quotas: QuotaGuard,
    ) -> None:
        self._comparisons = comparisons
        self._policies = policies
        self._catalog = catalog
        self._assessor = assessor
        self._summary_writer = summary_writer
        self._event_bus = event_bus
        self._parameters = parameters
        self._quotas = quotas

    async def _ready_policy(self, owner_id: str, policy_id: str) -> Policy:
        policy = await self._policies.get(policy_id)
        if policy is None or policy.owner_id != owner_id or policy.is_expired(utc_now()):
            raise not_found("POLICY_NOT_FOUND", "Apólice não encontrada.")
        if policy.status not in COMPARABLE_POLICY_STATUSES:
            raise conflict("POLICY_NOT_READY", "As duas apólices precisam estar processadas.")
        return policy

    async def create_comparison(self, command: CreateComparisonCommand) -> Comparison:
        if command.policy_a_id == command.policy_b_id:
            raise invalid("SAME_POLICY", "Escolha duas apólices diferentes.")
        policy_a = await self._ready_policy(command.owner_id, command.policy_a_id)
        policy_b = await self._ready_policy(command.owner_id, command.policy_b_id)
        self._quotas.consume_comparison(command.owner_id)
        comparison = Comparison(
            id=f"cmp_{uuid4().hex[:16]}",
            owner_id=command.owner_id,
            expires_at=min(policy_a.expires_at, policy_b.expires_at),
            knowledge_base_version=self._catalog.load().version,
            selected_profile=command.selected_profile,
            policy_a=_ref(policy_a),
            policy_b=_ref(policy_b),
            correlation_id=command.correlation_id,
        )
        await self._comparisons.save(comparison)
        await self._event_bus.publish(
            Event.create(
                COMPARISON_REQUESTED,
                command.correlation_id,
                {"comparison_id": comparison.id, "owner_id": command.owner_id},
            )
        )
        return comparison

    async def handle_comparison_requested(self, event: Event) -> None:
        comparison_id = str(event.payload["comparison_id"])
        owner_id = str(event.payload.get("owner_id") or "")
        with log_context(comparison_id=comparison_id, owner_ref=owner_ref(owner_id)):
            comparison = await self._comparisons.get(comparison_id)
            if comparison is None or comparison.owner_id != owner_id:
                logger.warning(
                    "ComparisonRequested discarded: comparison missing or owner mismatch"
                )
                return
            await self.run_comparison(comparison_id)

    async def run_comparison(self, comparison_id: str) -> None:
        comparison = await self._comparisons.get(comparison_id)
        if comparison is None or comparison.status in FINAL_COMPARISON_STATUSES:
            return  # idempotent
        with log_context(
            comparison_id=comparison_id,
            correlation_id=comparison.correlation_id,
            owner_ref=owner_ref(comparison.owner_id),
        ):
            try:
                await self._run_or_fail(comparison)
            except _ComparisonGone:
                logger.info("Comparison aborted: comparison deleted")

    async def _run_or_fail(self, comparison: Comparison) -> None:
        try:
            await self._run(comparison)
        except _ComparisonGone:
            raise
        except ApplicationError as exc:
            await self._finish_failed(
                comparison, exc.code, exc.message, bool((exc.details or {}).get("retryable"))
            )
        except Exception as exc:
            with log_context(**error_fields(exc)):
                logger.error("Comparison failed")
            await self._finish_failed(
                comparison, "UNEXPECTED_ERROR", "Falha inesperada ao comparar as apólices."
            )

    async def _run(self, comparison: Comparison) -> None:
        knowledge_base = self._catalog.load()
        policy_a = await self._policies.get(comparison.policy_a.id)
        policy_b = await self._policies.get(comparison.policy_b.id)
        if policy_a is None or policy_b is None:
            raise not_found("POLICY_NOT_FOUND", "Uma das apólices não existe mais.")

        pairs = build_pairs(knowledge_base, policy_a, policy_b)
        await self._advance(comparison, ComparisonStatus.DETERMINISTIC_COMPLETED)

        await self._advance(comparison, ComparisonStatus.ASSESSING)
        requests = [self._request(pair) for pair in pairs if pair.needs_assessment]
        degraded: Failure | None = None
        try:
            assessments = await self._assessor.assess(requests) if requests else []
            by_concept = {a.concept_id: a for a in assessments}
        except ApplicationError as exc:
            # Nothing is invented: concepts that needed AI keep no points and low
            # confidence, so the deterministic data still yields a partial result.
            logger.warning("Concept assessment unavailable; degrading to partial")
            by_concept = {
                pair.concept.id: unassessed_assessment(pair)
                for pair in pairs
                if pair.needs_assessment
            }
            degraded = _failure(exc, prefix="Avaliação por IA indisponível: ")
        comparison.models["assessment"] = self._assessor.model_name

        items = build_items(pairs, by_concept, self._parameters)
        profiles = build_profiles(items, self._parameters)
        comparison.items = items
        comparison.profiles = profiles
        await self._advance(comparison, ComparisonStatus.SCORED)

        base = next(p for p in profiles if p.profile == RiskProfile.BASE)
        summary = build_summary(items, base, self._parameters)
        await self._advance(comparison, ComparisonStatus.SUMMARIZING)
        final_status = ComparisonStatus.PARTIAL if degraded else ComparisonStatus.COMPLETED
        comparison.failure = degraded
        try:
            summary.conclusion = await self._summary_writer.write_conclusion(
                summary, self._facts(summary, base.a.adherence, base.b.adherence)
            )
        except ApplicationError as exc:
            # The deterministic summary stays; the comparison is marked partial (SPEC-009).
            final_status = ComparisonStatus.PARTIAL
            comparison.failure = degraded or _failure(exc, prefix="Resumo redigido sem IA: ")
        comparison.summary = summary
        comparison.quality_gate = build_quality_gate(
            policy_a, policy_b, items, summary, knowledge_base, self._parameters
        )
        comparison.completed_at = utc_now()
        await self._advance(comparison, final_status)
        logger.info("Comparison completed")

    @staticmethod
    def _request(pair: ConceptPair) -> AssessmentRequest:
        return AssessmentRequest(
            concept_id=pair.concept.id,
            concept_name=pair.concept.name,
            criterion=pair.concept.criterion,
            weight=pair.weight,
            policy_a=_side_payload(pair.a),
            policy_b=_side_payload(pair.b),
        )

    @staticmethod
    def _facts(
        summary: ExecutiveSummary, adherence_a: float, adherence_b: float
    ) -> dict[str, object]:
        return {
            "decision_mode": summary.decision_mode,
            "score_aderencia_apolice_01": format_percent(adherence_a),
            "score_aderencia_apolice_02": format_percent(adherence_b),
            "maior_score": summary.highest_score,
            "conclusao_deterministica": summary.conclusion,
            "vantagens_apolice_01": summary.advantages_a,
            "vantagens_apolice_02": summary.advantages_b,
            "pontos_de_atencao": summary.attention_points,
            "score_vs_qualitative": summary.score_vs_qualitative,
        }

    async def _advance(self, comparison: Comparison, status: ComparisonStatus) -> None:
        """Save progress, but never recreate a comparison erased meanwhile."""

        if await self._comparisons.get(comparison.id) is None:
            raise _ComparisonGone
        comparison.status = status
        await self._comparisons.save(comparison)

    async def _finish_failed(
        self, comparison: Comparison, code: str, message: str, retryable: bool = False
    ) -> None:
        comparison.failure = Failure(code=code, message=message, retryable=retryable)
        comparison.completed_at = utc_now()
        await self._advance(comparison, ComparisonStatus.FAILED)

    # ---------- Queries ----------

    async def get_comparison(self, owner_id: str, comparison_id: str) -> Comparison:
        comparison = await self._comparisons.get(comparison_id)
        if (
            comparison is None
            or comparison.owner_id != owner_id
            or comparison.is_expired(utc_now())
        ):
            raise _comparison_not_found()
        return comparison

    async def list_comparisons(self, owner_id: str, limit: int) -> list[Comparison]:
        """The owner's comparisons that are still within the retention period."""

        now = utc_now()
        comparisons = await self._comparisons.list_recent(owner_id, limit)
        return [c for c in comparisons if not c.is_expired(now)][:limit]

    async def count_active(self, owner_id: str) -> int:
        return await self._comparisons.count_active(owner_id, utc_now())
