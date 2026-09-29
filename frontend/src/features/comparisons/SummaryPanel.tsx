import { Badge } from '../../components/Badge';
import { Icon } from '../../components/Icon';
import { Illustration } from '../../components/Illustration';
import { DECISION_MODE_LABELS, POLICY_SLOT_LABELS } from '../../shared/labels';
import type { ComparisonResult } from '../../types/domain';
import { Scoreboard } from './Scoreboard';

/**
 * Resumo executivo (SPEC-010/017) na ordem fixa: conclusão, dois placares, vantagens e atenção.
 * O cálculo detalhado fica em "Ver cálculo".
 */
export function SummaryPanel({ comparison }: { comparison: ComparisonResult }) {
  const base = comparison.profiles.find((profile) => profile.profile === 'BASE');
  const { summary } = comparison;
  if (!summary || !base) {
    return (
      <p className="callout">
        O resumo executivo não foi gerado nesta comparação; consulte “Ver cálculo”.
      </p>
    );
  }
  const conditioned = summary.decisionMode === 'CONDITIONED';

  return (
    <div className="stack">
      <section
        className={`decision card${conditioned ? ' decision--conditioned' : ''}`}
        aria-labelledby="decision-title"
      >
        <div className="decision__header">
          <h2 id="decision-title" className="section-title">
            Conclusão
          </h2>
          <Badge
            tone={conditioned ? 'medium' : 'success'}
            icon={conditioned ? 'alert' : 'checkCircle'}
          >
            {DECISION_MODE_LABELS[summary.decisionMode]}
          </Badge>
        </div>
        <p className="decision__conclusion">{summary.conclusion}</p>
        {!conditioned && <Illustration name="success" />}
      </section>

      <div className="score-grid">
        <Scoreboard
          slot="A"
          policy={comparison.policyA}
          score={base.a}
          leader={base.winner === 'A'}
        />
        <Scoreboard
          slot="B"
          policy={comparison.policyB}
          score={base.b}
          leader={base.winner === 'B'}
        />
      </div>

      <div className="two-columns">
        <section className="card summary-list" aria-labelledby="advantages-title">
          <h3 id="advantages-title" className="summary-list__title">
            Vantagens
          </h3>
          <AdvantageList label={POLICY_SLOT_LABELS.A} items={summary.advantagesA} />
          <AdvantageList label={POLICY_SLOT_LABELS.B} items={summary.advantagesB} />
        </section>
        <section
          className="card summary-list summary-list--attention"
          aria-labelledby="attention-title"
        >
          <h3 id="attention-title" className="summary-list__title">
            <Icon name="alert" size={18} /> Atenção
          </h3>
          {summary.attentionPoints.length ? (
            <ul>
              {summary.attentionPoints.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="muted-text">Nenhum ponto de atenção.</p>
          )}
          {summary.scoreVsQualitative && (
            <p className="summary-list__note">{summary.scoreVsQualitative}</p>
          )}
        </section>
      </div>
    </div>
  );
}

function AdvantageList({ label, items }: { label: string; items: string[] }) {
  return (
    <div className="advantage-list">
      <h4>{label}</h4>
      {items.length ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="muted-text">Nenhuma vantagem comprovada.</p>
      )}
    </div>
  );
}
