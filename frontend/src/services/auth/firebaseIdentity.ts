import { initializeApp, type FirebaseOptions } from 'firebase/app';
import {
  browserLocalPersistence,
  initializeAuth,
  signInAnonymously,
  signOut,
  type Auth,
} from 'firebase/auth';
import { createIdentitySession, type IdentityPort } from './identity';

const STORAGE_PROBE_KEY = 'clauseai.storage-probe';

/** Sem armazenamento local a identidade não sobrevive ao recarregar: tratamos como falha. */
function assertLocalStorageAvailable(): void {
  window.localStorage.setItem(STORAGE_PROBE_KEY, '1');
  window.localStorage.removeItem(STORAGE_PROBE_KEY);
}

export function createFirebaseIdentity(options: FirebaseOptions): IdentityPort {
  let auth: Auth | null = null;

  const getAuth = (): Auth => {
    auth ??= initializeAuth(initializeApp(options), { persistence: browserLocalPersistence });
    return auth;
  };

  return createIdentitySession({
    async signIn() {
      assertLocalStorageAvailable();
      const instance = getAuth();
      await instance.authStateReady();
      if (!instance.currentUser) await signInAnonymously(instance);
    },
    async signOut() {
      await signOut(getAuth());
    },
    async getToken(forceRefresh) {
      const user = getAuth().currentUser;
      if (!user) throw new Error('Identidade anônima ausente.');
      return user.getIdToken(forceRefresh);
    },
  });
}
