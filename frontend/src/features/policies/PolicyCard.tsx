import { paths } from '../../app/router';
import { Badge } from '../../components/Badge';
import { Icon } from '../../components/Icon';
import { Spinner } from '../../components/Spinner';
import { COMPARABLE_POLICY_STATUSES } from '../../services/api/clause-api';
import {
  DOCUMENT_STATUS_LABELS,
  DOCUMENT_TYPE_LABELS,
  POLICY_STATUS_LABELS,
} from '../../shared/labels';
import { describeProcessing, isDocumentBusy, isPolicyBusy } from '../../shared/processing';
import { documentStatusTone, policyStatusTone } from '../../shared/tones';
import type { PolicySummary } from '../../types/domain';

type PolicyCardProps = {
  policy: PolicySummary;
};

export function PolicyCard({ policy }: PolicyCardProps) {
  const comparable = COMPARABLE_POLICY_STATUSES.includes(policy.status);
  return (
    <article className="card policy-card" aria-labelledby={`policy-${policy.id}`}>
      <div className="policy-card__header">
        <div>
          <h2 id={`policy-${policy.id}`} className="policy-card__title">
            <a href={paths.policy(policy.id)}>{policy.insurer}</a>
          </h2>
          <p className="muted-text">
            {policy.name}
            {policy.number ? ` · nº ${policy.number}` : ''}
          </p>
        </div>
        <Badge tone={policyStatusTone(policy.status)} busy={isPolicyBusy(policy.status)}>
          {POLICY_STATUS_LABELS[policy.status]}
        </Badge>
      </div>

      <ul className="doc-list" aria-label={`Documentos de ${policy.insurer}`}>
        {policy.documents.map((document) => (
          <li key={document.id} className="doc-list__item">
            <Icon name="file" size={18} />
            <span className="doc-list__name">
              {document.filename}
              <small>
                {DOCUMENT_TYPE_LABELS[document.type]}
                {document.pages ? ` · ${document.pages} p.` : ''}
              </small>
            </span>
            <Badge
              tone={documentStatusTone(document.status)}
              busy={isDocumentBusy(document.status)}
            >
              {DOCUMENT_STATUS_LABELS[document.status]}
            </Badge>
          </li>
        ))}
      </ul>

      {isPolicyBusy(policy.status) && (
        <p className="processing-note" role="status">
          <Spinner size="sm" />
          {describeProcessing(policy.documents)}
        </p>
      )}

      {policy.alerts.length > 0 && (
        <p className="inline-alert">
          <Icon name="alert" size={16} />
          {policy.alerts[0]}
        </p>
      )}

      <div className="policy-card__actions">
        <a className="btn btn--ghost" href={paths.policy(policy.id)}>
          Ver evidências
        </a>
        {comparable && (
          <a className="btn btn--secondary" href={paths.compare(policy.id)}>
            <Icon name="scale" size={18} />
            Comparar
          </a>
        )}
      </div>
    </article>
  );
}
