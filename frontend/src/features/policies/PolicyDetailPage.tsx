import { useState } from 'react';
import { paths } from '../../app/router';
import { Badge } from '../../components/Badge';
import { BrokerNotice } from '../../components/BrokerNotice';
import { EvidenceQuote } from '../../components/EvidenceQuote';
import { FilterChips } from '../../components/FilterChips';
import { Icon } from '../../components/Icon';
import { PageHeader } from '../../components/PageHeader';
import { Spinner } from '../../components/Spinner';
import { EmptyState, ErrorState, LoadingState } from '../../components/StateViews';
import { COMPARABLE_POLICY_STATUSES, clauseApi } from '../../services/api/clause-api';
import {
  CONTRACT_STATUS_LABELS,
  DOCUMENT_STATUS_LABELS,
  DOCUMENT_TYPE_LABELS,
  FILE_KIND_LABELS,
  IMPORTANCE_LABELS,
  LEVEL_LABELS,
  POLICY_STATUS_LABELS,
} from '../../shared/labels';
import {
  describeProcessing,
  isDocumentBusy,
  isPolicyBusy,
  PROCESSING_POLL_MS,
} from '../../shared/processing';
import { contractTone, documentStatusTone, policyStatusTone } from '../../shared/tones';
import { useApiData } from '../../shared/useApiData';
import type { Concept, ConceptOccurrence, ContractStatus, PolicyDetail } from '../../types/domain';

type Filter = 'ALL' | ContractStatus;

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'ALL', label: 'Todas' },
  { value: 'CONTRACTED', label: 'Contratadas' },
  { value: 'NOT_PROVEN', label: 'Não comprovadas' },
  { value: 'EXCLUDED', label: 'Excluídas' },
  { value: 'NOT_FOUND', label: 'Não localizadas' },
];

export function PolicyDetailPage({ policyId }: { policyId: string }) {
  const state = useApiData(
    `policy:${policyId}`,
    () => Promise.all([clauseApi.getPolicy(policyId), clauseApi.listConcepts()]),
    {
      pollMs: PROCESSING_POLL_MS,
      shouldPoll: ([policy]) => isPolicyBusy(policy.status),
    },
  );
  const back = { href: paths.policies, label: 'Apólices' };

  if (state.status === 'loading') return <LoadingState label="Carregando apólice…" />;
  if (state.status === 'error') {
    return (
      <div className="page">
        <PageHeader title="Apólice" back={back} />
        <ErrorState message={state.message} onRetry={state.reload} />
      </div>
    );
  }

  const [policy, concepts] = state.data;
  return <PolicyDetailView policy={policy} concepts={concepts} back={back} />;
}

type ViewProps = {
  policy: PolicyDetail;
  concepts: Concept[];
  back: { href: string; label: string };
};

