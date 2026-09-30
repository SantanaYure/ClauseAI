import { act, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { setIdentity } from '../src/services/api/clause-api';
import { createFakeIdentity } from './fakeIdentity';
import { apiPolicy, fetchMock, mockApi, openRoute, page, setupFetch } from './helpers';

const summary = { policies: 2, documents: 5, comparisons: 1 };

describe('Privacidade e dados', () => {
  let fake: ReturnType<typeof createFakeIdentity>;

  beforeEach(() => {
    setupFetch();
    fake = createFakeIdentity();
    setIdentity(fake.identity);
  });
  afterEach(() => vi.unstubAllGlobals());

  it('explica finalidade, operador, local, prazo, direitos e contato', async () => {
    await openRoute('#/privacidade');

    expect(screen.getByRole('heading', { level: 1, name: 'Privacidade e dados' })).toBeVisible();
    for (const title of ['Para quê', 'Quem processa', 'Onde fica', 'Por quanto tempo']) {
      expect(screen.getByRole('heading', { name: title })).toBeInTheDocument();
    }
    expect(screen.getByRole('heading', { name: 'Seus direitos' })).toBeInTheDocument();
    expect(screen.getByText(/Google Gemini/)).toBeInTheDocument();
    expect(screen.getByText(/24 horas após o envio/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'yure.s.santana@outlook.com' })).toHaveAttribute(
      'href',
      'mailto:yure.s.santana@outlook.com',
    );
    expect(screen.getByText(/Evite enviar documentos com dados pessoais/)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('tem link no rodapé das telas', async () => {
    mockApi([{ match: '/api/v1/comparisons', body: page([]) }]);
    await openRoute('#/');
    expect(screen.getByRole('link', { name: 'Privacidade e dados' })).toHaveAttribute(
      'href',
      '#/privacidade',
    );
  });

  it('mostra a contagem, foca "Cancelar" e não apaga ao cancelar', async () => {
    mockApi([{ match: '/api/v1/me/data/summary', body: summary }]);
    await openRoute('#/privacidade');

    fireEvent.click(screen.getByRole('button', { name: 'Apagar todos os meus dados' }));
    const dialog = screen.getByRole('alertdialog', { name: 'Apagar tudo deste navegador?' });

    expect(
      await within(dialog).findByText('Serão apagadas 2 apólices, 5 documentos e 1 comparação.'),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByText(
        'Isso não pode ser desfeito. Envios em processamento serão cancelados.',
      ),
    ).toBeInTheDocument();
    expect(within(dialog).getByRole('button', { name: 'Cancelar' })).toHaveFocus();

    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancelar' }));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'DELETE')).toBe(false);
  });

  it('apaga tudo, inicia novo espaço e volta para Apólices vazia com aviso', async () => {
    let deleted = false;
    let finishDelete: () => void = () => undefined;
    mockApi([
      { match: '/api/v1/me/data/summary', body: summary },
      {
        match: '/api/v1/me/data',
        method: 'DELETE',
        respond: () =>
          new Promise<Response>((resolve) => {
            finishDelete = () => {
              deleted = true;
              resolve(new Response(null, { status: 204 }));
            };
          }),
      },
      {
        match: '/api/v1/policies',
        respond: () =>
          new Response(JSON.stringify(page(deleted ? [] : [apiPolicy()])), { status: 200 }),
      },
    ]);
    await openRoute('#/privacidade');

    fireEvent.click(screen.getByRole('button', { name: 'Apagar todos os meus dados' }));
    await screen.findByText(/Serão apagadas 2 apólices/);
    fireEvent.click(screen.getByRole('button', { name: 'Apagar tudo' }));

    const busy = await screen.findByRole('button', { name: 'Apagando…' });
    expect(busy).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Cancelar' })).toBeDisabled();

    await act(async () => finishDelete());

    expect(
      await screen.findByText('Seus dados foram apagados deste navegador e dos nossos servidores.'),
    ).toBeInTheDocument();
    expect(window.location.hash).toBe('#/apolices');
    expect(await screen.findByText('Nenhuma apólice encontrada')).toBeInTheDocument();
    expect(fake.provider.signOut).toHaveBeenCalledTimes(1);
    const lastCall = fetchMock.mock.calls.at(-1)!;
    expect((lastCall[1] as RequestInit).headers).toMatchObject({
      Authorization: 'Bearer token-2',
    });
  });

  it('explica a falha e mantém o modal aberto para tentar de novo', async () => {
    mockApi([
      { match: '/api/v1/me/data/summary', body: summary },
      {
        match: '/api/v1/me/data',
        method: 'DELETE',
        status: 500,
        body: { error: { code: 'INTERNAL', message: 'erro' } },
      },
    ]);
    await openRoute('#/privacidade');

    fireEvent.click(screen.getByRole('button', { name: 'Apagar todos os meus dados' }));
    fireEvent.click(screen.getByRole('button', { name: 'Apagar tudo' }));

    expect(
      await screen.findByText('Não conseguimos apagar tudo agora. Tente de novo em instantes.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('alertdialog')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Apagar tudo' })).toBeEnabled();
    expect(fake.provider.signOut).not.toHaveBeenCalled();
  });

  it('sem a contagem, ainda permite apagar com texto genérico', async () => {
    mockApi([]);
    await openRoute('#/privacidade');
    fireEvent.click(screen.getByRole('button', { name: 'Apagar todos os meus dados' }));
    expect(
      await screen.findByText(
        'Serão apagadas todas as apólices, documentos e comparações deste navegador.',
      ),
    ).toBeInTheDocument();
  });
});
