/**
 * Test runner boundary:
 * - Vitest (pnpm test / vitest run): unit + integration under src/** only.
 * - Playwright (pnpm test:e2e): browser e2e under e2e/** — never collected here.
 */
import tsconfigPaths from 'vite-tsconfig-paths';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [tsconfigPaths()],
  test: {
    globals: true,
    setupFiles: ['./vitest.setup.global.js'],
    environment: 'happy-dom',
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      'e2e/**',
      '**/e2e/**',
    ],
  },
});
