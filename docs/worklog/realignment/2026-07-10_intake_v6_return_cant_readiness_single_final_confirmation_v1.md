# Intake V6 — Return/Cant Readiness + Single Final Confirmation V1

| Field | Value |
|-------|-------|
| Task | `INTAKE_V6_RETURN_CANT_READINESS_SINGLE_FINAL_CONFIRMATION_V1` |
| Verdict | **PASS** |
| Accepted HEAD | `92909f9` |
| Branch | `main` |
| Prior audit | `PARALLEL_TRUTH_CONFIRMED` |
| Runtime workspace | `22ef834d-f2d0-453b-a7a7-118928c98a39` / `IV6-189D2F12` |

## Owner decisions applied

| ID | Decision | Applied |
|----|----------|---------|
| DEC-CDRC-01 | Valid persisted return/cant must not surface missing/blocking operator diagnostics | Bridge + mapper derive readiness from values; confirmation demoted to technical |
| DEC-CDRC-02 | Per-row `confirmed` must not duplicate operator confirmation when values exist | `intakeV6ProductFinishCompleteness.ts` value-based completeness; review/header/handoff updated |
| DEC-CDRC-03 | Visible 3-step flow: Straturi → Configurare → Confirmare | `INTAKE_V6_VISIBLE_PROGRESS_STEPS`, workspace routing, separate `IntakeV6ConfirmStep` |
| DEC-CDRC-04 | Single final operator confirmation = `internal_draft_quote_confirmed` | Only on Pas 3; footer handoff gated to `confirm` step |
| DEC-CDRC-05 | Real persisted defaults are valid choices; no separate re-confirmation | Defaults count as configured in completeness + return/cant mapper |

## Root causes (audit confirmed)

1. Parallel truth: persisted product values vs per-row `confirmed` vs `product_truth.return_cant.confirmation_state`.
2. Return/cant bridge set `confirmation_state=blocked` even when depth + finish + layer refs were complete.
3. Step 3 visually merged into Step 2 (2-step UX).
4. Final confirmation mixed with field-level confirmation in review/footer.

## Return/cant logic

**Before:** Any non-confirmed component state → operator blockers including `RETURN_CANT_COMPONENT_CONFIRMATION_MISSING`; mapper treated legacy flags as operator missing.

**After:** `return_cant_product_truth_bridge.py` splits `operator_blockers` vs `technical_blockers`; when depth, finish, layer_group_ids, source_ref complete → `confirmation_state=confirmed`. Frontend mapper adds `operator_readiness`; hydrated canonical values → `ready`; perimeter/confirmation demoted to `technical_blockers`. Panel `variant=operator|technicalOnly`.

## Per-row confirmation

**Before:** `letter_group.confirmed=false` / `artwork.confirmed=false` produced “unconfirmed” warnings despite valid selections.

**After:** `intakeV6ProductFinishCompleteness.ts` evaluates required fields from persisted values; legacy flags retained internally only.

## Print + laminare

**Before:** `execution_type=print_laminate` with values present still showed artwork unconfirmed via flag.

**After:** Handoff/readiness uses `allArtworkProductConfigured`; distinguishes artwork classification vs binding vs final confirmation.

## Three-step flow

Restored `INTAKE_V6_STEP_ORDER = [layers, review, confirm]`. Review footer → “Continuă la Confirmare”. Progress bar shows Straturi / Configurare / Confirmare. Header step label fixed (`confirm` → Confirmare).

## Pas 3 behavior

- Real page (`IntakeV6ConfirmStep` → `IntakeV6FinalConfigurationSummary` legacy variant).
- Summary collapsed by default; operator copy: “Verifică rezumatul configurației și confirmă pentru continuare.”
- Technical details under separate accordion “Detalii tehnice”.
- Final handoff footer only on confirm step.

## Warning policy

Operator warnings require: missing decision + not persisted + operator can act. Classifications: `OPERATOR_ACTION_REQUIRED`, `FINAL_CONFIRMATION_REQUIRED`, `TECHNICAL_ONLY`, `INFORMATIONAL`. Raw codes remain in technical details/backend.

## Files changed

**Backend:** `return_cant_product_truth_bridge.py`, `test_return_cant_product_truth_bridge.py`

**Frontend:** progress steps, workspace shell, review/confirm steps, final summary, return/cant mapper + panel, product finish completeness, quote handoff/readiness/header status, final handoff hook, tests listed in commit.

**QA:** `docs/qa/intake-v6-return-cant-readiness-single-final-confirmation-v1/` (10 screenshots + index + capture script)

## Tests

| Area | Result |
|------|--------|
| Return/cant bridge (backend) | 11 passed |
| Product finish completeness | 4 passed |
| Progress steps (3-step) | 3 passed |
| Return/cant mapper | 6 passed |
| Quote handoff readiness | 9 passed |
| Review header status | 5 passed |
| Confirm step | 9 passed |
| Final configuration summary | 3 passed |
| Footer | 3 passed |
| Return/cant panel | 2 passed |
| Workspace header | 3 passed |
| SvgAnalyzer step | 11 passed |
| Operator blocker banner | passed |
| **Targeted batch total** | **70 passed** |

## Runtime verification

Route: `http://127.0.0.1:3000/intake-v6/22ef834d-f2d0-453b-a7a7-118928c98a39/operator`

- Three steps visible ✓
- 60 mm + Alb cant accepted on Pas 2 ✓
- print + laminare without false unconfirmed ✓
- Pas 3 separate with collapsed summary ✓
- Single final confirmation on Pas 3 ✓
- Technical details secondary ✓

## Screenshots

See `docs/qa/intake-v6-return-cant-readiness-single-final-confirmation-v1/SCREENSHOTS_INDEX.md`

## Forbidden scope

No DB migration, seed, pricing, ProductSystem templates, ProductDefinition/ProductAggregate architecture, Quote/Order/Execution, selected_layer_refs, SVG parsing, historical row mutation.

## Honest opinion

The parallel-truth split was the right minimal fix: keep audit paths, stop presenting internal confirmation as operator work when values exist. Remaining complexity is the handoff panel still using “draft intern” wording in checklist items — acceptable for this slice but could be softened later.

## Remaining debt

- `IntakeV6ConfirmHandoffPanel` checklist labels still mention “draft intern” internally.
- Full `test:frontend` / `validate:frontend` not run (repo TS debt).
- `test_intake_v4_internal_draft_quote_confirmation_policy.py` setup errors pre-existing.

## Next roadmap step

Runtime polish on handoff copy + broader E2E on confirm-only final checkbox; then Frontend Typecheck Debt Audit per AGENTS.md.

## Commit

Message: `Align Intake V6 final confirmation logic`

## Direction score

**92/100** — aligns with owner 3-step + single confirmation model; closes audit-proven false blockers at source.

## Dead pieces check

| Check | Result |
|-------|--------|
| Three-step flow restored | YES |
| Pas 3 removed | NO |
| Final confirmation duplicated | NO |
| Persisted defaults ignored | NO |
| Technical diagnostics deleted | NO |
| Real blockers hidden | NO |
| New truth source created | NO |
| Historical rows mutated | NO |
| Automatic backfill started | NO |

## Roadmap awareness

**9/10** — Controlled repair of contradictory completeness/confirmation logic after audit.
