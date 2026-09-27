import { useRef, useState, type KeyboardEvent } from 'react';
import { paths } from '../../app/router';
import { PageHeader } from '../../components/PageHeader';
import { ErrorState, LoadingState } from '../../components/StateViews';
import { clauseApi } from '../../services/api/clause-api';
import { formatDateTime } from '../../shared/format';
import { POLICY_SLOT_LABELS } from '../../shared/labels';
import { useApiData } from '../../shared/useApiData';
import type { ComparisonResult, ComparisonStatus } from '../../types/domain';
import { ConceptsPanel } from './ConceptsPanel';
import { ProfilesPanel } from './ProfilesPanel';
import { QualityPanel } from './QualityPanel';
import { SummaryPanel } from './SummaryPanel';

type Tab = 'summary' | 'concepts' | 'profiles' | 'quality';

const TABS: { id: Tab; label: string }[] = [
  { id: 'summary', label: 'Resumo' },
  { id: 'concepts', label: 'Conceitos' },
  { id: 'profiles', label: 'Perfis' },
  { id: 'quality', label: 'Qualidade' },
];

const FINAL_STATUSES: ComparisonStatus[] = ['COMPLETED', 'PARTIAL', 'FAILED'];
const POLL_MS = 3000;

const PROGRESS_LABELS: Partial<Record<ComparisonStatus, string>> = {
  REQUESTED: 'Comparação solicitada…',
  DETERMINISTIC_COMPLETED: 'Fatos comparados. Avaliando conceitos…',
  ASSESSING: 'Avaliando conceitos com IA…',
  SCORED: 'Pontuação calculada. Gerando resumo executivo…',
  SUMMARIZING: 'Gerando resumo executivo…',
};

export function ComparisonResultPage({ comparisonId }: { comparisonId: string }) {
  const state = useApiData(
    `comparison:${comparisonId}`,
    () => clauseApi.getComparison(comparisonId),
    { pollMs: POLL_MS, shouldPoll: (comparison) => !FINAL_STATUSES.includes(comparison.status) },
  );
  const back = { href: paths.history, label: 'Histórico' };

  if (state.status === 'loading') return <LoadingState label="Carregando comparação…" />;
  if (state.status === 'error') {
    return (
      <div className="page">
        <PageHeader title="Comparação" back={back} />
        <ErrorState message={state.message} onRetry={state.reload} />
      </div>
    );
  }
  const comparison = state.data;
  if (comparison.status === 'FAILED') {
    return (
      <div className="page">
        <PageHeader title="Comparação" back={back} />
        <ErrorState
          message={comparison.failure?.message ?? 'A comparação falhou.'}
          onRetry={state.reload}
        />
      </div>
    );
  }
  if (!FINAL_STATUSES.includes(comparison.status)) {
    return (
      <div className="page">
        <PageHeader title="Comparação" back={back} />
        <LoadingState label={PROGRESS_LABELS[comparison.status] ?? 'Processando comparação…'} />
      </div>
    );
  }
  return <ComparisonView comparison={comparison} back={back} />;
}

function ComparisonView({
  comparison,
  back,
}: {
  comparison: ComparisonResult;
  back: { href: string; label: string };
}) {
  const [tab, setTab] = useState<Tab>('summary');
  const tabRefs = useRef<Record<Tab, HTMLButtonElement | null>>({
    summary: null,
    concepts: null,
    profiles: null,
    quality: null,
  });

  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return;
    const index = TABS.findIndex((item) => item.id === tab);
    const next =
      TABS[(index + (event.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length].id;
    setTab(next);
    tabRefs.current[next]?.focus();
  };

  const title = `${comparison.policyA.insurer.replace('Seguradora ', '')} × ${comparison.policyB.insurer.replace('Seguradora ', '')}`;

  return (
    <div className="page">
      <PageHeader
        title={title}
        subtitle={`Comparação de ${formatDateTime(comparison.createdAt)}`}
        back={back}
      />

      <dl className="legend-slots">
        <div className="legend-slots__item legend-slots__item--a">
          <dt>{POLICY_SLOT_LABELS.A}</dt>
          <dd>
            <a href={paths.policy(comparison.policyA.id)}>{comparison.policyA.insurer}</a>
          </dd>
        </div>
        <div className="legend-slots__item legend-slots__item--b">
          <dt>{POLICY_SLOT_LABELS.B}</dt>
          <dd>
            <a href={paths.policy(comparison.policyB.id)}>{comparison.policyB.insurer}</a>
          </dd>
        </div>
      </dl>

      <div className="tabs" role="tablist" aria-label="Seções do resultado" onKeyDown={onKeyDown}>
        {TABS.map((item) => (
          <button
            key={item.id}
            ref={(element) => {
              tabRefs.current[item.id] = element;
            }}
            type="button"
            role="tab"
            id={`tab-${item.id}`}
            aria-selected={tab === item.id}
            aria-controls={`panel-${item.id}`}
            tabIndex={tab === item.id ? 0 : -1}
            className="tabs__tab"
            onClick={() => setTab(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`} className="tab-panel">
        {tab === 'summary' && <SummaryPanel comparison={comparison} />}
        {tab === 'concepts' && <ConceptsPanel comparison={comparison} />}
        {tab === 'profiles' && <ProfilesPanel comparison={comparison} />}
        {tab === 'quality' && <QualityPanel comparison={comparison} />}
      </div>
    </div>
  );
}
