# WorkOS desktop application scorecard — Wave 4 audit

Date: 2026-08-02  
Track: U4A (read-only audit)  
Scope: AppShell desktop routes only; Employee Mobile standalone routes excluded.  
Baseline: `10fca47801d3f672f0fd0811c9510550c33c8602`

## Method and scale

Scores separately assess visual readiness (V) and functional readiness (F), not business completion. `0` is broken/not a product route, `1` is unsafe or lab-only, `2` is partial/expert-only, `3` is usable with material debt, `4` is solid for its intended role, and `5` is production-ready. No route earned 5: the available evidence does not support that claim.

Evidence is code at the stated baseline plus Wave 0–3 reports, the full-route baseline, F3/U3 hardening, and actual-cost/profitability reports. Runtime was not recaptured: the most recent U3 runtime was blocked by incompatible API identity, so console health below is historical evidence rather than a fresh claim.

## Scores by route family

| Route family | V | F | Honest reading |
|---|---:|---:|---|
| AppShell desktop chrome | 4 | 4 | Day shell and role projection are proven; global search and notification controls are presentation-only. |
| `/dashboard` | 3 | 3 | Real gap/KPI view, but audit chrome competes with the decision. |
| `/shop-floor` | 3 | 3 | Live board is usable; internal work-centre identifiers and dark islands remain. |
| `/operator` | 3 | 3 | Queue and task actions exist; compatibility styling remains dense. Historical duplicate-key warning is closed. |
| `/tablet`, `/tablet/:stationId`, `/tablet/:stationId/:taskId` | 3 | 3 | Clear station entry; deepest task state lacks fresh audit coverage. |
| `/execution` | 3 | 3 | Good flow entry and next-step continuity; still overlaps other production homes. |
| `/execution/:order_id` | 3 | 4 | Backend-refreshed plan/reality actions and honest missing states; page is too dense and mixes task work, stock, gates, and profitability. |
| `/execution/ops-graph` | 3 | 3 | Useful expert graph; technical terminology and controlled-assignment surface need clarity work. |
| `/execution/reality-review` | 2 | 3 | Useful audit surface, not an operator home; should remain management/admin oriented. |
| `/intake`, `/intake/:id` | 4 | 3 | U1 made first-level flow readable; legacy deep route and readiness path need fresh coverage. |
| `/intake-v6/operator`, `/intake-v6/:workspaceId/operator` | 3 | 3 | Active specialist workspace, outside primary commercial story and not fully re-audited here. |
| `/product-system/products`, `:templateCode` | 4 | 3 | U3 improves product/admin story; frozen laboratory/reference depth remains. |
| Product System structure routes | 2 | 2 | Reference/laboratory detail, not a complete broadly usable authoring surface. |
| Planned Product System sections (`components`, `resources`, `operations`, `dependencies`, `validation`, `advanced`) | 2 | 1 | Explicitly planned/placeholder-oriented; honest but not runtime-complete. |
| Blueprint dossier / output preview | 2 | 2 | Expert/admin diagnostic and preview tools, not primary desktop workflow. |
| `/quotes`, `/quotes/:quoteId` | 4 | 3 | Commercial flow and backend gates preserved; list-card amount versus KPI mismatch remains a trust problem. |
| `/orders`, `/orders/:orderId` | 4 | 3 | Clear accepted-commercial-to-execution hand-off; deep detail coverage is incomplete. |
| `/clients`, `/clients/:clientName` | 3 | 2 | List is usable; no audited navigable path to workspace detail. |
| `/documents` | 2 | 2 | Functional surface exists, but “Document Center” conflicts with Romanian IA. |
| `/inventory` | 3 | 3 | Operational registry is usable; stock truth remains a protected, non-commercial source. |
| `/inventory/pricing` and pricing aliases | 3 | 2 | U3 clarifies ownership, but the pre-existing maximum-update-depth test failure and pricing complexity prevent a stronger score. |
| `/utilaje` | 3 | 3 | Capacity/feasibility vocabulary is clearer; interior registry/diagnostic styling remains. |
| `/colaboratori` | 3 | 3 | Straightforward list; no contrary evidence. |
| `/reports`, `/reports/operational` | 3 | 2 | General reports read adequately; operational report remains English/developer-facing. |
| `/employees`, `/employees-records`, `/:employeeId` | 3 | 3 | Core records are usable for permitted staff; deep profile discoverability is unproven. |
| `/attendance`, `/attendance/effects` | 3 | 3 | Usable HR workflow; secondary effects is not a broad role surface. |
| `/employee-payments`, `/employee-advances` | 2 | 3 | Sensitive workflows work by evidence, but high-risk content needs stronger role and visual isolation. |
| `/modules`, `/governance`, `/settings` | 2 / 2 / 3 | Admin reference surfaces; settings is the clearest operator-admin destination. |
| `/demo/*`, Product System legacy aliases, redirects | 1–2 | n/a–2 | Retain only as explicitly labelled DEV/legacy paths; they must not be product peers. |

## Aggregate

Desktop visual mean is approximately **3.0/5** for live primary routes; functional mean is approximately **2.9/5**. That is a usable staging/admin application, not a complete production operating system. The weakest material gap is not colour polish: it is the absence of a single, concise Execution Closure and Profitability truth surface after work is complete.

## Console and runtime health

Historical Wave 2 duplicate-key warnings on `/operator?orderId=973019` were explicitly closed, with day/dark proof. Wave 3 could not obtain fresh screenshots because its frontend blocked against an incompatible backend system identity. Therefore this audit records **console health as unverified at U4A time**, rather than calling it clean.
