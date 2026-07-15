# MODULE-INT-01 — AUDIT E2E COMPOUND ENGINEERING / MODULE CHAIN V1

**Task:** `MODULE-INT-01` — `AUDIT_E2E_COMPOUND_ENGINEERING_MODULE_CHAIN_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `6acadc0` (accepted); working tree at audit time `631f062`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Backend:** `http://127.0.0.1:8001`  
**Frontend:** `http://127.0.0.1:3000`  
**Route:** `/modules`  
**Scope:** Read-only audit — no code, DB, UI, endpoint, or status mutations.

**Evidence directory:** `docs/qa/product-system-active-path-isolation-v1/module_int_01/`  
**Screenshots:** `docs/qa/product-system-active-path-isolation-v1/module_int_01/screenshots/` (7 files)

---

## Executive summary

`/modules` (nav: **Module Chain**) is a **HYBRID** page: it polls a **real** public health endpoint for an aggregate `WARNING` badge and "Live Health" connectivity, but **all architectural substance** — module cards, contract handoffs, golden rules copy, event stream, snapshot points — is **static frontend documentation**. It does **not** implement a Compound Engineering control plane. Runtime handoffs, snapshots, and events exist **off-page** in services and DB, but are neither wired nor discoverable from this route.

**Verdict:** `MODULE_CHAIN_AUDIT_BLOCKED_STATIC_DEMO_DATA`  
**Next task:** `MODULE-RUNTIME-01-EVENT-SNAPSHOT-HEALTH-CLOSURE`

---

## 1. Verdict

`MODULE_CHAIN_AUDIT_BLOCKED_STATIC_DEMO_DATA`

PASS gate failed: event stream is static reference; handoffs hardcoded; snapshot points are labels; per-module health is misleading green while aggregate shows WARNING; forbidden-field badges are UI-only; Compound Engineering is not a runtime model on this page.

---

## 2. Repository safety

- **Code changed:** NO  
- **DB changed:** NO  
- **Implementation authorized:** NO  
- **Audit artifacts only:** worklog, evidence JSON, screenshots, canonical status/task graph updates.

---

## 3. Starting HEAD

Accepted: `6acadc0`. Audit executed on branch `feature/product-system-active-path-isolation-v1` (HEAD `631f062` at capture time).

---

## 4. Runtime ownership

| Surface | Owner | Live @ :8001/:3000 |
|---------|-------|---------------------|
| Aggregate health badge | `SystemHealthService` → public `/api/v1/system/health` | YES — `status: warning` |
| Per-module green dots | `useModuleChainData.buildModulesFromHealth` defaults | NO — checks `{}` on public health |
| Contract handoffs | `CONTRACT_HANDOFFS` constant | STATIC |
| Event stream | `REFERENCE_EVENTS` in `ModuleChain.tsx` | STATIC (labeled Referință) |
| Snapshot points | Inline array in `ModuleChain.tsx` | STATIC labels |
| Global `2 critical` | `productionAlerts` in `mockData.ts` | DEMO (unrelated) |

---

## 5. Route classification

**HYBRID** — subordinate classification: `ARCHITECTURE_OBSERVABILITY` + `DOCUMENTATION_UI` + partial `RUNTIME_OBSERVABILITY` (aggregate health only).

| Field | Value |
|-------|-------|
| React route | `/modules` |
| Component | `frontend/src/pages/ModuleChain.tsx` |
| Hook | `frontend/src/hooks/useModuleChainData.ts` |
| Nav label | Module Chain (section Sistem) |
| Functional name | Module Chain architecture reference dashboard |
| Endpoint consumed | `GET /api/v1/system/health` only |

---

## 6. Compound Engineering definition found

**DOCUMENTED / NOT_PROVEN as runtime feature.**

- `.compound-engineering/` folders are **research/workflow artifacts**, not application modules.
- The string "Compound Engineering" does **not** appear in `/modules` UI or its consuming code.
- The page **describes** multi-module truth/contract concepts; it does **not** enforce, observe, or govern them.

---

## 7. Module registry

| Registry | Location | Status |
|----------|----------|--------|
| Page module cards | `useModuleChainData.ts` `MODULE_DEFINITIONS` | STATIC_CODE |
| Mini-module registry (real) | `backend/data/mini_module_registry_volumetric_v2.py` | ACTIVE_CANONICAL — **not consumed by /modules** |
| Governance flows | `governanceData.ts` | STATIC — `/governance` only |
| mockData.moduleChain | `mockData.ts` | DEMO dead duplicate |

---

## 8–15. Per-module findings

### OC — Operational Core
- **Classification:** UI_ONLY  
- No backend module named Operational Core. Card is conceptual. OC in nav maps to Inventar & OC, not this card. Health mapping ties OC to `database`/`version`/`seed_pipeline` but public health returns empty `checks`, so card shows fake green `1 active`.

