import { act, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiDocument, apiPolicy, fetchMock, mockApi, openRoute, setupFetch } from './helpers';

const score = (adherence: number, completeness: number) => ({
  raw: 40,
  max: 100,
  adherence,
  documentary: 0.5,
  completeness,
  critical_unconfirmed_weight: 10,
  inconclusive_weight: 0,
  favorable: 3,
  equivalent: 1,
  inconclusive: 0,
});

const evidence = (documentId: string, documentName: string) => ({
  id: `ev_${documentId}`,
  document_id: documentId,
  document_name: documentName,
  page: 4,
  clause: 'Cláusula 2',
  text: 'Cobertura de custos de defesa.',
  method: 'NATIVE',
  confidence: 0.95,
});

const side = (documentId: string, documentName: string) => ({
  term: 'Custos de defesa',
  contract_status: 'CONTRACTED',
  base_result: 1,
  adjustment_factor: 1,
  points: 10,
  evidence: [evidence(documentId, documentName)],
  sufficient_evidence: true,
});

const comparison = (overrides: Record<string, unknown> = {}) => ({
  id: 'cmp_1',
  created_at: '2026-09-01T12:00:00Z',
  status: 'COMPLETED',
  knowledge_base_version: '1.0',
  selected_profile: 'BASE',
  policy_a: { id: 'pol_a', insurer: 'Seguradora Alfa', name: 'D&O Alfa' },
  policy_b: { id: 'pol_b', insurer: 'Seguradora Beta', name: 'D&O Beta' },
  items: [
    {
      concept_id: 'DO-001',
      concept_name: 'Custos de defesa',
      importance: 'CRITICAL',
      weight: 10,
      a: side('doc_a', 'alfa.pdf'),
      b: side('doc_b', 'beta.docx'),
      main_difference: 'Sem diferença',
      verdict: 'EQUIVALENT',
      confidence: 'HIGH',
      guidance: false,
    },
  ],
  profiles: [
    {
      profile: 'BASE',
      prioritized: [],
      multiplier: 1,
      a: score(0.72, 0.9),
      b: score(0.61, 0.8),
      winner: 'A',
      decisive_concepts: [],
      sensitivity: 'ROBUST',
      limitations: [],
    },
  ],
  summary: {
    decision_mode: 'TECHNICAL',
    highest_score: 'A',
    advantages_a: ['Limite maior'],
    advantages_b: [],
    equivalent_critical: ['Custos de defesa'],
    highest_impact: ['Retroatividade'],
    attention_points: ['Sublimite de multas'],
    score_vs_qualitative: null,
    conclusion: 'A Apólice 01 comprova mais coberturas.',
  },
  quality_gate: [{ id: 'q1', label: 'Arquivos lidos', passed: true, detail: 'Todos.' }],
  failure: null,
  ...overrides,
});

const policyRoutes = [
  {
    match: '/api/v1/policies/pol_a',
    body: { ...apiPolicy({ id: 'pol_a' }), occurrences: [] },
  },
  {
    match: '/api/v1/policies/pol_b',
    body: {
      ...apiPolicy({
        id: 'pol_b',
        documents: [apiDocument({ id: 'doc_b', filename: 'beta.docx', file_kind: 'DOCX' })],
      }),
      occurrences: [],
    },
  },
];

