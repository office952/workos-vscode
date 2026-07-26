# INTAKE_V6_AGGREGATE_COST_BOM_WORKSPACE_LINKED_LOGO_WIRING_V1 — Risk Register

**Phase:** PLAN  
**Accepted HEAD:** bee9757

| Risk | Probability | Impact | Mitigation | Test |
|---|---:|---:|---|---|
| Double-counted materials (print/laminate across segments) | MED | HIGH | Never merge rows with different `component_ref`; preserve PA dedupe keys | Tests 11–15 |
| Partial logo treated as complete | MED | HIGH | Respect PA empty logo materials; include partial warning; no zero-cost fabrication | Tests 6–10 |
| Duplicate operation costs | LOW | MED | Map each PA operation once; do not re-expand logo template in adapter | Tests 16–18 |
| Lost segment identity (`logo-stanga` / `logo-dreapta`) | MED | HIGH | Preserve namespaced `component_id` / `component_ref` on BOM rows | Tests 21–23 |
| Adapter recompiles product (PD/PA rebuild) | LOW | HIGH | Builder calls existing services once each; adapter pure function | Tests 27–29 |
| Recommendation used as truth | LOW | HIGH | No imports of recommendation service; code review gate | Test 28 |
| Commercial pricing accidentally activated | LOW | CRITICAL | No changes to price bridge, CPP, Quote; test asserts no commercial totals | Test 24 |
| Zero-cost interpreted as ready | MED | MED | Existing `pricing_availability=missing`; partial bom_status | Tests 9–10 |
| Letters-only regression | MED | HIGH | Baseline test: workspace letters-only ≡ template BOM | Test 1 |
| API compatibility break | LOW | MED | `workspace_id` remains optional; omit → unchanged path | Test 1 + regression |
| Provenance lost on logo rows | MED | MED | Pass through `source_template_code`, `provenance`, namespaced refs | Tests 21–23 |
| Missing tariff hidden | LOW | MED | Keep `missing_pricing` + blocked status | Test 19 |
| Logo module filter excludes all logo rows | **HIGH** | **HIGH** | DEC-CBOM-06 effective active modules | Tests 2–3, 11–12 |
| Builder still uses template-only aggregate | **HIGH** | **HIGH** | Single-line orchestration fix + test fixture alignment | Tests 2–5 |
| Geometry keys missing for logo formulas | MED | MED | Accept partial/blocked; do not invent `svg_area_m2` | Partial semantics tests |
| EIC drift (out of scope) | MED | LOW | Document follow-up; do not modify EIC in v1 | N/A |
| Test fixture mirrors production gap | MED | MED | Update `bom_context` to use `build_for_workspace` when workspace_id set | Implementation |

## Rollback

| Step | Action |
|---|---|
| 1 | Revert builder to `aggregate_svc.build(template_code)` |
| 2 | Revert adapter module-activation helpers |
| 3 | Remove new tests only |
| 4 | Endpoint unchanged — no migration |

Rollback risk: **LOW** — isolated orchestration + adapter filter logic.
