# COMPLETE_OFFER_BEFORE_AFTER

## Before

- CPP `complete_offer_total` = pre-adjustment line sum
- Dry-run applied adjustments (Manual RON bare into EUR)
- FE recomputed adjusted totals locally
- Confirm headline preferred CPP complete total
- Post-freeze offer zeroed markup/discount/manual

## After

- CPP `complete_offer_total` remains product composition base
- Official Ofertă client Net/VAT/Gross = dry-run `commercial_totals` after adjustments
- Manual RON→EUR via Settings FX when ≠0 (`_round_money`)
- FE displays backend totals only
- Post-freeze consumes quote columns + frozen adjustment trace (identity-checked)
- Order still copies frozen truth (no re-adjustment)
