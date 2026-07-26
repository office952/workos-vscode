# V2 Pilot Runtime Proof — POST SEED

**Task:** `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_V2_RUNTIME_PROOF_POST_SEED`  
**Date:** 2026-07-14  
**Worktree:** `C:\w\psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `9366a74` (+ pre-existing uncommitted implementation)  
**Accepted base HEAD:** `82a713e`  
**Seed rerun:** NO (post `FIXTURE_ACTIVATION_PASS`)

## Verdict

**`PASS_V2_PILOT_WITH_LEGACY_BRIDGE`**

Snapshot/execution sub-verdict: **`PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA`**

## Stack (1 start)

| Service | PID | Port | Stable | Notes |
|---------|-----|------|--------|-------|
| Backend | 11352 (reused) | 8000 | YES | Coordinator detected existing listener; health/OpenAPI 200 |
| Frontend | 12712 | 3000 | YES | Fresh vite from `npm run dev:stack` |

- **Command:** `npm run dev:stack` with `WORKOS_PYTHON=C:\Users\offic\workos_app_vs\backend\.venv\Scripts\python.exe`
- **Database:** `C:\w\psiso\backend\dev.db`
- **Coordinator:** single runtime owner; no duplicate stack starts

## Safety gate

| Check | Result |
|-------|--------|
| Workspace / git root | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `9366a74` |
| Pre-start ports | `:8000` ghost listener reused; `:3000` free then bound |
| Runtime application-code changes | **NO** (read-only probes + QA artifacts only) |

## Catalog population

| Requirement | Result |
|-------------|--------|
| Catalog not empty | **PASS** — LIVE / DB banner; operational products visible |
| No `Live DB (gol)` | **PASS** |
| Letters V2 visible | **PASS** — `TPL-VOLUMETRIC-LETTERS_v2` |
| ACM visible | **PASS** — `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| Premount visible in catalog list | **PARTIAL** — API offerable; direct URL/detail PASS; not listed under operational cards (FUNCTIONAL gap) |
| Canonical codes | **PASS** |
| No active legacy duplicate | **PASS** — `TPL-VOLUMETRIC-LETTERS` absent from DB |
| No five-bucket legacy regression | **PASS** — single operational + advanced split |
| Direct navigation / refresh | **PASS** on tested routes |

## Identity matrix (live API)

Probe: `docs/qa/product-system-active-path-isolation-v1/_post_seed_probe_out.json`

| Case | Endpoint | Requested | Status | Canonical in response | Verdict |
|------|----------|-----------|--------|----------------------|---------|
| canonical | aggregate | `TPL-VOLUMETRIC-LETTERS_v2` | 200 | `TPL-VOLUMETRIC-LETTERS_v2` | PASS |
| canonical | product-definition | `TPL-VOLUMETRIC-LETTERS_v2` | 200 | `TPL-VOLUMETRIC-LETTERS_v2` | PASS |
| trim | aggregate / product-definition | `  TPL-VOLUMETRIC-LETTERS_v2  ` | 200 | canonical casing restored | PASS |
| case | aggregate / product-definition | `tpl-volumetric-letters_v2` | 200 | canonical casing restored | PASS |
| legacy compile | aggregate | `TPL-VOLUMETRIC-LETTERS` | 422 | `resolution_type=rejected_alias`, `legacy_alias_used=true` | PASS |
| unknown | aggregate | `TPL-UNKNOWN-ALIAS` | 404 | `template_not_found` | PASS |

All three canonical templates — aggregate 200 with stored canonical code. ProductDefinition: Letters + ACM 200; Premount 404 `product_definition_preview_not_found` (**`ROOT_OFFERABLE_WITHOUT_CURRENT_FORM_CONTRACT`** — not a capability-policy failure).

## V2 Dossier authority (live)

| Question | Answer |
|----------|--------|
| Is Dossier independent product truth? | **NO** |
| Is Dossier a parallel compiler input? | **NO** |
| Can approved Dossier introduce components? | **NO** (runtime compile uses canonical contracts) |
| Can approved Dossier introduce operations? | **NO** |
| Can approved Dossier introduce task rules? | **NO** |
| Can approved Dossier override variants? | **NO** |
| Can approved Dossier control output blocks? | **NO** |
| Can Dossier bypass canonical contracts? | **NO** |
| Can operator write directly? | **NO** — product detail Dossier tab readonly; no inline editor |
| Can Advanced/Admin inspect metadata/provenance? | **YES** — entity API returns 4 approved dossiers with provenance fields; Blueprint Dossier UI placeholder (Active 0) |

DB: `product_blueprint_dossier=4`. Operator UI: *"Contract readonly de readiness — dossier-ul complet trăiește în editorul de șablon."*

## ACM capability truth

`TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`

