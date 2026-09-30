const DEFAULT_API_BASE_URL = 'http://localhost:8000';
const DEFAULT_REQUEST_TIMEOUT_MS = 20_000;
const DEFAULT_UPLOAD_TIMEOUT_MS = 300_000;
const DEFAULT_MAX_UPLOAD_MB = 20;

function positiveNumber(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

export const appConfig = {
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, ''),
  requestTimeoutMs: DEFAULT_REQUEST_TIMEOUT_MS,
  /** Envio multipart (vários arquivos, até o limite por arquivo) precisa de mais tempo. */
  uploadTimeoutMs: positiveNumber(
    import.meta.env.VITE_UPLOAD_TIMEOUT_MS,
    DEFAULT_UPLOAD_TIMEOUT_MS,
  ),
  /** Deve espelhar `MAX_UPLOAD_MB` do backend. */
  maxUploadBytes:
    positiveNumber(import.meta.env.VITE_MAX_UPLOAD_MB, DEFAULT_MAX_UPLOAD_MB) * 1024 * 1024,
} as const;
