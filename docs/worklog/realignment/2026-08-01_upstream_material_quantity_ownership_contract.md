# Worklog — Upstream Material Quantity & Ownership Contract

**Date:** 2026-08-01  
**Status:** PASS WITH WARNINGS  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401`

## Mini-decizie

Owner accepted audit `a1e35c9c` and authorized upstream material quantity/ownership contract (A/D), not inventory/materialize.

## Repo before

HEAD `a1e35c9c` · remote `8b960a19` · ahead 1/0 · stash intact.

## Audit commit push proof

Pushed `feat/capacity-batch-20d-scoped-b-92401` → local=remote=`a1e35c9c` · **0/0**.

## Architecture readback

Template BOM → PA materials (qty not copied from seed 0) → freeze scope → Snapshot V2 → ops-graph RO. Quantity owned at component formula path; Product Template composes.

## Alternatives

Parallel DTO / EIC heuristic / inventory qty rejected. Extended PA material + freeze apply chosen.

## Schema

See `MATERIAL_REQUIREMENT_CONTRACT.md`.

## Families

Model A: registered formulas + return_profile_linear_meter registration.  
Model D: formula-less.  
Model B: not implemented. Model C: OOS. Model E: rejected.

## Active variants / freeze / compatibility

Gate filters + face finish map; legacy 92401 → legacy_unspecified; no migration.

## Files changed

Product paths listed in report; QA pack + this worklog.

## Runtime fixture

92401 unchanged. New order fixture NOT VERIFIED.

## Tests

20 backend targeted + 207 frontend test:ci. Full pytest not gate.

## Screenshots

`docs/qa/upstream-material-quantity-ownership-contract/screenshots/`

## UI opinion

Honest status labels; task graph priority kept; no stock confusion if note retained.

## Boundaries / dead pieces / blockers / warnings

As in report. Remaining: unregistered return wrap/paint formulas; no new live order.

## Next Owner GO

Material Planning Hints RO **or** Owner decision to register remaining return formulas.

## Direction score

**98/100%**
