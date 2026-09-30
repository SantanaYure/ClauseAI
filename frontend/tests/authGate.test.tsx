import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { Root } from '../src/app/Root';
import { setIdentity } from '../src/services/api/clause-api';
import { createFakeIdentity } from './fakeIdentity';
import { fetchMock, mockApi, page, setupFetch } from './helpers';

async function renderRoot(fake: ReturnType<typeof createFakeIdentity>, hash = '#/apolices') {
  window.location.hash = hash;
  setIdentity(fake.identity);
  await act(async () => {
    render(<Root identity={fake.identity} />);
  });
}

describe('AuthGate', () => {
  beforeEach(() => {
    setupFetch();
    mockApi([{ match: '/api/v1/policies', body: page([]) }]);
  });
  afterEach(() => vi.unstubAllGlobals());

  it('mostra carregando e só libera o app (e a API) quando a identidade fica pronta', async () => {
    const fake = createFakeIdentity({ manual: true });
    await renderRoot(fake);

    expect(screen.getByText('Preparando seu espaço privado…')).toBeInTheDocument();
    expect(screen.queryByRole('navigation', { name: 'Menu principal' })).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();

    await act(async () => fake.release());

    expect(await screen.findByText('Nenhuma apólice encontrada')).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalled();
  });

  it('em falha mostra a tela cheia, sem chamar a API nem permitir envio', async () => {
    const fake = createFakeIdentity({ failSignIn: true });
    await renderRoot(fake);

    expect(
      await screen.findByRole('heading', { name: 'Não conseguimos criar seu espaço privado' }),
    ).toBeInTheDocument();
    expect(screen.getByText(/bloqueando o armazenamento local/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Por que isso é necessário?' })).toHaveAttribute(
      'href',
      '#/privacidade',
    );
    expect(screen.queryByRole('navigation', { name: 'Menu principal' })).toBeNull();
    expect(screen.queryByRole('button', { name: /Enviar/ })).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('"Tentar de novo" cria a identidade e abre o app', async () => {
    const fake = createFakeIdentity({ failSignIn: true });
    await renderRoot(fake);
    fake.setFailSignIn(false);

    fireEvent.click(await screen.findByRole('button', { name: 'Tentar de novo' }));

    expect(await screen.findByText('Nenhuma apólice encontrada')).toBeInTheDocument();
    expect(fake.provider.signIn).toHaveBeenCalledTimes(2);
  });

  it('explica a privacidade mesmo sem identidade, sem o botão de apagar', async () => {
    const fake = createFakeIdentity({ failSignIn: true });
    await renderRoot(fake, '#/privacidade');

    expect(await screen.findByRole('heading', { name: 'Por quanto tempo' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Apagar todos os meus dados' })).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
