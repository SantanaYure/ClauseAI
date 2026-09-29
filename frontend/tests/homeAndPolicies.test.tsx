import { screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiPolicy, mockApi, openRoute, page, setupFetch } from './helpers';

describe('Início', () => {
  beforeEach(() => {
    setupFetch();
    mockApi([{ match: '/api/v1/comparisons', body: page([]) }]);
  });
  afterEach(() => vi.unstubAllGlobals());

  it('mantém a chamada única e recolhe os blocos explicativos', async () => {
    await openRoute('#/');
    expect(screen.getByRole('link', { name: /Nova comparação/ })).toHaveClass('btn--primary');
    expect(screen.getByRole('link', { name: /Adicionar apólice/ })).toBeInTheDocument();
    for (const title of ['Como funciona', 'Como o ClauseAI decide']) {
      const details = screen.getByText(title).closest('details')!;
      expect(details).not.toHaveAttribute('open');
    }
    expect(screen.getByText('Consulte seu corretor de seguros.')).toBeInTheDocument();
  });
});

describe('Lista de apólices', () => {
  beforeEach(setupFetch);
  afterEach(() => vi.unstubAllGlobals());

  it('usa selo azul ou neutro e oferece "Comparar com outra" na apólice pronta', async () => {
    mockApi([{ match: '/api/v1/policies', body: page([apiPolicy()]) }]);
    await openRoute('#/apolices');
    const card = (await screen.findByRole('article')) as HTMLElement;
    const badge = within(card).getByText('Pronta para comparar');
    expect(badge).toHaveClass('badge--info');
    expect(badge.querySelector('svg')).not.toBeNull();
    expect(within(card).getByRole('link', { name: /Comparar .* com outra/ })).toHaveAttribute(
      'href',
      '#/comparar?a=pol_1',
    );
  });

  it('não oferece comparar enquanto a apólice é processada', async () => {
    mockApi([{ match: '/api/v1/policies', body: page([apiPolicy({ status: 'PROCESSING' })]) }]);
    await openRoute('#/apolices');
    const card = (await screen.findByRole('article')) as HTMLElement;
    expect(within(card).queryByRole('link', { name: /com outra/ })).toBeNull();
  });
});
