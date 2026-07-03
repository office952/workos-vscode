# WorkOS UI — Do Not Break Map

**Status:** Governance document — **no UI or runtime changes**  
**Purpose:** Fragility map for operational modules before any visual polish, theme work, or cross-cutting UI refactor  
**Related:** `TypographyGuard.md`, `SETTINGS_SCOPE.md`, `THEME_PHASE_PLAN.md`

---

## 1. Purpose

WorkOS has a **good operational foundation** (Intake V6 → ProductSystem → Pricing → Quote → Order → Execution) with partial visual consistency. Several modules are **fragile**: small typography, hardcoded dark surfaces, preview vs real boundaries, and mock/live splits.

Global redesign, theme toggle, or opportunistic UI polish **will break** operator trust and commercial flows if applied without guards.

This document defines:

- Which modules are CRITICAL / HIGH / MEDIUM / LOW fragility
- Global no-touch rules
- Data-truth labeling requirements
- Mandatory regression pages after any UI change

It does **not** implement fixes for known misleading UI (Utilaje utilization, Dashboard OTIF at zero, etc.) — those are separate P0 copy/label tasks.

---

## 2. Critical modules

| Module | Fragility | Why | Guard |
| ------ | --------- | --- | ----- |
| **Intake V6** | **CRITICAL** | Multi-step flow; `v6` presentation tokens; preview pricing vs draft handoff; layer/review/confirm semantics | No global CSS; no font changes; no layout redesign without scoped task + Layers/Review/Confirm regression |
| **ProductSystem** | **CRITICAL** | Large surface; 8–9px meta; mock loadMode; aggregate vs parent; blueprint/dossier sub-routes | No drive-by typography; preserve mock banners; library + editor regression |
| **App shell** (sidebar/header) | **CRITICAL** | Hardcoded hex (`#0A0F1C`, `#111827`, …); nav IA; all routes depend on shell | Theme changes Phase 3+ only; no sidebar redesign without IA review |
| **Pricing Registry** | **HIGH** | Cost Engine input surface; owner-confirmed gates; material/workcenter rates | No move into Settings merge; data truth labels; no reprice from UI tasks |
| **Inventory** | **HIGH** | Live vs mock-local split (plates/automation); amber banners | Preserve mock/live banners; stock ≠ pricing confusion |
| **Quotes / Orders** | **HIGH** | Commercial spine; gated actions (`source=db`); draft vs priced | No CTA copy change without backend alignment; preview vs final |
| **Utilaje** | **HIGH** | Read-only UI with hardcoded utilization display (known debt) | Do not add fake metrics; label/hide until API — no polish that implies live utilization |
| **Execution** | **MEDIUM** | Plan/reality/gate honesty; empty states are model | Preserve empty-state copy; gate labels |
| **Dashboard** | **MEDIUM** | KPI semantics (OTIF at 0 jobs); live vs error fallback | Do not mark critical on empty; distinguish error vs zero |
| **Settings** | **MEDIUM** | CostEngine + Integrations real writes; no Appearance yet | Admin boundary future task; no tab restructure without SETTINGS_SCOPE |
| **Employee Mobile V2** | **MEDIUM** | Separate token file; touch 44px; standalone routes | Do not merge desktop scale blindly |
| **Tablet mode** | **MEDIUM** | Shop floor queue; dedicated layout | Touch targets; no desktop density import |
| **Colaboratori** | **MEDIUM** | Supplier API with UI-synthesized fields (known debt) | No polish that implies verified commercial value |
| **Employees / Attendance** | **LOW / MEDIUM** | HR internal disclaimers; CostEngine validation counts | Preserve read-only/evidence copy |

---

## 3. Global no-touch rules

Unless the task **explicitly** names the file and phase:

