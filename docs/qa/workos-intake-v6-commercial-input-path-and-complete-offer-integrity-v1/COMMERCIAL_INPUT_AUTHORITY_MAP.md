# COMMERCIAL_INPUT_AUTHORITY_MAP

| Field | UI | Payload | CPP lines / complete_offer_total | Official money authority | Freeze | Order |
|-------|----|---------|----------------------------------|--------------------------|--------|-------|
| markup_percent | Adaos % | finish_setup.commercial_inputs | Ignored (base only) | Dry-run / priced-write `commercial_totals` | Frozen in quote columns + trace | Copy frozen |
| discount_percent | Discount % | same | Ignored | same | same | Copy frozen |
| manual_adjustment_ron | Ajustare manuală (RON) | same | Ignored | Dry-run converts→EUR via Settings FX when ≠0; adds into commercial math | Trace + quote columns | Copy frozen |
| vat_percent (workspace) | read-only Settings | same | N/A | Pre-freeze: Settings; post-freeze: frozen resolver | notes.commercial_adjustment_trace.vat_percent | accepted_vat_percent |

## Surfaces

- **CPP `complete_offer_total`**: pre-adjustment product composition (tax-exclusive line sum)
- **Official Ofertă client Net/VAT/Gross**: `commercial_totals` after adjustments
- **Frontend**: display backend totals only after this build
