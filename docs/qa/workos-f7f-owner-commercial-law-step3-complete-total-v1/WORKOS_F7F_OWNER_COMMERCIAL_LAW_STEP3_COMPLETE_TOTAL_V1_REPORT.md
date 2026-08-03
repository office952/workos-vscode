# WORKOS F7F — Owner Commercial Law Activation + Step 3 Complete Offer Total

**Verdict: `PASS_WITH_EXACT_BLOCKER`** — every Owner rate is activated and proven at runtime, and
Step 3 no longer labels a partial figure as the offer total. One Owner decision is required before
a single complete `Total ofertă` can be published for a real workspace (currency mix).

Date: 2026-08-03 · Branch `feat/capacity-batch-20d-scoped-b-92401` · Push **not** performed.

## 1. Identity gate

| Check | Observed |
|---|---|
| Branch | `feat/capacity-batch-20d-scoped-b-92401` |
| Start HEAD | `d4989b21` — "Document F7E commercial integrity runtime proof." |
| Ancestors | `00496d99` ancestor of HEAD ✅ · `d4989b21` ancestor of HEAD ✅ |
| Stash | `stash@{0}` wip-employee-unrelated — untouched |
| Worktrees | 22 pre-existing. A temporary read-only baseline worktree at `C:\w\_f7f_baseline` was added for regression comparison and **removed** afterwards. |
| Working tree | Unrelated `_tmp*` / capacity-batch / U* QA noise preserved; no `git add .`, no `-A`, no reset, no clean, no stash pop |

## 2. What was implemented

**Agent A — pricing registry + CPP** (`backend/data/commercial_rules_volumetric_v2.py`,
`backend/schemas/commercial_price_proposal.py`,
`backend/services/commercial_price_proposal_service.py`,
`backend/services/intake_v6_priced_quote_dry_run_service.py`)

- Oracal 651 → 5 EUR/m², one series rate for every colour code (supersedes the F7E seed-derived 9.0).
- Oracal 8500 → 17 EUR/m² @ 1000 mm, 13.5 EUR/m² @ 1260 mm, resolved from a **confirmed** roll
  width; missing or unsupported width raises `COMMERCIAL_CONFIGURATION_INCOMPLETE` and leaves the
  price `null` rather than falling back to a documented rate. The width is read from the letter
  groups that actually carry the 8500 face and only when the group is operator-confirmed, because
  the job-level `face_vinyl_roll_width_mm` is a derived dominant-value projection that can go null
  — or carry another face's width — on a mixed-face job. Groups that disagree on the roll resolve
  to no rate and fail closed. The job-level field is used only when no group carries the 8500 face.
- Print + laminate → 10 EUR/m²; the F7E `COMMERCIAL_RULE_MISSING` is gone. `printed_vinyl`
  (print without laminate) stays fail-closed as a separate Owner decision.
- Vinyl application → one 3 EUR/m² Owner rule replacing three registry-bound labour rules. Charged
  once per proven applied surface: face area for the face, developed wrap area
  (perimeter × return depth) for the cant. Never on stock cant, never when no vinyl is selected.
- ACM sheet → 15 EUR/m² standard/colorat; 40 EUR/m² mirror as a **replacement** rate (never
  15 + 25); unknown shell fails closed; mirror on an exterior installation without a proven SKU
  raises `TECHNICAL_MATERIAL_COMPATIBILITY_REQUIRED`.
- New `commercial_product_key` on every rule and line (`letters` / `acm_panel`), and a new
  `commercial_product_breakdown` on the CPP preview carrying per-product, per-currency subtotals,
  one complete offer total or an explicit refusal reason, Owner-pending line codes, and
  `tax_status = "tax_exclusive"`.
- The dry-run service stamps the VAT rate from `company_commercial_settings.default_vat_pct`.
  No layer hardcodes 21.

**Agent B — product / intake propagation** (`frontend/src/lib/intakeV6/acmPanel/*`,
`IntakeV6AcmShellFinishPanel.tsx`)

- New `acm_sheet_material_v1` contract (variant + installation environment + exterior SKU +
  operator confirmation), persisted at `acm_panel_instance.sheet_material`, with stale-child
  clearing of `exterior_sku` when it stops applying. Operator truth only — no rates in the contract.
