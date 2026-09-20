import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../src/app/App';

const { getHealth } = vi.hoisted(() => ({ getHealth: vi.fn() }));

vi.mock('../src/services/api/api-client', () => ({
  apiClient: {
    getHealth,
  },
}));

describe('App', () => {
  beforeEach(() => {
    getHealth.mockReset();
  });

  it('renders the project and shows the backend online status', async () => {
    getHealth.mockResolvedValue({ status: 'ok' });

    render(<App />);

    expect(screen.getByRole('heading', { name: 'ClauseAI' })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Backend status: Online')).toBeInTheDocument());
  });

  it('shows offline when the health check fails', async () => {
    getHealth.mockRejectedValue(new Error('connection refused'));

    render(<App />);

    await waitFor(() => expect(screen.getByText('Backend status: Offline')).toBeInTheDocument());
  });
});
