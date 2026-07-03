# TPL-VOLUMETRIC-LETTERS — Current State Context (Bounded Builds)

**Date:** 2026-06-07  
**HEAD reference:** `f6b47cf` (process reference clarification)  
**Audience:** Cursor agents, developers — **read this first** before bounded WorkOS/ProductSystem tasks.

---

## 1. Purpose

This document is the **current-state context** for future bounded builds in WorkOS. It tells agents:

- what is already validated on `TPL-VOLUMETRIC-LETTERS` (Product 001);
- which files and docs are authoritative for the next change;
- what **not** to re-audit from zero;
- how to avoid blind-copying volumetric product rules into new templates.

Use it to **start from maturity**, not from a full repo-wide discovery pass.

---

## 2. Scope warning

> **`TPL-VOLUMETRIC-LETTERS` is a process / maturity reference, not a universal product model.**

| Use volumetric for… | Do **not** use volumetric for… |
|---------------------|--------------------------------|
| Onboarding lifecycle, readiness discipline, smoke pattern | CNC/perimeter formulas, paint tubes, Oracal/RAL rules |
| simulate-ready vs quote-ready separation | Mounting bars, ACM panel policy, vector gate blockers |
| Work Intake → QuoteWizard safe prefill pattern | Operation list, material list, task order |
| Vector Studio workflow (file + mapping + manual review) | QuoteWizard field layout, CostEngine component defs |
| Final commercial quote gate pattern | Product001 labels, volumetric assumptions |

**Universal process:** `docs/architecture/PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md` — **§2**.  
**Product-specific contract:** `TPL_VOLUMETRIC_LETTERS_INPUT_CONTRACT_AUDIT.md`, `TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md`.  
**Form architecture audit:** `TEMPLATE_SPECIFIC_FORM_ARCHITECTURE_AUDIT.md`.  
**Full intake → quote → offer flow audit (2026-06-07):** `WORK_INTAKE_QUOTES_FORMS_AND_ACTIONS_AUDIT.md` — buttons, forms, field ownership, P0 handoff fixes.

Each future template needs its **own** dossier and audit before pricing/quote logic.

> **Form UI warning:** `Product001IntakeSpecEditor` and `IntakeProductSpec` are **template-specific to volumetric letters**, not a global Work Intake form. Do **not** reuse them as the default shape for new templates (business cards, flyers, exhibition systems, etc.). Each `template_code` must ship its own intake + QuoteWizard form contract — see `TEMPLATE_SPECIFIC_FORM_ARCHITECTURE_AUDIT.md`.

### Intake form v1 structure (2026-06-07)

Operator-facing sections in `Product001IntakeSpecEditor` (JSON keys unchanged):

1. Header — `TPL-VOLUMETRIC-LETTERS` identity  
2. Ce trebuie produs — text, font, notes  
3. Dimensiuni generale — width/height/return depth, indoor/outdoor  
4. Geometrie pentru ofertare — `letter_face_area_m2`, `letter_perimeter_m`, `letter_count` (manual only)  
5. Construcție litere — back bevel, face miter, volume finish  
6. Finisaj față / colantare — Oracal metadata  
7. Vopsire / RAL — paint metadata + `paint_tube_count`  
8. Iluminare — illumination type, PSU, LED estimate (read-only)  
9. Montaj / suport — mounting, bars, Forex template  
10. Vector Studio — file readiness (unchanged security)  
11. Pregătire ofertă — simulate/final hints + **Deschide ofertare preliminară**

Field tags in UI: *Afectează calculul*, *Necesită pentru ofertă finală*, *Doar producție*, *Opțional*, *Preluat în QuoteWizard*.

### Quote workspace v1 (2026-06-07)

`TPL-VOLUMETRIC-LETTERS` uses **`VolumetricLettersQuoteFlow`** — a template-specific quote workspace integrated in the WorkOS app shell (sidebar preserved via `/quotes` route).

