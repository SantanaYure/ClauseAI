import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const auth = {
  currentUser: null as null | { getIdToken: (force?: boolean) => Promise<string> },
  authStateReady: vi.fn(async () => undefined),
};

vi.mock('firebase/app', () => ({ initializeApp: vi.fn(() => ({})) }));
vi.mock('firebase/auth', () => ({
  browserLocalPersistence: {},
  initializeAuth: vi.fn(() => auth),
  signInAnonymously: vi.fn(async () => {
    auth.currentUser = { getIdToken: async (force?: boolean) => (force ? 'novo' : 'atual') };
  }),
  signOut: vi.fn(async () => {
    auth.currentUser = null;
  }),
}));

const { signInAnonymously, signOut } = await import('firebase/auth');
const { createFirebaseIdentity } = await import('../src/services/auth/firebaseIdentity');

const options = { apiKey: 'k', authDomain: 'd', projectId: 'p', appId: 'a' };

describe('createFirebaseIdentity', () => {
  beforeEach(() => {
    auth.currentUser = null;
    vi.mocked(signInAnonymously).mockClear();
  });
  afterEach(() => vi.restoreAllMocks());

  it('cria identidade anônima só quando não há uma guardada', async () => {
    const identity = createFirebaseIdentity(options);
    await identity.ready();
    expect(signInAnonymously).toHaveBeenCalledTimes(1);
    expect(await identity.getToken()).toBe('atual');
    expect(await identity.getToken(true)).toBe('novo');

    const again = createFirebaseIdentity(options);
    await again.ready();
    expect(signInAnonymously).toHaveBeenCalledTimes(1);
  });

  it('falha quando o armazenamento local está bloqueado', async () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('blocked', 'SecurityError');
    });
    const identity = createFirebaseIdentity(options);
    await expect(identity.ready()).rejects.toThrow();
    expect(identity.getStatus()).toBe('error');
    expect(signInAnonymously).not.toHaveBeenCalled();
  });

  it('reset troca o espaço anônimo', async () => {
    const identity = createFirebaseIdentity(options);
    await identity.ready();
    await identity.reset();
    expect(signOut).toHaveBeenCalled();
    expect(signInAnonymously).toHaveBeenCalledTimes(2);
    expect(identity.getStatus()).toBe('ready');
  });
});
