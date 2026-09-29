import { useState, type FormEvent } from 'react';
import { navigate, paths } from '../../app/router';
import { Icon } from '../../components/Icon';
import { PageHeader } from '../../components/PageHeader';
import { EmptyState, ErrorState, LoadingState } from '../../components/StateViews';
import { clauseApi } from '../../services/api/clause-api';
import { POLICY_STATUS_LABELS } from '../../shared/labels';
import { compareBlocker, isComparable } from '../../shared/compareSelection';
import { hasBusyPolicy, PROCESSING_POLL_MS } from '../../shared/processing';
import { useApiData } from '../../shared/useApiData';
import type { PolicySummary, RiskProfile } from '../../types/domain';
import { AdvancedOptions } from './AdvancedOptions';
import { PolicySlot } from './PolicySlot';

type ComparePageProps = {
  initialA?: string;
  initialB?: string;
};

export function ComparePage({ initialA, initialB }: ComparePageProps) {
  const state = useApiData('policies', () => clauseApi.listPolicies(), {
    pollMs: PROCESSING_POLL_MS,
    shouldPoll: hasBusyPolicy,
  });

  return (
    <div className="page">
      <PageHeader
        title="Comparar apólices"
        subtitle="Escolha duas apólices prontas. Os mesmos conceitos, critérios e pesos valem para as duas."
      />
      {state.status === 'loading' && <LoadingState label="Carregando apólices…" />}
      {state.status === 'error' && <ErrorState message={state.message} onRetry={state.reload} />}
      {state.status === 'success' && (
        <CompareForm policies={state.data} initialA={initialA} initialB={initialB} />
      )}
    </div>
  );
}

type CompareFormProps = ComparePageProps & { policies: PolicySummary[] };

function CompareForm({ policies, initialA, initialB }: CompareFormProps) {
  const comparableCount = policies.filter(isComparable).length;
  const validInitial = (id?: string) =>
    policies.some((policy) => policy.id === id && isComparable(policy)) ? (id ?? '') : '';

  const [policyAId, setPolicyAId] = useState(validInitial(initialA));
  const [policyBId, setPolicyBId] = useState(validInitial(initialB));
  const [profile, setProfile] = useState<RiskProfile>('BASE');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (comparableCount < 2) {
    const reading = policies.filter((policy) => policy.status === 'PROCESSING').length;
    return (
      <EmptyState
        icon="policy"
        illustration="compare"
        title="São necessárias duas apólices processadas"
        text={
          reading > 0
            ? `Há ${reading} ${reading === 1 ? 'apólice sendo lida' : 'apólices sendo lidas'}. Volte em alguns minutos ou adicione outra.`
            : 'Adicione outra apólice e aguarde o processamento para comparar.'
        }
        action={
          <a className="btn btn--primary" href={paths.newPolicy}>
            Adicionar apólice
          </a>
        }
      />
    );
  }

  const blocker = compareBlocker(policyAId, policyBId);
  const samePolicy = policyAId !== '' && policyAId === policyBId;
  const canSubmit = blocker === null && !submitting;
  const busy = policies.filter((policy) => !isComparable(policy));

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      const { id } = await clauseApi.createComparison({
        policyAId,
        policyBId,
        selectedProfile: profile,
      });
      navigate(paths.comparison(id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Não foi possível iniciar a comparação.');
      setSubmitting(false);
    }
  };

  return (
    <form className="stack" onSubmit={onSubmit} noValidate>
      <div className="slots">
        <PolicySlot slot="A" value={policyAId} onChange={setPolicyAId} policies={policies} />
        <div className="versus" aria-hidden="true">
          ×
        </div>
        <PolicySlot slot="B" value={policyBId} onChange={setPolicyBId} policies={policies} />
      </div>

      <div aria-live="polite">
        {samePolicy && (
          <p className="field-error" role="alert">
            <Icon name="alert" size={16} />
            As duas apólices escolhidas são a mesma. Escolha duas apólices diferentes.
          </p>
        )}
      </div>

      {busy.length > 0 && (
        <p className="muted-text">
          <Icon name="info" size={16} /> Indisponíveis para comparação:{' '}
          {busy
            .map(
              (policy) =>
                `${policy.insurer} (${POLICY_STATUS_LABELS[policy.status].toLowerCase()})`,
            )
            .join(', ')}
          .
        </p>
      )}

      <AdvancedOptions profile={profile} onChange={setProfile} />

      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}

      <button
        type="submit"
        className="btn btn--primary btn--block btn--stacked"
        disabled={!canSubmit}
        aria-describedby="compare-hint"
      >
        <span className="btn__row">
          <Icon name="scale" size={20} />
          {submitting ? 'Comparando…' : 'Comparar'}
        </span>
        <span id="compare-hint" className="btn__hint" aria-live="polite">
          {blocker}
        </span>
      </button>
      <a className="btn btn--ghost btn--block" href={paths.newPolicy}>
        <Icon name="plus" size={18} />
        Adicionar outra apólice
      </a>
    </form>
  );
}
