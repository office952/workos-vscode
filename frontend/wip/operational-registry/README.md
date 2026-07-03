# Operational registry WIP tests

Tests here are **outside** `src/` so they are excluded from:

- `tsc -b` (`tsconfig.app.json` includes only `src`)
- default Vitest discovery (convention: `src/**` only)

Run manually when working on the operational registry build:

```powershell
cd frontend
npx vitest run wip/operational-registry/tabletLiveBridge.test.ts
```

Move back into `src/lib/` only when the build is ready to commit.
