import { Badge } from '../../components/Badge';
import { MetricHelp } from '../../components/MetricHelp';
import { formatPercent } from '../../shared/format';
import { POLICY_SLOT_LABELS } from '../../shared/labels';
import type { ComparisonPolicyRef, ScoreSummary } from '../../types/domain';

const ADHERENCE_HELP =
  'Quanto das coberturas que importam a apólice comprova, dando mais peso às críticas.';
const COMPLETENESS_HELP = 'Quanto do que foi procurado apareceu nos documentos enviados.';

type ScoreboardProps = {
  slot: 'A' | 'B';
  policy: ComparisonPolicyRef;
  score: ScoreSummary;
  leader: boolean;
};

/** Placar de uma apólice: só dois números, aderência e completude. */
export function Scoreboard({ slot, policy, score, leader }: ScoreboardProps) {
  return (
    <section
      className={`card scoreboard scoreboard--${slot.toLowerCase()}`}
      aria-label={`Placar da ${POLICY_SLOT_LABELS[slot]}`}
    >
      <p className="scoreboard__slot">
        <span className="slot__letter" aria-hidden="true">
          {slot}
        </span>
        <span>
          {POLICY_SLOT_LABELS[slot]}
          <small>{policy.insurer}</small>
        </span>
        {leader && <Badge tone="neutral">Maior aderência</Badge>}
      </p>
      <dl className="scoreboard__metrics">
        <div>
          <dt>
            Aderência <MetricHelp term="aderência" explanation={ADHERENCE_HELP} />
          </dt>
          <dd className="scoreboard__number">{formatPercent(score.adherence)}</dd>
        </div>
        <div>
          <dt>
            Completude <MetricHelp term="completude" explanation={COMPLETENESS_HELP} />
          </dt>
          <dd className="scoreboard__number">{formatPercent(score.completeness)}</dd>
        </div>
      </dl>
    </section>
  );
}
