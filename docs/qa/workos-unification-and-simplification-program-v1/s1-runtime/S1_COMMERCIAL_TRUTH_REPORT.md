# S1 — Commercial truth and workflow honesty

| Field | Value |
|-------|--------|
| Task | `S1_COMMERCIAL_TRUTH_AND_WORKFLOW_HONESTY_V1` |
| Date | 2026-08-14 |
| Boundary | Display / label / FLUX membership only |
| Owner DB mutations | 0 |
| Push | NO |
| S2+ | Not authorized |

## Verdict

`GS-01` / `GS-02` / `GS-03` = **PASS** (display). No pricing, quote, order, Product Definition, Product Aggregate, execution, or RBAC change.

## What changed

- Commercial FLUX is **Cereri → Oferte → Comenzi**. Produse is not a sold-work step.
- Product System route and Lucrări sidebar **Produse** stay (deferred; not the S1 defect).
- Intake V6 live rail uses **Estimare curentă** / **Estimare cu TVA** / **Estimare netă**. `Ofertă client` remains official-offer language after quote write.
- `ready_for_quote` display is **Marcat intern** / **Marchează intern**. Enum, API, and DB value are unchanged. No join to V6 2/3, dry-run `is_ready_for_quote`, or `handoff_allowed`.

## Runtime

| Check | Result |
|-------|--------|
| FLUX `/intake` admin light/dark | Cereri → Oferte → Comenzi. Sidebar Produse still present. |
| FLUX `/intake` sales light/dark | Same FLUX. Sales nav reduced; Produse still in Lucrări. |
| FLUX `/quotes` sales light | Oferte highlighted. Next-step copy goes to Cereri / Comenzi. |
| V6 money | Workspace `IR-MSRB28PU` → `/intake-v6/IR-MSRB28PU/operator` (`IV6-F823AA06`). Rail: **Estimare curentă**, **Estimare cu TVA 729,04 EUR**, Estimare netă 602,51 EUR, TVA 126,53 EUR. |
| Wave 2 amount | Wave 2 observed **725,25 EUR** on the same workspace. Live dry-run now **729,04 EUR**. S1 did not change FE math or dry-run authority; record the live number. |
| Readiness | Summary card **Marcat intern** = 0. List rows show **Nou** (non-ready). No `ready_for_quote` list row present — `STATE_NOT_REACHED` for a row chip; card label is proven. |

## Screenshots

- [s1-flux-intake-admin-light.png](s1-flux-intake-admin-light.png)
- [s1-flux-intake-admin-dark.png](s1-flux-intake-admin-dark.png)
- [s1-flux-intake-sales-light.png](s1-flux-intake-sales-light.png)
- [s1-flux-intake-sales-dark.png](s1-flux-intake-sales-dark.png)
- [s1-flux-quotes-sales-light.png](s1-flux-quotes-sales-light.png)
- [s1-v6-estimate-sales-light.png](s1-v6-estimate-sales-light.png)
- [s1-v6-estimate-sales-dark.png](s1-v6-estimate-sales-dark.png)

## Tests

Targeted Vitest: 10 files, 141 passed (commercial FLUX, V6 chrome vocabulary, WorkIntake badges, StatusBadge, ux-helpers, shell nav reachability, V6 live summary, intake action summary, readiness stages, IntakeDetail).

`productSystemBlankWorkspaceIa.test.ts` still has pre-existing encoding failures. Not added to CI allowlist. S1 only asserts the FLUX strip is absent from Product System layout.

## Stop

S2+ not authorized. No push. No PR.