### WI — Work Intake
- **Classification:** LEGACY / MISNAMED  
- Canonical operator path is **Intake V6** (`/intake`). `WI_READY_FOR_QUOTE` appears in governance static list only; no backend emitter found. Product Definition step missing between Intake and ProductSystem on displayed chain.

### PS — ProductSystem
- **Classification:** CONFIRMED_CODE  
- Real services: product definition builder, product aggregate, mini-module registry. Page does not link to aggregates or dossiers. Payload text on handoff card is documentation.

### CE — CostEngine
- **Classification:** CONFIRMED_CODE  
- Real cost services and aggregate BOM adapters. Page does not show calculations. `time_estimate` in handoff payload is operational/commercial boundary — enforced off-page, not on chain.

### QT — Quotes / Oferta
- **Classification:** MISNAMED — runtime entity API is `quotes`; nav uses **Oferte**. Demo event `QT-2245` **not in DB** (exact code match 0). Real quotes exist (e.g. `QT-W5T01-GATE`).

### OR — Orders / Comanda
- **Classification:** CONFIRMED_RUNTIME (off-page)  
- Real locked orders (e.g. `ORD-W5T01-GATE` id 29991). Demo `ORD-1138` absent. `ORDER_LOCKED` not emitted as event code in backend grep. Snapshot immutability enforced via `snapshot_v2_json` + convert gates.

### WO — WorkOS / Execution Plan
- **Classification:** MISNAMED — card says WorkOS but means orchestrated execution; collapses ExecutionPlan, orchestration, and platform name. `WORK_SCHEDULED` / `JOB_RELEASED` static only.

### TK — Tasks / ExecutionReality
- **Classification:** PARTIAL  
- Tasks are projections from execution plan/reality, not standalone business-truth module. `TASK_STARTED` on page is demo; backend has `TASK_STARTED_NOT_COMPLETED` gap type in operational reality review only.

---

## 16. Displayed flow vs canonical flow

| Pozitie | Flux afisat | Flux canonic | Aliniat | Problema | Decizie necesara |
|---------|-------------|--------------|---------|----------|------------------|
| 1 | OC | Request/Intake | NO | OC conceptual | Owner: define or remove |
| 2 | WI | Intake | PARTIAL | Legacy label | Rename to Intake |
| 3 | PS | Product Definition → Product System | NO | PD missing | Insert PD step |
| 4 | CE | Cost | YES | — | Keep |
| 5 | QT | Oferta | PARTIAL | English Quotes | Align Oferte |
| 6 | OR | Comanda | PARTIAL | English Orders | Align Comenzi |
| 7 | WO | Execution Plan | NO | Platform name collision | Split Plan vs Reality |
| 8 | TK | ExecutionReality | NO | Tasks as terminal module | Reframe |

---

## 17–18. Contract handoffs & payloads

- **7 handoffs displayed**, **7 hardcoded**, **0 runtime-confirmed on page**.  
- Runtime analogs exist for PS→CE→QT→OR→WO→TK in services (see `handoff_contract_matrix.json`).  
- Payload strings on UI are **manual documentation**, not extracted from registry.  
- `lastEventTime` always `—` (static).

---

## 19. Forbidden fields

**Status: UI_ONLY / PARTIAL off-page.**

Forbidden badges on handoff cards have **no central governance enforcement** and **no violation events**. Scattered boundary tests exist (CPP, intake commercial, operator blueprint) but are not tied to `/modules`. See `forbidden_field_enforcement_matrix.json`.

---

## 20. Golden Rule enforcement

| Rule | Verdict |
|------|---------|
| Single truth per module | **PARTIAL** — real in services; page is documentation only |
| No truth theft | **PARTIAL** — enforced in specific builds/tests; contradictions possible in UI calc debt elsewhere |
| Events describe what happened | **CONTRADICTED on page** — stream is static fiction labeled reference |

---

## 21–23. Event stream

- **Classification:** `STATIC_DEMO` / `DOCUMENTATION_SAMPLE`  
- Title explicitly: **Event Stream — Cross-Module (Referință)**  
- No polling/websocket; 10 static events  
- Demo entities `JOB-0042`, `ORD-1138`, `QT-2245`, `WI-3320` — **no exact DB matches**  
- Timestamps `05:45–09:15` are sample times without date — **not runtime**  
- No event store, no outbox, no cross-module live feed

---

## 24–25. Snapshot points

- **Classification:** `LABELS_ONLY`  
- Five cards with no IDs, hashes, versions, or links  
- Real snapshots verified off-page: `quote_snapshot_v2`, `order.snapshot_v2_json`, `ExecutionPlan` for `ORD-W5T01-GATE`  
- Order snapshot immutability **CONFIRMED** in tests; **not visible** on `/modules`

