import { COMPARABLE_POLICY_STATUSES } from '../services/api/clause-api';
import type { PolicyStatus, PolicySummary } from '../types/domain';
import { POLICY_SLOT_LABELS } from './labels';

const UNAVAILABLE_REASONS: Partial<Record<PolicyStatus, string>> = {
  PROCESSING: 'ainda sendo lida',
  FAILED: 'a leitura falhou',
  CANCELLED: 'leitura cancelada',
};

export const isComparable = (policy: PolicySummary) =>
  COMPARABLE_POLICY_STATUSES.includes(policy.status);

/** Motivo pelo qual a apólice não pode ser escolhida; null quando pode. */
export const unavailableReason = (policy: PolicySummary): string | null =>
  isComparable(policy) ? null : (UNAVAILABLE_REASONS[policy.status] ?? 'indisponível');

/** O que ainda falta para comparar; null quando a escolha está completa e válida. */
export function compareBlocker(policyAId: string, policyBId: string): string | null {
  if (!policyAId && !policyBId) {
    return `Escolha a ${POLICY_SLOT_LABELS.A} e a ${POLICY_SLOT_LABELS.B}`;
  }
  if (!policyAId) return `Escolha a ${POLICY_SLOT_LABELS.A}`;
  if (!policyBId) return `Escolha a ${POLICY_SLOT_LABELS.B}`;
  if (policyAId === policyBId) return 'Escolha duas apólices diferentes';
  return null;
}
