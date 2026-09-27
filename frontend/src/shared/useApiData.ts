import { useCallback, useEffect, useState, useSyncExternalStore } from 'react';
import { ApiError, dataEvents } from '../services/api/clause-api';

export type LoadState<T> =
  { status: 'loading' } | { status: 'error'; message: string } | { status: 'success'; data: T };

type KeyedState<T> = { key: string; state: LoadState<T> };

type Options<T> = {
  /** Intervalo de atualização enquanto `shouldPoll` for verdadeiro (SPEC-014). */
  pollMs?: number;
  shouldPoll?: (data: T) => boolean;
};

function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    return error.correlationId
      ? `${error.message} (correlação ${error.correlationId})`
      : error.message;
  }
  return error instanceof Error ? error.message : 'Não foi possível carregar os dados.';
}

/**
 * Carrega dados da API e recarrega quando outra tela cria dados.
 * `key` identifica a consulta; ao mudar, a tela volta ao estado de carregamento.
 */
export function useApiData<T>(
  key: string,
  load: () => Promise<T>,
  options: Options<T> = {},
): LoadState<T> & { reload: () => void } {
  const version = useSyncExternalStore(dataEvents.subscribe, dataEvents.getVersion);
  const [attempt, setAttempt] = useState(0);
  const [current, setCurrent] = useState<KeyedState<T> | null>(null);

  useEffect(() => {
    let active = true;
    load()
      .then((data) => {
        if (active) setCurrent({ key, state: { status: 'success', data } });
      })
      .catch((error: unknown) => {
        if (active) setCurrent({ key, state: { status: 'error', message: describeError(error) } });
      });
    return () => {
      active = false;
    };
    // `load` é recriada a cada render; `key` representa suas dependências.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, version, attempt]);

  const state: LoadState<T> =
    current && current.key === key ? current.state : { status: 'loading' };

  const { pollMs, shouldPoll } = options;
  const polling =
    pollMs !== undefined && state.status === 'success' && (shouldPoll?.(state.data) ?? true);

  useEffect(() => {
    if (!polling) return;
    const timer = setTimeout(() => setAttempt((value) => value + 1), pollMs);
    return () => clearTimeout(timer);
  }, [polling, pollMs, current]);

  const reload = useCallback(() => {
    setCurrent(null);
    setAttempt((value) => value + 1);
  }, []);

  return { ...state, reload };
}
