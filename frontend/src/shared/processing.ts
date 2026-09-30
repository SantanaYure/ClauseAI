import type {
  ComparisonListItem,
  ComparisonStatus,
  DocumentStatus,
  PolicyStatus,
  PolicySummary,
} from '../types/domain';

/** Intervalo de consulta enquanto houver apólices em processamento (SPEC-014). */
export const PROCESSING_POLL_MS = 3000;

const BUSY_DOCUMENT_STATUSES: DocumentStatus[] = [
  'UPLOADED',
  'PROCESSING',
  'EXTRACTING',
  'VALIDATING',
];

export const isDocumentBusy = (status: DocumentStatus) => BUSY_DOCUMENT_STATUSES.includes(status);

export const isPolicyBusy = (status: PolicyStatus) => status === 'PROCESSING';

export const hasBusyPolicy = (policies: PolicySummary[]) =>
  policies.some((policy) => isPolicyBusy(policy.status));

/** Passos mostrados ao usuário (SPEC-010), em linguagem simples. */
export const PROCESS_STEPS = ['Recebido', 'Lendo', 'Conferindo'] as const;

/** Índice do passo atual; igual a PROCESS_STEPS.length quando o documento já terminou. */
export function documentStepIndex(status: DocumentStatus): number {
  switch (status) {
    case 'UPLOADED':
      return 0;
    case 'PROCESSING':
    case 'EXTRACTING':
      return 1;
    case 'VALIDATING':
      return 2;
    default:
      return PROCESS_STEPS.length;
  }
}

/** Passo do conjunto: o do documento menos adiantado que ainda está em andamento. */
export function policyStepIndex(documents: { status: DocumentStatus }[]): number {
  const busy = documents.filter((document) => isDocumentBusy(document.status));
  if (!busy.length) return PROCESS_STEPS.length;
  return Math.min(...busy.map((document) => documentStepIndex(document.status)));
}

/** Texto do que o backend está fazendo, a partir do estado dos documentos. */
export function describeProcessing(documents: { status: DocumentStatus }[]): string {
  const statuses = documents.map((document) => document.status);
  if (statuses.includes('VALIDATING')) return 'Validando as evidências extraídas…';
  if (statuses.includes('EXTRACTING')) return 'Lendo os documentos e extraindo as evidências…';
  return 'Documentos recebidos. Aguardando o início da leitura…';
}

const FINAL_COMPARISON_STATUSES: ComparisonStatus[] = ['COMPLETED', 'PARTIAL', 'FAILED'];

export const isComparisonBusy = (status: ComparisonStatus) =>
  !FINAL_COMPARISON_STATUSES.includes(status);

export const hasBusyComparison = (items: ComparisonListItem[]) =>
  items.some((item) => isComparisonBusy(item.status));
