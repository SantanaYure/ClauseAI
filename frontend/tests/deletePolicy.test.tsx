import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../src/app/App';

const policy = {
  id: 'pol_1',
  insurer: 'Seguradora Teste',
  name: 'D&O 2026',
  number: '123',
  validity: null,
  status: 'READY',
  alerts: [],
  documents: [
    {
      id: 'doc_1',
      filename: 'apolice.pdf',
      type: 'POLICY',
      file_kind: 'SEARCHABLE_PDF',
      pages: 9,
      status: 'COMPLETED',
      extraction_quality: 'HIGH',
      ocr_required: false,
      failure: null,
    },
  ],
};

describe('policy deletion', () => {
  let deleted = false;
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (init?.method === 'DELETE') {
      deleted = true;
      return new Response(null, { status: 204 });
    }
    if (url.includes('/api/v1/policies')) {
      const items = deleted ? [] : [policy];
      return new Response(JSON.stringify({ items, next_cursor: null }), { status: 200 });
    }
    throw new TypeError('Failed to fetch');
  });

  beforeEach(() => {
    deleted = false;
    fetchMock.mockClear();
    vi.stubGlobal('fetch', fetchMock);
    window.location.hash = '#/apolices';
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('asks for confirmation before deleting and shows the result', async () => {
    await act(async () => {
      render(<App />);
    });

    fireEvent.click(
      await screen.findByRole('button', { name: 'Excluir apólice Seguradora Teste' }),
    );
    const dialog = screen.getByRole('alertdialog', { name: 'Excluir apólice?' });
    expect(within(dialog).getByText(/Esta ação não pode ser desfeita/)).toBeInTheDocument();

    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancelar' }));
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'DELETE')).toBe(false);

    fireEvent.click(screen.getByRole('button', { name: 'Excluir apólice Seguradora Teste' }));
    fireEvent.click(screen.getByRole('button', { name: 'Excluir definitivamente' }));

    expect(await screen.findByText('Apólice Seguradora Teste excluída.')).toBeInTheDocument();
    expect(await screen.findByText('Nenhuma apólice encontrada')).toBeInTheDocument();
    const [url, init] = fetchMock.mock.calls.find(([, options]) => options?.method === 'DELETE')!;
    expect(url).toContain('/api/v1/policies/pol_1');
    expect(init?.method).toBe('DELETE');
  });

  it('does not allow deleting a policy that is still processing', async () => {
    const processing = { ...policy, status: 'PROCESSING' };
    fetchMock.mockImplementationOnce(
      async () =>
        new Response(JSON.stringify({ items: [processing], next_cursor: null }), { status: 200 }),
    );
    await act(async () => {
      render(<App />);
    });

    expect(
      await screen.findByRole('button', { name: 'Excluir apólice Seguradora Teste' }),
    ).toBeDisabled();
  });
});
