import { paths } from '../../app/router';
import { BrokerNotice } from '../../components/BrokerNotice';
import { Icon } from '../../components/Icon';
import { Illustration } from '../../components/Illustration';
import type { PolicySummary } from '../../types/domain';

/** Estado de sucesso do fim do envio e do processamento. */
export function PolicyReadyScreen({ policy }: { policy: PolicySummary }) {
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
        <a className="btn btn--ghost btn--block" href={paths.policies}>
          Voltar para Apólices
        </a>
      </div>
    </section>
  );
}
