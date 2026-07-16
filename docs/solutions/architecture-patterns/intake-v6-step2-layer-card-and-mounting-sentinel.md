---
title: Intake V6 Step2 layer-card shell and installation-template mounting sentinel
date: 2026-07-16
category: architecture-patterns
module: intake-v6
problem_type: architecture_pattern
component: documentation
severity: medium
applies_when:
  - Changing Step2 letter or logo finish cards
  - Persisting Montaj without ACM or metal Product System children
  - Mapping contains_missing_prices into the operator readiness banner
tags:
  - intake-v6
  - layer-card-shell
  - mounting-sentinel
  - backing-vs-mounting
  - readiness-banner
---

# Intake V6 Step2 layer-card shell and installation-template mounting sentinel

## Context

Step2 Configurare needed compact letter/logo cards (Față / Cant / Spate summaries when collapsed; stacked editors when expanded) plus an honest Montaj path for gradi-curat: installation template + site install, without treating Forex letter backs as a common ACM/metal panel.

## Guidance

1. **Shared shell** — Both letter and logo cards must use `IntakeV6LayerCardShell`. Collapsed headers show labeled Față / Cant / Spate summaries only; editable Forex/Spate controls exist only inside `expandedChildren`.
2. **Backing ≠ mounting** — `backing_mode` (Forex/PVC per letter/logo body) must never be conflated with `mounting_solution`. Individual Forex backs remain product truth; Montaj uses the installation-template sentinel.
3. **Mounting sentinel** — Empty extra solution persists as `{ kind: "installation_template", template_code: null, configuration: {} }` when șablon is enabled with area > 0 and material forex|paper. This clears `MOUNTING_SOLUTION_MISSING` without activating ACM/metal composition children.
4. **Banner severity** — Compact count summary with expandable details. Residual artwork copy uses “neconfirmat”. `contains_missing_prices` with **zero** concrete unpriced line keys is a **diagnostic warning** (`contains_missing_prices_inconsistent`); when line keys exist, list them. Derive keys via `collectMissingPriceLineKeysFromBreakdown` — never hardcode an empty list while claiming “no lines”.
5. **Runtime proof** — Prefer `npm run dev:stack` (backend `:8001`, frontend `:3000`). Reuse healthy listeners; do not kill foreign processes. Prove HEAD is served (Vite module for new shell + API totals) before declaring UI closed.

## Examples

- Workspace `11891d68-…`: `material-breakdown.totals.material_cost_total` stayed `725.16` EUR; keys retained `forex_backing` + `cnc_backing_cutting_forex_10mm`; mounting sentinel present; no ACM material keys.
- Evidence folder: `docs/qa/intake-v6-step2-runtime-closure/`.

## Related Issues

- `docs/solutions/intake-v6-backing-mode-not-common-panel.md`
- `.compound-engineering/intake-v6-step2-layer-ui-and-mounting-contract/plan.md`
- Commit `463707b` (implementation) + Step2 runtime closure commit