| Aspect | Behavior |
|--------|----------|
| Entry | Work Intake **Deschide ofertare preliminară** → `/quotes` with `templateCode=TPL-VOLUMETRIC-LETTERS` + persisted intake context |
| Routing | `QuoteWizard` delegates to `VolumetricLettersQuoteFlow`; other templates keep generic wizard |
| Primary UX | **„Cum vrei să calculezi?”** — `vector_first` / `manual_geometry` / `quick_estimate` |
| Value precedence | User edit > Work Intake `product_spec_json` > template defaults |
| Context | Compact client/request strip; client text card; materials collapsed by default |
| Photos | Context/readiness only — never CostEngine inputs |
| Cost options | Collapsed `<details>` — RAL, tubes, PSU, montaj, Forex |
| Teren | Read-only summary from intake `site_audit_json` — not CostEngine inputs |
| Right rail | Simulate status, final gate, total, CTAs |
| APIs | Unchanged — `POST simulate-cost`, `POST quotes/price`, `can_create_commercial_quote` |

**State module:** `frontend/src/lib/volumetricQuoteFlowState.ts`

---

## 3. Current validated status

| Area | Status |
|------|--------|
| **Active template scope** | Only **`TPL-VOLUMETRIC-LETTERS`** is active for owner-valid quote/pricing scope |
| **Simulate-ready** | Yes — manual baseline payload simulates without cost blockers |
| **Dossier-documented** | Yes — Blueprint Dossier v2 seeded, `approved`, `task_rules_json` + `output_blocks_json` |
| **Work Intake aligned** | Yes — Product001 spec, safe prefill, no invented geometry; `confirmed_template_code`, delivery, assignee, site audit, `ready_for_quote` persisted (build 2026-06-07) |
| **Quote workspace** | Yes — `VolumetricLettersQuoteFlow` (method-first, WorkOS shell) replaces generic QuoteWizard UX for this template |
| **QuoteWizard aligned** | Yes — non-volumetric templates still use generic wizard; volumetric routes to dedicated flow |
| **Vector Studio** | Yes — multi-layer mapping, preview, persisted analysis summary |
| **Final quote gate** | Yes — `can_create_commercial_quote` enforced on price endpoints |
| **Quote-ready (runtime)** | **Input-dependent** — satisfies gates only when vector, geometry, metadata, dossier blockers cleared |
| **Migration hygiene** | Yes — clean SQLite upgrade to s42; `dev.db` stamped (`83396d6`) — see `docs/qa/BUILD_MIGRATION_HYGIENE.md` |

**Distinction:** `simulate_ready=true` while `can_create_commercial_quote=false` is **expected** for baseline manual simulate without vector intake.

---

## 4. Current baseline

| Item | Value / rule |
|------|----------------|
| **Manual baseline simulate** | **844.41 EUR** |
| **Payload type** | Manual `quote_input` regression — **not** SVG-derived pricing |
| **Geometry** | Never invented from SVG, layer mapping, or preview |
| **SVG preview / mapping** | Orientative / readiness only — **does not** drive CostEngine totals |
| **persisted** | `simulate-cost` always `persisted=false` |

Optional regression: `back_bevel_enabled=true` → **898.41 EUR** (documented in input contract audit).

---

## 5. Major commits and what they mean

| Commit | Meaning |
|--------|---------|
| `d4264fa` | QC internal-only — does not block simulate/quote for missing workcenter rate |
| `a7022a8` | Unit-based volumetric operations (per letter, ml, mp, buc) |
| `544805d` | Paint as whole-tube material (`MAT-VOPSEA-RAL`) |
| `6f83e6b` | `paint_tube_count` in QuoteWizard |
| `cc7c2dc` | Optional `back_bevel_enabled` input |
| `2a3c321` | Captured finish/mounting options in quote_input |
| `a535b59` | Finish/mounting option pricing wired |
| `46c8260` | Mounting bar length from assembly width; profile pricing |
| `fe0be10` | Blueprint Dossier v2 seed for volumetric letters |
| `dd9fea9` | Work Intake fields aligned with quote contract |
| `ec9e57a` | Vector readiness flow (file + mapping + manual review policy) |
| `6b9f3c4` | CorelDRAW SVG sanitization (DOCTYPE-safe analysis copy) |
| `293aab6` | Manual SVG layer mapping (`svg_layer_mappings`) |
| `461de79` | Vector Studio UI — multi-layer preview and mapping |
| `eb04483` | Vector Studio saved analysis summary (no raw SVG stored) |
| `98bda64` | Final commercial quote readiness gate (backend + QuoteWizard) |
| `f6b47cf` | Docs: volumetric = process reference, not universal template |

---

## 6. Key backend files

