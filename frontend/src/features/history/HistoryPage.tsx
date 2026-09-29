import { useState } from 'react';
import { navigate, paths } from '../../app/router';
import { Badge } from '../../components/Badge';
import { FilterChips } from '../../components/FilterChips';
import { Icon } from '../../components/Icon';
import { PageHeader } from '../../components/PageHeader';
import { EmptyState, ErrorState, LoadingState } from '../../components/StateViews';
import { clauseApi } from '../../services/api/clause-api';
import { formatDateTime, formatPercent } from '../../shared/format';
import { DECISION_MODE_LABELS, POLICY_SLOT_LABELS } from '../../shared/labels';
import { hasBusyComparison, isComparisonBusy, PROCESSING_POLL_MS } from '../../shared/processing';
import { useApiData } from '../../shared/useApiData';
import type { ComparisonListItem } from '../../types/domain';

type Filter = 'ALL' | 'TECHNICAL' | 'CONDITIONED' | 'FAILED';

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'ALL', label: 'Todas' },
  { value: 'TECHNICAL', label: 'Técnicas' },
  { value: 'CONDITIONED', label: 'Condicionadas' },
  { value: 'FAILED', label: 'Falharam' },
];

function matchesFilter(item: ComparisonListItem, filter: Filter): boolean {
  if (filter === 'ALL') return true;
  if (filter === 'FAILED') return item.status === 'FAILED';
  return item.decisionMode === filter;
}

export function HistoryPage() {
  const state = useApiData('comparisons', () => clauseApi.listComparisons(), {
    pollMs: PROCESSING_POLL_MS,
    shouldPoll: hasBusyComparison,
  });
  const [filter, setFilter] = useState<Filter>('ALL');

  return (
    <div className="page">
      <PageHeader
        title="Histórico"
        subtitle="Comparações anteriores, com os scores e o tipo de resultado."
        action={
          <a className="btn btn--primary btn--compact" href={paths.compare()}>
            <Icon name="plus" size={18} />
            Nova
          </a>
        }
      />
      {state.status === 'loading' && <LoadingState label="Carregando histórico…" />}
      {state.status === 'error' && <ErrorState message={state.message} onRetry={state.reload} />}
      {state.status === 'success' && (
        <>
          <FilterChips
            label="Filtrar comparações"
            value={filter}
            onChange={setFilter}
            options={FILTERS.map((option) => ({
              ...option,
              count: state.data.filter((item) => matchesFilter(item, option.value)).length,
            }))}
          />
          <HistoryList items={state.data.filter((item) => matchesFilter(item, filter))} />
        </>
      )}
    </div>
  );
}

function HistoryList({ items }: { items: ComparisonListItem[] }) {
  if (!items.length) {
    return (
      <EmptyState
        icon="clock"
        title="Nenhuma comparação aqui"
        text="As comparações que você fizer aparecem nesta lista."
        action={
          <a className="btn btn--primary" href={paths.compare()}>
            Nova comparação
          </a>
        }
      />
    );
  }
  return (
    <ul className="stack">
      {items.map((item) => (
        <HistoryCard key={item.id} item={item} />
      ))}
    </ul>
  );
}

function HistoryCard({ item }: { item: ComparisonListItem }) {
  const [retrying, setRetrying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const failed = item.status === 'FAILED';
  const title = `${item.policyA.insurer.replace('Seguradora ', '')} × ${item.policyB.insurer.replace('Seguradora ', '')}`;

  const retry = async () => {
    setRetrying(true);
    setError(null);
    try {
      const { id } = await clauseApi.createComparison({
        policyAId: item.policyA.id,
        policyBId: item.policyB.id,
        selectedProfile: 'BASE',
      });
      navigate(paths.comparison(id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Não foi possível repetir a comparação.');
      setRetrying(false);
    }
  };

  return (
    <li className="card history-card">
      <div className="occurrence__header">
        <div>
          <h2 className="history-card__title">
            {failed ? title : <a href={paths.comparison(item.id)}>{title}</a>}
          </h2>
          <p className="muted-text">{formatDateTime(item.createdAt)}</p>
        </div>
        {failed ? (
          <Badge tone="danger" icon="alert">
            Falhou
          </Badge>
        ) : isComparisonBusy(item.status) ? (
          <Badge tone="info" busy>
            Em processamento
          </Badge>
        ) : (
          item.decisionMode && (
            <Badge tone={item.decisionMode === 'CONDITIONED' ? 'medium' : 'success'}>
              {DECISION_MODE_LABELS[item.decisionMode]}
            </Badge>
          )
        )}
      </div>

      {failed ? (
        <>
          <p className="muted-text">{item.failureReason}</p>
          {error && (
            <p className="field-error" role="alert">
              {error}
            </p>
          )}
          <button type="button" className="btn btn--secondary" onClick={retry} disabled={retrying}>
            <Icon name="refresh" size={18} />
            {retrying ? 'Comparando…' : 'Tentar novamente'}
          </button>
        </>
      ) : (
        <>
          <dl className="history-card__scores">
            <div>
              <dt>{POLICY_SLOT_LABELS.A}</dt>
              <dd>
                {item.policyA.insurer}{' '}
                <strong>{item.adherenceA !== null ? formatPercent(item.adherenceA) : '—'}</strong>
              </dd>
            </div>
            <div>
              <dt>{POLICY_SLOT_LABELS.B}</dt>
              <dd>
                {item.policyB.insurer}{' '}
                <strong>{item.adherenceB !== null ? formatPercent(item.adherenceB) : '—'}</strong>
              </dd>
            </div>
          </dl>
          <a className="btn btn--ghost" href={paths.comparison(item.id)}>
            Abrir resultado
            <Icon name="chevronRight" size={18} />
          </a>
        </>
      )}
    </li>
  );
}