| Rule | Detail |
| ---- | ------ |
| **No `index.css` changes** | Includes `color-scheme: dark`, shadcn vars |
| **No `tailwind.config.ts` changes** | Includes `darkMode`, theme extension |
| **No Intake V6 token changes** | `intakeV6Presentation.tsx` and `v6.*` consumers |
| **No ProductSystem layout refactor** | Without audit + library/editor regression |
| **No Pricing / Cost Engine UI changes** | Without data-truth verification |
| **No global theme toggle** | Without `THEME_PHASE_PLAN.md` approved phase |
| **No global font-family change** | System stack is intentional for now |
| **No QuoteOrchestrator / reprice / create flows** | From UI-only tasks |
| **No DB / seeds / migrations** | From UI tasks |

---

## 4. UI misleading guard

Any UI displaying the following must label data source clearly:

- Price / total / TVA
- Task (preview vs executable)
- Order / execution state
- Stock / inventory quantity
- Capacity / utilization
- Machine availability
- Employee availability
- Live / demo / mock status
- Commercial value (RON/EUR)

### Required source labels (copy or badge)

| Label | Meaning |
| ----- | ------- |
| **REAL** | From backend/API; actionable where permitted |
| **PREVIEW** | Client-side or draft calculation; not final |
| **MOCK** | Local/fallback data; not production truth |
| **PLACEHOLDER** | Static or incomplete config |
| **N/A** | Not applicable or not configured — prefer over `0` |
| **READONLY_EXPLANATORY** | Reference/diagnostic only |

### Rules

- **Preview must never look final** (e.g. Confirm hero total without preview disclaimer).
- **Mock must never look live** (use `SourceBadge` or amber banner).
- **`0` must not imply failure** when the honest state is empty or N/A.
- **Disabled actions** must explain blocker (handoff, gate, permissions).

Known P0 violations (document only — fix in separate tasks):

- Intake V6 Confirm hero pricing without preview label
- Utilaje utilization hardcoded
- Dashboard OTIF 0% critical on zero jobs
- Colaboratori synthesized RON/rating fields

---

## 5. Required regression pages

After **any** UI change touching shared components, typography, shell, or theme-adjacent code, manually verify at least:

| Page / route | Why |
| ------------ | --- |
| `/dashboard` | KPI semantics, error vs empty |
| `/intake-v6-app/*` — Layers, Review, Confirm | CRITICAL flow + preview boundaries |
| `/product-system` — library + editor | Density, mock mode, badges |
| `/inventory/pricing` | Registry gates, owner-confirmed |
| `/inventory` | Mock vs live banners |
| `/quotes`, `/quotes/:id` | Draft vs priced, DB source |
| `/orders`, `/orders/:id` | Commercial handoff |
| `/execution`, `/execution/:order_id` | Empty state, gates |
| `/settings` | Tabs intact; CostEngine not accidentally exposed |
| `/employee-app-v2/*` | Touch targets, task detail |
| `/tablet/*` | Queue, operator actions |
| `/utilaje` | Read-only honesty |

Add viewport checks when the change affects layout: **desktop (1280+)**, **tablet (~768)**, **employee mobile**.

---

## 6. Do-not-break checklist

Copy into any UI task report:

```text
Do-Not-Break Checklist:
- index.css touched: yes/no
- tailwind.config.ts touched: yes/no
- ThemeProvider / day-night touched: yes/no
- Intake V6 tokens or flow touched: yes/no — scope:
- ProductSystem layout/tokens touched: yes/no — scope:
- Pricing / Cost Engine UI touched: yes/no
- Quotes / Orders / Execution actions touched: yes/no
- Mock/live banners preserved: yes/no
- Preview vs REAL labels preserved or improved: yes/no
- New misleading metrics introduced: yes/no
- Regression pages checked (list):
- Fragile module approval (if CRITICAL touched): yes/no / N/A
```

---

## 7. Relationship to audit verdicts

This map implements governance for audit conclusions:

- `UI_GOVERNANCE_REQUIRED`
- `TYPOGRAPHY_GUARD_REQUIRED`
- `MISLEADING_UI_RISKS_PRESENT`
- `GLOBAL_REDESIGN_NOT_SAFE`
- `SAFE_TO_PLAN_INCREMENTAL_UI_SYSTEM`

Incremental, scoped UI work is allowed **with** this map and `TypographyGuard.md`. Global redesign is not.
