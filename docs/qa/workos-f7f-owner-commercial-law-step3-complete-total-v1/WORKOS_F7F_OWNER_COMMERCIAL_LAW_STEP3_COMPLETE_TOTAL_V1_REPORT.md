# WORKOS F7F — Owner Commercial Law Activation + Step 3 Complete Offer Total
## Owner 64-point follow-up report (§25)

Follow-up verification pass. The Lead finished F7F with `PASS_WITH_EXACT_BLOCKER` but the brief that
produced this report omitted the mandated §25 point list, so this document supplies it against the
Lead's own evidence files plus independent read-only re-verification performed in this pass.

## 1. Mini decision

| Field | Value |
|---|---|
| Purpose | Verify F7F Owner commercial-law activation + Step 3 complete-total work, then supply the missing mandated 64-point report |
| Scope of this pass | Read-only verification + one docs-only report file. No commercial code changed. |
| Outcome | Lead's technical claims independently reproduce. One evidence-accuracy correction found (§9/§48, order `973019`). One in-session commit rewrite observed and reconciled (§3). |
| Verdict carried forward | `PASS_WITH_EXACT_BLOCKER` (unchanged from Lead) |

## 2. Verdict

**`PASS_WITH_EXACT_BLOCKER`**

Completed and independently reproduced in this pass:

- Owner rates active at runtime: Oracal 651 = 5 EUR/m² (no colour tier), Oracal 8500 = 17 EUR/m² @
  1000 mm / 13.5 EUR/m² @ 1260 mm (by **confirmed** roll width only), print + laminate = 10 EUR/m²,
  vinyl application = one 3 EUR/m² rate per proven applied surface, ACM sheet = 15 EUR/m²
  standard/colorat, ACM mirror = 40 EUR/m² **replacement** rate (never 15 + 25).
- A-F4 closed: Step 3 shows `Subtotal Litere` and `Subtotal Panou ACM` as distinct rows instead of a
  Litere-only figure presented as the whole offer.
- Fail-closed held on: unknown ACM shell, missing/unsupported Oracal 8500 width, exterior mirror ACM
  without a proven supplier SKU — all raise a typed blocker and leave price `null`, never a
  neighbouring-rate guess.
- A same-session hardening was folded in after the Lead's first pass and is now committed: Oracal 8500
  width resolution reads the **per-letter-group** confirmed capture (not only the job-level derived
  projection), so a mixed-face job cannot silently price the wrong tier. See §14/§18/§25.

Remaining blocker (unresolved, Owner decision required):

- **`COMMERCIAL_CURRENCY_MIX_UNRESOLVED`** — registry operation rates resolve in RON, Owner material
  law is EUR. CPP has no authority to convert without a provenance-bearing exchange rate, so it
  refuses to publish a single `Total ofertă` for a mixed-currency workspace. Owner must choose: EUR
  operation rates, or an exchange rate with provenance on the quote/snapshot. No default, no live FX.

Carried, not blocking F7F acceptance: Oracal 641 rate not on the Owner list (F7E seed-derived 6.5
EUR/m² retained, flagged); `printed_vinyl` (print without laminate) fail-closed pending an Owner rate;
A-F3 finish-vocabulary normalization (`mirror_silver`) deferred, out of F7F scope.

## 3. Repo/branch/HEAD/remote/divergence

| Check | Observed |
|---|---|
| Repo | `C:\w\psiso` |
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| HEAD at task hand-off (brief) | `303ab38d` (cited by the brief as the tip of the two F7F commits) |
| HEAD at end of this verification pass | **`b14fde6f`** |
| Second F7F commit, current | `b14fde6f` — "Document F7F runtime and commercial proof" |
| First F7F commit, current | `e0a8d738` — "Activate Owner commercial rules and complete Step 3 offer total" |
| Parent of first F7F commit | `d4989b21` — "Document F7E commercial integrity runtime proof." (unchanged start point) |
| Remote | `origin` = `https://github.com/office952/workos-vscode.git`; local branch **ahead 16**, not pushed |

**Honest note on the cited hashes.** The brief asked to confirm `603ef0a5` and `303ab38d` are
ancestors of `HEAD`. At the start of this pass they were (`git merge-base --is-ancestor` returned
success for both). Mid-pass, the same two F7F commits were **rewritten in place** (same commit
messages, same author, same file set plus two extra small diffs) to fold in the per-letter-group
Oracal 8500 fix described in §25 — `603ef0a5` became `e0a8d738` and `303ab38d` became `b14fde6f`.
`git merge-base --is-ancestor 303ab38d HEAD` now fails (exit 1) because that exact commit object no
longer exists on this branch; its content is superseded by `b14fde6f`, which contains everything the
old commit did plus the additional fix. This was observed live during verification (a `git status`
that showed clean tracked files became `MM`/`M` mid-session, then clean again once the amend
completed) — it was **not** caused by this follow-up pass, which made no commercial-code edits. Every
claim below is checked against the **current** tip (`e0a8d738` / `b14fde6f`), not the stale hashes in
the brief.

## 4. Stash and working tree

