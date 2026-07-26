# UI-TRUTH-01B — Owner gates and unpause plan

**Task:** `UI-TRUTH-01B` / `BANNER_RENDERING_AND_ROMANIAN_TERMINOLOGY`  
**Type:** Planning + owner decision only — **no implementation**  
**Date:** 2026-07-17  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verified HEAD:** `3c149ab` (Wave 7 OWNER_ACCEPTED)  
**Status:** **PAUSED** — awaiting owner unpause GO  
**Verdict (planning):** `UI_TRUTH_01B_OWNER_GATES_READY`

---

## 1. Canonical definition (extracted, not invented)

| Field | Value |
|-------|-------|
| Exact title | **Banner rendering and Romanian terminology** |
| Full ID | `UI-TRUTH-01B-BANNER-RENDERING-AND-ROMANIAN-TERMINOLOGY` |
| Parent plan | UI-TRUTH-01 — Environment banner operational health truth (Option C) |
| Current status | **PAUSED** (owner 2026-07-15; still paused after Wave 7) |
| Dependency | **UI-TRUTH-01A COMPLETE** — `useRuntimeHealth` + types + normalizers; **banner visual UNCHANGED** |
| Downstream | UI-TRUTH-01C (failure/stale/drill-down) · 01D (test matrix) · 01E (runtime visual proof); **APP-AUTH-06C BLOCKED** until 01B+01E |
| Authority artifacts | `docs/worklog/runtime/2026-07-15_ui_truth_01_*.md` · `ui_truth_01/` · `ui_truth_01a/next_integration_contract.json` · `implementation_breakdown.json` |
| Existing DoD (from UI-TRUTH-01 breakdown) | Wire `useRuntimeHealth` → `EnvironmentBanner` + new `RuntimeStatusSummary`; replace `LIVE/DB` with Option C segments; Romanian labels; per-segment color/icon; component tests; visual proof on intake + orders |

### Pause reason (exact)

Owner decision **2026-07-15 post-01A** (session ledger): pause **UI-TRUTH-01B–01E** and return attention to **APP-AUTH-06C** / later FLEX / Wave 7 spine work. Pause was **priority sequencing**, not a technical blocker. Hook foundation remains valid; banner still **MISLEADING**.

### What is NOT in scope for 01B (from existing plan)

- UI-TRUTH-01C drill-down / diagnostics-gated DB confirm (follow-on)
- Full 25-case test matrix (01D) and final 7-state evidence pack (01E) — may share tests in 01B minimally, but full matrix stays 01D/01E unless owner expands
- Navigation redesign, layout modernization, new status engine
- Backend product behavior / health contract rewrite
- Wave 7 / PostJobTruth / TE2E-028 / FLEX-02 / Logo / PreOrder

---

## 2. Problem statement (operator-visible)

**Primary defect (still live at HEAD `3c149ab`):**

Global `EnvironmentBanner` maps `authState === authenticated` → green **`LIVE / DB — Sursa de date: backend live`**.

This:

- treats session success as backend availability;
- treats backend availability as DB proof;
- can stay green while routes show Network Error;
- contradicts Module Chain health (separate poller on `/modules`);
- uses EN short labels forbidden by Option C terminology matrix.

**Live proof (2026-07-17):** `http://127.0.0.1:3000/dashboard` shows `LIVE / DB` + `Sursa de date: backend live` while authenticated. Header still exposes mock **`2 critical`** (demo alerts — separate STALE path; out of 01B core unless G1 expands).

**Foundation ready:** `useRuntimeHealth` polls same-origin `/api/v1/system/health` (+ version); **not imported** by `EnvironmentBanner`.

---

## 3. UI-TRUTH-01A dependency result

| Check | Result |
|-------|--------|
| Types `runtimeStatus.ts` | Present |
| `runtimeHealth.ts` normalizers | Present |
| `useRuntimeHealth` hook | Present; tests exist; **unwired to UI** |
| Banner visual | Unchanged — defect remains |
| Same-origin health | Canonical `:3000` → proxy → `:8001` |
| Verdict | **DEPENDENCY READY** — safe to unpause 01B |

---

## 4. Banner inventory (operational priority)

