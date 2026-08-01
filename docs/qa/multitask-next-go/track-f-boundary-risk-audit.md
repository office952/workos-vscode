# Track F — Boundary Risk Audit (Read-Only)

**Repo:** `C:\w\psiso`  
**Branch tip:** `e8ea40a0` — *Accept 92401 owner review with warnings*  
**Date:** 2026-08-01  
**Mode:** READ-ONLY (grep / read / git scope — **no product edits**)

---

## Prior evidence cited

| Pack | Path | Relevance |
|------|------|-----------|
| Operator review 92401 | [`docs/qa/operator-review-92401/`](../operator-review-92401/) | Live 92401/13/MAT-02 RO review · pricing/time · UI hardcode · HR park |
| App integrity before next GO | [`docs/qa/app-integrity-before-next-go/`](../app-integrity-before-next-go/) | Boundary + product-direction integrity stamps |
| Exact-state Track E/F | [`docs/qa/exact-state-before-next-go/`](../exact-state-before-next-go/) | Pricing/time · SVG/DWG · ops-graph hardcode reconfirmation |

**Tip commit scope:** `e8ea40a0` is **docs-only** (13 files under `docs/qa/operator-review-92401/`). No `.py` / `.tsx` / `.ts` changes between prior product SHA `a1c28854` and tip.

---

## Boundary checks

### 1) Pricing / time mixing

| Evidence | Result |
|----------|--------|
| `pontaj` / `attendance` / `productive_hours` / `timesheet` in `backend/**/commercial*.py` | **No hits** (grep @ tip) |
| `commercial_price_proposal_service.py` — no capacity/pontaj/time imports | **Clean** |
| `capacity_batch_02_readiness.py` header | `no CostEngine, no HR hours denominator, no client pricing` |
| `capacity_shift_model.py` | `Client pricing is never derived from this model` |
| `execution_ops_graph_read_clarity.py` OR-09 | Strips EUR/ml parentheticals for ops display only — not price authority |
| Prior: [`live-task-graph-review.md`](../operator-review-92401/live-task-graph-review.md) #9 | minutes **null ×18** · no price fields · attendance **0** |
| Prior: [`boundary-integrity.md`](../app-integrity-before-next-go/boundary-integrity.md) §1 | **PASS** |

**Verdict:** **PASS**

---

### 2) HR / Pontaj into Pricing

| Evidence | Result |
|----------|--------|
| `employee_productive_hours.py` module header | `HR/Pontaj = internal cost & availability — never client tariff` |
| `employee_productive_hours.py` — no pricing/commercial/quote/tariff coupling | **Clean** (grep) |
| Owner accept: HR WIP **parked** — 5 employee files restored to HEAD | [`WORKOS_OWNER_ACCEPT_92401_WITH_WARNINGS_REPORT.md`](../operator-review-92401/WORKOS_OWNER_ACCEPT_92401_WITH_WARNINGS_REPORT.md) §3 |
| `employees.py` `EMPLOYEE_MOBILE_ACCESS_ROLES` | Role gate only — not Pricing Registry write path |
| Prior: [`boundary-integrity.md`](../app-integrity-before-next-go/boundary-integrity.md) §2 | **PASS WITH WARNINGS** (historical cost-engine validity helper) |

**Verdict:** **PASS WITH WARNINGS** — HR lifecycle surface pre-exists; no pontaj→Pricing Registry leak at tip. Carry WARN: `is_valid_for_cost_engine` historical coupling in `employees.py` (not new drift).

---

### 3) Employee Mobile expansion

| Evidence | Result |
|----------|--------|
| `App.tsx` routes `/employee-app/*`, `/employee-app-v2/*` | Pre-existing standalone PWA shells |
| Git log `a1c28854..e8ea40a0` on `EmployeeMobile*.tsx` | **No commits** |
| Recent tip-area commits on Mobile paths | None — only drawer fix + ops-graph add (Batch 18) on unrelated paths |
| `MaterializedOpsGraph.tsx` header | `MUST NOT: … Employee Mobile` |
| `dec009_materialize_gate.py` / `execution_ops_graph_read_clarity.py` | Explicit out-of-scope notes |
| Prior: [`track-f-product-direction-operator-readiness.md`](../exact-state-before-next-go/track-f-product-direction-operator-readiness.md) | No Employee Mobile scope |

**Verdict:** **PASS** — no expansion at tip; parallel v2 route is historical prototype, not new GO scope.

---

### 4) SVG / DWG processing added recently

