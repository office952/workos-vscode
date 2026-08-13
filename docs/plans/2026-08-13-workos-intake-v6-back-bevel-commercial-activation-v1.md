---
artifact_contract: ce-unified-plan/v1
artifact_readiness: requirements-only
product_contract_source: owner-go-WORKOS_INTAKE_V6_BACK_BEVEL_COMMERCIAL_ACTIVATION_V1
execution: code
title: Intake V6 back bevel commercial activation
date: 2026-08-13
branch: feat/f7i-owner-rate-activation
baseline_head: 5cb792f8
---

# Intake V6 — Back bevel commercial activation V1

## Goal Capsule

Activate **commercially price-bearing** șanfren CNC spate Forex 10 mm as a separate **Servicii / Operații** line when the operator selects „cu șanfren”, without creating a separate production CNC task/job.

```text
BEVEL_PRICE_BEARING = YES   # Owner decision supplied
COMMERCIAL_SERVICE ≠ SEPARATE_PRODUCTION_TASK
```

### Authority hierarchy

1. This Owner GO (commercial meaning + execution grouping invariant)
2. Prior audit pack `docs/qa/workos-intake-v6-back-bevel-commercial-authority-no-effect-audit-v1/`
3. Active CPP / Pricing Registry seeds (no invented rates)
4. Shared CNC operation model (`cnc_backing_bevel_forex_10mm`)

### Stop conditions (resolved by Owner GO 1 + 3)

```text
OWNER_RATE_DECISION_REQUIRED = NO
EXECUTION_TASK_GROUPING_CHANGE_REQUIRED = AUTHORIZED (backing CNC pair only)
ce-work = AUTHORIZED for this bounded plan only
```

---

## Product Contract

### Requirements

1. **R1 — Commercial line when ON:** Offer shows `Șanfren CNC spate Forex 10 mm` under Servicii / Operații only when bevel is active.
2. **R2 — Debitare unchanged:** `debitare_spate` rate/qty path stays as today (m² × 15 EUR); bevel is additive, not absorbed.
3. **R3 — Layer/group truth:** Layer/group `backing_mode` must reach pricing; mixed groups bill only bevel-enabled groups.
4. **R4 — No double charge:** One bevel line; no global+layer duplicate; no second charge from execution ops.
5. **R5 — Same CNC job:** Debitare + șanfren remain one execution task/job; `EXECUTION_TASK_COUNT_DELTA = 0` OFF→ON.
6. **R6 — Category:** Servicii / Operații (CNC), not Manoperă.
7. **R7 — No UI redesign:** Existing backing-mode selector remains intent source.
8. **R8 — Non-regression:** face finish, RETURN-CANT, Oracal labor, RAL, GET diet, save/recalc, Option B, D2, null FX, Confirm/VAT/FX.

### Acceptance examples

| Scenario | Commercial | Execution |
|----------|------------|-----------|
| Backing ON, bevel OFF | No sanfren line; debitare present | Cutting op; no bevel op; task count baseline |
| Same config, bevel ON | Sanfren line present; net/gross ↑ by bevel×(1+VAT) | Bevel op present; **same task count** as OFF |
| Mixed groups (if supported) | Qty = sum perimeters of ON groups only | Grouped CNC job still one backing task |

---

## Planning Contract

### Phase 1 — Quantity / unit authority (RESOLVED)

Technical op `cnc_backing_bevel_forex_10mm` / `VOLUMETRIC_BACKING_BEVEL_RULE`:

| Field | Value |
|-------|--------|
| `BEVEL_TECHNICAL_QUANTITY` | backing CNC contour length |
| `BEVEL_TECHNICAL_UNIT` | `ml` (path perimeter) |
| `SOURCE` | `shared_cnc_operation_model.VOLUMETRIC_BACKING_BEVEL_RULE.basis_key = backing_cnc_cutting_perimeter`; material-breakdown `operation_rows[].quantity` |
| Passes (machine) | `FOREX_10MM_BEVEL_PASSES_OWNER = 2` |
| Equivalent load | `quantity_ml × 2` → `ml-pass` |

Do **not** reuse `debitare_spate` m² for bevel.

