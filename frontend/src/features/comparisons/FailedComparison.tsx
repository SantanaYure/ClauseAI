import { BrokerNotice } from '../../components/BrokerNotice';
import { Icon } from '../../components/Icon';
import { useRecreateComparison } from '../../shared/useRecreateComparison';
import type { ComparisonResult } from '../../types/domain';

/** Comparação que falhou: mostra o motivo e cria uma nova comparação com as mesmas apólices. */
export function FailedComparison({ comparison }: { comparison: ComparisonResult }) {
  const { recreate, pending, error } = useRecreateComparison(comparison);
  return (
    <div className="stack">
      <div className="state-view state-view--error" role="alert">
        <Icon name="alert" size={28} />
        <p className="state-view__title">A comparação não foi concluída</p>
        <p>{comparison.failure?.message ?? 'A comparação falhou.'}</p>
        <button type="button" className="btn btn--primary" disabled={pending} onClick={recreate}>
          <Icon name="refresh" size={18} />
          {pending ? 'Criando nova comparação…' : 'Tentar de novo'}
        </button>
      </div>
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
      <BrokerNotice />
    </div>
  );
}
