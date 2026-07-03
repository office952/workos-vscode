# Frontend test runners

| Runner | Command | Scope |
|--------|---------|--------|
| **Vitest** | `pnpm test` / `pnpm exec vitest run` | Unit and integration tests under `src/**` (`*.test.ts`, `*.test.tsx`) |
| **Playwright** | `pnpm test:e2e` / `pnpm exec playwright test` | Browser e2e specs under `e2e/**` (`*.spec.ts`) |

`e2e/**` is excluded from Vitest (`vitest.config.ts`). Do not import Playwright specs into Vitest runs.
