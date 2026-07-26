# Intake V6 — Ofertă client visibility + Adaos wiring

**Date:** 2026-07-24  
**Scope:** Owner-directed Intake V6 / Quotes display fixes (lab reference). No CostEngine rewrite. No Order/Execution.

## Owner symptoms

1. Ofertă client total hard to see in Configurare / Confirm — felt buried under line details / product EUR estimates.
2. Quotes showed **Marjă 0%** while Intake had **Adaos** (e.g. 35–50%).
3. Changing Adaos in Intake V6 **did not change** the Ofertă client price.

## Root causes

| Issue | Cause |
|-------|--------|
| Adaos decorative | Official `commercial_totals` came from 7G (`_official_totals_from_7g`) with VAT only. Operator `commercial_inputs` (markup/discount/manual) fed only `diagnostic_cost_plus_trace` (`diagnostic_only`). |
| Quotes Marjă 0% | `intake_v6_priced_quote_write_service` hardcoded `margin_pct: 0.0`. Field was never written from Adaos. |
| Label mismatch | Quote UI said **Marjă**; V6 `margin_pct` (when set) is **Adaos comercial** (markup on commercial base), not true margin `(sell−cost)/sell`. |
| Totals hard to see | Rail hero lacked TVA + Adaos rows; Confirm CTA showed a single total without net/TVA breakdown. |

## Fix

1. **Backend dry-run:** Apply Adaos / Discount / Ajustare on the 7G commercial subtotal for official totals; expose `commercial_base_subtotal` + `commercial_adjustment_trace`. Default markup when unset = **0** (7G lines are already sell prices).
2. **Backend write:** Persist `margin_pct` from Adaos %; store adjustment trace in write linkage notes.
3. **Frontend rail / Confirm:** Prominent Ofertă client gross + net + TVA + Adaos; optimistic recompute from local sliders on `commercial_base_subtotal`.
4. **Quotes V6:** Label **Adaos comercial** (not Marjă) + short hint.

## Semantics (operator-facing)

- **Adaos comercial %** = majorare pe baza comercială 7G (cost-plus pe ofertă, nu pe cost intern).
- **Marjă** (legacy quote UI) = istoric alias pe `margin_pct`; for V6 we stop calling it Marjă.
- Diagnostic cost-plus pe cost intern remains API-only (`diagnostic_only`).

## Remus note

Workspace `7cedd889-…` had `markup_percent: 50` persisted while official totals stayed at pure 7G (1891.53 / 2288.75). After fix, dry-run Ofertă client includes the 50% Adaos. Already-written quote keeps old totals/`margin_pct=0` until a new priced write.
