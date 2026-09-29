import { paths } from '../../app/router';
import { BrokerNotice } from '../../components/BrokerNotice';
import { Icon } from '../../components/Icon';
import { Illustration } from '../../components/Illustration';
import type { PolicySummary } from '../../types/domain';

/** Estado de sucesso do fim do envio e do processamento. */
type PolicyReadyScreenProps = {
  policy: PolicySummary;
  onRestart: () => void;
};

export function PolicyReadyScreen({ policy, onRestart }: PolicyReadyScreenProps) {
  return (
    <section className="success-screen" aria-labelledby="success-title" aria-live="polite">
      <Illustration name="success" className="success-screen__art" />
      <h2 id="success-title" className="success-screen__title">
        Apólice pronta para comparar
      </h2>
      <p className="muted-text">
        {policy.insurer} · {policy.name}. Os documentos foram lidos e conferidos.
      </p>
      {policy.alerts.map((alert) => (
        <BrokerNotice key={alert} reason={alert} />
      ))}
      <div className="success-screen__actions">
        <a className="btn btn--primary btn--block" href={paths.compare(policy.id)}>
          <Icon name="scale" size={20} />
          Comparar com outra apólice
        </a>
        <a className="btn btn--secondary btn--block" href={paths.policy(policy.id)}>
          Ver detalhes da apólice
        </a>
        <button type="button" className="btn btn--ghost btn--block" onClick={onRestart}>
          <Icon name="plus" size={18} />
          Adicionar outra apólice
        </button>
        <a className="btn btn--ghost btn--block" href={paths.policies}>
          Voltar para Apólices
        </a>
      </div>
    </section>
  );
}
