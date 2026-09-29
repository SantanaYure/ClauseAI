import { formatPercent, formatPercentagePoints, formatPoints } from '../../shared/format';
import { POLICY_SLOT_LABELS } from '../../shared/labels';
import type { ComparisonResult } from '../../types/domain';
import { ConceptsPanel } from './ConceptsPanel';
import { ProfilesPanel } from './ProfilesPanel';
import { QualityPanel } from './QualityPanel';

/** "Ver cálculo": tudo que explica o resultado, recolhido por padrão. */
export function CalculationDetails({ comparison }: { comparison: ComparisonResult }) {
  const base = comparison.profiles.find((profile) => profile.profile === 'BASE');
  const { summary } = comparison;
  return (
    <details className="card calc">
      <summary>
        Ver cálculo
        <small>Pontos, score documental, conceitos, perfis e qualidade</small>
      </summary>
      <div className="stack calc__body">
        {base && (
          <section className="stack" aria-labelledby="calc-numbers">
            <h3 id="calc-numbers" className="section-title">
              Números do cálculo
            </h3>
            <div className="two-columns">
              {(['A', 'B'] as const).map((slot) => {
                const score = base[slot.toLowerCase() as 'a' | 'b'];
                return (
                  <dl key={slot} className="score-card__facts">
                    <div>
                      <dt>{POLICY_SLOT_LABELS[slot]} · pontos</dt>
                      <dd>
                        {formatPoints(score.raw)} de {formatPoints(score.max)}
                      </dd>
                    </div>
                    <div>
                      <dt>Score documental</dt>
                      <dd>{formatPercent(score.documentary)}</dd>
                    </div>
                    <div>
                      <dt>Conceitos favoráveis</dt>
                      <dd>{score.favorable}</dd>
                    </div>
                    <div>
                      <dt>Críticas sem confirmação</dt>
                      <dd>peso {score.criticalUnconfirmedWeight}</dd>
                    </div>
                  </dl>
                );
              })}
            </div>
            <p className="muted-text">
              Diferença entre os scores de aderência:{' '}
              {formatPercentagePoints(Math.abs(base.a.adherence - base.b.adherence))}. Pesos indicam
              importância para a decisão; não comprovam contratação.
            </p>
          </section>
        )}

        {summary && (
          <div className="two-columns">
            <TextList
              title="Coberturas críticas equivalentes"
              items={summary.equivalentCritical}
              empty="Nenhuma."
            />
            <TextList
              title="Diferenças de maior impacto"
              items={summary.highestImpact}
              empty="Nenhuma diferença de pontuação."
            />
          </div>
        )}

        <section className="stack" aria-labelledby="calc-concepts">
          <h3 id="calc-concepts" className="section-title">
            Conceitos
          </h3>
          <ConceptsPanel comparison={comparison} />
        </section>
        <section className="stack" aria-labelledby="calc-profiles">
          <h3 id="calc-profiles" className="section-title">
            Perfis de risco
          </h3>
          <ProfilesPanel comparison={comparison} />
        </section>
        <section className="stack" aria-labelledby="calc-quality">
          <h3 id="calc-quality" className="section-title">
            Qualidade
          </h3>
          <QualityPanel comparison={comparison} />
        </section>
      </div>
    </details>
  );
}

function TextList({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return (
    <section className="summary-list">
      <h4 className="summary-list__title">{title}</h4>
      {items.length ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="muted-text">{empty}</p>
      )}
    </section>
  );
}
