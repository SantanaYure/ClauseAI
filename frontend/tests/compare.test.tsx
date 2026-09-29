import { act, fireEvent, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiDocument, apiPolicy, fetchMock, mockApi, openRoute, page, setupFetch } from './helpers';

const policies = [
  apiPolicy({ id: 'pol_a', insurer: 'Seguradora Alfa', name: 'D&O Alfa' }),
  apiPolicy({ id: 'pol_b', insurer: 'Seguradora Beta', name: 'D&O Beta' }),
  apiPolicy({
    id: 'pol_c',
    insurer: 'Seguradora Gama',
    name: 'D&O Gama',
    status: 'PROCESSING',
    documents: [apiDocument({ status: 'EXTRACTING' })],
  }),
];

const select = (slot: 'A' | 'B') =>
  screen.getByLabelText(new RegExp(`Apólice 0${slot === 'A' ? 1 : 2}`));

describe('Comparar', () => {
  beforeEach(() => {
    setupFetch();
    mockApi([{ match: '/api/v1/policies', body: page(policies) }]);
  });
  afterEach(() => vi.unstubAllGlobals());

  it('usa um wrapper explícito com dois slots grandes, A e B', async () => {
    await openRoute('#/comparar');
    const slots = document.querySelector('.slots')!;
    expect(slots.querySelectorAll('.slot--a, .slot--b')).toHaveLength(2);
    expect(within(slots as HTMLElement).getByText('A')).toBeInTheDocument();
    expect(within(slots as HTMLElement).getByText('B')).toBeInTheDocument();
  });

  it('desabilita a apólice em processamento e escreve o motivo', async () => {
    await openRoute('#/comparar');
    const option = within(select('A')).getByRole('option', { name: /Gama.*ainda sendo lida/ });
    expect(option).toBeDisabled();
  });

  it('deixa o botão indisponível e diz o que falta', async () => {
    await openRoute('#/comparar');
    const button = screen.getByRole('button', { name: /Comparar/ });
    expect(button).toBeDisabled();
    expect(button).toHaveTextContent('Escolha a Apólice 01 e a Apólice 02');

    await act(async () => {
      fireEvent.change(select('A'), { target: { value: 'pol_a' } });
    });
    expect(button).toHaveTextContent('Escolha a Apólice 02');

    await act(async () => {
      fireEvent.change(select('B'), { target: { value: 'pol_b' } });
    });
    expect(button).toBeEnabled();
    expect(button).not.toHaveTextContent(/Escolha/);
  });

  it('alerta quando as duas apólices são iguais', async () => {
    await openRoute('#/comparar');
    await act(async () => {
      fireEvent.change(select('A'), { target: { value: 'pol_a' } });
      fireEvent.change(select('B'), { target: { value: 'pol_a' } });
    });
    expect(screen.getByRole('alert')).toHaveTextContent(/Escolha duas apólices diferentes/);
    expect(screen.getByRole('button', { name: /Comparar/ })).toBeDisabled();
  });

  it('recolhe o perfil de risco em "Opções avançadas", com Base como padrão', async () => {
    await openRoute('#/comparar');
    const details = screen.getByText('Opções avançadas').closest('details')!;
    expect(details).not.toHaveAttribute('open');
    fireEvent.click(screen.getByText('Opções avançadas'));
    expect(within(details).getByRole('radio', { name: /Geral \(pesos-base\)/ })).toBeChecked();
  });

  it('cria a comparação com as duas apólices e o perfil Base', async () => {
    mockApi([
      {
        match: '/api/v1/comparisons',
        method: 'POST',
        status: 202,
        body: { comparison_id: 'cmp_1', status: 'REQUESTED' },
      },
      { match: '/api/v1/policies', body: page(policies) },
    ]);
    await openRoute('#/comparar');
    await act(async () => {
      fireEvent.change(select('A'), { target: { value: 'pol_a' } });
      fireEvent.change(select('B'), { target: { value: 'pol_b' } });
    });
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Comparar/ }));
    });
    const post = fetchMock.mock.calls.find(([, init]) => init?.method === 'POST')!;
    expect(JSON.parse(post[1].body as string)).toEqual({
      policy_a_id: 'pol_a',
      policy_b_id: 'pol_b',
      selected_profile: 'BASE',
    });
  });
});