- `stash@{0}` = `wip-employee-unrelated` — present, untouched, unrelated to F7F.
- `stash@{1}`–`{5}` — pre-existing, unrelated, untouched.
- Working tree at the end of this pass: only pre-existing untracked QA/log noise (`docs/qa/*_tmp*`,
  `backend/logs/*`, `backend/dev.db`, etc. — present before this task started, per the git status
  baseline in the task brief). **No tracked file is modified.** No `git add .`, `-A`, `reset`,
  `clean`, or `stash pop` was run by this pass.

## 5. Exact A-F3/A-F4 register

| Id | Exact statement | Disposition |
|---|---|---|
| **A-F3** | F7D register, recovered text = `AGENT-B-F004` / P1: submitting `return_finish_type="mirror_silver"` (not offered by the live UI combobox) to CPP preview is silently accepted (`status=ready`, no warning); separately the UI emits short tokens (`white`/`black`) while schema/canonical map use suffixed tokens (`white_aluminum`) with no normalization bridge found. Scoped to G4 (finish contract vocabulary). | **Out of F7F scope, still open.** F7F changed no finish vocabulary or schema `Literal`s. `mirror_silver` stays a cant stock colour, deliberately not merged with the new ACM `oglinda_gold`/`oglinda_antracit` sheet variants. |
| **A-F4** | Step 3 showed a Litere-only figure labelled as the offer total; the ACM panel was missing from it. | **Closed by F7F.** Step 3 now shows `Subtotal Litere` and `Subtotal Panou ACM` as distinct rows; the complete total comes from CPP or is refused with a typed reason. |

## 6. Architecture readback

Source: `00-architecture-readback.md` (unchanged content across the in-session amend).

| Concern | Canonical owner |
|---|---|
| Commercial currency | The rule row (`documented_unit_price_currency`) + registry rate row; CPP preserves per-line currency and never converts without `currency_conversion_rate` + `currency_conversion_source`. |
| VAT / fiscal policy | `company_commercial_settings.default_vat_pct` (DB default 21); CPP is tax-exclusive, stores no VAT. |
| Commercial rule catalog | `RULES_BY_TEMPLATE` in `commercial_rules_volumetric_v2.py`. |
| Internal cost (EIC) | `EstimatedInternalCostService` — never read by CPP, never a client price. |
| ACM product ownership | Made explicit via `CommercialRuleDefinition.commercial_product_key` (`letters`/`acm_panel`). |
| Oracal selection | Operator, on the artwork-finish row; CPP resolves the rate, never picks a series. |
| Step 3 total source | Before: `handoff.pricedQuoteDryRunTotal` with hardcoded `?? "RON"`. After: `commercial_product_breakdown` from CPP. |
| Snapshot boundary | Snapshot V2 writer untouched; F7F touches only the read-only dry-run/preview path. |

Currency reality stated plainly by the Lead: CPP emits mixed-currency lines (registry ops in RON,
Owner materials in EUR); the pre-F7F `subtotal_commercial` summed them without conversion (a
pre-existing dishonesty). F7F does not keep fusing them silently — it reports per-currency buckets,
sets `currency_mix_detected`, and refuses a single total with `COMMERCIAL_CURRENCY_MIX_UNRESOLVED`.

## 7. Agents and ownership

| Agent | Ownership lane | Files |
|---|---|---|
| Agent A | Pricing registry + CPP | `backend/data/commercial_rules_volumetric_v2.py`, `backend/schemas/commercial_price_proposal.py`, `backend/services/commercial_price_proposal_service.py`, `backend/services/intake_v6_priced_quote_dry_run_service.py` |
| Agent B | Product / intake propagation | `frontend/src/lib/intakeV6/acmPanel/*`, `IntakeV6AcmShellFinishPanel.tsx` |
| Agent C | Step 3 UI | `intakeV6OfferProductSummary.ts`, `intakeV6PricedQuoteTypes.ts`, `IntakeV6FinalConfigurationSummary.tsx`, `IntakeV6LiveCalculationSummary.tsx` |

No agent crossed into another's lane; no CostEngine/EIC file, snapshot writer, or order/execution file
appears in the changed-file list for either commit (§13).

## 8. Commercial decisions implemented

1. Oracal 651 → 5 EUR/m², one series rate for every colour code (supersedes the F7E seed-derived 9.0).
2. Oracal 8500 → 17 EUR/m² @ 1000 mm, 13.5 EUR/m² @ 1260 mm, resolved from a confirmed roll width only.
3. Print + laminate → 10 EUR/m² (closes F7E's `COMMERCIAL_RULE_MISSING`). `printed_vinyl` (print
   without laminate) stays fail-closed, a separate Owner decision.
4. Vinyl application → one 3 EUR/m² Owner rule replacing three registry-bound labour rules, charged
   once per proven applied surface (face area for the face, developed wrap area for the cant); never
   on stock cant, never with no vinyl selected.
5. ACM sheet → 15 EUR/m² standard/colorat; 40 EUR/m² mirror as a **replacement** rate, never a
   15 + 25 surcharge stack; unknown shell fails closed; exterior mirror without a proven SKU raises
   `TECHNICAL_MATERIAL_COMPATIBILITY_REQUIRED`.
