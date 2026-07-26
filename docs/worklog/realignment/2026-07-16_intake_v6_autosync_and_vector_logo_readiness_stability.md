# 2026-07-16 — Intake V6 autosync + Vector Logo readiness stability

## Starting HEAD

`f1bf618` on `feature/product-system-active-path-isolation-v1`

## Autosync root cause

Review footer `Sincronizare automata in asteptare` = `pendingSave`, not a separate autosync module.

Two defects:

1. After successful `PUT finish-setup`, local mirrors were gated by partial `buildFinishSetupSyncSignature`, while pending used a fuller compare → stuck pending.
2. Remount/HMR initialized letter/artwork via `merge(derive, payload)` but pending compared against payload-only → permanent false dirty on remount.

## Autosync fix

- Always mirror form/letter/artwork/commercial after successful persist.
- Pending compare accepts expected remount baselines (`expectedForm`, `expectedLetterGroups`, `expectedArtworkFinishes`) matching Review hydration.

## False Vector Logo warning root cause

Residual gate required **all** artwork rows `confirmed=true` (all-or-nothing). Step 1-classified Vector Logos with decided execution but `confirmed=false` dropped entire logo perimeter → false `unclassified_vector_artwork_requires_decision` and “Confirmă Logo 1/2” copy.

## Readiness / perimeter fix

- Eligible perimeter = execution decided (per logo), like letters; incomplete logo excludes only itself.
- Material breakdown emits unclassified warning only when policy residual is true; otherwise info `vector_logo_perimeter_reconciled`.
- Operator copy uses Vector Logo (no hardcoded Logo 1/2).

## GENERAL VECTOR LOGO SCALABILITY CONTRACT

Tests cover 0 / 1 / 2 / 4 logos and Logo 3 incomplete while 1/2/4 remain eligible. No hardcoded two-logo assumptions in residual math.

## Artwork → Vector Logo terminology

Operator-facing residual/readiness strings say Vector Logo; perimeter residual is technical when logos are classified.

## Runtime proof (workspace `11891d68-…`)

| Check | Result |
|-------|--------|
| Autosave status | `Preturi si materiale actualizate` |
| Remount (pricing → operator) | still synced |
| False unclassified warning | absent |
| Logo 1 / Logo 2 | Confirmat in Pasul 1 |
| Dry-run line sum | **2513.5626** unchanged |
| Logo finish lines | 6 priced (registry-bound) |
| Blocker | montaj / Confirmare (`MONTAJ_COMMERCIAL_RULE` + review) |
| Registry print/lam/app | unchanged 8.50 / 5.00 / 5.00 EUR |

## Tests

- Backend residual/scalability: **8 passed**
- Frontend readiness + hydration: **20 passed** (10 + 10)

## Remaining owner decision

TRUE_OWNER_TARIFF_MISSING — SITE INSTALLATION only.
