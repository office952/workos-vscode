---
title: Scope Intake V6 operator_confirmation_missing to the step where it is actionable
date: 2026-07-16
problem_type: ui_bug
component: frontend_readiness_presentation
symptoms:
  - Step 2 shows red primary banner for operator_confirmation_missing
  - Problem count implies Configurare/product finishes are invalid
  - Legacy artwork wording still visible on active Step 2 surfaces
root_cause: Handoff surfacing used global !handoffAllowed for the Step 2 banner instead of step-scoped fatal filtering
tags:
  - intake-v6
  - confirmation
  - step-scoped
  - vector-logo
  - handoff-banner
module: intakeV6QuoteHandoffReadiness
applies_when:
  - A fatal gate is only actionable on a later operator step
  - Primary blocker counts must not include future-step gates
  - User-facing Vector Logo terminology must not rename backend artwork_* fields
---

# Scope Intake V6 operator_confirmation_missing to the step where it is actionable

## Context

Backend confirmation remained a legitimate fatal gate. Operators still saw a red Step 2 banner (“Handoff blocked”) when the only fatal was `operator_confirmation_missing`, which can only be cleared on Step 3.

## Guidance

1. Keep backend fatality and `handoff_allowed` unchanged — scope **presentation** by `currentStep`.
2. Filter `operator_confirmation_missing` out of Step 1/2 primary reasons and primary counts; show it on Step 3 with a checkbox-directed action.
3. When confirmation alone blocks handoff on Step 1/2, prefer neutral next-step guidance over a red product/configuration banner.
4. Suppress only the **loading** null-handoff flash; permanent preview fetch failure must still surface a banner.
5. Rename user-facing “artwork” copy to Vector Logo / Vector Logo N without renaming schema identifiers (`artwork_finishes`, moduleCodes, etc.).
6. Do not invent step query params in product navigation; if a query is needed for verification, set discrete `URLSearchParams` keys (never one encoded blob as a key).

## Why This Matters

False Step 2 blockers destroy trust immediately before the first real Quote. Operators must see blockers only where they can act.

## Related

- `docs/worklog/realignment/2026-07-16_intake_v6_step_scoped_confirmation_banner_vector_logo_copy.md`
- `docs/solutions/architecture-patterns/intake-v6-step3-confirmation-hydration.md`