6. VAT stamped from `company_commercial_settings.default_vat_pct` — no layer hardcodes 21.

## 9. Registry classification matrix

| Rule | `commercial_product_key` | Rate | Currency |
|---|---|---|---|
| `finisaje_oracal_651_material` | letters | 5.00 | EUR/m² |
| `finisaje_oracal_641_material` | letters | 6.50 (carried, F7E-derived, Owner decision open) | EUR/m² |
| `finisaje_oracal_8500_material` | letters | 17.00 @ 1000 mm / 13.50 @ 1260 mm | EUR/m² |
| `finisaje_print_laminate_material` | letters | 10.00 | EUR/m² |
| `finisaje_aplicare_autocolant_fata` / cant | letters | 3.00 | EUR/m² |
| `finisaje_cant_ral_material` / `_labor` | letters | 4.00 / 5.00 | EUR/ml |
| `acm_panel_face_material` (standard/colorat) | acm_panel | 15.00 | EUR/m² |
| `acm_panel_face_material` (mirror, replacement) | acm_panel | 40.00 | EUR/m² |

Every rule and every emitted line now carries `commercial_product_key`, which is what makes the Step 3
per-product breakdown (§32–34) possible without any frontend summing.

## 10. Currency policy

CPP preserves per-line currency (`source_currency`/`cpp_currency`) and never converts without an
explicit `currency_conversion_rate` + `currency_conversion_source`. Registry operations resolve in
RON; Owner material law is EUR. `commercial_product_breakdown` reports per-product, per-currency
subtotals and sets `currency_mix_detected: true` on a mixed workspace; it refuses to synthesize a
single converted total. No default FX rate exists anywhere in the changed code.

## 11. TVA policy

`company_commercial_settings.default_vat_pct` (DB, default 21) is the single source. CPP itself is
tax-exclusive and stores no VAT amount; the dry-run service stamps the rate onto its response. Step 3
now reads `Prețuri fără TVA (TVA 21% conform politicii fiscale)` from that source instead of a
frontend-hardcoded 19/21 split. Independently confirmed in the screenshot (§43) and in
`runtime-step3-dry-run.json`.

## 12. Files inspected

`docs/qa/workos-f7f-owner-commercial-law-step3-complete-total-v1/{WORKOS_F7F_OWNER_COMMERCIAL_LAW_STEP3_COMPLETE_TOTAL_V1_REPORT.md,
00-architecture-readback.md, 01-scenario-matrix-results.md, _f7f_protected_baselines.py,
_f7f_runtime_probe.py, evidence/*.json, evidence/*.txt, evidence/step3-offer-product-breakdown.png}`,
`docs/worklog/realignment/2026-08-03_f7f_owner_commercial_law_step3_complete_total.md`, both F7F
commit diffs (`git show --stat` / full diffs on the two touched backend files), `backend/dev.db`
(read-only, `mode=ro`), and the four backend/frontend test files named in §45.

## 13. Files changed

Backend (first commit): `backend/data/commercial_rules_volumetric_v2.py`,
`backend/schemas/commercial_price_proposal.py`,
`backend/services/commercial_price_proposal_service.py`,
`backend/services/intake_v6_priced_quote_dry_run_service.py`,
`backend/tests/test_commercial_price_proposal_preview.py`,
`backend/tests/test_f7f_owner_commercial_law_step3_total.py` (new).

Frontend (first commit): `IntakeV6FinalConfigurationSummary.tsx` (+test),
`IntakeV6LiveCalculationSummary.tsx` (+test), `IntakeV6AcmShellFinishPanel.tsx`,
`IntakeV6AcmSheetMaterialCapture.test.tsx` (new), `acmPanel/acmSheetMaterial.ts` (new, +test),
`acmPanel/acmSheetMaterialPatch.test.ts` (new), `acmPanel/operatorPatch.ts`, `acmPanel/types.ts`,
`acmPanel/index.ts`, `intakeV6OfferProductSummary.ts` (new, +test), `intakeV6PricedQuoteTypes.ts`,
`frontend/scripts/ci-unit-tests.txt` (gained the two new pure-module suites).

Docs (second commit): `00-architecture-readback.md`, `01-scenario-matrix-results.md`, this report,
`_f7f_protected_baselines.py`, `_f7f_runtime_probe.py`, five `evidence/*` files, the worklog entry.

No CostEngine, EIC, snapshot writer, order/execution, inventory, or migration file appears in either
commit's diff — confirmed by reading both `git show --stat` outputs directly.

## 14. Root-cause map