function PolicyDetailView({ policy, concepts, back }: ViewProps) {
  const [filter, setFilter] = useState<Filter>('ALL');
  const conceptById = new Map(concepts.map((concept) => [concept.id, concept]));
  const occurrences = [...policy.occurrences].sort(
    (x, y) =>
      (conceptById.get(y.conceptId)?.weight ?? 0) - (conceptById.get(x.conceptId)?.weight ?? 0),
  );
  const visible = occurrences.filter(
    (occurrence) => filter === 'ALL' || occurrence.contractStatus === filter,
  );
  const comparable = COMPARABLE_POLICY_STATUSES.includes(policy.status);

  return (
    <div className="page">
      <PageHeader
        title={policy.insurer}
        subtitle={policy.name}
        back={back}
        action={
          <Badge tone={policyStatusTone(policy.status)} busy={isPolicyBusy(policy.status)}>
            {POLICY_STATUS_LABELS[policy.status]}
          </Badge>
        }
      />

      {isPolicyBusy(policy.status) && (
        <p className="processing-note processing-note--block" role="status">
          <Spinner />
          <span>
            <strong>Processando esta apólice.</strong>
            {describeProcessing(policy.documents)} A página se atualiza sozinha.
          </span>
        </p>
      )}

      <dl className="facts card">
        <div>
          <dt>Número</dt>
          <dd>{policy.number ?? 'Não identificado'}</dd>
        </div>
        <div>
          <dt>Vigência</dt>
          <dd>{policy.validity ?? 'Não identificada'}</dd>
        </div>
        <div>
          <dt>Documentos</dt>
          <dd>{policy.documents.length}</dd>
        </div>
        <div>
          <dt>Evidências</dt>
          <dd>
            {policy.occurrences.reduce((sum, occurrence) => sum + occurrence.evidence.length, 0)}
          </dd>
        </div>
      </dl>

      {policy.alerts.map((alert) => (
        <BrokerNotice key={alert} reason={alert} />
      ))}

      {comparable && (
        <a className="btn btn--primary btn--block" href={paths.compare(policy.id)}>
          <Icon name="scale" size={20} />
          Comparar esta apólice
        </a>
      )}

      <section aria-labelledby="docs-title">
        <h2 id="docs-title" className="section-title">
          Documentos recebidos
        </h2>
        <ul className="stack">
          {policy.documents.map((document) => (
            <li key={document.id} className="card doc-card">
              <div className="doc-card__header">
                <Icon name="file" size={20} />
                <strong className="doc-card__name">{document.filename}</strong>
                <Badge
                  tone={documentStatusTone(document.status)}
                  busy={isDocumentBusy(document.status)}
                >
                  {DOCUMENT_STATUS_LABELS[document.status]}
                </Badge>
              </div>
              <p className="tag-row">
                <span className="tag">{DOCUMENT_TYPE_LABELS[document.type]}</span>
                <span className="tag">{FILE_KIND_LABELS[document.fileKind]}</span>
                {document.pages > 0 && <span className="tag">{document.pages} páginas</span>}
                <span className="tag">{document.ocrRequired ? 'Com OCR' : 'Sem OCR'}</span>
                {document.extractionQuality && (
                  <span className="tag">
                    Qualidade {LEVEL_LABELS[document.extractionQuality].toLowerCase()}
                  </span>
                )}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="evidence-title">
        <h2 id="evidence-title" className="section-title">
          Evidências por conceito
        </h2>
        {policy.status === 'PROCESSING' ? (
          <LoadingState label="Extração em andamento. As evidências aparecem aqui quando o processamento terminar." />
        ) : (
          <>
            <FilterChips
              label="Filtrar por contratação"
              value={filter}
              onChange={setFilter}
              options={FILTERS.map((option) => ({
                ...option,
                count: occurrences.filter(
                  (o) => option.value === 'ALL' || o.contractStatus === option.value,
                ).length,
              }))}
            />
            {visible.length ? (
              <ul className="stack">
                {visible.map((occurrence) => (
                  <OccurrenceCard
                    key={occurrence.conceptId}
                    occurrence={occurrence}
                    concept={conceptById.get(occurrence.conceptId)}
                  />
                ))}
              </ul>
            ) : (
              <EmptyState
                icon="search"
                title="Nada neste filtro"
                text="Nenhuma evidência com este status."
              />
            )}
          </>
        )}
      </section>
    </div>
  );
}

function OccurrenceCard({
  occurrence,
  concept,
}: {
  occurrence: ConceptOccurrence;
  concept?: Concept;
}) {
  return (
    <li className="card occurrence">
      <div className="occurrence__header">
        <div>
          <a className="occurrence__concept" href={paths.concept(occurrence.conceptId)}>
            {concept?.name ?? occurrence.conceptId}
          </a>
          <p className="muted-text">
            {occurrence.conceptId} · {concept ? IMPORTANCE_LABELS[concept.importance] : ''}
            {concept?.weight ? ` · peso ${concept.weight}` : ''}
          </p>
        </div>
        <Badge tone={contractTone(occurrence.contractStatus)}>
          {CONTRACT_STATUS_LABELS[occurrence.contractStatus]}
        </Badge>
      </div>
      <p>
        <span className="muted-text">Termo encontrado: </span>
        {occurrence.term}
      </p>
      {occurrence.justification && <p className="muted-text">{occurrence.justification}</p>}
      {occurrence.evidence.map((evidence) => (
        <EvidenceQuote key={evidence.id} evidence={evidence} />
      ))}
      {occurrence.contractStatus !== 'CONTRACTED' && occurrence.contractStatus !== 'EXCLUDED' && (
        <BrokerNotice compact />
      )}
    </li>
  );
}
