# F7F — Architecture readback (before production edits)

Branch `feat/capacity-batch-20d-scoped-b-92401` · start HEAD `d4989b21`.

## Ownership map (who is allowed to decide what)

| Concern | Canonical owner | Evidence |
|---|---|---|
| Commercial currency | The rule row itself (`documented_unit_price_currency`) plus the registry rate row. CPP preserves per-line currency in `source_currency` / `cpp_currency` and does **not** convert without `currency_conversion_rate` + `currency_conversion_source`. | `backend/data/commercial_rules_volumetric_v2.py`, `backend/services/commercial_price_proposal_service.py` |
| VAT / fiscal policy | `company_commercial_settings.default_vat_pct` (DB, default 21). CPP itself is tax-exclusive and stores **no** VAT. | `backend/models/company_commercial_settings.py`, `backend/services/company_commercial_settings_service.py::get_default_vat_pct` |
| Commercial rule catalog | `RULES_BY_TEMPLATE` in `commercial_rules_volumetric_v2.py` — every rate is a classified `CommercialRuleDefinition`. | same file |
| Internal cost (EIC) | `EstimatedInternalCostService`. Never read by CPP; never a client price. | `backend/services/estimated_internal_cost_service.py` |
| ACM product ownership | Was implicit. F7F makes it explicit via `CommercialRuleDefinition.commercial_product_key` (`letters` / `acm_panel`). | `commercial_rules_volumetric_v2.py` |
| Oracal selection | Operator, on the artwork-finish row (`face_finish_type`, `face_oracal_code`, roll width). CPP resolves the rate; it never picks a series. | `frontend/src/components/workos/intake-v6/IntakeV6ArtworkFinishSection.tsx` |
| Step 3 total source | **Before F7F:** `handoff.pricedQuoteDryRunTotal` (dry-run `commercial_totals.total_gross`) with a hardcoded `?? "RON"`. **After F7F:** `commercial_product_breakdown` from CPP. | `IntakeV6FinalConfigurationSummary.tsx` |
| Snapshot boundary | Snapshot V2 freezes an accepted offer. F7F touches **only** the read-only dry-run/preview path; no snapshot writer changed. | `backend/services/intake_v6_quote_snapshot_v2_service.py` (untouched) |

## Currency reality on this branch

CPP emits **mixed-currency** lines: registry operations resolve in RON, Owner material rates in EUR.
`subtotal_commercial` sums them **without conversion** — a pre-existing dishonesty inherited from
before F7F. F7F does not silently keep fusing them: `commercial_product_breakdown` reports
per-currency buckets, sets `currency_mix_detected`, and refuses a single `complete_offer_total`
with `COMMERCIAL_CURRENCY_MIX_UNRESOLVED`. No default FX rate, no `5`, no RON fallback.

## Residual register carried into F7F

| ID | Source | Exact statement | F7F disposition |
|---|---|---|---|
| **A-F3** | F7D register (`00-exact-f7d-finding-register.md`) — recovered text: **AGENT-B-F004 / P1**, "Submit `return_finish_type=\"mirror_silver\"` (not offered by the live UI combobox) to CPP preview → expected validation error/warning or documented confirmation the wider vocabulary is intentional; observed silently accepted, `status=ready`, no warning; separately UI emits short tokens (`white`/`black`) while schema/canonical map use suffixed tokens (`white_aluminum`) with no normalization bridge found." Scoped to G4 (finish contract vocabulary). | **Out of F7F scope, still open.** F7F changes no finish vocabulary or schema `Literal`s. `mirror_silver` remains a **cant stock colour**, deliberately not conflated with the new ACM `oglinda_gold` / `oglinda_antracit` sheet variants. |
| **A-F4** | F7D residual | Step 3 shows a Litere-only figure labelled as the offer total; the ACM panel is missing from it. | **CLOSED by F7F.** Step 3 now shows `Subtotal Litere` and `Subtotal Panou ACM` as distinct rows, and the complete total comes from CPP or is refused with a reason. |
| **F7E-OWNER-1** | F7E accepted `PASS_WITH_OWNER_RULE_BLOCKERS` | `print_laminate` had no commercial rule → `COMMERCIAL_RULE_MISSING`. | **CLOSED by F7F** (10 EUR/m²). `printed_vinyl` (print without laminate) stays fail-closed — a separate Owner decision. |
| **F7E-OWNER-2** | F7E | ACM mirror had no rule anywhere. | **CLOSED by F7F** (40 EUR/m² replacement rate; exterior needs a proven SKU). |
| **NEW-F7F-1** | F7F runtime | Oracal 641 was **not** in the Owner rate list; the F7E seed-derived 6.5 EUR/m² is retained unchanged and reported, not re-derived. | **Open — Owner decision requested.** |
| **NEW-F7F-2** | F7F runtime | Registry operations price in RON while Owner material law is EUR, so no single complete total can be published for a real workspace. | **Open — Owner decision requested** (either EUR commercial rates for operations, or a provenance-bearing exchange rate). |

## Files expected to change / protected

Changed: commercial rule registry, CPP schema + service, Intake V6 dry-run response, Step 3 offer
presentation, ACM sheet-material capture, plus tests.

Protected and untouched: CostEngine / EIC formulas, Snapshot V2 writers, quote acceptance, order
conversion, ExecutionPlan, inventory deduction, seeds, migrations, `pilot_gate_open`.

## Risk / rollback

All backend changes are additive to a read-only preview path. Rollback = revert the two F7F
commits; no data migration, no reseed, no snapshot rewrite.
