import { Badge } from '../../components/Badge';
import { BrokerNotice } from '../../components/BrokerNotice';
import {
  DOCUMENT_TYPE_LABELS,
  POLICY_SLOT_LABELS,
  POLICY_STATUS_LABELS,
} from '../../shared/labels';
import { unavailableReason } from '../../shared/compareSelection';
import { policyStatusIcon, policyStatusTone } from '../../shared/tones';
import type { PolicySummary } from '../../types/domain';

type PolicySlotProps = {
  slot: 'A' | 'B';
  value: string;
  onChange: (id: string) => void;
  policies: PolicySummary[];
};

/** Área grande de escolha de uma das duas apólices; a letra do slot é sempre visível. */
export function PolicySlot({ slot, value, onChange, policies }: PolicySlotProps) {
  const selected = policies.find((policy) => policy.id === value);
  const selectId = `policy-${slot}`;
  return (
    <section className={`card slot slot--${slot.toLowerCase()}`}>
      <label htmlFor={selectId} className="slot__label">
        <span className="slot__letter" aria-hidden="true">
          {slot}
        </span>
        {POLICY_SLOT_LABELS[slot]}
      </label>
      <select id={selectId} value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Selecione uma apólice</option>
        {policies.map((policy) => {
          const reason = unavailableReason(policy);
          return (
            <option key={policy.id} value={policy.id} disabled={reason !== null}>
              {policy.insurer} — {policy.name}
              {policy.documents[0] ? ` · ${policy.documents[0].filename}` : ''}
              {reason ? ` (${reason})` : ''}
            </option>
          );
        })}
      </select>
      {selected ? (
        <div className="slot__details">
          <Badge tone={policyStatusTone(selected.status)} icon={policyStatusIcon(selected.status)}>
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
      ) : (
        <p className="muted-text">Escolha a apólice que entra como {POLICY_SLOT_LABELS[slot]}.</p>
      )}
    </section>
  );
}