---

## 26–28. Live Health, WARNING, critical badge

### Live Health
- Polls `GET /api/v1/system/health` every 30s — **REAL connectivity**  
- Public response redacts `checks` to `{}` — per-module mapping **non-functional**  
- Diagnostics (not used by page) shows root cause:

```json
"execution_anchor_order_14": {
  "status": "warning",
  "details": { "order_exists": false, "reason": "anchor_order_missing" }
}
```

### WARNING source
- Page badge `WARNING` = `health.status` from public endpoint — **EXPLAINED** as anchor order 14 missing  
- Module cards remain green because empty checks → default `active` + `ok:1` — **misleading**

### Global `2 critical`
- From `productionAlerts` mock data in `App.tsx` — **UNRELATED** to Module Chain (shop-floor demo alerts)

---

## 29–30. Backend endpoints & frontend sources

See `route_endpoint_inventory.json`. Single live endpoint on page. All other substance is static TS constants.

---

## 31. Persistence

| Artifact | Classification |
|----------|----------------|
| module registry table | ABSENT |
| contract registry | ABSENT (partial service validators) |
| event store | ABSENT |
| snapshot metadata registry | ABSENT (embedded in entity rows) |
| governance violations | ABSENT |
| mini_module_registry | ACTIVE_CANONICAL (PS scope) |
| execution_anchor order 14 | CONFIG_ONLY invariant — **missing in this DB** |

---

## 32. Governance relation

`/governance` uses `governanceData.ts` + `agent_authority_registry.json` — **separate static source** from `/modules`. No shared enforcement engine. Duplicated architectural rules (events, flows, boundaries) with no single authority. Governance cannot activate/deactivate contracts at runtime.

---

## 33. Duplicate authorities

**Count: 4 major duplicates**

1. Module chain cards vs governance `moduleStatusFlows`  
2. Handoff payloads vs mini_module_registry vs intake contract services  
3. WorkOS platform name vs WO execution card vs ExecutionPlan/Reality services  
4. Global mock alerts vs system health vs governance severity

---

## 34. Dead pieces

| Piece | Location | Classification |
|-------|----------|----------------|
| mockData.moduleChain | mockData.ts | DEMO unused by page |
| mockData.contractHandoffs | mockData.ts | DEMO duplicate |
| mockData.systemEvents overlap | mockData.ts / ModuleChain | DEMO duplicate |
| HEALTH_CHECK_MODULE_MAP | useModuleChainData.ts | DEAD on public health (empty checks) |

---

## 35. Terminology

See `terminology_matrix.json`. **6 legacy**, **5 misnamed** concepts on page vs canonical nav/architecture.

---

## 36–40. E2E scenarios

### Scenario 1 — Cerere → Comanda
- Real path exists via Intake V6 → PD → PS → cost → quote → order (off-page).  
- `/modules` cannot show entity, handoff, event, or snapshot for a live request. **FAIL for observability.**

### Scenario 2 — Comanda → Executie
- `ORD-W5T01-GATE` (29991): locked, execution plan returned from API.  
- WO/TK cards do not reflect ExecutionPlan vs ExecutionReality split. **PARTIAL off-page only.**

### Scenario 3 — Violare contract
- Boundary tests exist (CPP, intake commercial).  
- Page does not surface incidents. **FAIL.**

### Scenario 4 — Eveniment runtime
- No live event appears in stream. Static `TASK_STARTED` etc. remain fixed. **FAIL on page.**

### Scenario 5 — Health defect
- Aggregate WARNING real; modules stay green; no drill-down. **FAIL truthful per-module health.**

---

## 41. Compound Engineering gap matrix

See `compound_engineering_gap_matrix.json` — **0 EXISTENT**, 11 PARTIAL, 7 LIPSA, 2 DEMO on control-plane criteria.

---

## 42–49. What is real / doc / demo / preserve / unify / isolate / lacks

| Category | Items |
|----------|-------|
| **Real** | Public health aggregate; diagnostics checks; mini_module_registry; snapshot v2; execution plan/reality APIs |
| **Documentation only** | Handoffs, golden rules, chain labels, reference events, snapshot cards |
| **Demo** | REFERENCE_EVENTS, productionAlerts critical badge, mockData duplicates |
| **Legacy** | WI, Quotes, Orders labels; OC conceptual card |
| **Preserve** | Health polling pattern; architectural intent text; separation of /governance |
| **Unify** | Terminology with nav (Oferte/Comenzi/Intake); single governance source |
| **Isolate** | Demo mock alerts from production shell; static reference events from "live" badges |
| **Lacks** | Event store, contract registry UI, snapshot drill-down, per-module health truth, violation feed |

---

