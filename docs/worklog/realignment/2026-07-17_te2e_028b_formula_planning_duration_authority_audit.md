# Worklog — TE2E-028B Formula Planning-Duration Authority Audit

**Date:** 2026-07-17  
**Type:** Audit / owner gates (no product implementation)  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD at audit:** `9761aa6`  
**Canonical audit:** `docs/audits/2026-07-17_te2e_028b_formula_planning_duration_authority_audit.md`

---

## Purpose

Determine current authority for formula-derived planned minutes before any TE2E-028B implementation. Preserve commercial isolation (7G + legacy `/price` isolation) and TE2E-028A static-minute closure.

---

## What was done

1. **Repository gate** — branch + HEAD `9761aa6` match; ports FE `:3000` / BE `:8001` up; refs 8/9/10 read-only.
2. **Code search** — `formula_based`, `estimated_minutes`, Plan V2 resolver, Aggregate ops map, seed `_op_formula`, `formula_handlers` duration functions, EIC capacity rules, CostEngine minute coercion.
3. **Runtime RO** — fixture order `972901` / plan `10`: 12 tasks, 11 null planning minutes, 1 static (qc 15).
4. **Authority model** — Product System owns definitions; Aggregate should emit resolved minutes; Plan consumes; CostEngine/EIC not Plan SoT.
5. **Zero semantics** — seed `formula_based+0` = PLACEHOLDER; Plan null = missing source; static 15/60 = explicit.
6. **Options** — Recommended Option A (evaluate in ProductAggregate). Rejected PD-owned minutes and CostEngine/EIC as Plan authority.
7. **Documents** — audit + this worklog only. No app code, schema, or test-data writes.

---

## Verdict

`TE2E_028B_OWNER_GATES_READY`

---

## Owner decision pack (proposed)

```text
TE2E-028B = UNPAUSE
FORMULA AUTHORITY = PRODUCT AGGREGATE
ZERO SEMANTICS = EXPLICIT ZERO ONLY
MISSING INPUT = NULL
SOURCE PRECEDENCE = CONTRACT RULE
PROOF SCOPE = LETTERS ONLY
REFERENCE DATA = NEW TEST DATA
AUDIT COMMIT = DA
IMPLEMENTATION = GO
```

---

## Owner gates applied (2026-07-17)

```text
TE2E-028B = UNPAUSE
FORMULA AUTHORITY = PRODUCT AGGREGATE
ZERO SEMANTICS = EXPLICIT ZERO ONLY
MISSING INPUT = NULL
SOURCE PRECEDENCE = CONTRACT RULE
PROOF SCOPE = LETTERS ONLY
REFERENCE DATA = NEW TEST DATA
AUDIT COMMIT = DA
IMPLEMENTATION = GO
```

## Commit policy

1. Audit docs only: `docs(execution): approve te2e-028b formula duration authority`
2. Implementation + tests: `feat(execution): resolve formula planned duration in aggregate`
3. Optional evidence close: `docs(execution): close te2e-028b formula proof`

Stage exact paths only. Never `git add .` / `-A`.

---

## Boundaries respected

- No reopen of 7G, Quote/Order snapshots, legacy pricing isolation, TE2E-028A static flow, plans 8/9/10.
- No Stock G3, labor money, lifecycle enforcement, template breadth expansion.
- Formula minutes remain operational-only (not customer price).
- CostEngine / EIC are not Plan duration authorities.
- No schema migration / permanent seed by default.

---

## Implementation section

*(Filled after GO implementation.)*
