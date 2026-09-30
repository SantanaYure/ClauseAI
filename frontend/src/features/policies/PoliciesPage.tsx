import { useState } from 'react';
import { paths } from '../../app/router';
import { FilterChips } from '../../components/FilterChips';
import { Icon } from '../../components/Icon';
import { PageHeader } from '../../components/PageHeader';
import { PrivacyNote } from '../../components/PrivacyNote';
import { SearchField } from '../../components/SearchField';
import { EmptyState, ErrorState, LoadingState } from '../../components/StateViews';
import { clauseApi } from '../../services/api/clause-api';
import { normalizeText } from '../../shared/text';
import { hasBusyPolicy, PROCESSING_POLL_MS } from '../../shared/processing';
import { useApiData } from '../../shared/useApiData';
import type { PolicyStatus, PolicySummary } from '../../types/domain';
import { PolicyCard } from './PolicyCard';
import { takeFlash } from '../../shared/flash';

type Filter = 'ALL' | PolicyStatus;

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'ALL', label: 'Todas' },
  { value: 'READY', label: 'Prontas' },
  { value: 'ATTENTION', label: 'Com alerta' },
  { value: 'PROCESSING', label: 'Processando' },
  { value: 'FAILED', label: 'Falharam' },
];

function matches(policy: PolicySummary, filter: Filter, query: string): boolean {
  if (filter !== 'ALL' && policy.status !== filter) return false;
  const term = normalizeText(query);
  if (!term) return true;
  return [
    policy.insurer,
    policy.name,
    policy.number ?? '',
    ...policy.documents.map((d) => d.filename),
  ]
    .map(normalizeText)
    .some((value) => value.includes(term));
}

export function PoliciesPage() {
  const [flash, setFlashMessage] = useState(takeFlash);
  const state = useApiData('policies', () => clauseApi.listPolicies(), {
    pollMs: PROCESSING_POLL_MS,
    shouldPoll: hasBusyPolicy,
  });
  const [filter, setFilter] = useState<Filter>('ALL');
  const [query, setQuery] = useState('');

  const action = (
    <a className="btn btn--primary btn--compact" href={paths.newPolicy}>
      <Icon name="plus" size={18} />
      Adicionar
    </a>
  );

  return (
    <div className="page">
      <PageHeader
        title="Apólices"
        subtitle="Cada apólice reúne seus documentos: apólice, especificação, condições e endossos."
        action={action}
      />
      {flash && (
        <p className="flash" role="status">
          <Icon name="checkCircle" size={18} />
          {flash}
        </p>
      )}
      <PrivacyNote icon="info">
        Estas apólices estão guardadas só neste navegador. Em outro navegador, aparelho ou janela
        anônima fechada, elas não aparecem. <a href={paths.privacy}>Privacidade e dados</a>
      </PrivacyNote>
      <SearchField
        label="Buscar apólices"
        placeholder="Buscar por seguradora, número ou arquivo"
        value={query}
        onChange={setQuery}
      />

      {state.status === 'loading' && <LoadingState label="Carregando apólices…" />}
      {state.status === 'error' && <ErrorState message={state.message} onRetry={state.reload} />}
      {state.status === 'success' && (
        <>
          <FilterChips
            label="Filtrar por status"
            value={filter}
            onChange={setFilter}
            options={FILTERS.map((option) => ({
              ...option,
              count: state.data.filter(
                (policy) => option.value === 'ALL' || policy.status === option.value,
              ).length,
            }))}
          />
          <PolicyList
            policies={state.data.filter((policy) => matches(policy, filter, query))}
            onDeleted={(policy) => setFlashMessage(`Apólice ${policy.insurer} excluída.`)}
          />
        </>
      )}
    </div>
  );
}

type PolicyListProps = {
  policies: PolicySummary[];
  onDeleted: (policy: PolicySummary) => void;
};

function PolicyList({ policies, onDeleted }: PolicyListProps) {
  if (!policies.length) {
    return (
      <EmptyState
        icon="policy"
        illustration="empty"
        title="Nenhuma apólice encontrada"
        text="Ajuste a busca ou adicione uma apólice com seus documentos. Apólices enviadas em outro navegador não aparecem aqui."
        action={
          <a className="btn btn--secondary" href={paths.newPolicy}>
            Adicionar apólice
          </a>
        }
      />
    );
  }
  return (
    <div className="stack">
      {policies.map((policy) => (
        <PolicyCard key={policy.id} policy={policy} onDeleted={onDeleted} />
      ))}
    </div>
  );
}