| Symptom | Root cause | Fix |
|---|---|---|
| F7E `COMMERCIAL_RULE_MISSING` on print+laminate and ACM mirror | Rates never entered the registry | Owner rates added as classified rules |
| Step 3 showed a Litere-only figure as "the offer" (A-F4) | No `commercial_product_key`; CPP had no concept of more than one commercial product | Added `commercial_product_key` + `commercial_product_breakdown` |
| Step 3 total silently plausible on a mixed-currency workspace | CPP's pre-F7F `subtotal_commercial` summed RON + EUR without conversion | CPP now detects the mix and refuses a single total (`COMMERCIAL_CURRENCY_MIX_UNRESOLVED`) instead of fixing the arithmetic with an invented FX rate |
| Oracal 8500 could silently price the wrong tier on a mixed-face job | `face_vinyl_roll_width_mm` is a **derived dominant-value projection** of per-letter-group captures, not the operator's actual selection for a given face; reading it directly can return null or a different face's width | CPP now resolves the width from the confirmed per-letter-group capture that actually carries the 8500 face, and fails closed when groups disagree or are unconfirmed |

## 15. Oracal 651 result

5.00 EUR/m² material + 3.00 EUR/m² application, one rate for every colour code (confirmed for codes
`021` and `032` — identical rate, "no colour tier" verified live). Supersedes the F7E seed-derived 9.0.
Reproduced against `01-scenario-matrix-results.md` scenarios `F2`/`F2b`.

## 16. Same-series color result

No colour tier inside a series: Oracal 651 code `021` and code `032` price identically at 5.00 EUR/m².
This was asserted directly by the live scenario probe (`F2b`), not inferred.

## 17. Oracal 8500 width result

17.00 EUR/m² @ 1000 mm confirmed roll width; 13.50 EUR/m² @ 1260 mm confirmed roll width (scenarios
`F4a`/`F4b`). Resolution order, verified in code (§14): confirmed per-letter-group capture for a group
that carries the 8500 face wins; the job-level field is used only when no group carries that face.
Groups that disagree on width, or are not `confirmed`, resolve to no rate.

## 18. Missing-width behavior

Scenario `F4` (width missing): material line resolves to `null` — no guess, no default tier — and the
preview carries a `COMMERCIAL_CONFIGURATION_INCOMPLETE` blocker with `status=blocked`. Independently
reproduced in this pass: `test_oracal_8500_blocks_on_unconfirmed_or_disagreeing_letter_groups` passes,
asserting `commercial_unit_price is None`, `subtotal is None`, the blocker code, and `status="blocked"`
for both an unconfirmed group and two groups that disagree on roll width.

## 19. Print + laminate result

10.00 EUR/m² material + 3.00 EUR/m² application (scenario `F5`). F7E's `COMMERCIAL_RULE_MISSING` for
this finish is gone. `printed_vinyl` (print without laminate, scenario `F6`) is a **separate** finish
that still has no rate and stays fail-closed by design — an explicit, not accidental, Owner-pending
item (§8, §25 point 4).

## 20. Application result

One 3.00 EUR/m² Owner rate replaces three registry-bound labour rules. It is charged once per proven
applied surface: face area for the face application line, developed wrap area (perimeter × return
depth) for the cant application line. Never charged on stock cant (`R1`, zero-delta preserved) and
never charged when no vinyl finish is selected.

## 21. ACM standard result

15.00 EUR/m² for both `standard` and `colorat` shell variants, and for an absent/unspecified shell
(owner-confirmed default sheet) — three scenarios, one rate, confirmed by
`tests/test_f7f_owner_commercial_law_step3_total.py`.

## 22. ACM mirror result

40.00 EUR/m² as a **replacement** rate — exactly one `acm_panel_face_material` line at 40.00, never a
15 (standard) + 25 (mirror surcharge) stack. Confirmed for `oglinda_gold` (interior) directly in the
scenario matrix table.

## 23. Mirror environment compatibility

`oglinda_antracit` (mirror) in an `exterior` installation with **no proven SKU** → blocked with
`TECHNICAL_MATERIAL_COMPATIBILITY_REQUIRED`. The same shell/environment combination **with** a proven
supplier SKU clears the blocker. Both branches are asserted in the new backend test file.

## 24. Unknown ACM shell behavior

An unrecognized shell token in an `interior` installation → blocked with `COMMERCIAL_RULE_MISSING`,
price `null`. It does **not** fall back to the 15.00 standard rate — verified as an explicit assertion
in the scenario matrix and reproduced by re-running the test file in this pass.

## 25. RAL regression

`R2` (`ral_paint` cant): `finisaje_cant_ral_material` 4.00 EUR/ml + `finisaje_cant_ral_labor` 5.00
EUR/ml — identical to F7E behaviour, unchanged by F7F. No regression.

## 26. Stock cant regression

`R1` (`white_aluminum`, stock cant): total stays at the 490.00 RON no-finish baseline, zero delta, no
`finisaje_cant_*` line and no application line generated. Unchanged by F7F. No regression.

## 27. Intake payload

Face finish (including Oracal roll width) is captured per **letter group** on the artwork-finish row
(`face_finish_type`, `face_oracal_code`, `face_vinyl_roll_width_mm`, `confirmed`), plus a job-level
projection field of the same name. A new `acm_sheet_material_v1` contract captures ACM variant,
installation environment, exterior SKU, and operator confirmation at
`acm_panel_instance.sheet_material`, with stale-child clearing of `exterior_sku` when it stops
applying. No commercial rate lives in either contract — operator truth only.

