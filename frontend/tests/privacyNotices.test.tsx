import { screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiPolicy, mockApi, openRoute, page, setupFetch } from './helpers';

const NOW = Date.parse('2026-09-30T12:00:00Z');
const inHours = (hours: number) => new Date(NOW + hours * 3_600_000).toISOString();

describe('Avisos de privacidade e expiração', () => {
  beforeEach(() => {
    setupFetch();
    vi.spyOn(Date, 'now').mockReturnValue(NOW);
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('mostra quanto falta para cada apólice expirar, com atenção perto do fim', async () => {
    mockApi([
      {
        match: '/api/v1/policies',
        body: page([
          apiPolicy({ id: 'p1', insurer: 'Seguradora Alfa', expires_at: inHours(20.5) }),
          apiPolicy({ id: 'p2', insurer: 'Seguradora Beta', expires_at: inHours(0.5) }),
          apiPolicy({ id: 'p3', insurer: 'Seguradora Gama' }),
        ]),
      },
    ]);
    await openRoute('#/apolices');

    const calm = await screen.findByText('Expira em 20 horas');
    expect(calm.closest('.badge')).toBeNull();
    const urgent = screen.getByText('Expira em menos de 1 hora');
    expect(urgent.closest('.badge')).toHaveClass('badge--neutral');
    expect(screen.getAllByText(/^Expira em/)).toHaveLength(2);
  });

  it('avisa que a lista é só deste navegador, inclusive no estado vazio', async () => {
    mockApi([{ match: '/api/v1/policies', body: page([]) }]);
    await openRoute('#/apolices');

    expect(screen.getByText(/Estas apólices estão guardadas só neste navegador/)).toBeVisible();
    expect(screen.getAllByRole('link', { name: 'Privacidade e dados' }).length).toBeGreaterThan(1);
    expect(
      await screen.findByText(/Apólices enviadas em outro navegador não aparecem aqui\./),
    ).toBeInTheDocument();
  });

  it('explica retenção e uso do Gemini antes do envio', async () => {
    await openRoute('#/apolices/nova');
    expect(
      screen.getByText(/ficam visíveis só neste navegador e são apagados automaticamente 24 horas/),
    ).toBeInTheDocument();
    expect(screen.getByText(/IA do Google \(Gemini\)/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Como tratamos seus dados' })).toHaveAttribute(
      'href',
      '#/privacidade',
    );
  });
});