## 50–54. Roadmap impact

- **ProductSystem:** Page under-represents PD + aggregate truth; real registry not linked.  
- **CostEngine:** Cost authority exists; page adds no observability.  
- **Offer/Order:** Snapshots real but invisible; terminology drift blocks governance use.  
- **Execution Plan/Reality:** Collapsed into WO/TK cards; blocks operator trust in chain view.  
- **Program:** MODULE-ARCH-01 **blocked** until runtime closure per task rules.

---

## 55. Screenshots

| # | File | Section | Verdict |
|---|------|---------|---------|
| 1 | `01_module_chain_full.png` | Full page | WARNING + green modules + static handoffs |
| 2 | `02_module_chain_header_warning.png` | Header | Live Health vs WARNING contradiction |
| 3 | `03_contract_handoffs.png` | Handoffs | Hardcoded payloads/forbidden |
| 4 | `04_regula_de_aur.png` | Regula de Aur | Documentation only |
| 5 | `05_event_stream.png` | Event Stream (Referință) | Static demo |
| 6 | `06_snapshot_points.png` | Snapshot Points | Labels only |
| 7 | `07_live_health_and_critical_badge.png` | Top bar | 2 critical unrelated mock |

All captured @ viewport 1440×900, URL `http://127.0.0.1:3000/modules`, timestamp ~2026-07-15 11:39 EEST, backend :8001.

---

## 56. Tests

| Suite | Passed | Failed | Skipped/Errors |
|-------|--------|--------|----------------|
| test_system_health.py | 18 | 0 | 0 |
| test_security_release_audit_fix_10_health_diagnostics.py | 1 | 1 | 0 |
| test_agent_authority_registry_parity.py | 0 | 0 | 8 collection errors |
| ModuleChain frontend tests | 0 | — | **none exist** |

**Overall:** PARTIAL — health tests mostly pass; governance parity suite broken; no frontend tests for `/modules`.

---

## 57. Honest opinion

The page is a well-intentioned **architecture poster** with a **live heartbeat** that currently **misleads**: green modules during a real WARNING, a "Live Health" badge that does not reflect per-module truth, and a reference event stream that could be mistaken for production telemetry. It should not be used for governance decisions until event/snapshot/health/handoff data are wired from canonical runtime sources or clearly demoted to a documentation-only mode without live signifiers.

---

## 58. Roadmap awareness checkpoint

Aligns with E2E program state: Wave 7 closed, owner decisions pending. This audit adds **module-chain/governance debt** and **event/snapshot observability debt** without authorizing implementation.

---

## 59. Dead pieces check

Confirmed dead/duplicate: `mockData.moduleChain`, `contractHandoffs` in mockData, ineffective health mapping on public endpoint.

---

## 60. Next task

`MODULE-RUNTIME-01-EVENT-SNAPSHOT-HEALTH-CLOSURE` — close health truth gap (expose safe checks or demote per-module dots), wire or quarantine static streams, link real snapshots/events before any control-plane architecture build.

`MODULE-ARCH-01` remains **blocked**.

---

## 61. Canonical updates

- `docs/master/workos-e2e/WORKOS_E2E_STATUS.md` — MODULE-INT-01 section added  
- `docs/master/workos-e2e/WORKOS_E2E_TASK_GRAPH.md` — MODULE-INT-01 node + observability debt  

---

## 62. Commit

Audit/docs/evidence only — single isolated commit requested.

---

## 63. Delivery footer

```
Task: MODULE-INT-01 — AUDIT_E2E_COMPOUND_ENGINEERING_MODULE_CHAIN_V1
Starting HEAD: 6acadc0
Backend: 8001
Frontend: 3000
Route: /modules
Route classification: HYBRID
Compound Engineering: DOCUMENTED
Modules displayed: 8
Modules runtime confirmed: 2
Modules UI-only: 6
Handoffs displayed: 7
Handoffs runtime confirmed: 0
Handoffs hardcoded: 7
Forbidden rules: UI_ONLY
Golden Rule: PARTIAL
Event Stream: STATIC_DEMO
Real events: 0
Static/demo events: 10
Snapshot Points: LABELS_ONLY
Real snapshots: 1
Live Health: PARTIAL
WARNING: EXPLAINED
Global critical relation: UNRELATED
Duplicate authorities: 4
Legacy concepts: 6
Demo/mock sources: 4
Dead pieces: 4
Screenshots: 7
Tests: PARTIAL
Code changed: NO
DB changed: NO
Implementation authorized: NO
Next task: MODULE-RUNTIME-01-EVENT-SNAPSHOT-HEALTH-CLOSURE
Commit: YES
Push: NO
PR: NO
Verdict: MODULE_CHAIN_AUDIT_BLOCKED_STATIC_DEMO_DATA
```
