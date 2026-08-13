# PRICED_QUOTE_RESPONSE_FIELD_CLASSIFICATION

| Field | Class | Notes |
|---|---|---|
| `pricing_status` | A official + B Confirm | Ready/blocked gate |
| `pricing_authority` | A | Official commercial authority stamp |
| `commercial_authority_status` | A / B | Mirror of authority |
| `commercial_totals` | A + B | Ofertă rail + Confirm money |
| `commercial_line_items` | A / C | Official lines |
| `commercial_product_breakdown` | A / C | Product money breakdown |
| `offer_composition_readiness` | B | Confirm composition gate |
| `acm_panel_commercial_preview` | C / A (panel) | Panel offer rail |
| `blockers` / `warnings` | A / B | Readiness honesty |
| `workspace_id` / `workspace_code` / `template_code` | A | Identity |
| `pricing_source` / `pricing_mode` | A | Provenance |
| `product_composition_*` / `composition_items` | B | Composition Confirm |
| `pricing_input_trace` | D | Adapter diagnostics |
| `commercial_proposal_trace` | D / C | CPP status metadata |
| `internal_cost_trace` | D | Deferred by default; write/snapshot opt-in |
| `estimated_internal_cost_trace` | D | Deferred by default |
| `diagnostic_cost_plus_trace` | D | Deferred by default |
| `can_write_quote_totals` / `can_create_quote_snapshot` / `dry_run_only` / `persistence` | A / E | Contract flags |

## Consumer notes

- Frontend types declare diagnostic traces; Step 2 Ofertă money does **not** read them for totals.
- Letters internal estimate UI uses sibling `material-breakdown`, not dry-run embeds.
- Write + Snapshot V2 pass `include_internal_cost_diagnostics=True` so snapshot/write summaries retain prior diagnostic content.
