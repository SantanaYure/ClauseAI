import { paths } from '../../app/router';
import { BrokerNotice } from '../../components/BrokerNotice';
import { Icon } from '../../components/Icon';
import { Illustration } from '../../components/Illustration';
import { ProcessSteps } from '../../components/ProcessSteps';
import { Spinner } from '../../components/Spinner';
import { ErrorState, LoadingState } from '../../components/StateViews';
import { clauseApi } from '../../services/api/clause-api';
import { policyStepIndex } from '../../shared/processing';
import { useApiData } from '../../shared/useApiData';
import type { PolicySummary } from '../../types/domain';
import { CancelExtractionButton } from './CancelExtractionButton';
import { PolicyReadyScreen } from './PolicyReadyScreen';
import { ProcessingDocumentRow } from './ProcessingDocumentRow';

const POLL_MS = 3000;

/** Acompanha o processamento assíncrono (SPEC-003): consulta o status até um estado final. */
type ProcessingProgressProps = {
  policyId: string;
  /** Volta à tela de envio para mandar de novo ou adicionar outra apólice. */
  onRestart: () => void;
};

export function ProcessingProgress({ policyId, onRestart }: ProcessingProgressProps) {
  const state = useApiData(`policy:${policyId}`, () => clauseApi.getPolicy(policyId), {
    pollMs: POLL_MS,
    shouldPoll: (policy) => policy.status === 'PROCESSING',
  });

  if (state.status === 'loading') return <LoadingState label="Consultando status…" />;
  if (state.status === 'error')
    return <ErrorState message={state.message} onRetry={state.reload} />;

  const policy = state.data;
  if (policy.status === 'READY' || policy.status === 'ATTENTION') {
    return <PolicyReadyScreen policy={policy} onRestart={onRestart} />;
  }
  if (policy.status === 'PROCESSING') {
    return <InProgress policy={policy} offline={state.refreshFailed} onCancelled={state.reload} />;
  }
  return <Stopped policy={policy} onRestart={onRestart} />;
}

type InProgressProps = {
  policy: PolicySummary;
  offline: boolean;
  onCancelled: () => void;
};

function InProgress({ policy, offline, onCancelled }: InProgressProps) {
  return (
    <div className="stack">
      <Illustration name="search" className="processing-art" />
      <ProcessSteps current={policyStepIndex(policy.documents)} />
      <div className="processing-note processing-note--block" role="status" aria-live="polite">
        {offline ? <Icon name="alert" size={20} /> : <Spinner />}
        <span>
          {offline ? (
            <strong>Sem conexão, tentando de novo…</strong>
          ) : (
            <strong>Estamos lendo sua apólice. Isso pode levar alguns minutos.</strong>
          )}
          Você pode sair desta tela: o processamento continua e o status aparece em Apólices.
        </span>
      </div>
      <CancelExtractionButton
        policyId={policy.id}
        policyName={policy.name}
        variant="block"
        onCancelled={onCancelled}
      />
      <ul className="stack" aria-label="Documentos enviados">
        {policy.documents.map((document) => (
          <ProcessingDocumentRow key={document.id} document={document} />
        ))}
      </ul>
    </div>
  );
}

function Stopped({ policy, onRestart }: { policy: PolicySummary; onRestart: () => void }) {
  const cancelled = policy.status === 'CANCELLED';
  return (
    <div className="stack">
      <Illustration name="search" className="processing-art" />
      <p className="processing-note processing-note--block" role="status" aria-live="polite">
        <Icon name="alert" size={20} />
        <span>
          <strong>{cancelled ? 'Processamento cancelado.' : 'Não foi possível processar.'}</strong>
          {cancelled
            ? 'A extração foi interrompida pelo usuário.'
            : 'Veja abaixo o motivo de cada documento.'}
        </span>
      </p>
      <ul className="stack" aria-label="Documentos enviados">
        {policy.documents.map((document) => (
          <ProcessingDocumentRow key={document.id} document={document} onResend={onRestart} />
        ))}
      </ul>
      {policy.alerts.map((alert) => (
        <BrokerNotice key={alert} reason={alert} />
      ))}
      <button type="button" className="btn btn--primary btn--block" onClick={onRestart}>
        <Icon name="upload" size={20} />
        Reenviar documentos
      </button>
      <a className="btn btn--secondary btn--block" href={paths.policies}>
        Voltar para Apólices
      </a>
    </div>
  );
}
