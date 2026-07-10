# Intake V6 — Selected Layer Refs Historical Impact Audit (V1)

**Date:** 2026-07-10
**Task:** INTAKE_V6_SELECTED_LAYER_REFS_HISTORICAL_IMPACT_AUDIT_V1
**Verdict:** **CONTROLLED_RESAVE_PILOT_RECOMMENDED**
**Accepted HEAD:** `9315fcf`
**Branch:** `main`
**Commit:** _pending_
**Implementation performed:** NO
**Database writes:** 0

---

## Purpose

Read-only measurement of historical drift between canonical `layer_role_setup` and derived `svg.selected_layer_refs` after commit `9315fcf`.

---

## Script safety review

| Script | Writes possible | Safe |
| --- | --- | --- |
| `docs/qa/intake-v6-selected-layer-refs-logo-role-handoff-v1/historical_impact_audit.py` | NO | YES |
| `docs/qa/intake-v6-selected-layer-refs-historical-impact-audit-v1/run_historical_impact_audit.py` | NO | YES |

Both use SQLite read-only URI and SELECT-only queries. No ORM, no commits, no mutation endpoints.

---

## Database target

- **Engine:** SQLite
- **File:** `backend/dev.db` (local development)
- **Config:** `DATABASE_URL` / `.env.example` pattern
- **Not production/staging** — owner should repeat audit on staging before any write GO

---

## Total counts

| Metric | Value |
| --- | --- |
| Workspaces audited | 147 |
| With layer_role_setup | 110 |
| Complete setup | 98 |
| Missing persisted refs | 109 |
| Derivation differs | 97 |
| Stale persisted refs | **0** |
| MATCH | 1 |
| Unknown roles | 0 |
| Ambiguous identity | 0 |

---

## Classification

- PRINTED_ARTWORK_LOGO_GAP: 78
- MISSING_PERSISTED_REFS: 19
- INCOMPLETE_SETUP: 12
- MATCH: 1

---

## Printed artwork

- 78 workspaces with confirmed `printed_artwork`
- All 78 derive `vector_logo` on recompute
- All 78 lack persisted logo refs
- 0 linked-template bindings
- 30 logo finish confirmed; all 78 remain blocked on binding and/or other gates
- 0 letter-only misclassification from stale persisted refs

---

## Downstream exposure

- HIGH risk: 5 workspaces (quote snapshot and/or quote/order linked)
- See `docs/qa/intake-v6-selected-layer-refs-historical-impact-audit-v1/high_risk_rows.json`

---

## Historical fixture

`22ef834d-f2d0-453b-a7a7-118928c98a39`:

- Persisted refs: absent
- Derived: 4× `vector_litere`, 2× `vector_logo`
- Row mutated: NO
- Classification: PRINTED_ARTWORK_LOGO_GAP, risk MEDIUM

---

## Backfill decision

**CONTROLLED_RESAVE_PILOT_RECOMMENDED**

- Drift is widespread but deterministic and uniformly *missing* (not wrong).
- Natural re-save handles the majority (no downstream linkage).
- Five HIGH-risk workspaces with quote/order exposure need a controlled pilot re-save before broader action.
- Bulk backfill not justified: no stale contradictions, canonical setup intact, promotion already blocked when refs absent.

---

## Tests

29/29 PASS (derivation, runtime capture, promotion planner). No test modifications.

---

## Files created

- `docs/qa/intake-v6-selected-layer-refs-historical-impact-audit-v1/audit_summary.md`
- `docs/qa/intake-v6-selected-layer-refs-historical-impact-audit-v1/impact_counts.json`
- `docs/qa/intake-v6-selected-layer-refs-historical-impact-audit-v1/representative_rows.json`
- `docs/qa/intake-v6-selected-layer-refs-historical-impact-audit-v1/high_risk_rows.json`
- `docs/qa/intake-v6-selected-layer-refs-historical-impact-audit-v1/run_historical_impact_audit.py`
- `docs/qa/intake-v6-selected-layer-refs-historical-impact-audit-v1/execution_log.md`

---

## Honest opinion

Drift is real and broad on local dev (99% of complete setups missing projection), but it is **predictable missing data**, not corrupted truth. Commercial exposure is limited to 5 workspaces on this DB. Natural re-save plus a small pilot is safer than bulk backfill. Staging/production audit is mandatory before any write plan.

---

## Next safe step

Re-run `run_historical_impact_audit.py` read-only against staging, then owner GO for controlled re-save pilot on the 5 HIGH-risk IDs + fixture `22ef834d-…`.

---

## Direction score

**94/100** — correct read-only validation gate before any backfill decision.

**Roadmap awareness:** 9/10
