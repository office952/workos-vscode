# INTAKE V6 MONTAJ AUTHORITY SPLIT REPORT

## 1. Verdict

**TECHNICAL PASS (authority repair)** with runtime caveat: proof BE is `:8013` because Windows ghost listeners keep stale code on `:8003`. Owner review still required before declaring product-complete.

## 2. Mini decizia agentului

Separated product support / commercial mounting / electrical / production consumables E2E (compilers + readiness + UI + pricing labels). Did not migrate DB, rename keys, change 5% formula, or redesign tasks.

## 3. Git state

- Branch: `feature/product-system-active-path-isolation-v1`
- Baseline HEAD at start: `392d6e1`
- Foreign WIP: present, untouched in commit staging

## 4. Runtime

| Surface | Value |
|---------|-------|
| FE | `http://127.0.0.1:3000` |
| Proof BE | `http://127.0.0.1:8013` |
| FE proxy | `BACKEND_PORT=8013` |
| Ghost BE | `:8003` still answers with **pre-fix** composition (`MOUNTING_SCOPE_INACTIVE`) |
| ACM WS | `3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982` (`IV6-EA145E74`) |

## 5. Owner decisions applied

D1–D5 applied as locked in `AUTHORITY_SPLIT_CHECKPOINT.md`.

## 6. Authority model before

Commercial `mounting_scope` gated product ACM composition → false `MOUNTING_SCOPE_INACTIVE`. Legacy corner required even when segmented multi-panel confirmed. Template + Accesorii language mixed with commercial Montaj.

## 7. Authority model after

| Authority | Owns |
|-----------|------|
| A Product support | ACM/support, dims, segmentation, bindings |
| B Commercial mounting | scope, template, site install (prep-gated) |
| C Electrical/service | segmented ECM / single-panel corner |
| D Production consumables | 5% accessories line (pricing) |

## 8. ACM + mounting none

Valid. PD includes `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`. UI Fundal remains active.

## 9. MOUNTING_SCOPE_INACTIVE

Removed emission from composition contract. Child inclusion uses `is_mounting_solution_composition_active`. Proof API: blockers `[]`.

## 10. Segmented status truth

API `CONFIRMED`; UI status `Confirmat` after reload. Coalesce protects CONFIRMED from accidental PROPOSED overwrite unless `force_repropose`.

## 11. Service corner ownership

Confirmed multi-panel segmented → skip `service_corner_required` even if ECM DRAFT. Single-panel still requires legacy corner.

## 12. Template conditionality

Scope none: template controls hidden; legacy notice when persisted `true`; process `template_selected=false`.

## 13. Accessories/connectors pricing

Operator label → Consumabile producție; still appears under scope none; missing tariff pricing-only; 5% formula unchanged.

## 14. Persistence

Keys unchanged. Save/reload UI authorities present; API finish matches UI segmented CONFIRMED.

## 15. ProductDefinition

`solution_status=confirmed`, ACM node included, no MOUNTING_SCOPE_INACTIVE. Evidence: `runtime/pd.json`.

## 16. ProductAggregate

Conflicts `[]` on proof BE. Evidence: `runtime/aggregate_conflicts.json`.

## 17. Confirmare

No `MOUNTING_SCOPE_INACTIVE` / process service-corner codes in Confirmare text on ACM WS. Other product blockers may remain (out of commercial-mounting scope).

## 18. Operator UI

Montaj clusters: Fundal și carcasă · Montaj comercial · Alimentare și service · Avansat. `data-authority` markers present.

## 19. Task/execution safety

No new task system. No Intake task generation changes. Aggregate task intent untouched by this repair.

## 20. Tests

| Suite | Result |
|-------|--------|
| `test_montaj_authority_split_v1.py` + composition contract | **31 passed** |
| FE LiveCalculationSummary + handoff + service corner | **51 passed** |

## 21. Runtime scenarios

| # | Scenario | Verdict |
|---|----------|---------|
| 1 | ACM single/multi + mounting none | **PASS** (live WS) |
| 2–3 | Segmented proposed/confirmed | **PASS** confirmed path; coalesce unit for proposed protect |
| 4–5 | prep / site | unit coverage for template active under preparation |
| 6 | Single-panel corner | unit **PASS** |
| 7 | Segmented without legacy corner | live + unit **PASS** |
| 8 | Template legacy true + none | live UI notice **PASS** |
| 9 | Template + preparation | unit **PASS** |
| 10 | Accesorii + none | live pricing banner **PASS** |

## 22. Screenshots

Under `screenshots/`. Key probes in `runtime/capture_summary.json` (fundal/commercial/electrical true; segmented Confirmat; consumabile label).

## 23. Compatibility handling

Legacy template: **retained but inactive**. No migration.

## 24. Hidden regressions

Ghost `:8003` can reintroduce false blockers if FE proxies there. Diagnostic “1 blocant” may reflect non-Montaj product issues.

## 25. Files modified

- `backend/schemas/product_process_contract.py`
- `backend/services/acm_segmented_background_service.py`
- `backend/services/gradi_logical_list_read_model_service.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/services/product_definition_composition_contract.py`
- `backend/services/product_process_resolve_input_adapter.py`
- `backend/services/product_process_resolver_service.py`
- `backend/tests/test_montaj_authority_split_v1.py` *(new)*
- `backend/tests/test_product_definition_composition_contract.py`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6LiveCalculationSummary.test.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/lib/intakeV6/intakeV4OperatorUiDisplay.ts`
- `frontend/src/lib/intakeV6/intakeV6QuoteHandoffReadiness.ts`
- `docs/qa/intake-v6-montaj-authority-split-2026-07-19/**`
- `docs/worklog/realignment/2026-07-19_intake_v6_montaj_authority_split.md`

## 26. Files intentionally not modified

Foreign WIP (product-system UI shell, unrelated architecture docs, `product_template_availability_service.py`, `productDefinitionPreview.ts`, seeds, migrations, CPP formulas, task graph).

## 27. Dead pieces check

`BLOCKER_MOUNTING_SCOPE_INACTIVE` constant kept for legacy handoff mapping only — no longer emitted by composition.

## 28. Duplicate truth check

Segmented electrical owns multi-panel service; legacy corner demoted/hidden when segmented CONFIRMED.

## 29. Plugin usage

| Tool | Use |
|------|-----|
| Git | branch/WIP isolation |
| pytest / vitest | focused suites |
| HTTP `:8013` | PD/Aggregate/finish truth |
| Playwright | screenshots + DOM authority probes |
| Browser MCP | available; Playwright used for pack |
| Figma | not required for authority repair |

## 30. Worklog

`docs/worklog/realignment/2026-07-19_intake_v6_montaj_authority_split.md`

## 31. Commit

`fix(intake-v6): split product support from commercial mounting` (isolated; exact paths).

## 32. Metoda de lucru si logica abordarii

Checkpoint first → fix ownership predicates (not UI-only) → unit invert old blocker expectations → prove on clean port after ghost `:8003` discovered → UI authority presentation → docs/commit.

## 33. Roadmap awareness checkpoint

Aligns with active-path isolation / Montaj E2E audit repair. Does not activate ACM commercial offer scope or Execution redesign.

## 34. Cat sunt in directia stabilita

Cat sunt in directia stabilita: **92/100%**

## 35. Ce am construit este conform planului?

**DA**, with evidence: D1–D5 coded; PD/Agg clean on proof runtime; UI authorities visible; tests green; ghost-port caveat documented.

## 36. Can implementation continue?

Only after owner review.
