import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../src/app/App';

type Route = { match: string; method?: string; status?: number; body: unknown };

const fetchMock = vi.fn();

function mockApi(routes: Route[]) {
  fetchMock.mockImplementation(async (url: string, init?: RequestInit) => {
    const method = init?.method ?? 'GET';
    const route = routes.find(
      (candidate) => url.includes(candidate.match) && (candidate.method ?? 'GET') === method,
    );
    if (!route) throw new TypeError('Failed to fetch');
    return new Response(JSON.stringify(route.body), { status: route.status ?? 200 });
  });
}

const emptyPage = { items: [], next_cursor: null };

async function openRoute(hash: string) {
  window.location.hash = hash;
  await act(async () => {
    render(<App />);
  });
}

describe('App', () => {
  beforeEach(() => {
    window.location.hash = '';
    fetchMock.mockReset();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows the five menu items and marks the active one', async () => {
    mockApi([{ match: '/api/v1/comparisons', body: emptyPage }]);
    await openRoute('#/');
    const nav = screen.getByRole('navigation', { name: 'Menu principal' });
    for (const label of ['Início', 'Apólices', 'Comparar', 'Conceitos', 'Histórico']) {
      expect(within(nav).getByRole('link', { name: label })).toBeInTheDocument();
    }
    expect(within(nav).getByRole('link', { name: 'Início' })).toHaveAttribute(
      'aria-current',
      'page',
    );
    expect(screen.getByText('Consulte seu corretor de seguros.')).toBeInTheDocument();
  });

  it('shows an empty state when there are no policies', async () => {
    mockApi([{ match: '/api/v1/policies', body: emptyPage }]);
    await openRoute('#/apolices');
    expect(await screen.findByText('Nenhuma apólice encontrada')).toBeInTheDocument();
  });

  it('shows a loading indicator while a policy is processing', async () => {
    const policy = (status: string, documentStatus: string) => ({
      items: [
        {
          id: 'pol_1',
          insurer: 'Seguradora Teste',
          name: 'D&O',
          number: null,
          validity: null,
          status,
          alerts: [],
          documents: [
            {
              id: 'doc_1',
              filename: 'apolice.pdf',
              type: 'POLICY',
              file_kind: 'SEARCHABLE_PDF',
              pages: 3,
              status: documentStatus,
              extraction_quality: null,
              ocr_required: false,
              failure: null,
            },
          ],
        },
      ],
      next_cursor: null,
    });
    mockApi([{ match: '/api/v1/policies', body: policy('PROCESSING', 'EXTRACTING') }]);
    await openRoute('#/apolices');

    expect(
      await screen.findByText('Lendo os documentos e extraindo as evidências…'),
    ).toBeInTheDocument();
    expect(document.querySelectorAll('.spinner').length).toBeGreaterThan(0);

    mockApi([{ match: '/api/v1/policies', body: policy('READY', 'COMPLETED') }]);
    expect(
      await screen.findByText('Pronta para comparar', {}, { timeout: 5000 }),
    ).toBeInTheDocument();
    expect(screen.queryByText('Lendo os documentos e extraindo as evidências…')).toBeNull();
    expect(document.querySelectorAll('.spinner')).toHaveLength(0);
  }, 10000);

  it('shows a retryable error when the API is unreachable', async () => {
    mockApi([]);
    await openRoute('#/apolices');
    expect(await screen.findByText(/Não foi possível conectar à API/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Tentar novamente' })).toBeInTheDocument();
  });

  it('shows the API error message with its correlation id', async () => {
    mockApi([
      {
        match: '/api/v1/comparisons/cmp_x',
        status: 404,
        body: {
          error: {
            code: 'COMPARISON_NOT_FOUND',
            message: 'Comparação não encontrada.',
            correlation_id: 'cor_9',
          },
        },
      },
    ]);
    await openRoute('#/comparar/cmp_x');
    expect(
      await screen.findByText('Comparação não encontrada. (correlação cor_9)'),
    ).toBeInTheDocument();
  });

  it('asks for two processed policies before comparing', async () => {
    mockApi([{ match: '/api/v1/policies', body: emptyPage }]);
    await openRoute('#/comparar');
    expect(
      await screen.findByText('São necessárias duas apólices processadas'),
    ).toBeInTheDocument();
  });

  it('shows progress while a comparison is still being processed', async () => {
    mockApi([
      {
        match: '/api/v1/comparisons/cmp_1',
        body: { comparison_id: 'cmp_1', status: 'ASSESSING', items: [], profiles: [] },
      },
    ]);
    await openRoute('#/comparar/cmp_1');
    expect(await screen.findByText('Avaliando conceitos com IA…')).toBeInTheDocument();
  });

  it('sends questions to the query endpoint', async () => {
    mockApi([
      { match: '/api/v1/concepts', body: emptyPage },
      {
        match: '/api/v1/queries',
        method: 'POST',
        body: {
          question: 'Qual é o LMG?',
          concept: null,
          answer: 'Sem evidência.',
          matches: [],
          guidance: true,
        },
      },
    ]);
    await openRoute('#/conceitos');
    fireEvent.change(screen.getByLabelText('Pergunte ou busque um conceito'), {
      target: { value: 'Qual é o LMG?' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Perguntar' }));
    expect(
      await screen.findByRole('heading', { name: 'Sem correspondência na base' }),
    ).toBeInTheDocument();
    const [, init] = fetchMock.mock.calls.find(([url]) => String(url).includes('/queries'))!;
    expect(JSON.parse(String(init.body))).toEqual({ question: 'Qual é o LMG?' });
  });
});
