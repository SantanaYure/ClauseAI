import { act, fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiPolicy, fetchMock, mockApi, openRoute, setupFetch } from './helpers';

const pdf = (name = 'apolice.pdf', type = 'application/pdf') =>
  new File(['conteudo'], name, { type });

function fileInput() {
  return document.querySelector<HTMLInputElement>('.dropzone-input')!;
}

async function choose(...files: File[]) {
  await act(async () => {
    fireEvent.change(fileInput(), { target: { files } });
  });
}

describe('Adicionar apólice', () => {
  beforeEach(setupFetch);
  afterEach(() => vi.unstubAllGlobals());

  it('anuncia PDF ou DOCX e o limite de tamanho', async () => {
    await openRoute('#/apolices/nova');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('PDF ou DOCX');
    expect(screen.getByText(/PDF, DOCX, JPG ou PNG · até 20 MB por arquivo/)).toBeInTheDocument();
    expect(fileInput().accept).toContain('.docx');
  });

  it('aceita PDF e DOCX com MIME vazio e mostra "Detectamos" editável', async () => {
    await openRoute('#/apolices/nova');
    await choose(pdf('condicoes_gerais.pdf', ''), pdf('apolice.docx', ''));

    const list = screen.getByRole('list', { name: 'Arquivos selecionados' });
    expect(within(list).queryByRole('alert')).toBeNull();
    expect(within(list).getAllByText('Detectamos:')).toHaveLength(2);

    const [general, policy] = within(list).getAllByRole('combobox');
    expect(general).toHaveValue('GENERAL_CONDITIONS');
    expect(policy).toHaveValue('POLICY');

    await act(async () => {
      fireEvent.change(general, { target: { value: 'ENDORSEMENT' } });
    });
    expect(general).toHaveValue('ENDORSEMENT');
    expect(within(list).getByText('Tipo:')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Enviar 2 arquivos' })).toBeEnabled();
  });

  it('não bloqueia os arquivos válidos por causa de um inválido', async () => {
    mockApi([
      {
        match: '/api/v1/policies',
        method: 'POST',
        status: 202,
        body: { policy_id: 'pol_1', status: 'PROCESSING', document_ids: [] },
      },
      { match: '/api/v1/policies/pol_1', body: apiPolicy({ status: 'PROCESSING' }) },
    ]);
    await openRoute('#/apolices/nova');
    await choose(pdf('ok.pdf'), new File(['x'], 'nota.txt', { type: 'text/plain' }));

    expect(screen.getByText(/Formato não aceito\. Envie PDF, DOCX, JPG ou PNG\./)).toBeVisible();
    expect(screen.getByRole('button', { name: /Trocar arquivo nota\.txt/ })).toBeInTheDocument();

    const send = screen.getByRole('button', { name: 'Enviar 1 arquivo' });
    expect(send).toBeEnabled();
    await act(async () => {
      fireEvent.click(send);
    });

    const post = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST')!;
    const sent = (post[1].body as FormData).getAll('files') as File[];
    expect(sent.map((file) => file.name)).toEqual(['ok.pdf']);
    expect(await screen.findByText(/pode levar alguns minutos/)).toBeInTheDocument();
  });

  it('troca um arquivo com problema por outro', async () => {
    await openRoute('#/apolices/nova');
    await choose(new File([], 'vazio.pdf', { type: 'application/pdf' }));
    expect(screen.getByText(/Arquivo vazio/)).toBeInTheDocument();

    const replace = screen.getByLabelText(/Escolher outro arquivo no lugar de vazio\.pdf/);
    await act(async () => {
      fireEvent.change(replace, { target: { files: [pdf('novo.pdf')] } });
    });
    expect(screen.queryByText(/Arquivo vazio/)).toBeNull();
    expect(screen.getByText('novo.pdf')).toBeInTheDocument();
  });

  it('mostra o erro do backend junto do arquivo com falha e move o foco até ele', async () => {
    mockApi([
      {
        match: '/api/v1/policies',
        method: 'POST',
        status: 422,
        body: {
          error: {
            code: 'DOCX_PROTECTED',
            message: 'O arquivo protegido.docx está protegido por senha.',
          },
        },
      },
    ]);
    await openRoute('#/apolices/nova');
    await choose(pdf('ok.pdf'), pdf('protegido.docx', ''));
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Enviar 2 arquivos' }));
    });

    const row = screen.getByText('protegido.docx').closest('li')!;
    const alert = await within(row).findByRole('alert');
    expect(alert).toHaveTextContent(/Word.*senha/);
    await waitFor(() => expect(alert).toHaveFocus());
    expect(within(screen.getByText('ok.pdf').closest('li')!).queryByRole('alert')).toBeNull();
    expect(screen.getByRole('button', { name: 'Enviar 1 arquivo' })).toBeEnabled();
  });

  it('avisa quando só há condições gerais', async () => {
    await openRoute('#/apolices/nova');
    await choose(pdf('condicoes_gerais.pdf'));
    expect(screen.getByText(/não comprovam|Não comprovado/)).toBeInTheDocument();
    expect(screen.getByText('Consulte seu corretor de seguros.')).toBeInTheDocument();
  });
});