| Evidence | Result |
|----------|--------|
| AGENTS.md §1.1 | Desktop app owns SVG/DWG/DXF intelligence; WorkOS must not extend in-repo parsers |
| `acm_dxf_path_measurement.py` | In-repo DXF SPLINE measurement (commit `69e0260f`, Jul 2026) — **pre-tip**, not new at `e8ea40a0` |
| Intake V6 `svgAnalyzer/*`, `IntakeV6SvgAnalyzerStep.tsx` | Pre-existing lab/intake surfaces — metadata + preview, not central pricing authority |
| DWG paths (`intakeVolumetricSpec.ts`, `VectorStudioPanel.tsx`) | Attachment / manual-review only — `attached_source_only_no_auto_analysis` |
| `artwork_analysis_contract_v1.py` | `WorkOS does not parse SVG/DWG/DXF` |
| Git log `a1c28854..e8ea40a0` on svg/dxf/dwg product paths | **No commits** |
| Prior: [`track-e-boundary-truth.md`](../exact-state-before-next-go/track-e-boundary-truth.md) §7 | **PASS WITH WARNINGS** (AGENTS ownership tension on ACM DXF module) |

**Verdict:** **PASS WITH WARNINGS** — no **new** parser expansion since owner accept; carry WARN on pre-existing in-repo DXF measurement + Intake V6 SVG lab surfaces vs AGENTS external-analyzer rule.

---

### 5) Hardcoded 92401 / 13 / MAT-02 in UI (`MaterializedOpsGraph`)

| Evidence | Result |
|----------|--------|
| Grep `MaterializedOpsGraph.tsx` for `92401`, `MAT-02`, plan `13` | **No hits** |
| Grep `MaterializedOpsGraph*.tsx` for `92401` | **No hits** |
| Present constants | `FIX_DEC009_MAT_01_ORDER_ID = 973010` · `FIX_DEC009_MAT_01_LABEL` only |
| Load path for 92401 review | `?orderId=92401` query param — not hardcoded |
| Prior: [`track-b-live-92401-task-graph.md`](../operator-review-92401/track-b-live-92401-task-graph.md) UI table | **NO** 92401/13/MAT-02 hardcode |
| Prior: [`product-direction-integrity.md`](../app-integrity-before-next-go/product-direction-integrity.md) | **NO** 92401/MAT-02 · WARN carry 973010 default |

**Verdict:** **PASS WITH WARNINGS** — 92401/13/MAT-02 not productized in UI; fixture default **973010 / MAT-01** remains (hygiene WARN, not blocker).

---

### 6) Gap / badge product UI drift on ops-graph path

| Evidence | Result |
|----------|--------|
| `MaterializedOpsGraph.tsx` gap usage | Operational null honesty (`GAP_LABEL`: min, WC, assignee, …) — not readiness queue productization |
| `data-testid="ops-graph-ro-badge"` | **RO** chrome only — not gap-app badge |
| Grep ops-graph for `NOT READY`, `readiness`, `gap-app` | **No hits** |
| Page constraints | READ-ONLY · no start/stop/assign/complete · no POST materialize |
| Prior: [`product-direction-integrity.md`](../app-integrity-before-next-go/product-direction-integrity.md) | Ops-graph remains operational RO surface; lab Product System badges are historical context, not new drift |
| Prior: [`cant-finish-owner-policy.md`](../operator-review-92401/cant-finish-owner-policy.md) | No gap/badge productization this GO |

**Verdict:** **PASS WITH WARNINGS** — ops-graph gap tags = null-field honesty, not gap-app productization; do not expand readiness/badge UI on this path.

---

## Integrated verdict

| # | Boundary | Verdict |
|---|----------|---------|
| 1 | Pricing / time mixing | **PASS** |
| 2 | HR / Pontaj → Pricing | **PASS WITH WARNINGS** |
| 3 | Employee Mobile expansion | **PASS** |
| 4 | SVG / DWG processing (recent) | **PASS WITH WARNINGS** |
| 5 | 92401 / 13 / MAT-02 UI hardcode | **PASS WITH WARNINGS** |
| 6 | Gap / badge ops-graph drift | **PASS WITH WARNINGS** |

**Overall:** **PASS WITH WARNINGS**

Core pricing/time, HR/Pontaj separation, Capacity planning-only posture, and ExecutionPlan null-minutes honesty **hold** at `e8ea40a0`. No product-code drift since owner accept. Non-blocker carries: 973010 fixture default, AGENTS §1.1 tension on in-repo DXF measurement, historical lab SVG/intake surfaces, HR cost-engine validity helper.

**0 BLOCKER** for Track F boundary risk on this tip.

---

## Audit method

- `git rev-parse HEAD` → `e8ea40a0`
- `git log a1c28854..e8ea40a0 -- "*.py" "*.tsx" "*.ts"` → empty (docs-only tip)
- Targeted grep on `MaterializedOpsGraph.tsx`, `commercial*.py`, `employee_productive_hours.py`, svg/dwg paths
- Read prior QA packs under `docs/qa/operator-review-92401/` and `docs/qa/app-integrity-before-next-go/`

**No product edits performed.**
