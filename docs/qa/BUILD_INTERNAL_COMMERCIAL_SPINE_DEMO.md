# BUILD-INTERNAL-COMMERCIAL-SPINE-DEMO

**Date:** 2026-06-07  
**Build status:** PASS  
**Warn-ack prerequisite commit:** `bedc25fff8b6846680dbf27ed490a9273c31ad8e`  
**This build commit:** `821bd3735f8593104338e7683032bfbd586bff1e`

## Summary

Internal dev/onboarding entry point at `/demo/commercial-spine` with two scenario cards (ready + warn acknowledgement), live backend fixture probe, deep links to real WorkOS routes, and setup documentation.

## Route

`/demo/commercial-spine` — labeled **Internal Demo — not production workflow**; not added to sidebar.

## Files changed

| File | Change |
|------|--------|
| `frontend/src/pages/CommercialSpineDemo.tsx` | Demo page |
| `frontend/src/lib/commercialSpineDemoProbe.ts` | Browser-safe API fixture probe |
| `frontend/src/App.tsx` | Route registration |
| `frontend/e2e/commercial-spine-demo.spec.ts` | Read-only smoke test |
| `frontend/package.json` | `test:e2e:commercial-spine-demo` |
| `docs/demo/COMMERCIAL_SPINE_DEMO.md` | Operator walkthrough |
| `docs/qa/BUILD_INTERNAL_COMMERCIAL_SPINE_DEMO.md` | This doc |

## What the demo proves

- TPL-VOLUMETRIC-LETTERS commercial spine is traceable end-to-end
- Both fixture scenarios visible with expected gate fields
- Real deep links: `/quotes/:code`, `/orders/:code`, `/execution/:order_id` when data exists
- Setup commands and E2E references documented

## What it does not prove

- Public sales readiness
- Non-volumetric templates
- CostEngine / readiness policy internals

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe scripts/seed_commercial_e2e_fixture.py
cd frontend
npm run lint
npm run test:e2e:commercial-live
npm run test:e2e:commercial-warn-ack
npm run test:e2e:commercial-spine-demo
```

| Suite | Result |
|-------|--------|
| `seed_commercial_e2e_fixture.py` | PASS |
| `npm run lint` | PASS |
| `test:e2e:commercial-live` | 1/1 OK (5.4s) |
| `test:e2e:commercial-warn-ack` | 1/1 OK (5.5s) |
| `test:e2e:commercial-spine-demo` | 1/1 OK (2.4s) |

## Remaining gaps (superseded by Finalization Pack)

See `docs/qa/BUILD_VOLUMETRIC_COMMERCIAL_SPINE_FINALIZATION_PACK.md` for combined E2E, list chips, and status doc.

## Suggested next build

Production CI job: seed + `npm run test:e2e:commercial` on merge queue.
