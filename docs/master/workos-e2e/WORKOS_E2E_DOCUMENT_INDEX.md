# WorkOS E2E — Document Index

**Program:** `WORKOS_E2E_MASTER_ALIGNMENT_AND_FINALIZATION_V1`  
**Scope:** Master program authority for connected-flow E2E direction under `docs/master/workos-e2e/`.  
**Not B2 / Important Documents** unless the owner later promotes individual files.  
**Living progress:** read `WORKOS_E2E_STATUS.md` first for phase, Accepted HEAD, and wave closure.  
**Evidence baseline:** TRUE E2E audit at `fe6c6f7` (see `KNOWN_COVERAGE_GAPS.md`).

## Classification legend

| Class | Meaning |
|-------|---------|
| MASTER | Program authority in this folder — agents read for E2E direction |
| LIVING | Advances with implementation (STATUS, TASK_GRAPH, ISSUE_REGISTRY, DECISION_LOG) |
| BASELINE | Narrative/map frozen at TRUE E2E evidence; defer maturity to LIVING docs |
| SUPPORTING_EVIDENCE | Historical proof — do not override master |
| SUPERSEDED | Replaced by master — archaeology only |
| ARCHIVE | Old builds — not active direction |
| DUPLICATE | Copy of another doc |
| CONTRADICTORY | Conflicts master — resolve before use |
| INVALIDATED | Proven wrong at evidence baseline `fe6c6f7` |
| UNKNOWN | Needs owner classification |

---

## MASTER (10 primary — this folder)

| Document | Role | Purpose |
|----------|------|---------|
| `WORKOS_E2E_STATUS.md` | **LIVING** | Current phase, Accepted HEAD, wave outcomes |
| `WORKOS_E2E_DECISION_LOG.md` | **LIVING** | Owner decisions |
| `WORKOS_E2E_TASK_GRAPH.md` | **LIVING** | Executable tasks |
| `WORKOS_E2E_ISSUE_REGISTRY.md` | **LIVING** | Single issue inventory |
| `WORKOS_E2E_IMPLEMENTATION_ROADMAP.md` | MASTER | Waves 0–7 |
| `WORKOS_E2E_IMPLEMENTATION_OPERATING_MODEL.md` | MASTER | Wave coordinator, gates, lanes |
| `WORKOS_E2E_ACCEPTANCE_PLAN.md` | MASTER | E2E acceptance gates |
| `WORKOS_E2E_SYSTEM_MAP.md` | **BASELINE** | Boundaries, owners, contracts |
| `WORKOS_E2E_MASTER_DOSSIER.md` | **BASELINE** | Human-readable program narrative (maturity may lag STATUS) |
| `WORKOS_E2E_DOCUMENT_INDEX.md` | MASTER | This file |

---

## SUPPORTING_EVIDENCE (audits & reviews)

| Path | Topic | Notes |
|------|-------|-------|
| `docs/qa/workos-e2e-operational-coherence-audit-v1-true-e2e/` | TRUE E2E audit | Primary evidence base |
| `docs/qa/workos-e2e-figma-master-maps-v1/` | Figma MASTER 00–13 creation | Screenshots + review; nodes `14:2`–`14:15` |
| `docs/qa/workos-e2e-operational-coherence-audit-v1/` | First E2E audit | Superseded for direction; Intake depth valid |
| `docs/qa/workos-e2e-operational-coherence-audit-v1/QUALITY_REVIEW_REPORT.md` | Audit quality | Explains TRUE E2E requirement |
| `docs/qa/connected-product-flow-coherence-audit-v1/` | Prior connected audit | SUPPORTING |
| `docs/qa/intake-v6-review-autosave-setpayload-fix-v1/` | F-001 closure | SUPPORTING |
| `docs/qa/workos-e2e-operational-coherence-audit-v1-true-e2e/KNOWN_COVERAGE_GAPS.md` | Coverage gaps | Absorbed from removed review package (2026-07-16); no in-repo ZIP duplicate |

---

## SUPPORTING_EVIDENCE (plans)

