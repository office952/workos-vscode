---
title: Split Aggregate info diagnostics from Order/Execution review gates
date: 2026-07-16
problem_type: architecture_pattern
component: service_object
severity: medium
tags:
  - intake-v6
  - readiness
  - review-warnings
  - diagnostic-warnings
  - dossier
  - trigger
module: intake_v6_canonical_readiness
applies_when:
  - ProductAggregate emits DOSSIER_METADATA_ONLY CANONICAL_CONTRACT_AUTHORITY or TEMPLATE_IDENTITY
  - TRIGGER_FIELD_MISMATCH must remain Order or Execution sensitive
  - Quote draft must stay gated only by fatal blockers such as operator confirmation
---

# Split Aggregate info diagnostics from Order/Execution review gates

## Context

Intake V6 lifted every ProductDefinition `unresolved_warning` into handoff `review_warnings`. `merge_policy_findings` and `client_order_production_flags_for_quote` then cleared `accept_allowed` / convert / production whenever that list was non-empty. Aggregate `severity=info` traces (`DOSSIER_METADATA_ONLY`, `CANONICAL_CONTRACT_AUTHORITY`, `TEMPLATE_IDENTITY`) therefore blocked offer acceptance and Order/Execution even though commercial dry-run was READY and Quote draft only required Step 3 operator confirmation.

## Guidance

1. Keep Aggregate/form diagnostics emitted — do not delete or suppress codes at ProductDefinition / ProductAggregate.
2. In `collect_canonical_readiness_findings` / `partition_canonical_unresolved_warnings`, route the three info codes into `diagnostic_warnings`.
3. Keep `TRIGGER_FIELD_MISMATCH` (and other real review codes) on `review_warnings` so Order/Execution stay gated.
4. Gate `accept_allowed` / `convert_to_order_allowed` / `production_allowed` on `review_warnings` only.
5. Surface `diagnostic_warnings` on the handoff preview and Confirm UI as nonblocking technical details.
6. Never auto-clear `operator_confirmation_missing`; never treat diagnostics as a global warning bypass.

## Why This Matters

Operators can create a priced offer after explicit Step 3 confirmation without false dossier/identity friction, while TRIGGER alias drift and genuine review warnings still protect Order/Execution until Product System migrates the link field or equivalent truth is accepted.

## When to Apply

- Intake V6 quote handoff / confirm after commercial dry-run READY with Aggregate info noise.
- Any future Aggregate `severity=info` code that must stay visible without clearing client/order/production flags — add its code to `NONBLOCKING_DIAGNOSTIC_WARNING_CODES` only with owner gate.

## Examples

Before: five `review_warnings` (2× TRIGGER + 3 info) → `accept_allowed=false` even with commercial READY.

After: three info codes on `diagnostic_warnings` (visible); TRIGGER remains on `review_warnings` (Order/Execution blocked); Step 3 fatal alone blocks Quote draft.

Related audit: `.compound-engineering/gradi-curat-dossier-trigger-truth-audit/`.
