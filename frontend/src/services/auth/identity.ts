// Porta de identidade anônima por navegador. O restante do app depende só desta abstração;
// o Firebase fica isolado em firebaseIdentity.ts.

export type IdentityStatus = 'idle' | 'loading' | 'ready' | 'error';

export interface IdentityPort {
  getStatus(): IdentityStatus;
  /** Avisa mudanças de status (para `useSyncExternalStore`). */
  subscribe(listener: () => void): () => void;
  /** Garante uma identidade ativa; nova tentativa se a anterior falhou. */
  ready(): Promise<void>;
  /** Token de acesso atual; `forceRefresh` pede um token novo ao provedor. */
  getToken(forceRefresh?: boolean): Promise<string>;
  /** Descarta a identidade atual e cria um novo espaço anônimo. */
  reset(): Promise<void>;
}

/** Operações mínimas que um provedor concreto (Firebase, desenvolvimento, testes) implementa. */
export interface IdentityProvider {
  signIn(): Promise<void>;
  signOut(): Promise<void>;
  getToken(forceRefresh: boolean): Promise<string>;
}

export class IdentityUnavailableError extends Error {
  constructor() {
    super('Não foi possível criar a identidade anônima deste navegador.');
    this.name = 'IdentityUnavailableError';
  }
}

/** Máquina de estados comum a todos os provedores: idle → loading → ready | error. */
export function createIdentitySession(provider: IdentityProvider): IdentityPort {
  let status: IdentityStatus = 'idle';
  let pending: Promise<void> | null = null;
  const listeners = new Set<() => void>();

  const setStatus = (next: IdentityStatus) => {
    if (next === status) return;
    status = next;
    listeners.forEach((listener) => listener());
  };

  const track = (operation: () => Promise<void>): Promise<void> => {
    pending = operation()
      .then(
        () => setStatus('ready'),
        () => {
          setStatus('error');
          throw new IdentityUnavailableError();
        },
      )
      .finally(() => {
        pending = null;
      });
    return pending;
  };

  const ready = (): Promise<void> => {
    if (pending) return pending;
    if (status === 'ready') return Promise.resolve();
    setStatus('loading');
    return track(() => provider.signIn());
  };

  return {
    getStatus: () => status,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    ready,
    async getToken(forceRefresh = false) {
      await ready();
      return provider.getToken(forceRefresh);
    },
    // Mantém o status "ready" durante a troca para não desmontar a tela atual;
    // chamadas à API feitas nesse intervalo aguardam o novo espaço.
    reset: () =>
      track(async () => {
        await provider.signOut();
        await provider.signIn();
      }),
  };
}
