import { act, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiDocument, apiPolicy, mockApi, openRoute, setupFetch, type MockRoute } from './helpers';

const processing = (documentStatus: string) =>
  apiPolicy({
    status: 'PROCESSING',
    documents: [apiDocument({ status: documentStatus })],
  });

const created: MockRoute = {
  match: '/api/v1/policies',
  method: 'POST',
  status: 202,
  body: { policy_id: 'pol_1', status: 'PROCESSING', document_ids: [] },
};

/** Envia um arquivo e chega à tela de acompanhamento com a consulta do status mockada. */
async function sendOneFile(statusRoute: MockRoute) {
  mockApi([created, statusRoute]);
  await openRoute('#/apolices/nova');
  const input = document.querySelector<HTMLInputElement>('.dropzone-input')!;
  await act(async () => {
    fireEvent.change(input, {
      target: { files: [new File(['x'], 'apolice.pdf', { type: 'application/pdf' })] },
    });
  });
  await act(async () => {
    fireEvent.click(screen.getByRole('button', { name: 'Enviar 1 arquivo' }));
  });
}

const status = (body: unknown): MockRoute => ({ match: '/api/v1/policies/pol_1', body });

describe('Processando apólice', () => {
  beforeEach(setupFetch);
  afterEach(() => vi.unstubAllGlobals());

  it('mostra três passos com o atual em destaque, aviso de tempo e Cancelar', async () => {
    await sendOneFile(status(processing('EXTRACTING')));

    const steps = await screen.findByRole('list', { name: 'Etapas do processamento' });
    const items = within(steps).getAllByRole('listitem');
    expect(items.map((item) => item.textContent)).toEqual([
      expect.stringContaining('Recebido'),
      expect.stringContaining('Lendo'),
      expect.stringContaining('Conferindo'),
    ]);
    expect(items[0]).toHaveClass('process-steps__item--done');
    expect(items[1]).toHaveAttribute('aria-current', 'step');
    expect(items[2]).toHaveClass('process-steps__item--todo');
    expect(screen.getByText(/pode levar alguns minutos/)).toBeInTheDocument();
    expect(screen.getByText(/Você pode sair desta tela/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Cancelar extração/ })).toBeInTheDocument();
  });

  it('avança para "Conferindo" quando o documento está sendo validado', async () => {
    await sendOneFile(status(processing('VALIDATING')));
    const steps = await screen.findByRole('list', { name: 'Etapas do processamento' });
    expect(within(steps).getAllByRole('listitem')[2]).toHaveAttribute('aria-current', 'step');
  });

  it('mantém a tela e avisa "Sem conexão, tentando de novo" quando a consulta falha', async () => {
    let calls = 0;
    await sendOneFile({
      match: '/api/v1/policies/pol_1',
      respond: () => {
        calls += 1;
        if (calls === 1) return new Response(JSON.stringify(processing('EXTRACTING')));
        throw new TypeError('Failed to fetch');
      },
    });
    await screen.findByRole('list', { name: 'Etapas do processamento' });

    expect(
      await screen.findByText(/Sem conexão, tentando de novo/, {}, { timeout: 6000 }),
    ).toBeInTheDocument();
    expect(screen.getByRole('list', { name: 'Etapas do processamento' })).toBeInTheDocument();
  }, 10000);

  it('mostra o motivo do documento que falhou e o botão Reenviar', async () => {
    await sendOneFile(
      status(
        apiPolicy({
          status: 'FAILED',
          documents: [
            apiDocument({
              status: 'FAILED',
              failure: 'O arquivo apolice.pdf está protegido por senha.',
            }),
          ],
        }),
      ),
    );
    expect(await screen.findByText(/protegido por senha/)).toBeInTheDocument();
    const resend = screen.getAllByRole('button', { name: /Reenviar/ })[0];
    await act(async () => {
      fireEvent.click(resend);
    });
    expect(screen.getByRole('button', { name: /Enviar/ })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('PDF ou DOCX');
  });

  it('mostra a tela de sucesso com a ilustração e a ação de comparar', async () => {
    await sendOneFile(status(apiPolicy()));
    expect(
      await screen.findByRole('heading', { name: 'Apólice pronta para comparar' }),
    ).toBeVisible();
    expect(document.querySelector('.success-screen .illustration')).not.toBeNull();
    expect(screen.getByRole('link', { name: /Comparar com outra apólice/ })).toHaveAttribute(
      'href',
      '#/comparar?a=pol_1',
    );

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Adicionar outra apólice/ }));
    });
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('PDF ou DOCX');
  });
});