| Page | Banner/component | Trigger | Source truth | Visible text | Status |
|------|------------------|---------|--------------|--------------|--------|
| Global shell | `EnvironmentBanner` | `authState` + mock flags | Auth only — **no health API** | `LIVE / DB — Sursa de date: backend live` | **MISLEADING** — **01B primary** |
| Global header | `AppShell` critical badge | `productionAlerts` | **Mock** `mockData` | `2 critical` | **STALE** — recommend OUT_OF_SCOPE V1 or OWNER_DECISION |
| Global (unused) | `useRuntimeHealth` | Poll health/version | `/api/v1/system/health` | *(not rendered)* | **CORRECT** foundation |
| `/modules` | ModuleChain health cards | Local 30s poll | Same health API | Aggregate WARNING/OK | **DUPLICATE** poller — must not contradict banner after 01B |
| Intake V6 | `IntakeV6SmartBanner` | Analyzer / unsaved | Workspace state | RO operational | **CORRECT** — OUT_OF_SCOPE V1 |
| Intake V6 Review | Operator blocker banner | Handoff/capture blockers | Backend codes → RO map | `probleme blochează…` | **CORRECT** — OUT_OF_SCOPE V1 |
| Intake V6 Review | `IntakeV6ReviewHandoffBlockerBanner` | Orphan | Handoff | Blocked confirm copy | **DUPLICATE/DEAD** — do not expand 01B to delete unless tiny safe cleanup |
| Quotes/Orders | Freeze / policy notices | Spine / status | Hardcoded RO policy | Snapshot înghețat… | **CORRECT** — OUT_OF_SCOPE V1 |
| Quotes | `SnapshotGovernanceStatus` | — | — | — | **DEAD** — OUT_OF_SCOPE |
| Execution / Post-Job | Plan gates + `PostJobTruthPanel` | Plan/API | Mix RO + EN title | `Post-job truth` EN | **TECHNICAL_ONLY** mix — OUT_OF_SCOPE V1 (Wave 7 closed) |
| `/governance` | Honesty / TabHonesty | Always | Honesty baseline | read-only RO | **CORRECT** — OUT_OF_SCOPE |
| `/modules` | Honesty strip | Always | Hardcoded RO | proiecție read-only | **CORRECT** — OUT_OF_SCOPE |
| Inventory | Critical stock | Stock status | Inventory data | material(e) critică | **CORRECT** domain — OUT_OF_SCOPE |

**01B V1 focus:** global EnvironmentBanner Option C + shared summary component. Do not reopen Wave 7 Post-Job wording in this build.

---

## 5. Terminology rules (authoritative for 01B)

**Authorities:**

1. UI-TRUTH-01 `terminology_matrix.json` — **banner segment strings** (binding for 01B)
2. `WORKOS_UI_TERMINOLOGY_REGISTRY.md` — product spine labels (do not silently rename nav in 01B)
3. G13 / UTF-8 — mandatory diacritics on all new RO text

### Banner Option C segments (01B canonical)

| Technical segment | Romanian operator term | Allowed exceptions |
|-------------------|------------------------|--------------------|
| Session | **Sesiune** (+ `Sesiune expirată` / `Sesiune neautentificată` / `Sesiune dev`) | Auth debug codes in tooltip only |
| Backend | **Backend** (+ `disponibil` / `cu avertisment` / `indisponibil` / `critic`) | Health `status` enum stays EN in API |
| Database | **DB** / **Baza de date** (+ `neverificată` / `necunoscută` / `confirmată`) | Confirmed only via authorized diagnostics (01C) |
| Environment | **Mediu** / **Local** / **Mod demo** | `VITE_*` names stay EN in logs |

**Replace (forbidden after 01B):** `LIVE / DB`, `Sursa de date: backend live`, `DEV / MOCK`, `DEV / NO AUTH` as operator primary labels.

### Broader spine terms (do not rewrite whole app in 01B)

| Technical term | Romanian operator term | Where used | Allowed exceptions |
|----------------|------------------------|------------|-------------------|
| Work Intake | Preluare lucrare | Registry APPROVED | Nav may stay EN until dedicated nav pass |
| ProductDefinition | Definiție produs | Registry | PD debug |
| ProductAggregate | Structura tehnică a produsului | Registry | Tech note „Agregat/BOM” |
| Quote | Ofertă / Oferte | Nav RO | Route `/quotes` |
| Order | Comandă / Comenzi | Nav RO | Route `/orders` |
| ExecutionPlan | Plan de execuție | Registry / honesty | — |
| Execution Reality | Realitate execuție (short: Execuție) | Dual short label OK on nav | — |
| Post-job | analiză post-job / Post-job (tech title) | Panel EN title | OUT_OF_SCOPE 01B |
| Reconciliation states | potrivit / parțial / fără actual / varianță | PostJobTruthPanel | Wave 7 closed — do not reopen |
| Blocked / Partial | Blocat / Parțial | Registry | — |
| Missing data | Câmpuri lipsă / neînregistrat | Context-specific | — |

**Rules:** operator UI Romanian; IDs/API/logs English; no silent rename of enums/routes/DB; G13 UTF-8 mandatory.

---

## 6. Runtime truth map (every banner one trigger)