**Chosen commercial quantity source (for implementation):** sum of backing CNC perimeter ml for letter groups with `backing_mode == forex_10_with_bevel` only (fallback: material-breakdown bevel row quantity when single-mode).

```text
BEVEL_COMMERCIAL_UNIT = ml   # contour; pass factor applied via rate basis ml/pass
BEVEL_QUANTITY_SOURCE = backing_cnc_cutting_perimeter_ml (bevel-enabled groups only)
```

### Phase 2 — Rate authority (BLOCKING)

| Field | Finding |
|-------|---------|
| `EXISTING_REUSABLE_RATE` | **YES (provisional family)** — `CNC_ROUTER` |
| `RATE_CODE` | `CNC_ROUTER` |
| `RATE_VALUE` | `1.5` |
| `RATE_UNIT` | EUR / **ml / pass** (seed notes) |
| `PROVENANCE` | `backend/seeds/seed_volumetric_workcenter_rates.py` — Owner-defined active workcenter rate; already used for face CNC commercial reuse (F7H) and for bevel **preview** costing in material-breakdown |

**No dedicated** “șanfren spate” commercial tariff exists in CPP/registry.

Recommended commercial formula (pending Owner confirm):

```text
subtotal_eur = perimeter_ml × bevel_passes(2) × 1.5
             = perimeter_ml × 3.0   # effective EUR/ml if passes fixed at 2
```

Example (prior QA clone ON): `7.4175 × 2 × 1.5 = 22.2525 EUR` net surcharge (then × VAT).

```text
OWNER_RATE_DECISION_REQUIRED = YES
```

Owner authorized price-bearing behavior, **not** silent numeric activation. Need explicit GO on:

1. Reuse `CNC_ROUTER` 1.5 EUR/ml/pass × 2 passes, **or**
2. Alternate Owner number/unit.

### Execution task grouping (BLOCKING STOP)

Current generator (`build_iv3_cnc_candidate_tasks_from_operation_rows` in `intake_v4_cnc_operation_dry_run_service.py`):

```text
EXECUTION_TASK_GROUPING_BEFORE = 1 operation_row → 1 candidate_task (cnc_op:{key})
```

Observed: bevel ON adds `cnc_op:cnc_backing_bevel_forex_10mm` → task count **16 → 17**.

Owner PASS requires `EXECUTION_TASK_COUNT_DELTA = 0` and same task contains cut + bevel.

```text
SEPARATE_EXECUTION_TASK_CREATED (today, bevel ON) = YES  # already true before commercial work
```

Per Owner GO: **STOP before casually changing task architecture.**

Bounded fix proposal (needs Owner authorize as part of this GO or a sibling GO):

- Merge only the pair `cnc_backing_cutting_forex_10mm` + `cnc_backing_bevel_forex_10mm` into **one** candidate task (title e.g. CNC spate Forex 10 mm / pregătire spate) with both ops as membership/inputs.
- Do not merge face cut/bevel in this slice unless Owner expands scope.
- Keep separate **operation** identity for instructions/traceability.
- Commercial lines remain separate.

```text
EXECUTION_TASK_GROUPING_AFTER (proposed) = one backing CNC task containing cut + conditional bevel ops
SEPARATE_EXECUTION_TASK_CREATED (target) = NO
```

Without this grouping fix, commercial-only implementation **cannot PASS** Owner criteria.

### Pricing handoff repair (ready once unblocked)

| Item | Plan |
|------|------|
| `LAYER_PATH_FIX` | Teach `resolve_volumetric_backing_state` / `_resolve_v4_backing_presence` to honor `letter_group_finishes[].backing_mode`; expose per-group bevel qty into quote_input / CPP |
| `CPP_ADDITIONAL_RULE` | New rule e.g. `sanfren_spate` / `VOL_V2_BACK_BEVEL_CNC_ML` gated on bevel-enabled qty > 0; category Servicii; **do not** change `debitare_spate` |
| Mixed groups | Quantity = Σ perimeter of groups with `forex_10_with_bevel` only |

### Key technical decisions (KTDs)

| ID | Decision | Rationale |
|----|----------|-----------|
| KTD-1 | Separate CPP line, not absorb into debitare | Owner GO; debitare is m² sell |
| KTD-2 | Bill ml contour (+ pass factor via registry) | Matches bevel op basis; not m² |
| KTD-3 | Reuse CNC_ROUTER only after Owner numeric confirm | No dedicated bevel tariff |
| KTD-4 | Fix layer→QI before/with CPP | Otherwise group truth lost |
| KTD-5 | Grouping fix required for PASS | Current 1:1 op→task violates Owner invariant |

