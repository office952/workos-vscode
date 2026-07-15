# UI-TRUTH-01 — Environment Banner Operational Health Truth Plan V1

**Task:** `UI-TRUTH-01` / `ENVIRONMENT_BANNER_OPERATIONAL_HEALTH_TRUTH_PLAN_V1`  
**Type:** PLAN ONLY — no application, backend, DB, or UI code changes  
**Starting HEAD:** `6eea3e3`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Worktree:** `C:\w\psiso`  
**Date:** 2026-07-15  
**Verdict:** `UI_TRUTH_01_PLAN_READY_FOR_OWNER_GO`

---

## 1. Repository safety

| Check | Result |
|-------|--------|
| Code changed | **NO** |
| DB changed | **NO** |
| Backend changed | **NO** |
| Scope respected | **YES** — plan/evidence/docs only |
| Forbidden areas touched | **NO** |

---

## 2. Accepted runtime configuration

| Item | Value |
|------|-------|
| Trusted frontend | `http://127.0.0.1:3000` |
| Canonical backend | `http://127.0.0.1:8001` |
| Start command | `npm run dev:stack` |
| API browser path | same-origin `/api` → Vite proxy → `8001` |
| RUNTIME-CONFIG-03 | `bb60f1f` (app/config) + `6eea3e3` (docs/evidence) |
| Owner P1–P10 | **CONFIRMED** |
| Parity flags | ALL_FALSE |

---

## 3. Accepted defect (RUNTIME-RECOVERY-02)

`EnvironmentBanner` classifies **`authState === "authenticated"` → `LIVE / DB`** (green). This is **MISLEADING**:

- Authentication success is shown as backend availability.
- Backend availability is shown as DB availability.
- A route may show **Network Error** while the global banner stays green.
- No operational health probe; no DB proof; contradicts Module Chain health badges.

**Evidence:** `docs/qa/product-system-active-path-isolation-v1/runtime_recovery_02/banner_truth_check.json`

---

## 4. Current banner E2E trace

### 4.1 UI

| Aspect | Current behavior |
|--------|------------------|
| Position | Global shell in `App.tsx` — below header, above `<main>` |
| Persistence | All routes in authenticated layout |
| `live_db` | Green strip: **LIVE / DB** + *Sursa de date: backend live* |
| `dev_mock` | Amber: **DEV / MOCK** |
| `dev_no_auth` | Amber: **DEV / NO AUTH** + Shield *Auth demo* |
| Icons | `Database` (live), `AlertTriangle` (dev), `Monitor` (unknown) |
| Tooltip | None |
| Refresh | None — re-renders when `authState` changes |
| Mobile/desktop | Same `text-[11px]` flex row |

### 4.2 Frontend

- **Component:** `frontend/src/components/workos/EnvironmentBanner.tsx`
- **Consumer:** `frontend/src/App.tsx` only
- **Auth:** `useAuth().authState` — no health fetch
- **Mock:** `isMockEnabled()`, `isDevAuthFallback()` from `mockGuard.ts`
- **Tests:** **NONE** for EnvironmentBanner
- **Related pattern:** `useModuleChainData` polls `/api/v1/system/health` every 30s on `/modules` only

### 4.3 Backend contracts (inspected)

| Endpoint | Auth | Role |
|----------|------|------|
| `GET /api/v1/system/health` | Public | Aggregate `status`, `service`, `generated_at`, **`checks: {}`** always |
| `GET /api/v1/system/diagnostics` | `system.diagnostics.read` (admin) | Full `checks` including `database` |
| `GET /api/v1/system/version` | Public | `environment`, `release_version` |
| `GET /health` | Public | Liveness only `{status: healthy}` |

**Live probe (2026-07-15, stack up):**

```json
// GET http://127.0.0.1:3000/api/v1/system/health
{"status":"warning","service":"workos","generated_at":"...","checks":{}}
```

Public health is **PARTIAL** for DB proof — by design (`run_public_health` redacts checks).

### 4.4 Current mismatch matrix

See `docs/qa/product-system-active-path-isolation-v1/ui_truth_01/current_state_mismatch_matrix.json`.

**Summary:** 6/8 situations mismatch; **auth used as health: YES**.

---

## 5. Banner purpose decision

| Option | Evaluation |
|--------|------------|
| **A — Auth only** | Honest for session but hides operational truth operators need. |
| **B — Runtime only** | Good backend signal but splits session awkwardly. |
| **C — Combined separated segments** | **RECOMMENDED** — Sesiune / Backend / Baza de date / Mediu; no segment infers another. |

**Decision:** **Option C** with compact Romanian strip + tooltip drill-down.

---

## 6. Target truth model

| Segment | Authority | Refresh |
|---------|-----------|---------|
| Frontend loaded | Banner mount | n/a |
| Sesiune | `AuthContext.authState` | existing focus/visibility auth refresh |
| Backend | `GET /api/v1/system/health` via **same-origin `/api`** | 45s poll + visibility + manual |
| Baza de date | `diagnostics.checks.database` **only if authorized**; else **NECUNOSCUTA** | with diagnostics fetch when permitted |
| Mediu | `import.meta.env` + `GET /api/v1/system/version` | on load + health cadence |
| Mock/demo | `isMockEnabled()` | build-time |
| Ultima verificare | `health.generated_at` | each successful health |