- Roll width was already captured per letter group on the artwork-finish row. The job-level field
  CPP first read turned out to be a *derived projection* of those captures, so CPP now prefers the
  per-group capture (see §2 Agent A) and no frontend change was needed.

**Agent C — Step 3 UI** (`intakeV6OfferProductSummary.ts`, `intakeV6PricedQuoteTypes.ts`,
`IntakeV6FinalConfigurationSummary.tsx`, `IntakeV6LiveCalculationSummary.tsx`)

- `Litere volumetrice` / `Subtotal Litere` and `Panou ACM` / `Subtotal Panou ACM` as distinct rows.
- One complete `Total ofertă` taken straight from CPP, or `Total ofertă indisponibil` with an
  actionable reason. The view model formats and selects only — it never sums lines and never
  converts currency.
- A total that omits Owner-pending lines is labelled `Total ofertă (parțial)`.
- Currency comes from the backend bucket; the hardcoded `?? "RON"` on this path is gone.

## 3. Residual register

See `00-architecture-readback.md`. A-F3 (exact F7D wording recovered, = AGENT-B-F004, finish
contract vocabulary / `mirror_silver`) remains **out of scope and open**. A-F4 (Step 3 Litere-only
total) is **closed**.

Opened during F7F and **left open for the Owner**:

| Id | Finding | Why it is not fixed here |
|----|---------|--------------------------|
| F7F-R1 | The Oracal 8500 width select is pre-filled with 1000 mm, so "the operator confirmed 1000" and "the operator never touched the default" are indistinguishable at the field level. CPP therefore requires the *letter group's* `confirmed` flag before it trusts the width. | A field-level `roll_width_confirmed` flag is an intake contract change and needs an Owner decision on whether a defaulted width may price at all. |
| F7F-R2 | `frontend/src/lib/intakeV6/intakeV6OfferCalculator.ts` still defaults `vatPercent` to 19 (canonical is 21), hardcodes `offerCurrency: "RON"` and carries `DEFAULT_EUR_TO_RON_RATE`. | Operator *Adaos* live-preview path only. It does not feed the Step 3 total, and the file is outside the three F7F ownership lanes. |
| F7F-R3 | `useIntakeV6FinalHandoff.ts` still sends `commercial_totals.total_gross` as `expected_total_gross`. Once `complete_offer_total` is authoritative the handoff should send the breakdown total and refuse the write when the total is unavailable. | The brief explicitly fenced handoff gating out of scope. |
| F7F-R4 | Running `tests/test_commercial_price_proposal_preview.py` before any ACM-seeding suite tears down the global `db_manager`, so the seeding fixture raises `TypeError: 'NoneType' object is not callable`. | Pre-existing shared-conftest debt, not F7F: the untouched `tests/test_acm_boxed_mounting_owner_rates_cpp_v1.py` fails identically in the same pairing. Each file is green on its own. |

## 4. Scenario matrix

See `01-scenario-matrix-results.md` and `evidence/runtime-scenario-matrix.json`. All Owner
arithmetic verified live at A = 2.5 m²: A×5+3, A×17+3, A×13.5+3, A×10+3; ACM 15 / mirror 40;
stock cant zero-delta preserved; RAL cant preserved; no colour tier.

## 5. Step 3 before / after

| | Before | After |
|---|---|---|
| Litere | ~249.98 EUR presented as the offer total | `Subtotal Litere` 71.36 EUR + 1 724.44 RON |
| Panou ACM | missing from the total | `Subtotal Panou ACM` 190.78 EUR |
| Complete total | implied complete | `Total ofertă indisponibil` — `COMMERCIAL_CURRENCY_MIX_UNRESOLVED` |
| VAT | hardcoded | `TVA 21% conform politicii fiscale` |

Screenshot: `evidence/step3-offer-product-breakdown.png`.

