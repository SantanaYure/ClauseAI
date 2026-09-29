import { useState, type FormEvent } from 'react';
import { navigate, paths } from '../../app/router';
import { Badge } from '../../components/Badge';
import { BrokerNotice } from '../../components/BrokerNotice';
import { Icon } from '../../components/Icon';
import { PageHeader } from '../../components/PageHeader';
import { EmptyState, ErrorState, LoadingState } from '../../components/StateViews';
import { COMPARABLE_POLICY_STATUSES, clauseApi } from '../../services/api/clause-api';
import {
  DOCUMENT_TYPE_LABELS,
  POLICY_SLOT_LABELS,
  POLICY_STATUS_LABELS,
  PROFILE_LABELS,
} from '../../shared/labels';
import { policyStatusTone } from '../../shared/tones';
import { hasBusyPolicy, PROCESSING_POLL_MS } from '../../shared/processing';
import { useApiData } from '../../shared/useApiData';
import type { PolicySummary, RiskProfile } from '../../types/domain';
import { PROFILE_DESCRIPTIONS, PROFILE_ORDER } from './profiles';

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
        subtitle="Escolha exatamente duas apólices. Os mesmos conceitos, critérios e pesos valem para as duas."
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
  const comparable = policies.filter((policy) =>
    COMPARABLE_POLICY_STATUSES.includes(policy.status),
  );
  const unavailable = policies.filter(
    (policy) => !COMPARABLE_POLICY_STATUSES.includes(policy.status),
  );
  const validInitial = (id?: string) =>
    comparable.some((policy) => policy.id === id) ? (id ?? '') : '';

  const [policyAId, setPolicyAId] = useState(validInitial(initialA));
  const [policyBId, setPolicyBId] = useState(validInitial(initialB));
  const [profile, setProfile] = useState<RiskProfile>('BASE');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (comparable.length < 2) {
    return (
      <EmptyState
        icon="policy"
        illustration="compare"
        title="São necessárias duas apólices processadas"
        text="Adicione outra apólice e aguarde o processamento para comparar."
        action={
          <a className="btn btn--primary" href={paths.newPolicy}>
            Adicionar apólice
          </a>
        }
      />
    );
  }

  const samePolicy = policyAId !== '' && policyAId === policyBId;
  const canSubmit = policyAId !== '' && policyBId !== '' && !samePolicy && !submitting;

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
      <PolicySlot
        slot="A"
        value={policyAId}
        onChange={setPolicyAId}
        policies={comparable}
        disabledId={policyBId}
      />
      <div className="versus" aria-hidden="true">
        ×
      </div>
      <PolicySlot
        slot="B"
        value={policyBId}
        onChange={setPolicyBId}
        policies={comparable}
        disabledId={policyAId}
      />

      {samePolicy && (
        <p className="field-error" role="alert">
          Escolha duas apólices diferentes.
        </p>
      )}

      {unavailable.length > 0 && (
        <p className="muted-text">
          <Icon name="info" size={16} /> Indisponíveis para comparação:{' '}
          {unavailable
            .map(
              (policy) =>
                `${policy.insurer} (${POLICY_STATUS_LABELS[policy.status].toLowerCase()})`,
            )
            .join(', ')}
          .
        </p>
      )}

      <fieldset className="card profile-picker">
        <legend className="section-title">Perfil de risco em destaque</legend>
        <p className="muted-text">
          Todos os perfis são calculados. O escolhido abre em destaque; os pesos-base nunca são
          alterados.
        </p>
        <div className="radio-list">
          {PROFILE_ORDER.map((option) => (
            <label key={option} className="radio-card">
              <input
                type="radio"
                name="profile"
                value={option}
                checked={profile === option}
                onChange={() => setProfile(option)}
              />
              <span>
                <strong>{PROFILE_LABELS[option]}</strong>
                <small>{PROFILE_DESCRIPTIONS[option]}</small>
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}

      <button type="submit" className="btn btn--primary btn--block" disabled={!canSubmit}>
        <Icon name="scale" size={20} />
        {submitting ? 'Comparando…' : 'Comparar apólices'}
      </button>
      <a className="btn btn--ghost btn--block" href={paths.newPolicy}>
        <Icon name="plus" size={18} />
        Adicionar outra apólice
      </a>
    </form>
  );
}

type PolicySlotProps = {
  slot: 'A' | 'B';
  value: string;
  onChange: (id: string) => void;
  policies: PolicySummary[];
  disabledId: string;
};

function PolicySlot({ slot, value, onChange, policies, disabledId }: PolicySlotProps) {
  const selected = policies.find((policy) => policy.id === value);
  const selectId = `policy-${slot}`;
  return (
    <section className={`card slot slot--${slot.toLowerCase()}`}>
      <label htmlFor={selectId} className="slot__label">
        {POLICY_SLOT_LABELS[slot]}
      </label>
      <select id={selectId} value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Selecione uma apólice</option>
        {policies.map((policy) => (
          <option key={policy.id} value={policy.id} disabled={policy.id === disabledId}>
            {policy.insurer} — {policy.name}
          </option>
        ))}
      </select>
      {selected && (
        <div className="slot__details">
          <Badge tone={policyStatusTone(selected.status)}>
            {POLICY_STATUS_LABELS[selected.status]}
          </Badge>
          <p className="tag-row">
            {selected.documents.map((document) => (
              <span key={document.id} className="tag">
                {DOCUMENT_TYPE_LABELS[document.type]}
              </span>
            ))}
          </p>
          {selected.alerts.map((alert) => (
            <BrokerNotice key={alert} reason={alert} compact />
          ))}
        </div>
      )}
    </section>
  );
}
