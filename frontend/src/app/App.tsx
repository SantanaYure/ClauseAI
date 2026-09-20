import { useEffect, useState } from 'react';
import { apiClient } from '../services/api/api-client';
import type { BackendStatus } from '../types/health';
import '../styles/app.scss';

const STATUS_LABELS: Record<BackendStatus, string> = {
  checking: 'Verificando…',
  online: 'Online',
  offline: 'Offline',
};

export function App() {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('checking');

  useEffect(() => {
    const controller = new AbortController();

    void apiClient
      .getHealth(controller.signal)
      .then((health) => {
        setBackendStatus(health.status === 'ok' ? 'online' : 'offline');
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') {
          return;
        }
        setBackendStatus('offline');
      });

    return () => controller.abort();
  }, []);

  return (
    <main className="app-shell">
      <section className="hero-card" aria-labelledby="app-title">
        <p className="eyebrow">MVP foundation</p>
        <h1 id="app-title">ClauseAI</h1>
        <p className="description">
          Base executável para análise e comparação inteligente de apólices D&amp;O.
        </p>
        <div className={`status status--${backendStatus}`} role="status" aria-live="polite">
          <span className="status__dot" aria-hidden="true" />
          Backend status: {STATUS_LABELS[backendStatus]}
        </div>
      </section>
    </main>
  );
}
