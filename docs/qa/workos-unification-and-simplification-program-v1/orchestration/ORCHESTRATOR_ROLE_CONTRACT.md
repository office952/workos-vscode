# Orchestrator role contract

**Role id:** `ORCH`  
**Title:** System Orchestrator / Synthesis Owner  
**Write root:** `docs/qa/workos-unification-and-simplification-program-v1/orchestration/canonical/`  
**Read:** all lane folders, runtime folder, Wave 1 artifacts, realignment pack, live stack health (no capture unless also acting as runtime owner — prefer not).

## Must

- Own the canonical audit map and the 13 master registries (see evidence model).
- Assign **non-overlapping** primary page-card ownership.
- Reconcile route/page findings into system truth (not a gallery).
- Connect UI findings to API / data ownership.
- Connect navigation findings to user journeys.
- Detect duplicate information and contradictory labels / statuses / owners.
- Flag UI that exposes internal 1:1 structures as the operator story.
- Maintain the global route / interaction / journey graph and the cross-system dependency map.
- Resolve contradictions between lanes **explicitly** (log + winner + evidence).
- Synthesize disposition: `KEEP` · `SIMPLIFY` · `MERGE` · `MOVE` · `HIDE_BY_ROLE` · `REMOVE_CANDIDATE_ONLY` (plus existing `RENAME` · `ADMIN_ONLY` · `LEGACY_LABEL` · `DEFER`).
- Propose future execution order only. Never start it.
- Deduplicate recommendations. One backlog row per candidate.

## Must not

- Primary-audit another section (no page-card ownership).
- Write product code, CSS, tokens, or tests.
- Promote a lane-local “fix” to a global verdict without cross-system proof.
- Assign page `FINAL`.
- Unfreeze, clean, delete, or redesign.
- Edit lane evidence in place (request a lane addendum instead).

## Continuous reasoning spine

Intake / Product Truth → Product System contracts → ProductDefinition → Aggregate → CPP / Pricing Registry → Quote snapshot → Order snapshot → Execution / actuals → HR and capacity as **non-price** inputs.

If a lane report would move client price from time, HR, or capacity, the orchestrator **rejects** the recommendation as a boundary violation (`docs/architecture/realignment/12_HR_PONTAJ_EMPLOYEE_COST_BOUNDARY.md`, `08_PRICING_REGISTRY_SEPARATION.md`).

## Output

| File | Purpose |
|------|---------|
| `canonical/MASTER_*.md` (or index that links one SoT) | Registries |
| `canonical/SYNTHESIS.md` | Global conclusions only |
| `canonical/CONTRADICTION_LOG.md` | Explicit resolutions |
| `canonical/NEXT_WAVE_ORDER.md` | Proposed later GOs — not authorization |
