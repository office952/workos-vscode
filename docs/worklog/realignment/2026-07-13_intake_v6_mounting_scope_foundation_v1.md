# Worklog — INTAKE_V6_MOUNTING_SCOPE_FOUNDATION_V1

**Date:** 2026-07-13  
**Accepted HEAD:** 620f019  
**Delivery HEAD:** b4124a5 (`6bdfb48` + `b4124a5`)  
**Task:** INTAKE_V6_MOUNTING_SCOPE_FOUNDATION_V1

## Owner decision applied

Scope-first model with canonical V1 `mounting_scope` values:

- `none`
- `preparation_only`
- `preparation_and_site_installation`

Deferred `MOUNTING` sold module **not** activated.

## Legacy mapping (on read / normalize)

| Legacy | V1 | site_installation_included |
|--------|-----|----------------------------|
| `no_mounting` | `none` | preserved / null |
| `mounting_included` | `preparation_and_site_installation` | `true` when absent |
| `mounting_external` | `preparation_only` | never inferred true |
| `to_be_decided` | `none` | preserved |
| null + prep signals | `preparation_only` | preserved |
| null + no prep | `none` | preserved |

**Rule:** Site installation is never inferred from preparation fields alone.

## Implementation summary

### UI (IntakeV6ReviewStep Montaj tab)

- Top compact scope selector (Romanian labels)
- **Pregătire** subsection: existing 6 prep fields, gated read-only when `none`
- **Montaj la locație** subsection: `site_installation_included` boolean when scope includes site install
- Persisted prep values preserved when scope=`none`

### Backend

- Schema: V1 enum + legacy accept + `site_installation_included`
- `mounting_scope_service.py`: normalize, hydrate, prep/site active helpers
- Finish normalize hydrates legacy → V1 on save
- Gated: readiness blockers, template enabled policy, plan CNC tasks, live calc mounting rows, EIC/CPP sablon lines, dossier warnings

### Files changed

| Area | File |
|------|------|
| Service | `backend/services/mounting_scope_service.py` |
| Schema | `backend/schemas/intake_v4.py` |
| Finish truth | `backend/services/intake_v4_finish_truth_service.py` |
| Quote policy | `backend/services/volumetric_quote_input_policy.py` |
| Readiness | `backend/services/volumetric_quote_ready_policy.py` |
| Pricing input | `backend/services/intake_v4_pricing_input_service.py` |
| Plan tasks | `backend/services/volumetric_conditional_plan_tasks_service.py` |
| Live calc | `backend/services/intake_v6_offer_scope_live_calc_service.py` |
| EIC/CPP | `estimated_internal_cost_service.py`, `commercial_price_proposal_service.py` |
| Dossier | `intake_v4_template_option_contract_service.py` |
| Frontend lib | `frontend/src/lib/intakeV6/mountingScope.ts` |
| UI | `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx` |
| Product truth | `productTruthDraftBuilder.ts`, `productTruthTypes.ts` |
| Tests | `backend/tests/test_mounting_scope_foundation.py`, `frontend/src/lib/intakeV6/mountingScope.test.ts` |
| E2E | `frontend/e2e/intake-v6-mounting-scope-foundation-v1.spec.ts` |

## Validation

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_mounting_scope_foundation.py -q
# 14 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/mountingScope.test.ts
# 8 passed

npx --yes pnpm@8.10.0 run build
# PASS
```

## Runtime QA

Route: `http://127.0.0.1:3000/intake-v6/IR-MRI01769/operator`  
Screenshots: `docs/qa/intake-v6-mounting-scope-foundation-v1/screenshots/`  
Evidence: `docs/qa/intake-v6-mounting-scope-foundation-v1/evidence_report.json`

## Out of scope (honored)

- MOUNTING sold module
- Pricing rates / CostEngine formulas
- Logistics / transport
- DB migrations
- LIGHTING/ELECTRICAL/SYSTEM_LED/adhesive changes

## BLOCKED_BY_MISSING_MOUNTING_SOLUTION_TEMPLATE (preparation-solution part)

**Verdict for bars/ACM solution picker:** deferred — not in this slice.

| Item | Status |
|---|---|
| Local editable `mounting_system` / `mounting_bar_profile` | **Prevented** — read-only legacy display + deferral note |
| `TPL-METAL-PREMOUNT-STRUCTURE_v1` | Exists as linked optional module; **not** wired as Intake solution picker |
| `TPL-COMP-LETTER-MOUNTING_v1` | Inert contract-only — not executable |
| Boxed ACM mounting template | **Does not exist** as separately offerable solution |
| Template prep fields (`mounting_template_*`) | Retained transitional (letters dossier); gated by `mounting_scope` |

Next bounded task: `.compound-engineering/intake-v6-mounting-ownership-sold-scope-audit-v1/next-product-system-mounting-solution-v1.md`

## Scope correction (Product System modularity)

Applied after owner direction:

- `mounting_scope` foundation **kept** (commercial/operational gate)
- Metal bars / ACM **not** modeled as new local Intake truth
- Legacy persisted values preserved read-only; calc bridge unchanged for existing workspaces
- Site install: `site_installation_included` only (no pricing rates)

## BLOCKED_BY_MISSING_OWNER_RATE

Not triggered — no new site-install pricing rates added; `site_installation_included` is commercial intent only.
