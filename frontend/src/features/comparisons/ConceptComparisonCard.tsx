import { paths } from '../../app/router';
import { Badge } from '../../components/Badge';
import { BrokerNotice } from '../../components/BrokerNotice';
import { EvidenceQuote } from '../../components/EvidenceQuote';
import { formatFactor, formatPoints } from '../../shared/format';
import {
  CONTRACT_STATUS_LABELS,
  IMPORTANCE_LABELS,
  LEVEL_LABELS,
  POLICY_SLOT_LABELS,
  VERDICT_LABELS,
} from '../../shared/labels';
import { DIFFERENCE_TONE_LABELS, contractTone, differenceTone } from '../../shared/tones';
import type { ComparisonItem, ComparisonSide } from '../../types/domain';

type ConceptComparisonCardProps = {
  item: ComparisonItem;
  insurerA: string;
  insurerB: string;
};

/** Uma linha da tabela final (prompt 15), em formato de card para telas estreitas. */
export function ConceptComparisonCard({ item, insurerA, insurerB }: ConceptComparisonCardProps) {
  const tone = differenceTone(item);
  return (
    <li className={`card concept-row concept-row--${tone}`}>
      <div className="concept-row__header">
        <div>
          <a className="concept-row__name" href={paths.concept(item.conceptId)}>
            {item.conceptName}
          </a>
          <p className="muted-text">
            {item.conceptId} · {IMPORTANCE_LABELS[item.importance]} · peso {item.weight}
          </p>
        </div>
        <Badge tone={tone}>{VERDICT_LABELS[item.verdict]}</Badge>
      </div>
      <p className="visually-hidden">{DIFFERENCE_TONE_LABELS[tone]}</p>

      <div className="concept-row__sides">
        <SideSummary label={POLICY_SLOT_LABELS.A} side={item.a} weight={item.weight} />
        <SideSummary label={POLICY_SLOT_LABELS.B} side={item.b} weight={item.weight} />
      </div>

      <p className="concept-row__difference">{item.mainDifference}</p>

      <details className="concept-row__details">
        <summary>Ver evidências e cálculo</summary>
        <SideDetails
          label={`${POLICY_SLOT_LABELS.A} · ${insurerA}`}
          side={item.a}
          weight={item.weight}
        />
        <SideDetails
          label={`${POLICY_SLOT_LABELS.B} · ${insurerB}`}
          side={item.b}
          weight={item.weight}
        />
        <p className="muted-text">Confiança da análise: {LEVEL_LABELS[item.confidence]}</p>
      </details>

      {item.guidance && <BrokerNotice compact />}
    </li>
  );
}

function SideSummary({
  label,
  side,
  weight,
}: {
  label: string;
  side: ComparisonSide;
  weight: number;
}) {
  return (
    <div className="side">
      <span className="side__label">{label}</span>
      <Badge tone={contractTone(side.contractStatus)}>
        {CONTRACT_STATUS_LABELS[side.contractStatus]}
      </Badge>
      <span className="side__points">
        <strong>{formatPoints(side.points)}</strong> / {weight} pts
      </span>
    </div>
  );
}

function SideDetails({
  label,
  side,
  weight,
}: {
  label: string;
  side: ComparisonSide;
  weight: number;
}) {
  return (
    <div className="side-details">
      <h4>{label}</h4>
      <p>
        <span className="muted-text">Termo: </span>
        {side.term}
        {side.amount ? ` — ${side.amount}` : ''}
      </p>
      <p className="formula">
        {weight} × {formatFactor(side.baseResult)} × {formatFactor(side.adjustmentFactor)} ={' '}
        <strong>{formatPoints(side.points)}</strong>
        <small>peso × resultado-base × fator de ajuste</small>
      </p>
      {side.justification && <p className="muted-text">{side.justification}</p>}
      {side.evidence.length ? (
        side.evidence.map((evidence) => <EvidenceQuote key={evidence.id} evidence={evidence} />)
      ) : (
        <p className="muted-text">Sem trecho localizado nos documentos enviados.</p>
      )}
    </div>
  );
}
