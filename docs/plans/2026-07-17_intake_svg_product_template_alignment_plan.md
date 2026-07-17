# Plan — Intake SVG ↔ Product System alignment

| Field | Value |
|-------|-------|
| Date | 2026-07-17 |
| Status | Recommendation only — **no implementation** |
| Depends on | Audit `docs/audits/2026-07-17_intake_v6_step1_svg_product_system_template_mapping_audit.md` |
| Owner GO next | Awaited |

## Answers to final questions

1. **Product System first?** **Yes.**
2. **Missing contract:** assignable **SVG-bindable components** exposed by the active Product Template; unified geometry-unit → component association; retire stale `TPL-BOND-CASETAT` recommendation.
3. **Need:**
   - Product Template **new**? No for ACP.
   - Component Template **new**? No — use `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` + process `ALUCOBOND_CASED_PANEL`.
   - Extension of existing? **Yes** — publish SVG-bindable component contract on letters root.
   - SVG role new? Optional geometric **Contur suport** (generic); not “Vector ACP”.
   - Mapping new? **Yes** — PS-driven options + unify dual flows.
   - UI exposure only? **Insufficient** — dual SoT + FinishSetup schema gap remain.
4. **Owner label:** Contur suport → Panou Alucobond casetat (component).
5. **Technical codes:** contour/geometry ids + `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` / `alucobond_cased` / process `ALUCOBOND_CASED_PANEL`.
6. **Activation:** Product Template optional support component active → then associate contour.
7. **SVG association:** layer and/or closed contour identity → component instance.
8. **Storage:** ProductDefinition / finish typed fields (mounting_solution + durable selection schema).
9. **Avoid duplicates:** one assignment UI; kill parallel Alucobond-only island once unified; delete pending `TPL-BOND-CASETAT` path.
10. **First build:** Product System vector-component template alignment.

## Implementation order

```text
A. Product System — SVG-bindable component contract on TPL-VOLUMETRIC-LETTERS_v2
B. Retire TPL-BOND-CASETAT pending recommendation → ACM boxed / metal
C. Unify layer-role + closed-contour into one assignment model
D. Persist typed selection (FinishSetup schema) — small dedicated GO
E. Intake Step 1 consumes PS option list (no hardcoded ACP product list)
F. Owner runtime validation on LITERE-VOLUMETRICE-ACP.svg
G. Later: materials / CUT-FOLD / CPP / tasking
```

## Explicit non-goals (this track)

- Hardcoded ACP list in FE as final design
- `Vector ACP` as Product Template
- Analyzer deciding material
- CPP / DXF / task materialization in Step 1
- Broad Intake redesign

## Next safe step (single)

**Option 1 — GO PRODUCT SYSTEM VECTOR-COMPONENT TEMPLATE ALIGNMENT**