| Segment | Backend / source field | Frontend mapping | Fallback | Severity | Blocking? |
|---------|------------------------|------------------|----------|----------|-----------|
| Sesiune | `AuthContext.authState` | Separate from health hook | `Sesiune neautentificată` / loading | amber/red if unauth | Soft (auth gate elsewhere) |
| Backend | `GET /api/v1/system/health` → `status` | `useRuntimeHealth` normalizer | `Backend indisponibil` on fail/timeout | emerald / amber / red | Informational strip (routes show own errors) |
| DB | Public health `checks: {}` → unknown; diagnostics later (01C) | `DB neverificată` / `necunoscută` | Never invent „DB OK” from auth | neutral / help icon | Informational |
| Mediu | `GET /api/v1/system/version` + mock flags | Local / demo / unknown | `Mediu necunoscut` | neutral / amber demo | Informational |

**UI truth rule:** Frontend renders mapped segments; does not invent commercial readiness; does not claim DB confirmed without diagnostics; must not stay emerald when backend fetch failed.

---

## 7. Candidate builds

| Candidate | Problem solved | Value | Risk | Recommendation |
|-----------|----------------|-------|------|----------------|
| **A — Shared banner truth normalization** | Wire hook + Option C segments + `RuntimeStatusSummary` | High — fixes global MISLEADING trust | Narrow-screen overflow; ModuleChain dual poll | **RECOMMENDED** |
| **B — Terminology-only correction** | Rename LIVE/DB strings without health | Low — still lies about DB/backend | False sense of fix | Reject |
| **C — Banner + broad operational terminology** | A + Intake/PostJob/nav renames | Diffuse | Scope creep; Wave 7 reopen | Reject for V1 |

---

## 8. Recommended coherent build (Option A)

### Objective

> On active WorkOS pages, the global environment banner consistently reflects separated session/backend/DB/environment truth, uses approved Romanian terminology with correct diacritics, and never shows green `LIVE / DB` from auth alone.

### Pages (G1 default recommendation)

| URL | Role in V1 |
|-----|------------|
| `http://127.0.0.1:3000/intake` or active Intake V6 workspace | Visual smoke — healthy/warning |
| `http://127.0.0.1:3000/orders` | Visual smoke — global strip |
| `http://127.0.0.1:3000/modules` | Non-contradiction with ModuleChain health |
| Any authenticated route | Global strip always present |

**Exclude V1:** header `N critical` mock (unless G1=EXPAND); Post-Job EN title; full nav Romanian pass; Inventory critical stock.

### Components / files (expected)

| Path | Change |
|------|--------|
| `frontend/src/components/workos/EnvironmentBanner.tsx` | Consume `useRuntimeHealth` + session; Option C render |
| `frontend/src/components/workos/RuntimeStatusSummary.tsx` | **New** — segment summary (per 01A contract) |
| `EnvironmentBanner.test.tsx` | Happy / warning / unauth / mock |
| Optional tiny: ModuleChain note only if contradiction proven — prefer share hook later (01C/01E) |

### Boundaries

- No backend changes
- No Wave 7 / PostJobTruth / UTF-8 tooling
- No DB mutation; do not touch Build 1 / 92403
- No policy invent; G13 already covers UTF-8
- Keep 01C diagnostics drill-down out unless owner collapses 01B+01C (not recommended)

### Tests

| Category | Scope |
|----------|-------|
| Unit | Label maps from `terminology_matrix.json` targets |
| Component | Segment visibility, severity colors, mock/unauth, no LIVE/DB |
| Page regression | Mount on App shell; snapshot or RTL smoke |
| HTTP truth | With stack up: banner backend segment matches `GET /api/v1/system/health` status |
| Visual smoke | See §9 |
| UTF-8 | All new strings: disponibil, avertisment, neverificată, necunoscută, Sesiune — no mojibake |

### Visual proof plan

| URL | State | Expected banner (compact) | Severity | Resolved behavior |
|-----|-------|---------------------------|----------|-------------------|
| `/intake` (or dashboard) | auth OK, health ok/warning, public checks empty | `Local · Backend disponibil|cu avertisment · DB neverificată` | emerald/amber backend; never full green LIVE/DB | Persist until health changes |
| `/modules` | same | Same strip; ModuleChain must not claim opposite backend health | — | No contradict |
| `/orders` | same | Same global strip | — | — |
| Mock mode | `VITE_ENABLE_MOCK_DATA` | `Mod demo · Date demonstrative` | amber | Not emerald |
| Backend down (manual) | stop backend / break proxy | `… Backend indisponibil · DB necunoscută` | red | Never green LIVE |

Use read-only stack; **do not mutate** IR-BUILD1 / 92402 / 92403.

### Commit strategy (after GO)

One coherent feature commit preferred:

`feat(ui-truth): honest runtime status banner segments`

Optional follow-up docs evidence in 01E. Avoid micro-commits for label tweaks.

