import { useCallback, useEffect, useSyncExternalStore, type ReactNode } from 'react';
import { LoadingState } from '../components/StateViews';
import type { IdentityPort } from '../services/auth/identity';

type AuthGateProps = {
  identity: IdentityPort;
  children: ReactNode;
  /** Tela cheia exibida quando não há como criar a identidade anônima. */
  renderError: (retry: () => void) => ReactNode;
};

/** Só libera o app (e as chamadas à API) depois que a identidade anônima está pronta. */
export function AuthGate({ identity, children, renderError }: AuthGateProps) {
  const status = useSyncExternalStore(identity.subscribe, identity.getStatus);

  const start = useCallback(() => {
    identity.ready().catch(() => undefined);
  }, [identity]);

  useEffect(start, [start]);

  if (status === 'ready') return children;
  if (status === 'error') return renderError(start);
  return (
    <div className="auth-screen">
      <LoadingState label="Preparando seu espaço privado…" />
    </div>
  );
}
