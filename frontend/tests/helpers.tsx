import { act, render } from '@testing-library/react';
import { vi } from 'vitest';
import { App } from '../src/app/App';

export type MockRoute = {
  match: string;
  method?: string;
  status?: number;
  body?: unknown;
  /** Resposta calculada a cada chamada; tem prioridade sobre `body`. */
  respond?: (init?: RequestInit) => Response | Promise<Response>;
};

export const fetchMock = vi.fn();

export function mockApi(routes: MockRoute[]) {
  fetchMock.mockImplementation(async (url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET';
    const route = routes.find(
      (candidate) => url.includes(candidate.match) && (candidate.method ?? 'GET') === method,
    );
    if (!route) throw new TypeError('Failed to fetch');
    if (route.respond) return route.respond(init);
    return new Response(JSON.stringify(route.body), { status: route.status ?? 200 });
  });
}

export const page = (items: unknown[]) => ({ items, next_cursor: null });

export async function openRoute(hash: string) {
  window.location.hash = hash;
  await act(async () => {
    render(<App />);
  });
}

export const apiDocument = (overrides: Record<string, unknown> = {}) => ({
  id: 'doc_1',
  filename: 'apolice.pdf',
  type: 'POLICY',
  file_kind: 'SEARCHABLE_PDF',
  pages: 3,
  status: 'COMPLETED',
  extraction_quality: 'HIGH',
  ocr_required: false,
  failure: null,
  ...overrides,
});

export const apiPolicy = (overrides: Record<string, unknown> = {}) => ({
  id: 'pol_1',
  insurer: 'Seguradora Alfa',
  name: 'D&O Alfa',
  number: null,
  validity: null,
  status: 'READY',
  alerts: [],
  documents: [apiDocument()],
  ...overrides,
});

export function setupFetch() {
  fetchMock.mockReset();
  vi.stubGlobal('fetch', fetchMock);
}
