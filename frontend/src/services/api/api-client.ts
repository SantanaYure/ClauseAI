import { appConfig } from '../../config/env';
import type { HealthResponse } from '../../types/health';

export class ApiClientError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
  }
}

export class ApiClient {
  constructor(private readonly baseUrl: string = appConfig.apiBaseUrl) {}

  async getHealth(signal?: AbortSignal): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      signal,
    });

    if (!response.ok) {
      throw new ApiClientError('Backend health check failed.', response.status);
    }

    return (await response.json()) as HealthResponse;
  }
}

export const apiClient = new ApiClient();
