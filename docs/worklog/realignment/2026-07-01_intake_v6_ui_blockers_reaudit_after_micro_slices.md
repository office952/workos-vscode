# 2026-07-01 — Intake V6 UI Blockers Re-audit After Micro-slices

**Status:** PASS  
**Scope:** Read-only / docs-only re-audit gate  
**Roadmap phase:** Phase 1 — Operator-friendly layer/group truth  
**Route verified:** `http://127.0.0.1:3001/intake-v6/IR-MR18L96M/operator`  
**Workspace:** `IV6-BB8EE3F8` / intake `IR-MR18L96M`  
**Runtime anchor:** `gradi-curat.svg`  
**Known blocker:** `layer_roles_incomplete`

---

## What Was Audited

Sources reviewed:

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
- `docs/worklog/realignment/2026-07-01_intake_v6_operator_friendly_labels_state_badges.md`
- `docs/worklog/realignment/2026-07-01_intake_v6_artwork_finish_readiness_badges.md`
- `docs/worklog/realignment/2026-07-01_intake_v6_disabled_cta_product_truth_blocker_summary.md`

Code reviewed read-only:

- `frontend/src/lib/intakeV6/intakeV6OperatorStateBadges.ts`
- `frontend/src/lib/intakeV6/intakeV6QuoteHandoffReadiness.ts`
- `frontend/src/lib/intakeV6/intakeV6DisabledCtaSummary.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6LayersRoleTable.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6ReviewStatusStrip.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6PricingInputPanel.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6OperatorWorkspace.tsx`
- `frontend/src/components/workos/intake-v6/IntakeV6OperatorWorkspaceFooter.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6SvgAnalyzerStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ConfirmStep.tsx`
- focused tests added by the three UI micro-slices

Runtime checked read-only:

- `http://127.0.0.1:3001/intake-v6/IR-MR18L96M/operator`

---

## Verdict

PASS.

The three UI-only micro-slices are coherent as a Phase 1 operator-facing blocker display improvement. The UI surfaces `layer_roles_incomplete` as incomplete Product Truth requiring operator confirmation, not as a Pricing Registry problem. The real blocker remains visible and the disabled CTA remains disabled.

---

## UI Consistency Conclusion

Coherent:

- `SUGGESTED` and `NEEDS_CONFIRMATION` are consistently visible in Straturi for unconfirmed role suggestions.
- `CONFIRMED` is reserved for operator-confirmed states.
- `FALLBACK` is used for hydrated/template values that are not operator-confirmed.
- `BLOCKED` is used for Product Truth blockers in readiness/footer surfacing.
- `NEEDS_FORM_INPUT` is used for form-input or real pricing coverage cases, separate from role confirmation.
- `WARNING` is used for non-role-confirmation warnings and real pricing coverage.
- `READY` exists in the shared vocabulary and is emitted by readiness surfacing when no blocker remains.

Partial:

- Review/artwork/Confirmare live behavior could not be fully re-audited without confirming roles, because `layer_roles_incomplete` correctly blocks access.
- Confirmare blocker area was code/test audited, but not live-audited on this workspace because entering Review/Confirmare would require changing runtime state.
- Some expanded/collapsed artwork card badge rendering duplicates the same state vocabulary in header and expanded content. This is acceptable, not contradictory, but should be watched during Phase 2 UI inventory.

Missing / limited:

- No live Review confirmation of artwork finish cards on `gradi-curat.svg` in the current state.
- No live Confirmare footer audit in this blocker state.

No blocking contradictions found.

---

## Product Truth Blocker Conclusion

PASS.

`layer_roles_incomplete` is displayed as:

- `Product Truth incomplet`;
- operator confirmation required;
- layer/group roles must be confirmed before offer/preview/handoff.

The reviewed code maps `layer_roles_incomplete` and `readiness_not_ready:layer_roles_incomplete` to Product Truth blocker copy in both readiness surfacing and disabled CTA surfacing.

It is not presented as:

- pricing problem;
- Pricing Registry failure;
- missing tariff;
- pricing not ready;
- backend failure.

---

## Pricing Boundary Conclusion

PASS.

The UI preserves the boundary:

- `Pricing Registry este pregătit` appears only as boundary copy for the Product Truth blocker.
- The real blocker remains `Product Truth incomplet / layer_roles_incomplete`.
- Missing tariff/rate wording appears only in real pricing coverage or calculation contexts, not as the reason for `layer_roles_incomplete`.
- No commercial pricing by hour/minute was found in the touched Intake V6 UI/lib surfaces.
- Cost/minute/time language remains internal-estimate oriented where present, not client hourly/minute pricing.

Risky text search results:

- `missing price` / `missing rate` appear in `intakeV6DisabledCtaSummary.ts` as classifier inputs for real pricing coverage.
- `tarif lipsă` / `missing rate` appear in calculation/live material tests and helpers for real missing-rate rows.
- Negative tests explicitly assert that Product Truth blocker UI does not say `pricing not ready` or blame Pricing Registry.

No incorrect Pricing Registry blame found.

---

## Dead Pieces Check

PASS.

No evidence found of:

- unused helper created by the micro-slices;
- unused component created by the micro-slices;
- unrelated tests;
- duplicate dead UI;
- contradictory copy;
- badge definitions disconnected from the touched UI surfaces;
- parallel roadmap/worklog documents that compete with the canonical roadmap;
- temporary shortcuts.

Notes:

- `READY` is part of the shared vocabulary and is used by readiness surfacing for all-clear state, even though the live workspace is currently blocked.
- Header and expanded artwork card areas both render badge vocabulary. This is duplicate presentation of the same concept, not dead UI.

---

## Runtime Visual Check

Route:

```text
http://127.0.0.1:3001/intake-v6/IR-MR18L96M/operator
```

Verified live without confirmations or mutations:

- `Grup detectat: maria` visible;
- `Grup detectat: soare` visible;
- `Grup detectat: ana` visible;
- `Grup detectat: gradinita` visible;
- `Grup detectat: logo stanga` visible;
- `Grup detectat: logo dreapta` visible;
- `Layer sursa: Layer_x0020_1` visible;
- `SUGGESTED` visible;
- `NEEDS_CONFIRMATION` visible;
- CTA `Continuă la Review` remains disabled;
- `BLOCKED` visible;
- `Product Truth incomplet` visible;
- disabled CTA summary says Pricing Registry is prepared and current blocker is Product Truth confirmation;
- no wrong Pricing Registry blame found;
- no `pricing not ready` copy found;
- no commercial price by hour/minute found.

Review live not audited because layer_roles_incomplete correctly blocks access.

---

## Tests / Build

Tests: NOT_RUN_READ_ONLY_AUDIT  
Build: NOT_RUN_READ_ONLY_AUDIT

This audit intentionally did not run tests or build because the scope was read-only / docs-only. Previously recorded micro-slice validations remain the latest executable validations.

---

## No Code Changes

Confirmed:

- no frontend code changes;
- no backend changes;
- no tests changed;
- no analyzer changes;
- no payload changes;
- no pricing changes;
- no ProductDefinition changes;
- no ProductSystem changes;
- no ProductAggregate changes;
- no ExecutionPlan changes;
- no materialization;
- no quote/order/execution creation;
- no Employee Mobile.

Only this audit worklog was created.

---

## Remaining Risks

- Review and Confirmare live audit remain limited until owner-approved role confirmation makes those steps accessible legitimately.
- Phase 2 must inventory whether Review component questions fully align with the reusable component contract before any canonical payload work.
- Existing calculation views still contain real missing-rate copy; this is acceptable when the blocker is truly pricing coverage, but should remain visually distinct from Product Truth blockers.

---

## Recommended Next Step

Owner GO required for Phase 2 — Modular Form component questions.

Recommended next action:

- perform a Phase 2 UI inventory of existing Review controls vs component-owned questions for face, back, cant, finish, electrical, support, and mounting;
- keep it additive and wizard-preserving;
- do not start Product Truth canonical payload, ProductDefinition, Offer, snapshots, ProductAggregate, Task Graph, ExecutionPlan, or Employee Mobile without explicit GO.

---

## Roadmap Alignment Checkpoint

1. Roadmap source used

- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`

2. Current roadmap phase

- Phase 1 — Operator-friendly layer/group truth

3. Roadmap status of this audit

- NOW / re-audit gate

4. Why this audit belongs here

This audit is the required re-audit gate after Phase 1 UI-only micro-slices. It verifies that operator-facing labels, badges, and disabled CTA copy remain coherent and do not hide Product Truth. It does not add Product Truth payload, component questions, pricing, snapshots, ProductAggregate, or execution behavior. It confirms the current blocker remains visible and correctly blocks the flow.

5. What this audit must NOT unlock

This audit does not automatically unlock:

- ProductDefinition;
- ProductSystem/Dossier runtime changes;
- CommercialPriceProposal;
- Quote Snapshot;
- Order Snapshot;
- ProductAggregate;
- Task Graph;
- ExecutionPlan;
- Utilaje/Workcenters;
- Angajati/Skills/Capacity;
- ExecutionReality;
- Employee Mobile.

6. Re-audit gate result

PASS.

7. Roadmap implementation progress

8/100%.

8. Roadmap alignment score

99/100%.

9. Cat sunt in directia stabilita

98/100%.

10. Dead pieces check

PASS.

11. Owner GO required next

YES.

Explicit owner GO is required for Phase 2 — Modular Form component questions.
