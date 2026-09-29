// Único ponto de acesso a dados das telas. Chama a API REST de
// docs/architecture/PERSISTENCE_AND_API.md (base /api/v1). As respostas em snake_case
// são convertidas para os tipos camelCase de src/types/domain.ts.
import { appConfig } from '../../config/env';
import { friendlyMessage } from '../../shared/apiErrors';
import type {
  ComparisonListItem,
  ComparisonPolicyRef,
  ComparisonResult,
  Concept,
  ConceptId,
  ConceptOccurrence,
  ConceptWithOccurrences,
  NewPolicyInput,
  PolicyDetail,
  PolicyStatus,
  PolicySummary,
  QueryAnswer,
  RiskProfile,
} from '../../types/domain';

export class ApiError extends Error {
  readonly code: string;
  readonly correlationId: string | null;
  /** Mensagem original da API (cita o nome do arquivo); `message` é a versão amigável. */
  readonly detail: string;

  constructor(
    code: string,
    message: string,
    correlationId: string | null = null,
    detail: string = message,
  ) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.correlationId = correlationId;
    this.detail = detail;
  }
}

/** Limite de upload por arquivo (configuração operacional, SPEC-001). */
export const MAX_FILE_SIZE_BYTES = appConfig.maxUploadBytes;
export const COMPARABLE_POLICY_STATUSES: PolicyStatus[] = ['READY', 'ATTENTION'];

const BASE_URL = `${appConfig.apiBaseUrl}/api/v1`;

// ---------- Sinal de mudança para as telas recarregarem ----------

type Listener = () => void;
const listeners = new Set<Listener>();
let version = 0;

function notifyChange(): void {
  version += 1;
  listeners.forEach((listener) => listener());
}

export const dataEvents = {
  subscribe(listener: Listener): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  getVersion: () => version,
};

// ---------- HTTP ----------

const toCamel = (key: string) =>
  key.replace(/_([a-z0-9])/g, (_, char: string) => char.toUpperCase());
const toSnake = (key: string) => key.replace(/[A-Z]/g, (char) => `_${char.toLowerCase()}`);

function convertKeys(value: unknown, convert: (key: string) => string): unknown {
  if (Array.isArray(value)) return value.map((item) => convertKeys(item, convert));
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [convert(key), convertKeys(item, convert)]),
    );
  }
  return value;
}

type ErrorEnvelope = {
  error?: { code?: string; message?: string; correlation_id?: string };
};

type RequestOptions = { timeoutMs?: number; timeoutCode?: string };

async function request<T>(
  path: string,
  init: RequestInit = {},
  { timeoutMs = appConfig.requestTimeoutMs, timeoutCode = 'REQUEST_TIMEOUT' }: RequestOptions = {},
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { Accept: 'application/json', ...init.headers },
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'TimeoutError') {
      throw new ApiError(timeoutCode, friendlyMessage(timeoutCode, 'A API demorou demais.'));
    }
    throw new ApiError('NETWORK_ERROR', friendlyMessage('NETWORK_ERROR', 'Sem conexão.'));
  }

  if (!response.ok) {
    const envelope = (await response.json().catch(() => ({}))) as ErrorEnvelope;
    const code = envelope.error?.code ?? `HTTP_${response.status}`;
    const detail = envelope.error?.message ?? 'A API não conseguiu atender a solicitação.';
    throw new ApiError(
      code,
      friendlyMessage(code, detail),
      envelope.error?.correlation_id ?? null,
      detail,
    );
  }

  if (response.status === 204) return undefined as T;
  return convertKeys(await response.json(), toCamel) as T;
}

const postJson = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(convertKeys(body, toSnake)),
});

type Page<T> = { items: T[]; nextCursor: string | null };

const PAGE_LIMIT = 100;

// ---------- Endpoints ----------

export const clauseApi = {
  async listPolicies(): Promise<PolicySummary[]> {
    const page = await request<Page<PolicySummary>>(`/policies?limit=${PAGE_LIMIT}`);
    return page.items;
  },

  getPolicy(policyId: string): Promise<PolicyDetail> {
    return request(`/policies/${encodeURIComponent(policyId)}`);
  },

  /** Cancela o processamento/extração de uma apólice. */
  async cancelPolicy(policyId: string): Promise<PolicyDetail> {
    const policy = await request<PolicyDetail>(`/policies/${encodeURIComponent(policyId)}/cancel`, {
      method: 'POST',
    });
    notifyChange();
    return policy;
  },

  /** Exclui a apólice, suas evidências e os arquivos originais. */
  async deletePolicy(policyId: string): Promise<void> {
    await request<void>(`/policies/${encodeURIComponent(policyId)}`, { method: 'DELETE' });
    notifyChange();
  },

  async createPolicy(input: NewPolicyInput): Promise<{ policyId: string }> {
    const form = new FormData();
    if (input.insurer.trim()) form.append('insurer', input.insurer.trim());
    if (input.name.trim()) form.append('name', input.name.trim());
    for (const upload of input.files) {
      form.append('files', upload.file, upload.file.name);
      form.append('document_types', upload.type);
    }
    const created = await request<{ policyId: string }>(
      '/policies',
      { method: 'POST', body: form },
      { timeoutMs: appConfig.uploadTimeoutMs, timeoutCode: 'UPLOAD_TIMEOUT' },
    );
    notifyChange();
    return created;
  },

  async listConcepts(): Promise<Concept[]> {
    const page = await request<Page<Concept>>(`/concepts?limit=${PAGE_LIMIT}`);
    return page.items;
  },

  async getConcept(conceptId: ConceptId): Promise<ConceptWithOccurrences> {
    const id = encodeURIComponent(conceptId);
    const [concept, occurrences] = await Promise.all([
      request<Concept>(`/concepts/${id}`),
      request<Page<{ policy: ComparisonPolicyRef; occurrence: ConceptOccurrence }>>(
        `/concepts/${id}/occurrences?limit=${PAGE_LIMIT}`,
      ),
    ]);
    return { ...concept, occurrences: occurrences.items };
  },

  ask(question: string): Promise<QueryAnswer> {
    return request('/queries', postJson({ question }));
  },

  async createComparison(input: {
    policyAId: string;
    policyBId: string;
    selectedProfile: RiskProfile;
  }): Promise<{ id: string }> {
    const created = await request<{ comparisonId: string }>('/comparisons', postJson(input));
    notifyChange();
    return { id: created.comparisonId };
  },

  getComparison(comparisonId: string): Promise<ComparisonResult> {
    return request(`/comparisons/${encodeURIComponent(comparisonId)}`);
  },

  async listComparisons(): Promise<ComparisonListItem[]> {
    const page = await request<Page<ComparisonListItem>>(`/comparisons?limit=${PAGE_LIMIT}`);
    return page.items;
  },
};
