import '@testing-library/jest-dom/vitest';
import { vi } from 'vitest';

window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;
