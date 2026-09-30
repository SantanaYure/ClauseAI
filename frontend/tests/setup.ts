import '@testing-library/jest-dom/vitest';
import { beforeEach, vi } from 'vitest';
import { setIdentity } from '../src/services/api/clause-api';
import { createFakeIdentity } from './fakeIdentity';

window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;

beforeEach(() => {
  setIdentity(createFakeIdentity().identity);
});