**Rules:**

1. Auth cannot prove backend health.
2. `checks: {}` cannot produce DB **CONFIRMATA**.
3. No sensitive diagnostics in banner DOM for unauthorized users.
4. Route errors stay visible; global banner does not claim “all routes OK.”

Full model: `target_truth_model.json`

---

## 7. Target state machine

Finite states per segment — see `target_state_machine.json`.

**Backend mapping:**

| `health.status` | Segment |
|-----------------|---------|
| `ok` | Backend disponibil |
| `warning` / `degraded` | Backend cu avertisment |
| `fail` | Backend critic |
| fetch error | Backend indisponibil |
| pending | Se verifică |

**DB mapping:**

| Condition | Segment |
|-----------|---------|
| Public health only | DB neverificată / necunoscută |
| Diagnostics 401/403 | DB necunoscută |
| Diagnostics `database.status === ok` | Baza de date confirmată |
| Diagnostics `database.status === fail` | Baza de date indisponibilă |

---

## 8. Romanian terminology

Replace **LIVE / DB** and false production claims.

**Healthy example:** `Local · Backend disponibil · DB neverificată`  
**Warning example:** `Local · Backend cu avertisment · DB neverificată`  
**Backend down:** `Local · Backend indisponibil · DB necunoscută`  
**Mock:** `Mod demo · Date demonstrative`

Full mapping: `terminology_matrix.json`

---

## 9. Color and icon semantics

| Semantic | Color | Icon | Text required |
|----------|-------|------|---------------|
| Unknown/checking | slate | Loader2 / HelpCircle | Da |
| Healthy | emerald | CheckCircle2 | Da |
| Warning | amber | AlertTriangle | Da |
| Critical/down | red | XCircle / WifiOff | Da |
| Session | blue/slate | Shield | Separate from Database |

**Accessibility:** `aria-label` on strip; tooltip; never status by color alone.

---

## 10. Route-level error interaction

**Rule:** Global banner = **aggregate platform** state; route error = **local** state. **No direct interaction.**

- Health OK + route Network Error → allowed if paths differ; banner must not say “toate serviciile OK.”
- Evaluated and rejected for v1: centralized API tracker, last-request failure coupling.

See `route_error_interaction.json`.

---

## 11. Polling / refresh

| Parameter | Value |
|-----------|--------|
| Initial | on mount |
| Interval | 45s (30–60s acceptable) |
| Visibility | refresh when tab visible (mirror AuthContext) |
| Timeout | 5s |
| Retry | 2s / 4s / 8s max 3 on failure |
| Stale | 120s — show age, optional stale hint |
| Manual | RefreshCw on banner |
| Cleanup | AbortController + clearInterval |

Pattern reference: `useModuleChainData.ts` (30s). New shared `useRuntimeHealth` — avoid duplicate polls in banner.

See `polling_refresh_plan.json`.

---

## 12. Failure behavior

See `failure_behavior_matrix.json` (11 scenarios).

**Never:** fallback to green LIVE/DB on health failure.

---

## 13. Mock / demo mode

| Detection | `VITE_ENABLE_MOCK_DATA === "true"` |
| Label | **Mod demo** / **Date demonstrative** |
| Visual | Distinct from emerald operational strip |
| With backend | Demo segment + independent backend segment from health |

See `mock_demo_matrix.json`.

---

## 14. Split API path decision

| Path | Use |
|------|-----|
| **same-origin `/api/v1/system/health`** | **Primary banner truth** (proxy chain) |
| **direct `http://127.0.0.1:8001`** | Diagnostic only — not operator banner |
| **Auth `getAPIBaseURL()`** | Unchanged — session segment only |

**Do not refactor API clients in UI-TRUTH-01.**

---

## 15. Target component architecture

```
EnvironmentBanner
├── useAuth()              → session segment
├── useRuntimeHealth()     → backend segment + timestamp (NEW)
├── useRuntimeDiagnostics()? → optional gated DB segment (NEW, lazy)
├── RuntimeStatusSummary   → compact RO segments (NEW)
└── RuntimeStatusDetails   → tooltip / drill-down (NEW)
```

**Types:** `frontend/src/types/runtimeStatus.ts`  
**No over-engineering:** single health poll owner; diagnostics fetch only when drill-down opened or user authorized.

---

## 16. File impact plan

6 frontend files create/modify; **0 backend changes.**

See `file_impact_plan.json`.

---

## 17. Backend boundary

- **No new endpoint.**
- **No health/diagnostics redesign.**
- Public health **sufficient for backend aggregate**; **insufficient for DB** → show NECUNOSCUTA.
- Record contract debt separately if owner later wants public DB ping.

---

## 18. Test plan

- **25** planned cases (component + hook + integration).
- Regression routes: intake, orders, execution, product-system, modules, governance, login.

See `test_plan.json`.

---

## 19. Visual verification

Owner paths: `/intake`, `/orders`, `/modules`  
**7** visual states documented with labels, icons, screenshots targets.