---

## 9. Owner gates G1–G4

### G1 — Scope of pages

| | |
|--|--|
| Decision | Which surfaces prove V1? |
| Alternatives | **CORE** = global strip only (intake + orders + modules smoke) · **EXPAND** = + header critical badge honesty · **BROAD** = + Post-Job/nav terminology |
| Recommendation | **CORE** |
| Impact | Keeps build small; matches UI-TRUTH-01 visual checklist |
| Risk | Header `2 critical` remains STALE until later |
| Answer format | `G1 PAGINI = CORE / EXPAND / BROAD` |

### G2 — Terminology authority

| | |
|--|--|
| Decision | Which RO labels are binding for the banner? |
| Alternatives | **MATRIX** = UI-TRUTH-01 `terminology_matrix.json` only · **REGISTRY** = also force nav spine renames · **CUSTOM** = owner overrides list |
| Recommendation | **MATRIX** for banner; registry for future nav pass |
| Impact | Avoids OD-TERM nav churn inside 01B |
| Risk | Sidebar still shows Work Intake / Product System EN |
| Answer format | `G2 TERMINOLOGIE = MATRIX / REGISTRY / CUSTOM` (+ paste overrides if CUSTOM) |

### G3 — Technical code visibility

| | |
|--|--|
| Decision | Where may EN/technical codes appear? |
| Alternatives | **TOOLTIP** = compact RO strip; EN codes only in tooltip/details · **STRIP** = allow short EN tokens (Backend, DB, Local) · **HIDE** = pure RO words only |
| Recommendation | **STRIP** (Option C already uses Backend/DB/Local as approved tokens) + deeper codes in tooltip |
| Impact | Matches existing Option C plan |
| Risk | Pure RO may be verbose on mobile |
| Answer format | `G3 CODURI TEHNICE = TOOLTIP / STRIP / HIDE` |

### G4 — Banner consolidation depth

| | |
|--|--|
| Decision | Mapping-only vs new summary component vs share ModuleChain poller |
| Alternatives | **MAP** = rewrite EnvironmentBanner only · **SUMMARY** = Banner + `RuntimeStatusSummary` (plan default) · **SHARE** = also unify ModuleChain poll into shared hook now |
| Recommendation | **SUMMARY** (plan default); defer SHARE to 01C/01E unless contradiction blocks PASS |
| Impact | Matches `next_integration_contract.json` |
| Risk | Temporary dual poll until SHARE |
| Answer format | `G4 CONSOLIDARE = MAP / SUMMARY / SHARE` |

---

## 10. Dirty-tree exclusions

Intersecting 01B (expected active set after GO):

- `EnvironmentBanner.tsx` (+ tests)
- `RuntimeStatusSummary.tsx` (new)
- possibly `App.tsx` import only if wiring needs it (already mounts banner)

**Explicitly exclude from staging:** PreOrder / Product Truth prototypes · Logo · Employee Mobile · FLEX-02 · TE2E-028 product work · Wave 7 code · UTF-8 repair scripts · DB backups · unrelated QA JSON dirt · broad cleanup · PostJobTruthPanel EN title rewrite.

Current dirty tree has unrelated worklog/QA mods — **leave untouched**.

---

## 11. Modules / Governance impact

| Surface | Expected |
|---------|----------|
| Harta sistemelor | **NO NODE CHANGE**; optional evidence row after implementation |
| Guvernanța sistemului | **NO POLICY CHANGE** — G13 UTF-8 already active; Romanian-first + frontend-as-projection already in honesty baseline / Page Completion Foundation |

Optional future guardrail (owner approval only, not now): „Bannerul global de mediu nu poate infera sănătatea backend/DB din starea de autentificare.”

---

## 12. Readiness for unpause

| Question | Answer |
|----------|--------|
| Is 01A ready? | **YES** |
| Is DoD clear enough? | **YES** (existing Option C + breakdown + terminology matrix) |
| Is unpause safe? | **YES** — frontend-only; Wave 7 closed work untouched |
| Remaining owner need | **G1–G4 + UNPAUSE + IMPLEMENTARE GO** |

---

## 13. Owner decision pack — APPROVED 2026-07-17

```text
UI-TRUTH-01B = UNPAUSE
G1 PAGINI = CORE
G2 TERMINOLOGIE = MATRIX
G3 CODURI TEHNICE = STRIP
G4 CONSOLIDARE = SUMMARY
DOCS-ONLY COMMIT = DA
IMPLEMENTARE = GO
```

Binding: CORE = global shell + Intake/Orders/Modules smoke; MATRIX = `terminology_matrix.json`; STRIP = technical codes secondary; SUMMARY = `RuntimeStatusSummary`; remove auth-derived `LIVE / DB`.
