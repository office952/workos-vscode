# Runtime evidence — Layer role / template wiring audit

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD / expected served commit:** `f39c260`  
**Acceptance stack:** FE `http://127.0.0.1:3000` · BE `http://127.0.0.1:8003` (`/health` → healthy)  
**`:3001`:** down — Windows exit `3221226505` recorded as **operational incident only** (not acceptance).

## Fixture inventory (Desktop)

Path: `C:/Users/offic/Desktop/fisiere-teste-svg/`

| File | Used as |
|------|---------|
| `litere-cu-fundal-acm-segmentat.svg` | Mandatory ACM segmented |
| `litere-cu-fundal-acm-segmentat-litera-peste-imbinare.svg` | Crossing variant |
| `situatie-3.svg` | Situation 3 (same layer pattern as ACM fixtures) |
| `litere-vol-1-layer.svg` | Simple non-segmented letters |
| Also present (not mandatory walk): `gradi-curat.svg`, `LITERE-VOLUMETRICE-ACP.svg`, `logo.svg`, `litere-vol-2-layere.svg` | Inventory only |

## Paths exercised

1. **Server upload API** (`POST /workspaces/{id}/svg`) — fills `path_geometry_summary` + weak `layer_role_setup` (`auto_role=unknown`); does **not** hydrate Page 1 client analyzer UI (still shows empty “Încarcă SVG”).
2. **Client file chooser** (Page 1 “Încarcă SVG”) — frontend analyzer produces `pseudo:fill-*` layers; both ACM gray + letter red proposed as **Vector Litere**.
3. **Known wired workspace** `bd26e3d5-1e63-4e39-8e72-ebaaea501e49` (prior segmented live) — operator-corrected roles + confirmed bindings.

## Key API facts (known wired)

| Binding | Template | Status |
|---------|----------|--------|
| LETTER_VECTOR_SET | `TPL-VOLUMETRIC-FACE_v1` | CONFIRMED |
| SUPPORT_CONTOUR | `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | CONFIRMED |

| Layer | auto_role | confirmed_role |
|-------|-----------|----------------|
| `pseudo:fill-c5c6c6` | **face** | **support_panel** |
| `pseudo:fill-e31e24` | face | face |

Composition: `letters_plus_support` · recommended templates include LETTERS_v2 + ACM shell · `product_composition_confirmed=false` (still needs Confirmă compoziția).  
Segmented: `CONFIRMED`.  
PD ACM endpoint 200 · `template_code=TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` · components=3.  
Production task dry-run 200 (preview only).

## Client-path role select navigation

Workspaces after client upload (`ba331a8e-…`, `184c55b6-…`):

- Both layers proposed `face` / label **Vector Litere**
- Changing role `face` → `printed_artwork` kept `aria-current` on **Straturi**; `jumpedToConfirm=false`
- Handler: `updateLayerRole` → `LAYER_ROLE_CONFIRMATION_UPDATE` only (no `setStep`)
- Progress bar: `canAccessIntakeV6Step` opens **both** `review` and `confirm` once analysis ready — operator can manually open Confirmare without role-select auto-nav

## Screenshots (selected)

| Path | Meaning |
|------|---------|
| `screenshots/acm_segmented_ui_01_after_client_upload.png` | Both elements Vector Litere; Contur suport guidance; FinishSetup support save error visible |
| `screenshots/known_wired_02_montaj.png` | Wired ACM authority `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` in composition; Montaj IA Fundal/carcasă |
| `screenshots/acm_segmented_01_page1_after_upload.png` | Server-only upload: UI still empty upload (dual-path gap) |
| `runtime/*_ui_client_path.json` | Probes |
| `runtime/known_wired_bundle.json` | Roles/bindings/composition |
| `runtime/known_pd_letters.json` / `known_pd_acm.json` | PD |
| `runtime/known_task_dry_run.json` | Aggregate-ish dry-run |

## Letter pilot runtime closure (related)

Updated `docs/qa/workos-configurator-letter-pilot-2026-07-19/` to state PASS evidence is **only** `:3000+:8003` under commit `f39c260`; `:3001` crash is not PASS.
