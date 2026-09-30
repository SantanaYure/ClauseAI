import { appConfig } from '../../config/env';
import { createDevIdentity } from './devIdentity';
import { createFirebaseIdentity } from './firebaseIdentity';
import type { IdentityPort } from './identity';

export function createIdentity(): IdentityPort {
  return appConfig.useDevIdentity
    ? createDevIdentity()
    : createFirebaseIdentity(appConfig.firebase);
}
