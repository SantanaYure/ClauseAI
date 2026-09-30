import { createIdentitySession, type IdentityPort } from './identity';

const DEV_ID_KEY = 'clauseai.dev-identity';

/**
 * Identidade de desenvolvimento local: envia `Bearer dev-<id>`, aceito pelo backend com
 * AUTH_BACKEND=fake. Cada navegador guarda o próprio id; `reset` gera outro.
 */
export function createDevIdentity(storage: Storage = window.localStorage): IdentityPort {
  const newId = () => crypto.randomUUID().replaceAll('-', '');
  return createIdentitySession({
    async signIn() {
      if (!storage.getItem(DEV_ID_KEY)) storage.setItem(DEV_ID_KEY, newId());
    },
    async signOut() {
      storage.removeItem(DEV_ID_KEY);
    },
    async getToken() {
      const id = storage.getItem(DEV_ID_KEY);
      if (!id) throw new Error('Identidade de desenvolvimento ausente.');
      return `dev-${id}`;
    },
  });
}
