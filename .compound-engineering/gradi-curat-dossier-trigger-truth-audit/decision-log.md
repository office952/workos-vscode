# Decision log — Gradi-curat dossier + trigger truth audit

**Date:** 2026-07-16  
**Task:** `WORKOS-GRADI-CURAT-DOSSIER-AND-TRIGGER-TRUTH-AUDIT-V1`  
**Workspace:** `11891d68-c4c8-4719-acc5-f8fcb22a44af`  
**Baseline HEAD:** `c6302b9e30eb04a4a80aa82f16ce76c0ecb4dd84`  
**Mode:** Docs-only (no product / severity-mapping implementation)

---

## Audit decisions (locked)

| ID | Decision |
|----|----------|
| D1 | Classification = `READY_FOR_QUOTE_BUT_NOT_EXECUTION` |
| D2 | Can continue after Step 3 confirm = `YES_FOR_QUOTE_ONLY` |
| D3 | `operator_confirmation_missing` remains the only legitimate Step 3 quote fatal; do not remove/bypass/auto-confirm |
| D4 | Live `fatal_blockers` = only `operator_confirmation_missing` |
| D5 | Live `review_warnings` = 5 dossier/trigger codes (2× TRIGGER + 3 Aggregate info traces) |
| D6 | `DOSSIER_METADATA_ONLY` class = `INFORMATIONAL_METADATA_WARNING` (root letters dossier v3/approved) |
| D7 | Commercial dry-run READY; totals net 3513.56 / VAT 737.85 / gross 4251.41 RON — non-regression target |
| D8 | Dossier/trigger codes do not invalidate commercial CPP/dry-run truth |
| D9 | First coherent friction cause = `UI_SEVERITY_MAPPING` (info/diagnostics lifted into gating `review_warnings`) |
| D10 | Codes are **not** promoted into draft `fatal_blockers`; they **are** promoted to accept/convert/production blockers via `client_order_production_flags_for_quote` |
| D11 | All five review codes are **root** Aggregate/form — not per Vector Logo child |
| D12 | TRIGGER cause = legacy alias (`metal_support_required` vs `mounting_system`); equivalent Intake truth exists for this workspace |
| D13 | Do not suppress or delete diagnostics |
| D14 | Do not make all warnings nonblocking globally |
| D15 | Do not bypass ProductDefinition / ProductAggregate truth |
| D16 | No product implementation in this audit; correction is a separate owner GO |

---

## Intended lifecycle (locked direction — move, do not delete)

| Code | Quote | Order/Execution |
|------|-------|-----------------|
| `operator_confirmation_missing` | BLOCK until checkbox | Keep |
| `DOSSIER_METADATA_ONLY` | Never block | Never block (stay visible diagnostic) |
| `CANONICAL_CONTRACT_AUTHORITY` | Never block | Never block |
| `TEMPLATE_IDENTITY` | Never block | Never block |
| `TRIGGER_FIELD_MISMATCH` | Never block Quote | Remain review gate until link migration or equivalent-truth acceptance |

---

## Owner gates (answered 2026-07-16)

| Gate | Answer |
|------|--------|
| G1 | **YES** — Quote draft and priced offer may proceed after explicit Step 3 confirmation if no other fatal blockers remain |
| G2 | **TRIGGER_FIELD_MISMATCH** remains Order/Execution-sensitive; must not block Quote |
| G3 | **DOSSIER_METADATA_ONLY**, **CANONICAL_CONTRACT_AUTHORITY**, **TEMPLATE_IDENTITY** remain visible technical diagnostics; must not block Quote, offer accept, Order convert, or Execution |

Do not re-ask these gates.

## Correction implementation (authorized)

| ID | Decision |
|----|----------|
| I1 | Task `WORKOS-GRADI-CURAT-READINESS-SEVERITY-CHANNEL-SPLIT-V1` |
| I2 | Channel split in `intake_v6_canonical_readiness_service` — info codes → `diagnostic_warnings`; TRIGGER (+ other) stay in `review_warnings` |
| I3 | Gating (`accept_allowed` / convert / production) uses `review_warnings` only |
| I4 | Diagnostics remain visible via handoff `diagnostic_warnings` + Confirm UI section |
| I5 | `operator_confirmation_missing` unchanged as Step 3 fatal |
| I6 | No pricing / Quote / Order creation / diagnostic deletion / global nonblock |

---

## Forbidden (held)

- Suppress or delete diagnostics
- Global “all warnings nonblocking”
- Auto-confirm / remove Step 3 gate
- PD/PA compile bypass
- Pricing / registry / workspace writes in audit
- Quote/Order creation in this audit
- Commit until owner review; push/PR NO/NO

---

## Artifacts

1. `.compound-engineering/gradi-curat-dossier-trigger-truth-audit/plan.md` (29-section final report)
2. `.compound-engineering/gradi-curat-dossier-trigger-truth-audit/decision-log.md` (this file)
3. `docs/worklog/realignment/2026-07-16_gradi_curat_dossier_trigger_truth_audit.md`
4. `docs/qa/gradi-curat-e2e/dossier-trigger-truth-evidence.json`
