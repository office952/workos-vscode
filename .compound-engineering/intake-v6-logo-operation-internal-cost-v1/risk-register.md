# INTAKE_V6_LOGO_OPERATION_INTERNAL_COST_V1 — Risk Register

**Phase:** PLAN  
**Accepted HEAD:** 49896b2

| Risk | Probability | Impact | Mitigation | Test |
|---|---|---|---|---|
| Letters operation double-count | HIGH if Option B | CRITICAL | Namespaced logo filter only; letters stay on RULES | Assert letters op lines unchanged with workspace logos |
| Same logo operation incorrectly deduped | MED | HIGH | No EIC dedupe; key lines by `operation_code + component_ref` | Two segments same code → two EIC lines |
| Shared operation duplicated letters+logo | LOW | HIGH | Different operation codes + refs in evidence | Assert no namespaced letter refs in logo ops |
| Missing time treated as zero | MED | HIGH | quantity None → blocker; no subtotal | Missing geometry → `INTERNAL_GEOMETRY_MISSING` |
| Missing rate treated as zero | MED | HIGH | `INTERNAL_OPERATION_RULE_MISSING` | Empty rate map → blockers not zero cost |
| Artwork area misused for CNC/LED | MED | HIGH | DEC-EIC-03 op codes set; unit tests per category | CNC op with only artwork area → qty None |
| Lost segment identity | LOW | HIGH | `component_code` = BOM `component_ref` | Assert `::logo-stanga` preserved |
| RULES_BY_TEMPLATE divergence | LOW | MED | Do not edit letters rules in V1 | Regression: existing EIC preview tests |
| Commercial pricing coupling | MED | CRITICAL | Reject workcenter_rates; scan_hourly_contamination | No hourly tokens in logo lines |
| API break | LOW | MED | Same POST route/schema | Endpoint regression tests |
| Provenance loss | MED | MED | Extend provenance detail + line warnings | Assert source_template in input_summary/provenance |
| Partial finish fabricates ops | MED | HIGH | Trust BOM omission | Partial finish → zero logo op lines |
| Operator expects minutes×rate | HIGH | MED | Document debt; capacity_hints optional later | Notes in preview + worklog |