## 28. ProductDefinition propagation

Not touched by F7F. The registry/CPP change is entirely inside the commercial pricing layer; no
`ProductDefinition` schema, template, or propagation path was modified by either F7F commit (confirmed
by the file lists in §13).

## 29. ProductAggregate provenance

Not touched by F7F for the same reason as §28 — no aggregate/provenance file appears in either
commit's diff.

## 30. CPP lines

Every commercial line (`finisaje_*`, `acm_panel_*`) now carries `commercial_product_key` (`letters` or
`acm_panel`). This is the mechanism the per-product `commercial_product_breakdown` (§9, §32–34) is
built from — no frontend summation is involved.

## 31. EIC separation

`EstimatedInternalCostService` is never imported by or referenced from the CPP service; confirmed by
absence from both commits' file lists (§13) and from the architecture readback's explicit ownership
row. CPP's rates are commercial (client-facing) rates only; EIC remains internal cost, untouched.

## 32. Step 3 Litere subtotal

Live capture, workspace `IV6-9C5D9538`: `Subtotal Litere` = **71.36 EUR + 1 724.44 RON** (two
currencies, reported separately, not summed). Before F7F this workspace showed a single ~249.98 EUR
figure presented as if it were the whole offer.

## 33. Step 3 Panou ACM subtotal

Live capture, same workspace: `Subtotal Panou ACM` = **190.78 EUR**. Before F7F this subtotal did not
exist on Step 3 at all (residual A-F4) — the ACM panel's commercial value was simply absent from the
presented total.

## 34. Step 3 complete total

**`Total ofertă indisponibil`**, reason `COMMERCIAL_CURRENCY_MIX_UNRESOLVED`. This is the exact
blocker carried forward to §2/§35 — the workspace mixes RON (letters application/cant lines) and EUR
(Owner material rates), and CPP refuses to publish one number rather than sum across currencies.
Visually confirmed in the screenshot (§43): an amber "Total ofertă indisponibil" panel, not a number.

## 35. Partial/blocked total behavior

Two distinct states exist, and this pass confirmed they are distinct in code, not just in wording:

- **Unavailable** (`Total ofertă indisponibil`): no total can be computed at all — used for the
  currency-mix case (§34) and would also apply to any unresolved blocking line.
- **Partial** (`Total ofertă (parțial)`): a total exists but omits lines that are still waiting on an
  Owner decision (Owner-pending line codes surface with it). This state is not exercised in the
  captured workspace (its blocker is the unavailable case), but is asserted directly by
  `preview.complete_offer_total_is_partial` in the CPP schema/service and its test coverage.

## 36. Persistence

Not part of F7F's boundary. No snapshot writer, order/quote persistence path, or DB write was touched
— CPP/dry-run remain a read-only preview (§13, §50). Nothing about Step 3's product breakdown is
persisted differently from before; it is computed fresh on each dry-run call.

## 37. Refresh/direct URL

Not independently re-tested with a live navigation in this pass (no dev stack was started for this
read-only follow-up, per the workspace rule against agent-initiated stack starts outside an explicit
Owner "pornește" request). The Lead's screenshot evidence shows the Step 3 confirm screen rendered
correctly from the dry-run response; no code path in the diff suggests refresh/direct-URL-specific
state, since the breakdown is derived fresh from `commercial_product_breakdown` on each load rather
than cached client state.

## 38. Reverse recalculation

Not applicable to this GO's scope — F7F did not touch any reverse-calculation (target-price-to-input)
path; no such file appears in either commit's diff.

## 39. Stale-state clearing

Confirmed in the ACM sheet-material contract: `exterior_sku` is cleared when the installation
environment or shell variant changes such that the SKU no longer applies (stale-child clearing),
exercised by `acmSheetMaterialPatch.test.ts` (new file, §13).

## 40. Duplicate-line check

Explicitly verified as a non-double-charge property, not assumed: the cant is priced as a distinct
proven surface (developed wrap area) from the face (face area), so face and cant application lines
never charge the same square metre twice (§20, `01-scenario-matrix-results.md` §"Return cant" note).
ACM mirror emits exactly **one** `acm_panel_face_material` line at the replacement rate, never a second
surcharge line stacked on top of the standard rate (§22).

## 41. Snapshot V2 preview

Untouched. `backend/services/intake_v6_quote_snapshot_v2_service.py` does not appear in either F7F
commit's diff. Snapshot V2 continues to freeze an accepted offer independently of this preview-layer
change; F7F's read of protected order/snapshot state (§47/§48) confirms nothing there moved.

## 42. Runtime identity

The Lead's runtime scenario matrix and Step 3 capture were produced against a live dev stack
(`:8000`/`:3000`) with the UI stamp `WorkOS BUILD_25 · STAGING` visible in the corner of the screenshot
(§43). This follow-up pass did **not** start or stop the dev stack — all verification here is read-only
(git history, DB read with `mode=ro`, and re-running the existing pytest files against the checked-out
tree), consistent with the workspace rule that only an explicit Owner "pornește/live" request starts
the stack.

