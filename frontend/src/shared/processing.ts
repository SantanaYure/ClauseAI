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
