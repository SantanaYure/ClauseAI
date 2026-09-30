import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../src/app/App';

const processingPolicy = {
  id: 'pol_proc',
  insurer: 'Seguradora Alfa',
  name: 'Apólice D&O Alfa',
  number: null,
  validity: null,
  status: 'PROCESSING',
  alerts: [],
  documents: [
    {
      id: 'doc_1',
      filename: 'alfa_do.pdf',
      type: 'POLICY',
      file_kind: 'SEARCHABLE_PDF',
      pages: 10,
      status: 'EXTRACTING',
      extraction_quality: null,
      ocr_required: false,
      failure: null,
    },
  ],
};

const cancelledPolicy = {
  ...processingPolicy,
  status: 'CANCELLED',
  alerts: ['Extração cancelada pelo usuário.'],
  documents: [
    {
      ...processingPolicy.documents[0],
      status: 'CANCELLED',
      failure: 'Extração cancelada pelo usuário.',
    },
  ],
};

describe('policy extraction cancellation', () => {
  let isCancelled = false;

  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (url.includes('/api/v1/policies/pol_proc/cancel') && init?.method === 'POST') {
      isCancelled = true;
      return new Response(JSON.stringify(cancelledPolicy), { status: 200 });
    }
    if (url.includes('/api/v1/policies')) {
      const current = isCancelled ? cancelledPolicy : processingPolicy;
      return new Response(JSON.stringify({ items: [current], next_cursor: null }), { status: 200 });
    }
    throw new TypeError(`Unhandled fetch: ${url}`);
  });

  beforeEach(() => {
    isCancelled = false;
    fetchMock.mockClear();
    vi.stubGlobal('fetch', fetchMock);
    window.location.hash = '#/apolices';
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders cancel button for processing policy and allows cancellation via confirmation', async () => {
    await act(async () => {
      render(<App />);
    });

    const cancelButton = await screen.findByRole('button', {
      name: 'Cancelar extração de Apólice D&O Alfa',
    });
    expect(cancelButton).toBeInTheDocument();

    await act(async () => {
      fireEvent.click(cancelButton);
    });
    const dialog = screen.getByRole('alertdialog', { name: 'Cancelar extração?' });
    expect(
      within(dialog).getByText(/O processamento dos documentos será interrompido/),
    ).toBeInTheDocument();

    // Cancel the dialog
    await act(async () => {
      fireEvent.click(within(dialog).getByRole('button', { name: 'Cancelar' }));
    });
    expect(screen.queryByRole('alertdialog')).toBeNull();
    expect(fetchMock.mock.calls.some(([url]) => url.includes('/cancel'))).toBe(false);

    // Reopen and confirm
    await act(async () => {
      fireEvent.click(
        screen.getByRole('button', { name: 'Cancelar extração de Apólice D&O Alfa' }),
      );
    });
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Sim, cancelar extração' }));
    });

    const cancelCall = fetchMock.mock.calls.find(([url]) =>
      url.includes('/api/v1/policies/pol_proc/cancel'),
    );
    expect(cancelCall).toBeDefined();
    expect(cancelCall![1]?.method).toBe('POST');
  });
});
