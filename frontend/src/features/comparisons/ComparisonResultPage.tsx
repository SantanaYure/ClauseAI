import { paths } from '../../app/router';
import { BrokerNotice } from '../../components/BrokerNotice';
import { ExpiryNote } from '../../components/ExpiryNote';
import { PageHeader } from '../../components/PageHeader';
import { ErrorState, LoadingState } from '../../components/StateViews';
import { clauseApi } from '../../services/api/clause-api';
import { formatDateTime } from '../../shared/format';
import { POLICY_SLOT_LABELS } from '../../shared/labels';
import { DocumentKindsContext } from '../../shared/evidenceLocation';
import { useApiData } from '../../shared/useApiData';
import { useComparisonDocumentKinds } from '../../shared/useComparisonDocumentKinds';
import type { ComparisonResult, ComparisonStatus } from '../../types/domain';
import { CalculationDetails } from './CalculationDetails';
import { FailedComparison } from './FailedComparison';
import { SummaryPanel } from './SummaryPanel';

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
        <BrokerNotice />
      </div>
    );
  }
  const comparison = state.data;
  if (comparison.status === 'FAILED') {
    return (
      <div className="page">
        <PageHeader title="Comparação" back={back} />
        <FailedComparison comparison={comparison} />
      </div>
    );
  }
  if (!FINAL_STATUSES.includes(comparison.status)) {
    return (
      <div className="page">
        <PageHeader title="Comparação" back={back} />
        <LoadingState label={PROGRESS_LABELS[comparison.status] ?? 'Processando comparação…'} />
        <BrokerNotice />
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
  const kinds = useComparisonDocumentKinds(comparison.policyA.id, comparison.policyB.id);
  const title = `${comparison.policyA.insurer.replace('Seguradora ', '')} × ${comparison.policyB.insurer.replace('Seguradora ', '')}`;

  return (
    <DocumentKindsContext.Provider value={kinds}>
      <div className="page">
        <PageHeader
          title={title}
          subtitle={`Comparação de ${formatDateTime(comparison.createdAt)}`}
          back={back}
        />
        <ExpiryNote
          expiresAt={comparison.expiresAt}
          format={(phrase) => `Esta comparação expira ${phrase}.`}
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

        <div className="stack">
          <SummaryPanel comparison={comparison} />
          <CalculationDetails comparison={comparison} />
          <BrokerNotice />
        </div>
      </div>
    </DocumentKindsContext.Provider>
  );
}