| Path | Class |
|------|-------|
| `docs/plans/2026-07-14-002-audit-workos-e2e-operational-coherence-plan.md` | SUPPORTING |
| `docs/plans/2026-07-14-003-audit-workos-e2e-operational-coherence-true-e2e-plan.md` | SUPPORTING |
| `docs/plans/2026-07-14-004-feat-workos-e2e-master-alignment-finalization-plan.md` | SUPPORTING (this program plan) |

---

## SUPPORTING_EVIDENCE (worklogs)

| Path | Topic |
|------|-------|
| `docs/worklog/realignment/2026-07-14_workos_e2e_operational_coherence_audit_v1.md` | First audit |
| `docs/worklog/realignment/2026-07-14_workos_e2e_operational_coherence_audit_v1_quality_review.md` | Quality review |
| `docs/worklog/realignment/2026-07-14_workos_e2e_operational_coherence_audit_v1_true_e2e.md` | TRUE E2E |
| `docs/worklog/realignment/2026-07-14_intake_v6_review_autosave_setpayload_fix_v1.md` | F-001 |
| `docs/worklog/realignment/2026-07-14_workos_e2e_master_alignment_and_finalization_v1.md` | This program |
| `docs/worklog/realignment/2026-07-14_workos_e2e_figma_master_maps_v1.md` | Figma MASTER maps |
| `docs/worklog/realignment/2026-07-14_workos_e2e_controlled_implementation_orchestration_v1.md` | Implementation orchestration |

---

## ARCHITECTURE (SUPPORTING — align to canonical)

| Path | Notes |
|------|-------|
| `docs/architecture/realignment/01_INTAKE_V6_PRODUCT_TRUTH.md` | Align with D-005, D-006 |
| `docs/architecture/realignment/04_PRODUCT_AGGREGATE_TECHNICAL_GRAPH.md` | Wave 2 |
| `docs/architecture/app-flows/06_PRICING_AND_INTERNAL_COST_FLOW.md` | Wave 3 |
| `docs/architecture/app-flows/07_OFFER_QUOTE_ORDER_FLOW.md` | Wave 4 |
| `docs/architecture/product-system/VOLUMETRIC_LETTERS_FULL_E2E_PRODUCT_TRUTH_TO_EXECUTION_ALIGNMENT.md` | Target alignment doc — verify vs canonical |

---

## SUPERSEDED for active direction

| Path | Superseded by |
|------|---------------|
| `docs/qa/workos-e2e-operational-coherence-audit-v1/ISSUE_REGISTRY.md` (E2E-001–015) | `WORKOS_E2E_ISSUE_REGISTRY.md` |
| `docs/qa/workos-e2e-operational-coherence-audit-v1-true-e2e/ISSUE_REGISTRY.md` | Same (copy — TE2E authoritative in master) |
| Shallow E2E implementation sequence in first audit §37 | `WORKOS_E2E_IMPLEMENTATION_ROADMAP.md` |

**Do not add supersession headers to source files until owner approves** (per program spec).

---

## DUPLICATE / CONTRADICTORY watchlist

| Item | Issue |
|------|-------|
| Dual pricing: CostEngine vs 7G/7H | CONTRADICTORY until W3-T01 resolves (TE2E-025) |
| `support_type` vs `mounting_solution` | CONTRADICTORY until W1-T01 (TE2E-001) |
| `ALL_STAGES_INSPECTED: YES` vs coverage gaps | Clarified in `docs/qa/.../KNOWN_COVERAGE_GAPS.md` — not contradictory if read with D-012 |

---

## Archive plan (no deletion)

1. Keep all `docs/qa/BUILD_*.md` as ARCHIVE
2. Keep all audit folders immutable
3. New work logs only under `docs/worklog/realignment/`
4. Implementation QA under `docs/qa/BUILD_<TASK>.md` when waves start
5. Master folder versioned by DECISION_LOG entries

## Documents inventoried (count)

| Area | Approx count |
|------|--------------|
| `docs/qa/` BUILD + audit | 200+ |
| `docs/plans/` | 4+ relevant |
| `docs/worklog/realignment/` | 30+ E2E-related |
| `docs/architecture/` | 15+ connected |
| **Master folder** | **10** |

Full inventory of every file deferred — classify on demand when touching a topic.