### Sequencing

1. Owner answers rate + grouping authorization  
2. `/ce-work` only after both green  
3. Handoff fix → CPP rule → grouping merge → tests → QA matrix → local commit, PUSH=NO  

### Assumptions / non-goals

- No face/return/Oracal/RAL/VAT/FX changes  
- No new top-level UI controls  
- No back bevel into Manoperă  
- No arbitrary registry invention without Owner number  

---

## Implementation Units (draft — blocked)

### U1 — Layer/group bevel handoff

- Files: `backend/services/intake_v4_backing_mode_service.py`, `backend/services/intake_v4_pricing_input_service.py`, tests under `backend/tests/`
- Deliver: quote_input / finish matrix carries per-group bevel; mixed groups correct

### U2 — CPP `sanfren_spate` rule

- Files: `backend/data/commercial_rules_volumetric_v2.py`, `commercial_price_proposal_service.py` (gate only if needed), tests
- Deliver: OFF absent / ON present; debitare unchanged; Servicii category

### U3 — Backing CNC task grouping

- Files: `backend/services/intake_v4_cnc_operation_dry_run_service.py` (+ any V4 twin path), tests
- Deliver: OFF→ON task count delta 0; same task contains cut + bevel ops
- **Requires Owner authorize**

### U4 — Evidence + regressions

- QA pack `docs/qa/workos-intake-v6-back-bevel-commercial-activation-v1/`, worklog, focused pytest + commercial parity

---

## Verification Contract

Commands (after unblocked implementation):

- Targeted pytest: new bevel commercial + handoff + grouping tests; existing face/return/commercial suites from Owner list  
- QA-clone runtime matrix OFF/ON/mixed  
- Prove `EXECUTION_TASK_COUNT_DELTA = 0` and commercial deltas  

---

## Definition of Done

- Plan gate fields fully filled with Owner-confirmed rate  
- PASS criteria: `COMMERCIAL_EFFECT = CORRECT` **and** `PRODUCTION_TASK_FRAGMENTATION = NONE`  
- Local commit only; PUSH=NO  

---

## Mandatory plan gate (current)

```text
BEVEL_PRICE_BEARING = YES
BEVEL_COMMERCIAL_UNIT = ml
BEVEL_QUANTITY_SOURCE = backing_cnc_cutting_perimeter_ml (bevel-enabled groups only)
BEVEL_RATE_AUTHORITY = CNC_ROUTER (provisional reuse — OWNER CONFIRM REQUIRED)
RATE_VALUE = 1.5   # proposed
RATE_UNIT = EUR/ml/pass × 2 passes   # proposed
LAYER_PATH_FIX = resolve_volumetric_backing_state + letter_group handoff
CPP_ADDITIONAL_RULE = sanfren_spate / VOL_V2_BACK_BEVEL_CNC_ML (name TBD at implement)
EXECUTION_TASK_GROUPING_BEFORE = 1 op row → 1 task
EXECUTION_TASK_GROUPING_AFTER = BLOCKED (propose merge backing cut+bevel)
SEPARATE_EXECUTION_TASK_CREATED = YES today / must become NO
```

```text
OWNER GO 1+3 CONFIRMED
RATE = CNC_ROUTER 1.5 EUR/ml/pass × 2
GROUPING = backing cut + bevel → one task
ce-work = DONE (local commit only; PUSH = NO)
```

---

## Appendix — research crumbs

- Audit: `docs/qa/workos-intake-v6-back-bevel-commercial-authority-no-effect-audit-v1/`
- Op rule: `backend/services/shared_cnc_operation_model.py` (`VOLUMETRIC_BACKING_BEVEL_RULE`)
- Task 1:1 map: `backend/services/intake_v4_cnc_operation_dry_run_service.py` `build_iv3_cnc_candidate_tasks_from_operation_rows`
- Registry: `backend/seeds/seed_volumetric_workcenter_rates.py` `CNC_ROUTER` 1.5 EUR/ml/pass