describe('Resultado da comparação', () => {
  beforeEach(setupFetch);
  afterEach(() => vi.unstubAllGlobals());

  it('avisa quando a comparação expira', async () => {
    const expiresAt = new Date(Date.now() + 5.5 * 3_600_000).toISOString();
    mockApi([
      { match: '/api/v1/comparisons/cmp_1', body: comparison({ expires_at: expiresAt }) },
      ...policyRoutes,
    ]);
    await openRoute('#/comparar/cmp_1');
    expect(await screen.findByText('Esta comparação expira em 5 horas.')).toBeInTheDocument();
    expect(screen.getByText('Consulte seu corretor de seguros.')).toBeInTheDocument();
  });

  it('segue a ordem fixa: conclusão, placares, vantagens e atenção, Ver cálculo', async () => {
    mockApi([{ match: '/api/v1/comparisons/cmp_1', body: comparison() }, ...policyRoutes]);
    await openRoute('#/comparar/cmp_1');

    const conclusion = await screen.findByText('A Apólice 01 comprova mais coberturas.');
    const boardA = screen.getByRole('region', { name: 'Placar da Apólice 01' });
    const advantages = screen.getByRole('heading', { name: 'Vantagens' });
    const attention = screen.getByRole('heading', { name: /Atenção/ });
    const calc = screen.getByText('Ver cálculo').closest('details')!;

    const follows = (a: Node, b: Node) =>
      Boolean(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
    expect(follows(conclusion, boardA)).toBe(true);
    expect(follows(boardA, advantages)).toBe(true);
    expect(follows(advantages, calc)).toBe(true);
    expect(follows(attention, calc)).toBe(true);
    expect(calc).not.toHaveAttribute('open');
  });

  it('mostra só aderência e completude nos placares, com "?" explicativo', async () => {
    mockApi([{ match: '/api/v1/comparisons/cmp_1', body: comparison() }, ...policyRoutes]);
    await openRoute('#/comparar/cmp_1');

    const board = await screen.findByRole('region', { name: 'Placar da Apólice 01' });
    expect(
      within(board)
        .getAllByRole('term')
        .map((term) => term.textContent),
    ).toEqual([expect.stringContaining('Aderência'), expect.stringContaining('Completude')]);
    expect(within(board).getByText('72,0%')).toBeInTheDocument();
    expect(within(board).getByText('90,0%')).toBeInTheDocument();
    expect(within(board).queryByText(/Score documental|Pontos/)).toBeNull();

    const help = within(board).getByRole('button', { name: 'O que é aderência?' });
    expect(help).toHaveAttribute('aria-expanded', 'false');
    await act(async () => {
      fireEvent.click(help);
    });
    expect(help).toHaveAttribute('aria-expanded', 'true');
  });

  it('guarda pontos, score documental, favoráveis e críticas em "Ver cálculo"', async () => {
    mockApi([{ match: '/api/v1/comparisons/cmp_1', body: comparison() }, ...policyRoutes]);
    await openRoute('#/comparar/cmp_1');
    const calc = (await screen.findByText('Ver cálculo')).closest('details')!;
    expect(within(calc).getAllByText('Score documental').length).toBeGreaterThan(0);
    expect(within(calc).getAllByText('Conceitos favoráveis').length).toBeGreaterThan(0);
    expect(within(calc).getAllByText('Críticas sem confirmação').length).toBeGreaterThan(0);
  });

  it('mantém "Consulte seu corretor de seguros." visível', async () => {
    mockApi([{ match: '/api/v1/comparisons/cmp_1', body: comparison() }, ...policyRoutes]);
    await openRoute('#/comparar/cmp_1');
    await screen.findByText('Ver cálculo');
    expect(screen.getByText('Consulte seu corretor de seguros.')).toBeVisible();
  });

  it('usa "bloco" no lugar de "página" nas evidências de DOCX', async () => {
    mockApi([{ match: '/api/v1/comparisons/cmp_1', body: comparison() }, ...policyRoutes]);
    await openRoute('#/comparar/cmp_1');
    const calc = (await screen.findByText('Ver cálculo')).closest('details')!;
    fireEvent.click(calc.querySelector('summary')!);
    for (const summary of calc.querySelectorAll('.concept-row__details summary')) {
      fireEvent.click(summary);
    }
    const sources = Array.from(calc.querySelectorAll('.evidence__source')).map(
      (element) => element.textContent,
    );
    expect(sources.some((text) => text?.includes('alfa.pdf') && text.includes('p. 4'))).toBe(true);
    expect(sources.some((text) => text?.includes('beta.docx') && text.includes('bloco 4'))).toBe(
      true,
    );
  });

  it('em FAILED mostra o motivo e recria a comparação', async () => {
    mockApi([
      {
        match: '/api/v1/comparisons/cmp_1',
        body: comparison({
          status: 'FAILED',
          summary: null,
          profiles: [],
          selected_profile: 'FINANCIAL',
          failure: { code: 'AI_TIMEOUT', message: 'O serviço de análise não respondeu.' },
        }),
      },
      {
        match: '/api/v1/comparisons',
        method: 'POST',
        status: 202,
        body: { comparison_id: 'cmp_2', status: 'REQUESTED' },
      },
    ]);
    await openRoute('#/comparar/cmp_1');
    expect(await screen.findByText('O serviço de análise não respondeu.')).toBeInTheDocument();
    expect(screen.getByText('Consulte seu corretor de seguros.')).toBeVisible();

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }));
    });
    const post = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST')!;
    expect(JSON.parse(post[1].body as string)).toEqual({
      policy_a_id: 'pol_a',
      policy_b_id: 'pol_b',
      selected_profile: 'FINANCIAL',
    });
    expect(window.location.hash).toBe('#/comparar/cmp_2');
  });
});