## 43. Screenshots and routes

`evidence/step3-offer-product-breakdown.png` — Step 3 "Confirmare finală" / "Ofertă client" card on
the Intake V6 confirm route, workspace `IV6-9C5D9538`. Visually confirms: `Litere volumetrice` row with
`Subtotal Litere` (71.36 EUR / 1 724.44 RON), `Panou ACM` row with `Subtotal Panou ACM` (190.78 EUR),
an amber unavailable-total block, the `Prețuri fără TVA (TVA 21% conform politicii fiscale)` note, and
a still-blocked "Confirmă" gate ("1 blocant · 1 avertizare · 6 informații" / "Handoff blocat — verifică
verdictul.") — this pass viewed the image directly and confirms the Lead's written description matches
what is rendered.

## 44. Honest UI/UX opinion

The structure reads correctly: two products, two clearly labelled subtotals, and a refusal instead of
a fabricated total. Two real presentation weaknesses, confirmed by looking at the image directly in
this pass, not just trusting the Lead's prose: the amber "Total ofertă indisponibil" block sits at low
contrast inside an already-dimmed confirm card and could be mistaken for disabled chrome rather than an
active refusal state that needs attention; and the stacked per-currency rows (EUR line, RON line) have
no visual separator or label hinting that they are *not* addable into one figure, which a fast-scanning
operator could misread. Neither is a correctness defect — both are worth a small, scoped contrast/
spacing pass, not a redesign.

## 45. Tests and exact counts

Re-run in this pass against the current tip (`e0a8d738`/`b14fde6f`):

| Command | Result (this pass) | Lead's claim |
|---|---|---|
| `pytest tests/test_commercial_price_proposal_preview.py` | **32 passed** | 32 passed (report already corrected from an earlier 30) |
| `pytest tests/test_f7f_owner_commercial_law_step3_total.py` | **9 passed** | 9 passed |
| `pytest` (both files together) | **41 passed** | consistent with the two rows above |
| Backend CI-equivalent 4 files (`test_dashboard_kpi_metrics`, `test_operational_data_gaps`, `test_pricing_registry`, `test_cost_engine_config`) | **28 passed** | 28 passed |

Not independently re-run in this pass (relied on the Lead's evidence, no reason found to doubt them
given the small, backend-only nature of the residual diff folded in mid-session): `pnpm run lint`,
`pnpm run build`, `tsc --noEmit`, `pnpm run test:ci` (274 passed / 4 pre-existing failures claimed),
the 6 F7F frontend unit files (105 passed claimed), and the 5-file ACM+dry-run backend sweep (50
passed / 1 pre-existing failure claimed).

## 46. Pre-existing vs new failures

- `test_acm_boxed_mounting_standalone_offer_v1::test_standalone_payload_derivation_and_detection` —
  `panel_perimeter_m` `KeyError`, claimed pre-existing on an untracked F7E test whose geometry-
  derivation path F7F does not touch. Plausible given F7F's file list (§13) has no geometry-derivation
  file, but **not independently re-run** in this pass.
- 4 failures in `src/pages/MaterializedOpsGraph.test.tsx`
  (`executionApi.getEmployeeEligibilityReadModel is not a function`) — claimed pre-existing, unrelated
  to commercial pricing. Not independently re-run in this pass.
- Backend sweep comparison (baseline 99 failing node IDs at `d4989b21` vs 100 on the F7F tree, single
  difference passing in isolation) — evidence files exist at the claimed line counts (99 / 100 lines
  respectively, counted directly in this pass) but the sweep itself was not re-executed here.

## 47. Protected commercial baselines

Re-verified read-only against `backend/dev.db` (`mode=ro`) in this pass, independently of the Lead's
own script/JSON:

- Order `880811` (`ORD-F7B-880811`): `status=locked`, `total_amount=1847.5` — **confirmed unchanged**.
- `execution_plan` id 22 → `order_id=880811`, `plan_source=order_snapshot_v2` — present, unchanged
  (per the Lead's evidence; re-confirmed structurally, not re-derived digit-by-digit in this pass).

## 48. Protected quote/order hashes

- Snapshot `QSN2-F7B-880811` (order 880811's linked snapshot): `status=frozen`,
  `content_hash=f7b00880811hash` — confirmed unchanged.
- **Correction to the Lead's evidence for order `973019`.** The Lead's report and worklog state
  "`973019` did not resolve as an order code in this database; reported rather than guessed." That
  statement is narrowly true — the Lead's own script (`_f7f_protected_baselines.py`) queries
  `orders.code LIKE '%973019%'`, and order 973019's `code` is `ORD-IV6-V2-1785676969-19`, which does
  not contain the substring "973019". But **order id `973019` does exist and is intact**: `status=
  locked`, `total_amount=847.5`, linked via `quote_snapshot_v2_id=20` to snapshot `QSN2-2026-0020`
  (`status=frozen`, `content_hash=3894d928c1b4db8b38d04d75c58de62e`) — verified directly by primary-
  key lookup in this pass. The Lead's own script docstring even names this order and its 847.5 total
  from a prior build, so the negative result came from the query's substring-match method, not from
  the order being absent. **No commercial baseline was disturbed** — the order is still locked and its
  snapshot still frozen — this is a QA-script precision gap in the F7F evidence, not a commercial-code
  defect, and does not change the F7F verdict. Recommend the Lead's script be corrected (query by `id`
  as well as `code LIKE`) the next time this evidence pack is touched.

## 49. Assignment/session counts

Not applicable to F7F's boundary (no scheduling, assignment, or session table was created, read, or
written by either F7F commit — confirmed by the file lists in §13). No employee/session artifacts
exist for this GO to count.

## 50. Materialization gate

`pilot_gate_open=false` is asserted as "protected and untouched" by the Lead's own architecture
readback (§6) and is consistent with the last direct evidence of the gate's closed state,
`docs/qa/workos-f7b-controlled-product-linked-materialization-pilot-v1/gate-closed-runtime.json`
(`"pilot_gate_open": false`, `"verified": "GATE_CLOSED_VERIFIED"`). This pass did not re-run the live
`dec009_materialize_gate` evaluation (it requires a running stack and fixture state this pass did not
stand up) — the gate check here is a documentary cross-reference, not a fresh runtime assertion.
Neither F7F commit touches `backend/services/dec009_materialize_gate.py` (confirmed absent from §13's
file lists), so nothing in F7F itself could have moved this gate.

## 51. QA/worklog paths

- `docs/qa/workos-f7f-owner-commercial-law-step3-complete-total-v1/` (architecture readback, scenario
  matrix, protected-baseline read, backend-sweep comparison, Step 3 screenshot, this report).
- `docs/worklog/realignment/2026-08-03_f7f_owner_commercial_law_step3_complete_total.md`.

## 52. Commits

| Commit | Message | Note |
|---|---|---|
| `e0a8d738` | Activate Owner commercial rules and complete Step 3 offer total | Was `603ef0a5` at brief hand-off; rewritten mid-session to fold in the per-letter-group Oracal 8500 fix (§3, §14, §25) |
| `b14fde6f` | Document F7F runtime and commercial proof | Was `303ab38d` at brief hand-off; rewritten mid-session for the same reason plus updated docs |

This follow-up pass adds one further docs-only commit (see hash in the parent handoff / commit log at
push-time of this change) titled "Complete F7F Owner 64-point report", touching only this report file.

## 53. Push status

**Not performed.** Local branch is 16 commits ahead of `origin/feat/capacity-batch-20d-scoped-b-92401`
(includes F7F plus prior unpushed work on this branch). No push was executed by the Lead or by this
follow-up pass.

## 54. Final tree identity

HEAD after this pass's own commit = the docs-only commit on top of `b14fde6f` (see §52, §3). Working
tree otherwise matches the pre-existing untracked-noise baseline described in the task brief — no
tracked file left modified by this pass beyond the one report file.

## 55. Dead pieces check

No dead/orphaned code introduced: every new file (`acmSheetMaterial.ts`, `intakeV6OfferProductSummary.ts`,
their test files, the new backend test file) is imported/exercised by the changed production files or
by CI (`ci-unit-tests.txt` gained the two new pure-module suites, §13). No temporary worktree,
baseline clone, or probe script was left behind — the Lead's own report states the temporary
`C:\w\_f7f_baseline` worktree was removed after use, and this pass's own temporary DB-read script was
deleted after use.

## 56. Architecture score

**Strong.** Ownership stays inside its three declared lanes (registry/CPP, intake contract, Step 3
UI); no CostEngine/EIC/snapshot/order file is touched; the new `commercial_product_key` concept is a
minimal, additive extension of the existing rule/line model rather than a parallel structure.

## 57. Functional-spine score

**Strong, with one honest gap named.** Every scenario in the matrix (§15–§26) reproduces at runtime or
in tests; the currency-mix refusal (§34) is the correct behavior for an unresolved input, not a defect
in the spine itself — the spine correctly detects and reports what it cannot yet do.

## 58. Commercial-integrity score

**Strong.** No invented FX rate, no silent registry-labour fallback, no surcharge-stacking on ACM
mirror, no neighbouring-rate guess on a missing width or unknown shell. The one integrity question this
pass raised (§48, order 973019) turned out to be a QA-script substring-match gap, not a commercial
defect — the underlying protected data was never at risk.

## 59. Intake V6 UX score

**Good, with named polish debt.** The Step 3 breakdown is structurally honest (§44) but the
unavailable-total contrast and non-addable-currency-row hinting are real, small UX debts worth a
follow-up pass — not blockers to this GO's acceptance.

## 60. Cât suntem în direcția stabilită: **86/100%**

| Slice | Contribution |
|---|---|
| Owner commercial law fully activated and runtime-proven | Strong |
| A-F4 closed; Step 3 shows true per-product structure | Strong |
| Fail-closed discipline held on every edge case tested (width, shell, mirror-exterior, currency mix) | Strong |
| Mid-session hardening (per-group Oracal 8500 width) closed a real silent-wrong-tier risk before Owner review | Strong |
| Currency-mix blocker is a genuine, unresolved Owner decision — the offer cannot yet be closed for a mixed workspace | − |
| Oracal 641 and `printed_vinyl` still un-rated; A-F3 still open | − |
| QA evidence had one substring-match inaccuracy (973019), now corrected | − (small) |
| Push not performed; Owner has not yet reviewed | − |

## 61. Roadmap awareness checkpoint (Owner GO §26)

- **Is scheduling safe to start?** **No — HOLD.** F7F does not touch scheduling, assignment, or
  session code, but the commercial-law blocker (§2/§34) means Step 3 cannot yet produce one honest
  `Total ofertă` for a real mixed-currency workspace, and this whole GO is still awaiting Owner review
  and is unpushed. Starting scheduling work now would build on top of an unreviewed, unpushed
  commercial state.
- **Is materialization safe?** **No change from before.** `pilot_gate_open=false` remains asserted and
  untouched by F7F (§50); no further materialization was executed by this pass or claimed by the Lead.
- **Is the next Owner GO (Capacity, per `AGENTS.md`) unblocked?** Conditionally — `AGENTS.md` names
  Capacity as the next recommended build only once the CI Preflight Gate is green. This pass
  independently re-confirmed the backend CI-equivalent 4-file pytest set (28 passed) and the two F7F
  test files (41 passed) but did not re-run frontend lint/test:ci/build in this pass (§45) — those
  should be re-confirmed on the current tip before treating the gate as green for a next-GO decision.
- **Are protected baselines intact?** Yes for both order 880811 and order 973019, with the correction
  in §48 about how 973019 was verified, not about its state.
- **Recommendation:** hold scheduling and any further product/pricing GO until the Owner has resolved
  the currency-mix decision and reviewed this F7F pass; do not push without Owner sign-off.

## 62. Recommended next Owner gate

1. Owner decision on `COMMERCIAL_CURRENCY_MIX_UNRESOLVED`: publish operation rates in EUR, or attach a
   provenance-bearing exchange rate to the quote/snapshot. This is the single gate blocking a complete
   `Total ofertă` for a real workspace.
2. Owner rate decisions, non-blocking but open: Oracal 641, `printed_vinyl`.
3. Only after the above: re-run the full CI Preflight Gate (`pnpm run lint`, `pnpm run test:ci`,
   `pnpm run build`, backend 4-file pytest) on the current tip, then consider push.
4. Do not start Capacity, scheduling, or any further materialization GO before that push and Owner
   review land.

## 63. Metoda de lucru și logica abordării

This pass treated the Lead's own commits, evidence JSON, screenshots, and DB as the ground truth to
re-derive against, rather than re-implementing or re-deriving the commercial logic from scratch:
(1) confirmed repo/branch/HEAD/ancestry state first, including catching and reconciling an in-session
commit rewrite rather than treating the brief's stale hashes as fact; (2) read every QA/worklog file
named in the brief plus the architecture readback and scenario matrix in full; (3) independently
re-ran the two most decision-relevant test files and the CI-equivalent 4-file backend pytest set
against the current tip, rather than trusting reported numbers uncritically; (4) opened the Step 3
screenshot directly to confirm the written description matches what is rendered, instead of
paraphrasing the Lead's prose; (5) ran a targeted, read-only SQLite check (`mode=ro`) against the two
protected order IDs by primary key, which is how the 973019 evidence-script gap (§48) was found; (6)
wrote no commercial code and made no product-code edit — the only artifact this pass produces is this
report (plus, per the task's commit-discipline instruction, one docs-only commit).

## 64. Părerea sinceră despre rezultat

The F7F work itself is honest and well-scoped: it closes real Owner-rate gaps, closes A-F4 for real
(not by hiding the ACM subtotal, but by naming it), and — notably — the Lead kept working after its
first pass to close a genuine silent-wrong-price risk (the mixed-face Oracal 8500 width) before Owner
review rather than shipping the narrower fix and calling it done. That is the right instinct. The
currency-mix refusal is the correct behavior, not a bug to be smoothed over, and it is good that Step 3
says "indisponibil" instead of quietly adding RON to EUR. The one real process defect in this round is
that the mandated 64-point report was skipped in the original hand-off, and the evidence pack had one
small self-inconsistency (a QA script that reported "did not resolve" for an order its own docstring
already knew the total of) — neither is a commercial-code problem, both are worth tightening before the
next GO. The Owner's actual decision — EUR ops rates vs. a provenanced exchange rate — is the one thing
standing between this branch and a single trustworthy `Total ofertă`, and nothing in this codebase
should guess it.

```text
No SVG/DWG parser implementation was performed.
No Product Template embedded commercial rate was introduced.
No inventory unit_cost was used directly as client price.
CPP was not coupled to EstimatedInternalCost.
No live or inferred FX conversion was introduced.
No accepted quote or order was repriced.
No scheduling, assignment, session or atelier phase was started.
No additional materialization was executed.
Push was not executed.
Waiting for Owner review.
```
