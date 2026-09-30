import type { IdentityPort } from '../services/auth/identity';
import { App } from './App';
import { AuthErrorScreen } from './AuthErrorScreen';
import { AuthGate } from './AuthGate';

export function Root({ identity }: { identity: IdentityPort }) {
  return (
    <AuthGate identity={identity} renderError={(retry) => <AuthErrorScreen onRetry={retry} />}>
      <App />
    </AuthGate>
  );
}
