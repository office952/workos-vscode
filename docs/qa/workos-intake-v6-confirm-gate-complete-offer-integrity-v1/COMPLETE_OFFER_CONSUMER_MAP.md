# COMPLETE_OFFER_CONSUMER_MAP

## `complete_offer_total` (product composition base)

| Consumer | Class |
|----------|-------|
| CPP `_build_commercial_product_breakdown` | PRODUCT_COMPOSITION_BASE |
| CPP `subtotal_commercial` assignment | PRODUCT_COMPOSITION_BASE |
| dry-run breakdown passthrough + official base input | PRODUCT_COMPOSITION_BASE |
| `buildOfferProductSummary` | DISPLAY_ONLY (composition honesty) |
| Confirm product rows | DISPLAY_ONLY / composition (must not masquerade as Ofertă) |
| Audit / tests | DISPLAY_ONLY |

**Must not** be treated as adjusted final offer money after commercial-input closure.

## `commercial_totals` (official adjusted offer)

| Consumer | Class |
|----------|-------|
| dry-run producer | CONFIRM_HEADLINE + QUOTE_WRITE authority |
| priced-quote write | QUOTE_WRITE |
| snapshot freeze identity | FREEZE_GATE |
| Confirm Ofertă Net/VAT/Gross | CONFIRM_HEADLINE |
| LiveCalculationSummary / PricingInputPanel | DISPLAY_ONLY |
| `applyIntakeV6CommercialAdjustments` | LEGACY / tests-only |

## Post-repair Confirm rule

- Headline money ← `commercial_totals` only when dry-run READY
- Product EUR ← composition info only; when blocked, clearly labeled non-Ofertă