| Path | Role |
|------|------|
| `backend/services/product_readiness_service.py` | Dossier/template readiness; vector warnings when `product_spec` present |
| `backend/services/product_system_cost_simulation_service.py` | Read-only simulate; attaches `readiness.quote_gate` |
| `backend/services/quote_orchestrator.py` | Cost snapshot / pricing orchestration |
| `backend/services/volumetric_quote_ready_policy.py` | Final commercial quote gate (`can_create_commercial_quote`) |
| `backend/services/volumetric_vector_readiness_policy.py` | Vector/file gate (`vector_gate_satisfied`) |
| `backend/services/volumetric_quote_input_policy.py` | Captured options, metadata warnings, ACM/bar profile |
| `backend/services/intake_product_spec_loader.py` | Load `product_spec_json` for gates |
| `backend/services/svg_sanitization_service.py` | Safe SVG copy for analysis |
| `backend/services/svg_layer_analysis_service.py` | Layer detection + `preview_svg` |
| `backend/services/svg_manual_layer_mapping.py` | Manual mapping targets and status derivation |
| `backend/services/svg_preview_service.py` | Safe preview builder |
| `backend/routers/vector_assets.py` | `analyze-layers`, vector asset API |
| `backend/schemas/vector_assets.py` | Request/response schemas (`manual_layer_mappings`, `mapped_by`, `preview_svg`) |
| `backend/validators/intake_product_spec.py` | Product001 `product_spec_json` validation |
| `backend/routers/quotes.py` | `_assert_commercial_quote_gate` on `POST /price` |
| `backend/routers/product_system_cost_simulation.py` | `POST /simulate-cost` (+ optional `intake_id`) |
| `backend/seeds/seed_tpl_volumetric_letters_dossier.py` | Dossier v2 seed |

---

## 7. Key frontend files

| Path | Role |
|------|------|
| `frontend/src/components/workos/Product001IntakeSpecEditor.tsx` | **TPL-VOLUMETRIC-LETTERS** intake form v1 (10 sections) + Vector Studio + quote prep |
| `frontend/src/lib/volumetricIntakeFormPrep.ts` | Quote-prep summary helpers (geometry source, missing fields) |
| `frontend/src/components/workos/VectorStudioPanel.tsx` | Vector file, mapping, manual review, readiness hints |
| `frontend/src/lib/vectorStudioPreview.ts` | Preview helpers, persisted analysis summary sync |
| `frontend/src/lib/intakeVectorLayerMapping.ts` | Manual mapping targets and helpers |
| `frontend/src/lib/intakeVolumetricSpec.ts` | Canonical intake face/mounting enums |
| `frontend/src/lib/intakeProductSpec.ts` | `IntakeProductSpec` types and parse |
| `frontend/src/lib/volumetricQuoteInput.ts` | QuoteWizard fields, payload builder, validation |
| `frontend/src/lib/volumetricQuoteReady.ts` | Human-readable quote gate blockers |
| `frontend/src/components/workos/QuoteWizard.tsx` | Preliminary simulate + commercial quote gate UI |
| `frontend/src/api/costSimulation.ts` | `simulate-cost` client (+ `intake_id`) |
| `frontend/src/api/quotes.ts` | `POST /entities/quotes/price` |

---

## 8. Key docs

| Document | Use when… |
|----------|-----------|
| `docs/architecture/PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md` | Onboarding any new template (process — **§2**) |
| `docs/architecture/TPL_VOLUMETRIC_LETTERS_INPUT_CONTRACT_AUDIT.md` | Quote input, intake, vector, quote gate policy |
| `docs/architecture/TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md` | CostEngine formulas, materials, operations |
| `docs/architecture/TPL_VOLUMETRIC_LETTERS_CURRENT_STATE.md` | **This file** — start of bounded builds |
| `docs/architecture/TEMPLATE_SPECIFIC_FORM_ARCHITECTURE_AUDIT.md` | Work Intake / QuoteWizard form ownership, registry proposal |
| `docs/architecture/WORK_INTAKE_QUOTES_FORMS_AND_ACTIONS_AUDIT.md` | End-to-end buttons, forms, handoffs, P0/P1 recommendations |

---

## 9. Current validated rules

