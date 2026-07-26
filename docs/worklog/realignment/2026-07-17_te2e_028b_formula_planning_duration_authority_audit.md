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

### Owner gates applied
UNPAUSE · FORMULA AUTHORITY = PRODUCT AGGREGATE · EXPLICIT ZERO ONLY · MISSING = NULL · CONTRACT RULE · LETTERS ONLY · NEW TEST DATA · GO

### Selected formula
| Field | Value |
|-------|--------|
| Formula ID | `count_based_time` (Product System `FormulaId`) |
| Operation | `vector_prep` (Pregătire vector / font) |
| Params | `minutes_per_letter = 2.0` |
| Input | `letter_count` (ProductDefinition geometry / product facts) |
| Expected | 5 × 2.0 = **10.0** min |
| Not used | `perimeter_pass_linear_meter` / other quantity formulas |

### Authority model
Product System contract (`planning_duration_contract.py`) → Aggregate resolve (`product_aggregate_planning_duration_service.py`) on workspace compose + freeze facts → Plan V2 consumer (no re-eval) → task → Post-Job read-only.

### Contract mode
- `static` via `calculation_type=static` (028A preserved)
- `formula` via Product System duration contract for `vector_prep`
- `none` for quantity placeholders without duration contract → minutes null

### Zero semantics
Placeholder seed 0 cleared to null; missing/malformed input → null; explicit 0 only with `planning_duration_status=resolved` + provenance.

### Code changes
- `backend/services/planning_duration_contract.py` (new)
- `backend/services/product_aggregate_planning_duration_service.py` (new)
- Aggregate schema optional planning fields
- Plan V2 consumer accepts Aggregate-emitted formula provenance
- Hooks: workspace composition + quote snapshot freeze facts
- `backend/scripts/_te2e028b_live_proof.py` (LOCAL_TEST_FIXTURE seed helper)
- Control Center evidence/limitation updates

### Tests
`backend/tests/test_te2e_028b_formula_planning_duration.py` — 10 tests PASS  
`test_te2e_028a_planning_minute_source.py` — regression PASS  
Commercial isolation + legacy `/price` isolation — PASS

### Fixture
`LOCAL_TEST_FIXTURE` order **972910** · plan **11** · commercial **1888** · retention `dev_ephemeral`  
Refs 8/9/10 and 92402/92403/972901 untouched.

### Runtime/UI proof
URL `http://127.0.0.1:3000/execution/972910`  
Plan vs execuție: Pregătire vector / font = **10 min**; Control calitate = **15 min**; other formula qty ops = **lipsă**; actual = neînregistrat; revenue 1888.00; write_back false.

### Modules / Governance
LIMITATION / EVIDENCE UPDATE on ProductAggregate + ExecutionPlan + Post-Job in Control Center. No new node. Boundary clarification only (PS defs · Aggregate resolve · Plan consume · CostEngine/EIC excluded).

### Commits
1. `docs(execution): approve te2e-028b formula duration authority`
2. `feat(execution): resolve formula planned duration in aggregate`
3. `docs(execution): close te2e-028b formula proof`

### Remaining breadth
TE2E-028 open: Stock G3 · labor money · fixture qualification · more templates/ops.
