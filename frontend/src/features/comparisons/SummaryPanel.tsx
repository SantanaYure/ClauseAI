import { Badge } from '../../components/Badge';
import { BrokerNotice } from '../../components/BrokerNotice';
import { Icon } from '../../components/Icon';
import { Illustration } from '../../components/Illustration';
import { ScoreBar } from '../../components/ScoreBar';
import { formatPercent, formatPercentagePoints, formatPoints } from '../../shared/format';
import { DECISION_MODE_LABELS, POLICY_SLOT_LABELS } from '../../shared/labels';
import type { ComparisonPolicyRef, ComparisonResult, ScoreSummary } from '../../types/domain';

type SummaryPanelProps = {
  comparison: ComparisonResult;
};

/** Resumo executivo (SPEC-017), sempre separado da análise documental por conceito. */
export function SummaryPanel({ comparison }: SummaryPanelProps) {
  const base = comparison.profiles.find((profile) => profile.profile === 'BASE');
  const { summary } = comparison;
  if (!summary || !base) {
    return (
      <BrokerNotice reason="O resumo executivo não foi gerado nesta comparação; consulte as abas Conceitos e Qualidade." />
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
            Resumo executivo
          </h2>
          <Badge
            tone={conditioned ? 'medium' : 'success'}
            icon={conditioned ? 'alert' : 'checkCircle'}
          >
            {DECISION_MODE_LABELS[summary.decisionMode]}
          </Badge>
        </div>
        <p>{summary.conclusion}</p>
        {!conditioned && <Illustration name="success" />}
        {conditioned && <BrokerNotice compact />}
      </section>

      <div className="score-grid">
        <ScoreCard
          slot="A"
          policy={comparison.policyA}
          score={base.a}
          leader={base.winner === 'A'}
        />
        <ScoreCard
          slot="B"
          policy={comparison.policyB}
          score={base.b}
          leader={base.winner === 'B'}
        />
      </div>
      <p className="muted-text center">
        Diferença entre os scores de aderência:{' '}
        {formatPercentagePoints(Math.abs(base.a.adherence - base.b.adherence))}
      </p>

      {summary.scoreVsQualitative && (
        <section className="callout" aria-labelledby="divergence-title">
          <h3 id="divergence-title">
            <Icon name="info" size={18} /> Score × análise qualitativa
          </h3>
          <p>{summary.scoreVsQualitative}</p>
        </section>
      )}

      <div className="two-columns">
        <SummaryList
          title={`Vantagens da ${POLICY_SLOT_LABELS.A}`}
          items={summary.advantagesA}
          empty="Nenhuma vantagem comprovada."
        />
        <SummaryList
          title={`Vantagens da ${POLICY_SLOT_LABELS.B}`}
          items={summary.advantagesB}
          empty="Nenhuma vantagem comprovada."
        />
      </div>
      <SummaryList
        title="Coberturas críticas equivalentes"
        items={summary.equivalentCritical}
        empty="Nenhuma."
      />
      <SummaryList
        title="Diferenças de maior impacto"
        items={summary.highestImpact}
        empty="Nenhuma diferença de pontuação."
        ordered
      />
      <SummaryList
        title="Pontos de atenção"
        items={summary.attentionPoints}
        empty="Nenhum ponto de atenção."
        tone="attention"
      />

      <p className="footnote">
        Pesos indicam importância para a decisão; não comprovam contratação. A análise documental
        completa está em “Conceitos”.
      </p>
    </div>
  );
}

type ScoreCardProps = {
  slot: 'A' | 'B';
  policy: ComparisonPolicyRef;
  score: ScoreSummary;
  leader: boolean;
};

function ScoreCard({ slot, policy, score, leader }: ScoreCardProps) {
  return (
    <section
      className={`card score-card score-card--${slot.toLowerCase()}`}
      aria-label={`Scores da ${POLICY_SLOT_LABELS[slot]}`}
    >
      <p className="score-card__slot">
        {POLICY_SLOT_LABELS[slot]}
        {leader && <Badge tone="neutral">Maior score</Badge>}
      </p>
      <p className="score-card__insurer">{policy.insurer}</p>
      <ScoreBar label="Score de aderência" value={score.adherence} />
      <ScoreBar label="Índice de completude" value={score.completeness} variant="secondary" />
      <dl className="score-card__facts">
        <div>
          <dt>Pontos</dt>
          <dd>
            {formatPoints(score.raw)} de {formatPoints(score.max)}
          </dd>
        </div>
        <div>
          <dt>Score documental</dt>
          <dd>{formatPercent(score.documentary)}</dd>
        </div>
        <div>
          <dt>Favoráveis</dt>
          <dd>{score.favorable}</dd>
        </div>
        <div>
          <dt>Críticas sem confirmação</dt>
          <dd>peso {score.criticalUnconfirmedWeight}</dd>
        </div>
      </dl>
    </section>
  );
}

type SummaryListProps = {
  title: string;
  items: string[];
  empty: string;
  ordered?: boolean;
  tone?: 'attention';
};

function SummaryList({ title, items, empty, ordered = false, tone }: SummaryListProps) {
  const List = ordered ? 'ol' : 'ul';
  return (
    <section className={`card summary-list${tone ? ` summary-list--${tone}` : ''}`}>
      <h3 className="summary-list__title">{title}</h3>
      {items.length ? (
        <List>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </List>
      ) : (
        <p className="muted-text">{empty}</p>
      )}
    </section>
  );
}
