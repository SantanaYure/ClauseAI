const DEFAULT_API_BASE_URL = 'http://localhost:8000';

export const appConfig = {
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, ''),
} as const;
