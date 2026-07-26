# INTAKE_V6_LINKED_LOGO_ARTWORK_BOM_OWNERSHIP_DEDUPE_V1 — Review

**Phase:** REVIEW COMPLETE  
**Accepted HEAD before:** `0df2c79`  
**Branch:** main  
**Review verdict:** **APPROVED_WITH_DOCUMENTED_DEBT**

---

## Checklist

| Question | Verdict |
|---|---|
| Exactly one owner per artwork concept? | **YES** — `comp_logo_finish::{segment}` |
| Finish component owns all artwork rows? | **YES** |
| Face component = substrate + CNC only? | **YES** |
| mapping_only non-costable? | **YES** — `linked_segment::*` suppressed |
| Generic dedupe by material/operation code? | **NO** — not introduced |
| Cross-segment collapse? | **NO** |
| Quantities changed? | **NO** — formulas untouched |
| ProductDefinition changed? | **NO** |
| EIC hides duplicates via new dedupe? | **NO** — consumes canonical BOM only |
| 35 RON/m² rates active? | **NO** |
| Commercial pricing changed? | **NO** |
| Seed change limited to contract? | **YES** — `seed_tpl_volumetric_logo_v1.py` only |
| Live DB reseeded? | **NO** |
| Tests assert 1 row/concept/segment? | **YES** |
| Letters-only unchanged? | **YES** |

---

## Documented debt

1. **35 RON/m² artwork operation rates** remain unconfigured — parent task `INTAKE_V6_LOGO_OPERATION_INTERNAL_RATE_CATALOG_V1` on hold.
2. **`logo_print_finish` task bundling** — print/lam/application may share task label text; BOM cardinality is now separated; Execution/task generation not modified in this task.
3. **Historical workspaces** seeded before contract realignment may still carry parallel rows until isolated fixture reseed or future migration/backfill (explicitly out of scope).

---

## Forbidden scope respected

No changes to: frontend, CPP, pricing registry, Quote, Order, Execution, DB schema, migrations, binding persistence, ProductDefinition builder, EIC rate catalog.

---

**REVIEW COMPLETE**
