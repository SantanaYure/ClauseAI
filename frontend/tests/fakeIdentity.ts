import { vi } from 'vitest';
import { createIdentitySession, type IdentityProvider } from '../src/services/auth/identity';

type FakeOptions = {
  /** Falha no signIn (ex.: armazenamento bloqueado). */
  failSignIn?: boolean;
  /** Mantém o signIn pendente até `release()`. */
  manual?: boolean;
};

/** Provedor de identidade sem rede: tokens `token-<n>` e contadores inspecionáveis. */
export function createFakeIdentity({ failSignIn = false, manual = false }: FakeOptions = {}) {
  let generation = 1;
  let refreshes = 0;
  let shouldFail = failSignIn;
  let release: () => void = () => undefined;

  const provider: IdentityProvider = {
    signIn: vi.fn(async () => {
      if (manual) await new Promise<void>((resolve) => (release = resolve));
      if (shouldFail) throw new Error('storage blocked');
    }),
    signOut: vi.fn(async () => {
      generation += 1;
      refreshes = 0;
    }),
    getToken: vi.fn(async (forceRefresh: boolean) => {
      if (forceRefresh) refreshes += 1;
      return `token-${generation}${refreshes ? `-r${refreshes}` : ''}`;
    }),
  };

  return {
    identity: createIdentitySession(provider),
    provider,
    release: () => release(),
    setFailSignIn: (value: boolean) => {
      shouldFail = value;
    },
  };
}