**Honest UI opinion.** The structure reads correctly — two products, two labelled subtotals, and a
refusal instead of a fake total. Two presentation weaknesses are visible in the capture: the amber
`Total ofertă indisponibil` block renders at low contrast inside the dimmed confirm card and can be
mistaken for disabled chrome, and per-currency rows are stacked without a visual hint that they are
*not* addable. Neither is a correctness defect; both are worth a small contrast/spacing pass.

## 6. Protected baselines

`evidence/protected-baselines.json`, read-only SQLite (`mode=ro`) on `backend/dev.db`:

- Order `ORD-F7B-880811`: `status=locked`, `total_amount=1847.5`, snapshot `QSN2-F7B-880811`
  `status=frozen` — **unchanged**.
- `execution_plan` id 22 → order 880811, `plan_source=order_snapshot_v2` — **unchanged**.
- `973019` did not resolve as an order code in this database; reported rather than guessed.
- No accept, no reprice, no materialize, no ExecutionPlan write, no scheduling, no DB write of any
  kind. CPP remains a read-only preview.

## 7. Tests

| Command | Result |
|---|---|
| `pytest tests/test_commercial_price_proposal_preview.py` | **32 passed** (30 + 2 covering the per-group 8500 roll-width resolution) |
| `pytest tests/test_f7f_owner_commercial_law_step3_total.py` (new, 9 tests) | **9 passed** |
| `pytest` ACM + dry-run suites (5 files) | 50 passed, 1 failed (`test_acm_boxed_mounting_standalone_offer_v1::test_standalone_payload_derivation_and_detection`, `panel_perimeter_m` KeyError — pre-existing, untracked F7E test, geometry-derivation path untouched by F7F) |
| Backend CI-equivalent four files | **28 passed** |
| `pnpm run lint` | **clean** |
| `pnpm run build` | **clean** |
| `tsc --noEmit` | **clean** |
| `pnpm run test:ci` | 274 passed / 4 failed — all 4 in `src/pages/MaterializedOpsGraph.test.tsx` (`executionApi.getEmployeeEligibilityReadModel is not a function`), **pre-existing**, unrelated to F7F |
| F7F frontend units (6 files) | **105 passed** |

`frontend/scripts/ci-unit-tests.txt` gained the two new pure-module suites so the Owner law is
gated in CI rather than only locally: `intakeV6OfferProductSummary.test.ts` (19) and
`acmPanel/acmSheetMaterial.test.ts` (25), both green.

**Regression proof.** The same broad backend sweep (`-k "commercial or intake_v6 or acm or
volumetric"`, ~1100 tests) was run on a pristine worktree at `d4989b21` and on the F7F tree.
Baseline: 99 failing node IDs. F7F: 100. The single difference,
`test_te2e_028b_formula_planning_duration::test_formula_duration_inputs_do_not_change_commercial_total`,
**passes in isolation** and fails only under the combined sweep's shared-DB ordering — the same
class as the 99 pre-existing failures. Lists: `evidence/backend-sweep-baseline-d4989b21.txt` and
`evidence/backend-sweep-f7f.txt`. No assertion was weakened; the three rewritten CPP tests were
re-pointed at the new Owner rates and made stricter (explicit currency and no-registry-labour
assertions added).

## 8. Blockers requiring an Owner decision

1. **`COMMERCIAL_CURRENCY_MIX_UNRESOLVED` (blocking a single complete total).** Registry operation
   rates resolve in RON; Owner material law is EUR. CPP has no authority to convert without a
   provenance-bearing exchange rate, so it refuses. Owner must choose: publish operation rates in
   EUR, or supply an exchange rate with provenance on the quote/snapshot. No default, no live FX.
2. **Oracal 641 rate not in the Owner list.** The F7E seed-derived 6.5 EUR/m² is retained unchanged
   and flagged, not re-derived.
3. **`printed_vinyl`** (print without laminate) remains fail-closed pending an Owner rate.
4. **A-F3 / AGENT-B-F004** finish-vocabulary normalization remains open, out of F7F scope.

## 9. Boundary

Scheduling HOLD respected. Materialization BLOCKED respected. Push NOT performed. No CostEngine or
EIC change. No inventory `unit_cost` used as a client price. No frontend-computed commercial total.
No machine or employee rates in CPP. No DB reseed or reset. No global currency refactor and no
global UI redesign.
