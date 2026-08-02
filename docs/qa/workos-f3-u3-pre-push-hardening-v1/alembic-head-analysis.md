# Alembic head analysis — F3/U3 pre-push

## Heads before correction

| Head | Parent | Nature |
|---|---|---|
| `s50_execution_plan_prepared_by_clarification_target` | `s49_employee_monthly_internal_pay_amount` | Accidental side branch (name collision with main `s50_employee_payment_records`) |
| `s60_actual_cost_policy_runtime_v1` | `s59_employee_end_date_lifecycle` | F3 main-chain tip |

Main chain after s49:

```text
s49 → s50_employee_payment_records → s51 → … → s59 → s60
```

## Root cause

Not “multi-head is fine”. The clarification migration forked from s49 while payments continued on a differently named s50. F3 correctly parented s60 on s59. Repo precedent for merge-only closure: `s31_merge_heads_production_gate`.

## Fresh-DB failure before hygiene

`s50_execution_plan_prepared_by_clarification_target` ALTERed `task_clarification_requests`, but no prior migration creates that table (local DBs obtained it via ORM bootstrap). Fresh `upgrade head` after merge therefore failed on the side branch.

## Correction

1. Harden side-branch upgrade/downgrade with inspect-before-mutate and create table when missing (schema intent unchanged).
2. Add merge-only `s61_merge_heads_actual_cost_policy` revising both heads.

## Deploy command

```text
alembic upgrade head
```

Single head after correction: `s61_merge_heads_actual_cost_policy`.
