import { Badge } from '../../components/Badge';
import { Icon } from '../../components/Icon';
import { DOCUMENT_STATUS_LABELS, DOCUMENT_TYPE_LABELS } from '../../shared/labels';
import { PROCESS_STEPS, documentStepIndex, isDocumentBusy } from '../../shared/processing';
import { documentStatusIcon, documentStatusTone } from '../../shared/tones';
import type { PolicyDocument } from '../../types/domain';

const FALLBACK_FAILURE = 'Não foi possível ler este documento.';

type ProcessingDocumentRowProps = {
  document: PolicyDocument;
  onResend?: () => void;
};

export function ProcessingDocumentRow({ document, onResend }: ProcessingDocumentRowProps) {
  const failed = document.status === 'FAILED';
  return (
    <li className="card">
      <div className="doc-card__header">
        <Icon name="file" size={20} />
        <strong className="doc-card__name">
          {document.filename}
          <small>{DOCUMENT_TYPE_LABELS[document.type]}</small>
        </strong>
        <Badge
          tone={documentStatusTone(document.status)}
          busy={isDocumentBusy(document.status)}
          icon={documentStatusIcon(document.status)}
        >
          {isDocumentBusy(document.status)
            ? PROCESS_STEPS[documentStepIndex(document.status)]
            : DOCUMENT_STATUS_LABELS[document.status]}
        </Badge>
      </div>
      {failed && (
        <div className="doc-failure">
          <p className="field-error" role="alert">
            <Icon name="alert" size={16} />
            {document.failure ?? FALLBACK_FAILURE}
          </p>
          {onResend && (
            <button type="button" className="btn btn--secondary btn--compact" onClick={onResend}>
              <Icon name="refresh" size={16} />
              Reenviar
            </button>
          )}
        </div>
      )}
    </li>
  );
}