| Rule | Detail |
|------|--------|
| No hardcoded prices | Rates from Pricing Registry / owner-confirmed seed |
| No TVA in unit costs | TVA applied at quote pricing layer |
| No invented geometry | Area/perimeter/count only manual or trusted extraction |
| No pricing from SVG preview | Preview ≠ CostEngine input |
| CostEngine regression ≠ vector analysis | 844.41 EUR baseline is manual payload |
| Simulation-ready ≠ quote-ready | `simulate_ready` vs `can_create_commercial_quote` |
| Final quote gate blocks commercial quote | HTTP 422 when blockers exist; UI disables create button |
| `support_bars` ≠ letter geometry | Support layer does not satisfy letters mapping gate alone |
| Manual layer mapping ≠ metrics | `svg_layer_mappings` does not fill `letter_face_area_m2` etc. |
| Internal-only QC does not block | `qc_letters` / `internal_only` excluded from cost blockers |
| ACM panel = separate template | `captured_option_requires_separate_template` blocks final quote here |

---

## 10. Current runtime assumptions

| Assumption | Detail |
|------------|--------|
| **Frontend** | `http://127.0.0.1:3000` — Vite dev; proxies `/api` → backend |
| **Backend** | `http://127.0.0.1:8000` — canonical API for smoke/validation |
| **Health** | `GET /health` → `{"status":"healthy"}` |
| **OpenAPI freshness** | Stale `:8000` has occurred before. Before browser/API validation, confirm OpenAPI includes vector fields: `manual_layer_mappings`, `mapped_by`, `preview_svg` on analyze-layers schema |
| **Do not validate browser against stale backend** | If OpenAPI missing fields → runtime audit/restart uvicorn before UI smoke |

**Dev auth:** Local/dev may use dev auth bypass on `:8000` (unauthenticated simulate in development).

---

## 11. Known untracked / local artifacts

Do **not** commit unless explicitly approved:

| Path | Notes |
|------|-------|
| `backend/validation_input/` | Local validation payloads |
| `exports/` | Backup/staging ZIP snapshots |
| `experiments/` | Local experiments |
| `.cursor/` | Editor rules/skills |
| `docs/architecture/PRICING_RATE_BASIS_AND_CURRENCY_AUDIT.md` | Separate audit draft |
| `.gitignore` (modified) | Local ignore tweaks — stage only if intended |

---

## 12. What not to re-audit unless touched

Skip full rediscovery for:

- Active template scope (only `TPL-VOLUMETRIC-LETTERS` active)
- Archived templates (out of quote flows)
- CostEngine formulas (unless task changes costing)
- Pricing rates / registry rows
- ProductSystem UI base structure
- SVG sanitizer security limits
- Vector Studio core behavior (mapping, preview, persisted summary)
- Final quote gate behavior (`volumetric_quote_ready_policy`)

Re-audit only when the task modifies that subsystem or tests/smoke contradict this document.

---

## 13. Bounded-search instruction for future Cursor tasks

1. **Start here** + playbook §2 + relevant audit section.
2. **Inspect only** files listed in §6–§7 for the task scope.
3. **Repo-wide search** is allowed only if:
   - a referenced file is missing;
   - runtime/API contradicts this doc;
   - tests fail unexpectedly;
   - the task explicitly enters a new subsystem (e.g. new template, new router).
4. **Do not** copy volumetric blockers, fields, or formulas into another `template_code` without owner confirmation.
5. **Smoke discipline:** API on `:8000`; no quote/order creation unless explicit dry-run; record intakes/quotes/orders counts before/after.

---

## 14. Next possible work areas (options, not decisions)

- Choose and onboard the **next ProductSystem template** (new dossier first)
- Create **template-specific dossier** for ACM casetted panel or other archived candidate
- **Quote document / output generation** from `output_blocks_json`
- Clean **git/local artifacts** (`exports/`, `validation_input/`) with owner approval
- **Trusted SVG geometry extraction** (today: manual geometry only)
- **ProductSystem template creation UI** (admin tooling)
- Harden **runtime audit** script for OpenAPI vs HEAD parity

---

## 15. PASS criteria for this document

- [x] File exists at `docs/architecture/TPL_VOLUMETRIC_LETTERS_CURRENT_STATE.md`
- [x] Process-reference warning (§2)
- [x] Current validated state (§3–§4, §9)
- [x] Bounded-search rules (§13)
- [x] Documentation-only — no runtime changes in this task
- [x] Unrelated local artifacts not committed

---

*Maintained alongside `PRODUCTSYSTEM_TEMPLATE_ONBOARDING_PLAYBOOK.md` §2. Update this file when a bounded build changes validated behavior, baseline totals, or active scope.*
