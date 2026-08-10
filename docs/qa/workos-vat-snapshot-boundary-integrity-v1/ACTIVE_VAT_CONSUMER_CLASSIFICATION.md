# ACTIVE_VAT_CONSUMER_CLASSIFICATION

| Consumer | Classification | Notes after this build |
|----------|----------------|------------------------|
| `get_default_vat_pct` + Settings PUT | CURRENT DEFAULT | Live authority for new work |
| `intake_v6_priced_quote_dry_run_service` | PRE_FREEZE_LIVE_DEFAULT | Allowed |
| `intake_v6_priced_quote_write_service` notes stamp | FROZEN_COMMERCIAL_TRUTH | Writes primary rate |
| `intake_v6_quote_snapshot_v2_service` CPP stamp | PRE_FREEZE_LIVE_DEFAULT → freeze stamp | Supplementary only on **new** freezes |
| `intake_v6_snapshot_authoritative_offer_service` | FROZEN_COMMERCIAL_TRUTH | Uses frozen resolver; **no** live Settings |
| `intake_v6_snapshot_authoritative_pricing_review_service` post-freeze | FROZEN_COMMERCIAL_TRUTH | Uses frozen resolver; **no** live Settings |
| pricing-review pre-freeze branch | PRE_FREEZE / quote projection | Unchanged lifecycle |
| `order_snapshot_v2_convert_service` | FROZEN_COMMERCIAL_TRUTH | `accepted_vat_percent` from notes |
| `quote_document_service` | DOCUMENT_FALLBACK | Snapshot/`quote.vat`/constant — no live Settings GET |
| `productsystem_pricing_preview_service` | PRE_FREEZE_LIVE_DEFAULT | Lab preview |
| `product_system_cost_simulation_service` | PRE_FREEZE_LIVE_DEFAULT | Simulation |
| `routers/quotes._apply_settings_vat_to_pricing` | DEAD | No production callers |
| QuoteWizard / Intake FE vatPct hooks | PRE_FREEZE_LIVE_DEFAULT | New commercial UI |
