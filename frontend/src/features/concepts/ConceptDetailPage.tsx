import { paths } from '../../app/router';
import { Badge } from '../../components/Badge';
import { BrokerNotice } from '../../components/BrokerNotice';
import { EvidenceQuote } from '../../components/EvidenceQuote';
import { PageHeader } from '../../components/PageHeader';
import { EmptyState, ErrorState, LoadingState } from '../../components/StateViews';
import { clauseApi } from '../../services/api/clause-api';
import { CONTRACT_STATUS_LABELS, IMPORTANCE_LABELS } from '../../shared/labels';
import { contractTone, importanceTone } from '../../shared/tones';
import { useApiData } from '../../shared/useApiData';
import type { ConceptId, ConceptWithOccurrences } from '../../types/domain';

export function ConceptDetailPage({ conceptId }: { conceptId: string }) {
  const state = useApiData(`concept:${conceptId}`, () =>
    clauseApi.getConcept(conceptId as ConceptId),
  );
  const back = { href: paths.concepts(), label: 'Conceitos' };

  if (state.status === 'loading') return <LoadingState label="Carregando conceito…" />;
  if (state.status === 'error') {
    return (
      <div className="page">
        <PageHeader title="Conceito" back={back} />
        <ErrorState message={state.message} onRetry={state.reload} />
      </div>
    );
  }
  return <ConceptView concept={state.data} back={back} />;
}

function ConceptView({
  concept,
  back,
}: {
  concept: ConceptWithOccurrences;
  back: { href: string; label: string };
}) {
  return (
    <div className="page">
      <PageHeader title={concept.name} subtitle={`${concept.id} · ${concept.domain}`} back={back} />

      <p className="tag-row">
        <Badge tone={importanceTone(concept.importance)}>
          {concept.weight
            ? `${IMPORTANCE_LABELS[concept.importance]} · peso ${concept.weight}`
            : 'Sem peso'}
        </Badge>
        <Badge tone="neutral">
          Revisão humana {concept.humanReview === 'REQUIRED' ? 'obrigatória' : 'recomendada'}
        </Badge>
      </p>

      <dl className="card definition">
        {concept.justification && (
          <div>
            <dt>Por que tem esse peso</dt>
            <dd>{concept.justification}</dd>
          </div>
        )}
        <div>
          <dt>Critério de avaliação</dt>
          <dd>{concept.criterion}</dd>
        </div>
        <div>
          <dt>Variantes e gatilhos de busca</dt>
          <dd className="tag-row">
            {concept.variants.map((variant) => (
              <span key={variant} className="tag">
                {variant}
              </span>
            ))}
          </dd>
        </div>
        {concept.related.length > 0 && (
          <div>
            <dt>Conceitos relacionados</dt>
            <dd className="tag-row">
              {concept.related.map((id) => (
                <a key={id} className="tag tag--link" href={paths.concept(id)}>
                  {id}
                </a>
              ))}
            </dd>
          </div>
        )}
      </dl>

      {concept.weight === null && (
        <p className="footnote">
          Sem peso definido: é extraído e exibido, mas não entra no score até a validação da equipe
          de seguros.
        </p>
      )}
      {concept.pendingValidation && (
        <p className="footnote">
          Conceito acrescentado pela matriz de pesos; as variantes ainda estão em validação.
        </p>
      )}

      <section aria-labelledby="where-title" className="stack">
        <h2 id="where-title" className="section-title">
          Onde aparece nas apólices
        </h2>
        {concept.occurrences.length ? (
          <ul className="stack">
            {concept.occurrences.map(({ policy, occurrence }) => (
              <li key={policy.id} className="card occurrence">
                <div className="occurrence__header">
                  <a href={paths.policy(policy.id)}>
                    <strong>{policy.insurer}</strong>
                  </a>
                  <Badge tone={contractTone(occurrence.contractStatus)}>
                    {CONTRACT_STATUS_LABELS[occurrence.contractStatus]}
                  </Badge>
                </div>
                <p>
                  <span className="muted-text">Termo encontrado: </span>
                  {occurrence.term}
                </p>
                {occurrence.justification && (
                  <p className="muted-text">{occurrence.justification}</p>
                )}
                {occurrence.evidence.map((evidence) => (
                  <EvidenceQuote key={evidence.id} evidence={evidence} />
                ))}
                {occurrence.contractStatus !== 'CONTRACTED' &&
                  occurrence.contractStatus !== 'EXCLUDED' && <BrokerNotice compact />}
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon="search"
            title="Não localizado nas apólices"
            text="Nenhum documento armazenado cita este conceito. Não localizado não significa excluído."
          />
        )}
      </section>
    </div>
  );
}