See `visual_acceptance_checklist.json`.

---

## 20. Implementation breakdown

| Task | Scope |
|------|-------|
| **UI-TRUTH-01A** | Types + `useRuntimeHealth` hook |
| **UI-TRUTH-01B** | Banner + Romanian `RuntimeStatusSummary` |
| **UI-TRUTH-01C** | Failure/stale/retry + gated `RuntimeStatusDetails` |
| **UI-TRUTH-01D** | Tests + route regression |
| **UI-TRUTH-01E** | Runtime + visual verification evidence |

**Implementation authorized:** **NO** — `OWNER_GO_REQUIRED`  
**First task after GO:** `UI-TRUTH-01A-RUNTIME-TRUTH-CONTRACT-AND-HEALTH-HOOK`

See `implementation_breakdown.json`.

---

## 21. Acceptance criteria (future implementation)

- [ ] Auth is not health
- [ ] Backend from real same-origin health request
- [ ] DB shown only when proven; empty checks → unknown
- [ ] Backend failure never shows green LIVE
- [ ] Mock clearly labeled in Romanian
- [ ] No secret leakage
- [ ] Route errors remain visible
- [ ] No new backend endpoint
- [ ] Targeted tests PASS
- [ ] Visual checklist PASS

---

## 22. Forbidden scope (unchanged)

Backend health redesign; new endpoints; API client refactor; parity; APP-AUTH-06C; `/modules` remediation; `/governance` consolidation; Product System / Intake changes.

---

## 23. Risks

See `risk_matrix.json` — highest: diagnostics leak (mitigate with gating); medium: public health cannot prove DB (mitigate with NECUNOSCUTA).

---

## 24. APP-AUTH-06C gate

**BLOCKED** until UI-TRUTH-01 implementation **and** runtime verification (01E) complete.

**Sequence (P10):** RUNTIME-CONFIG-03 ✓ → **UI-TRUTH-01** (plan ✓) → implement → **APP-AUTH-06C**

---

## 25. Evidence index

`docs/qa/product-system-active-path-isolation-v1/ui_truth_01/`

| File | Purpose |
|------|---------|
| `current_banner_trace.json` | E2E trace |
| `current_state_mismatch_matrix.json` | Mismatch proof |
| `health_contract_matrix.json` | Health/diagnostics audit |
| `target_truth_model.json` | Authority table |
| `target_state_machine.json` | Finite states |
| `terminology_matrix.json` | RO labels |
| `failure_behavior_matrix.json` | Failure rules |
| `mock_demo_matrix.json` | Demo mode |
| `polling_refresh_plan.json` | Poll contract |
| `file_impact_plan.json` | Files |
| `test_plan.json` | Tests |
| `visual_acceptance_checklist.json` | Visual states |
| `implementation_breakdown.json` | Tasks 01A–01E |
| `risk_matrix.json` | Risks |
| `route_error_interaction.json` | Route vs global |

---

## 26. Honest opinion

The defect is real and cheap to fix on the frontend: the hard part is **discipline** — resisting the urge to show green when auth succeeds. Option C is the right UX for operators who already see contradictory signals on `/modules`. The public health contract is intentionally minimal; **NECUNOSCUTA** is the honest DB line until diagnostics auth exists — do not invent a backend endpoint just to greenwash DB.

Split API path (auth direct `:8001` vs Intake proxy) remains **MEDIUM debt**; UI-TRUTH-01 correctly tests the proxy path for backend segment without opening a refactor.

---

## 27. Roadmap awareness

- UI-TRUTH-01 plan closes the banner debt opened in RUNTIME-RECOVERY-02 and RUNTIME-CONFIG-03.
- APP-AUTH-06C parity interpretation must wait for honest banner baseline.
- MODULE-INT-01 “health UI contradiction” resolves when banner uses same health source as Module Chain.

---

## DELIVERY FOOTER

```
Task: UI-TRUTH-01 — ENVIRONMENT_BANNER_OPERATIONAL_HEALTH_TRUTH_PLAN_V1
Starting HEAD: 6eea3e3
Current banner: MISLEADING
Auth used as health: YES
Backend health source: none (auth proxy only)
DB health source: none (inferred from auth)
Health endpoint sufficient: PARTIAL
Diagnostics required for banner: PARTIAL
Banner purpose: Option C — combined separated segments
Target model: AUTH_BACKEND_DB_ENV_SEPARATED
Same-origin health path: YES
Direct health path: diagnostic only
Mock/demo: Mod demo / Date demonstrative
DB unknown state: DEFINED
Failure states: 11
Polling: 45s + visibility + manual
Manual refresh: YES
New backend endpoint planned: NO
Backend changes planned: NO
Frontend files planned: 6
Implementation tasks: 5
Tests planned: 25
Visual states planned: 7
Implementation authorized: NO
APP-AUTH-06C: BLOCKED
Next task: OWNER_GO_REQUIRED
Code changed: NO
DB changed: NO
Commit: pending
Push: NO
PR: NO
Verdict: UI_TRUTH_01_PLAN_READY_FOR_OWNER_GO
```
