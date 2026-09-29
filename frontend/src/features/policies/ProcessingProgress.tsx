import { paths } from '../../app/router';
import { Badge } from '../../components/Badge';
import { BrokerNotice } from '../../components/BrokerNotice';
import { Icon } from '../../components/Icon';
import { Illustration } from '../../components/Illustration';
import { Spinner } from '../../components/Spinner';
import { ErrorState, LoadingState } from '../../components/StateViews';
import { clauseApi } from '../../services/api/clause-api';
import { DOCUMENT_STATUS_LABELS, DOCUMENT_TYPE_LABELS } from '../../shared/labels';
import { describeProcessing, isDocumentBusy } from '../../shared/processing';
import { documentStatusTone } from '../../shared/tones';
import { useApiData } from '../../shared/useApiData';
import type { DocumentStatus } from '../../types/domain';
import { CancelExtractionButton } from './CancelExtractionButton';

const STEPS: DocumentStatus[] = ['UPLOADED', 'PROCESSING', 'EXTRACTING', 'VALIDATING', 'COMPLETED'];

const POLL_MS = 3000;

/** Acompanha o processamento assíncrono (SPEC-003): consulta o status até um estado final. */
export function ProcessingProgress({ policyId }: { policyId: string }) {
  const state = useApiData(`policy:${policyId}`, () => clauseApi.getPolicy(policyId), {
    pollMs: POLL_MS,
    shouldPoll: (policy) => policy.status === 'PROCESSING',
  });

  if (state.status === 'loading') return <LoadingState label="Consultando status…" />;
  if (state.status === 'error')
    return <ErrorState message={state.message} onRetry={state.reload} />;

  const policy = state.data;
  const done = policy.status !== 'PROCESSING';
  const cancelled = policy.status === 'CANCELLED';

  return (
    <div className="stack">
      <Illustration name={done && !cancelled ? 'success' : 'search'} className="processing-art" />
      <p className="processing-note processing-note--block" role="status" aria-live="polite">
        {done ? (
          cancelled ? (
            <>
              <Icon name="alert" size={20} />
              <span>
                <strong>Processamento cancelado.</strong>A extração foi interrompida pelo usuário.
              </span>
            </>
          ) : (
            <>
              <Icon name="checkCircle" size={20} />
              <span>
                <strong>Processamento concluído.</strong>
              </span>
            </>
          )
        ) : (
          <>
            <Spinner />
            <span>
              <strong>{describeProcessing(policy.documents)}</strong>
              Você pode sair desta tela: o processamento continua e o status aparece em Apólices.
            </span>
          </>
        )}
      </p>

      {!done && (
        <CancelExtractionButton
          policyId={policy.id}
          policyName={policy.name}
          variant="block"
          onCancelled={state.reload}
        />
      )}

      <ul className="stack">
        {policy.documents.map((document) => {
          const current = STEPS.indexOf(document.status);
          return (
            <li key={document.id} className="card">
              <div className="doc-card__header">
                <Icon name="file" size={20} />
                <strong className="doc-card__name">
                  {document.filename}
                  <small>{DOCUMENT_TYPE_LABELS[document.type]}</small>
                </strong>
                <Badge
                  tone={documentStatusTone(document.status)}
                  busy={isDocumentBusy(document.status)}
                >
                  {DOCUMENT_STATUS_LABELS[document.status]}
                </Badge>
              </div>
              <ol className="progress-steps" aria-label={`Etapas de ${document.filename}`}>
                {STEPS.map((step, index) => (
                  <li
                    key={step}
                    className={`progress-steps__item${index <= current ? ' progress-steps__item--done' : ''}`}
                    aria-current={index === current ? 'step' : undefined}
                  >
                    {DOCUMENT_STATUS_LABELS[step]}
                  </li>
                ))}
              </ol>
            </li>
          );
        })}
      </ul>

      {done && (
        <>
          {policy.alerts.map((alert) => (
            <BrokerNotice key={alert} reason={alert} />
          ))}
          <a className="btn btn--primary btn--block" href={paths.policy(policy.id)}>
            Ver detalhes da apólice
          </a>
          <a className="btn btn--secondary btn--block" href={paths.policies}>
            Voltar para Apólices
          </a>
        </>
      )}
    </div>
  );
}