| Field | Expected | Live |
|-------|----------|------|
| root_offerable | true | true |
| linked_child_offerable | true | true |
| internal_only | false | false |
| db_active | true | true |
| ProductAggregate | 200 | PASS |
| ProductDefinition | 200 | PASS |
| Catalog card | visible | PASS |
| Detail route | `/product-system/products/TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | PASS |

## Premount capability truth

`TPL-METAL-PREMOUNT-STRUCTURE_v1`

| Field | Expected | Live |
|-------|----------|------|
| root_offerable | true | true |
| linked_child_offerable | true | true |
| internal_only | false | false |
| db_active | true | true |
| ProductAggregate | 200 | PASS |
| ProductDefinition | 404 | **`ROOT_OFFERABLE_WITHOUT_CURRENT_FORM_CONTRACT`** |
| Detail route (direct) | PASS | PRODUS OFERTABIL |
| Catalog list card | expected visible | **MISSING from operational list** (FUNCTIONAL) |

## Snapshot / execution

Existing rows only — **no fabrication**.

| Table | Rows |
|-------|------|
| `quote_snapshots_v2` | 0 |
| `orders` | 0 |
| `execution_plan` | 0 |

**Verdict:** `PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA` — does not invalidate V2 identity/dossier/capability pilot.

## UI routes

| Route | Direct | Refresh | Result |
|-------|--------|---------|--------|
| `/product-system/products` | PASS | PASS | Populated catalog |
| `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` | PASS | PASS | Detail + tabs |
| `/product-system/products/TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | PASS | PASS | Detail + tabs |
| `/product-system/products/TPL-METAL-PREMOUNT-STRUCTURE_v1` | PASS | PASS | Detail offerable |
| `/inventory/pricing` | PASS | PASS | Registry populated for Letters V2 |
| `/product-system/blueprint-dossier` | PASS | PASS | Placeholder admin surface |

## Figma comparison

**File:** `911Q6oRKcEursrRoT4Qj0h` — Page 11 — Product System (Canonical Plan)  
**Account:** ERP PUBLIMEDIA / office@p-media.ro

| Node | Runtime URL | Severity | Verdict |
|------|-------------|----------|---------|
| 7:6 Catalog | `/product-system/products` | FUNCTIONAL | PARTIAL — structure matches; Premount missing from list; readiness badges differ |
| 7:18 Detail | `/product-system/products/TPL-VOLUMETRIC-LETTERS_v2` | FUNCTIONAL | PARTIAL — tab naming differs (Prezentare vs Overview); content present |
| 7:29 Unavailable | natural unavailable N/A post-seed | NONE | PASS — no forced unavailable state |
| Dossier operator/admin frames | — | — | **NO_RELEVANT_FIGMA_FRAME** |

## Screenshots (post-seed, real runtime)

| File | URL | PASS |
|------|-----|------|
| `01-canonical-catalog.png` | `/product-system/products` | YES |
| `02-canonical-product-detail-letters.png` | `.../TPL-VOLUMETRIC-LETTERS_v2` | YES |
| `03-canonical-product-detail-acm.png` | `.../TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | YES |
| `04-canonical-product-detail-premount.png` | `.../TPL-METAL-PREMOUNT-STRUCTURE_v1` | YES |
| `05-dossier-operator-state.png` | Letters detail → Dossier tab | YES |
| `06-dossier-advanced-admin-state.png` | `/product-system/blueprint-dossier` | YES (placeholder UI) |

## Scope compliance

- Application source: **unchanged during runtime phase**
- Allowed artifacts updated under `.compound-engineering/...` and `docs/qa/...`
- `backend/dev.db`: **not staged/committed**
- Ephemeral probes: `_post_seed_runtime_probe.py`, `_post_seed_probe_out.json`, `_snapshot_tables_probe.py`

## Remaining blockers

1. Snapshot chain proof requires separate fixture owner GO.
2. Premount catalog list visibility (UI filter) — follow-up, not V2 isolation regression.
3. Blueprint Dossier studio list shows Active (0) despite 4 entity rows — admin UI wiring follow-up.

## Delivery footer

| Field | Value |
|-------|--------|
| Runtime started | **YES** |
| Stack starts | **1** |
| Backend stable | **YES** |
| Frontend stable | **YES** |
| Catalog populated | **YES** |
| Figma plugin used | **YES** |
| Runtime screenshots complete | **YES** |
| Identity runtime proven | **YES** |
| V2 Dossier isolated (V2 pilot scope) | **YES** |
| ACM capability proven | **YES** |
| Premount capability proven | **YES** (form contract gap documented) |
| Snapshot/execution | **PARTIAL** |
| Application code changed | **NO** |
| DB committed | **NO** |
| Ready for `/ce-code-review` | **YES** |
| Verdict | **`PASS_V2_PILOT_WITH_LEGACY_BRIDGE`** |
