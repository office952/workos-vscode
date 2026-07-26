// Minimal window mock for Vitest node environment
if (typeof globalThis.window === 'undefined') {
  globalThis.window = {};
}

// Enable jest-dom matchers (toBeInTheDocument, etc.)
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
});
