# Decision log — Gradi-curat pricing truth audit + logo commercial correction

**Date:** 2026-07-16  
**Workspace:** `11891d68-c4c8-4719-acc5-f8fcb22a44af`  
**Baseline HEAD:** `99d5c71`  

## Audit decisions (locked)

| ID | Decision |
|----|----------|
| D1 | Official commercial authority is CPP 7G via priced-quote-dry-run |
| D2 | Pre-correction live gross was 2606.96 RON (letters-only) |
| D3 | 725.16 EUR is internal MB cost |
| D4–D8 | Logos omitted commercially → COMMERCIAL_PARTIAL_NOT_CONFIRMABLE |
| D9 | contains_missing_prices was informational false positive |
| D10 | MIXED_CURRENCY_MISLEADING labeling |

## Owner gates (answered)

| Gate | Answer |
|------|--------|
| G1 | YES |
| G2 | YES — LINKED-CHILD-ONLY |
| G3 | YES — COMPONENTIZED COMMERCIAL RULE |
| G4 | YES — LOGO ILLUMINATION INCLUDED |
| G5 | SITE INSTALLATION REQUIRED / PACKAGING DEFERRED |

## Implementation decisions

| ID | Decision |
|----|----------|
| I1 | Idempotent `seed_tpl_volumetric_logo_v1` only (not root offerable) |
| I2 | CPP linked-logo evaluation under letters root |
| I3 | Reuse DEV_BRIDGE classes for logo face/return/back/LED |
| I4 | Print/laminate/application fail-closed until owner tariffs **or binding to existing registry rates** |
| I5 | LED split letters vs emblem; no double count |
| I6 | Montaj required when installation included |
| I7 | Packaging deferred optional |
| I8 | Informational led_total_watts excluded from missing-price flag |

## Pricing Registry UI audit (2026-07-16) — STOP before new tariff asks

**Proof:** Live browser inspection of `http://127.0.0.1:3000/inventory/pricing` + `GET /api/v1/pricing/registry`.  
**Evidence:** `docs/qa/gradi-curat-e2e/pricing-registry-ui-audit-2026-07-16.md`

| Missing commercial line | Verdict | Action |
|-------------------------|---------|--------|
| Logo print (`VOL_V2_LOGO_PRINT_M2`) | **EXISTING_TARIFF_BINDING_DEFECT** | Reuse `LARGE_FORMAT_PRINT` 8.50 EUR/mp — do **not** ask owner for a new print rate |
| Logo laminate (`VOL_V2_LOGO_LAMINATE_M2`) | **EXISTING_TARIFF_BINDING_DEFECT** | Reuse `LAMINATION` 5.00 EUR/mp — ignore stub `SVC-LAMINATION-SERVICE` (buc / missing) |
| Logo application (`VOL_V2_LOGO_APPLICATION_M2`) | **EXISTING_TARIFF_BINDING_DEFECT** | Reuse `FACE_VINYL_APPLICATION_LABOR` 5.00 EUR/mp |
| Site install montaj (`VOL_V2_SITE_MOUNT_FUTURE`) | **TRUE_OWNER_TARIFF_MISSING** | Only eligible owner new-tariff ask |
| Installation template materials | **EXISTING_TARIFF_REUSABLE** | `MAT-SABLON-HARTIE` / `MAT-SABLON-MONTAJ` already Owner-confirmed |
| Mounting accessories | Not site-install labor | `MAT-CONSUMABILE-MONTAJ` needs_review; `MAT-SURUBURI-GEN` ACM-only |

### Owner decision pack T1–T6 (revised)

Only `TRUE_OWNER_TARIFF_MISSING` may be in T1–T6:

| ID | Ask |
|----|-----|
| **T1** | Define **site installation (montaj șantier)** commercial tariff for `MONTAJ_COMMERCIAL_RULE` / `VOL_V2_SITE_MOUNT_FUTURE` (CPP unit: `locatie` / fixed). No equivalent row exists under any alias in Pricing Registry. |
| T2–T6 | **Vacant** — do not invent duplicate print/laminate/application tariffs |

**Optional non-T reuse confirmation (not a new rate):** confirm CPP may bind logo finish lines to existing letters rates `LARGE_FORMAT_PRINT` / `LAMINATION` / `FACE_VINYL_APPLICATION_LABOR` (EUR/mp), including commercial currency conversion policy vs current RON CPP body lines.

## Remaining (post binding correction)

1. ~~Engineering: bind logo print/laminate/application to existing registry rates~~ **DONE** — `LARGE_FORMAT_PRINT` / `LAMINATION` / `FACE_VINYL_APPLICATION_LABOR` via `registry_pricing_code` + company EUR→RON settings.
2. Owner: **T1 only** — site installation commercial tariff (`MONTAJ_COMMERCIAL_RULE`).
3. Then same-workspace dry-run → commercial ready / Confirmare.
