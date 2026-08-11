# READINESS_STATE_MODEL

Derived dry-run field: `offer_composition_readiness`  
**Not a second authority** — mirrors existing dry-run / CPP / freeze signals.

| State | Derivation |
|-------|------------|
| `product_composition_complete` | No `PRODUCT_COMPOSITION_NOT_CONFIRMED` blocker |
| `commercial_composition_complete` | CPP `status==ready` **and** `complete_offer_total` is a finite number |
| `confirmation_complete` | No `COMMERCIAL_CONFIGURATION_INCOMPLETE` in dry-run blockers (dependency-aware commercial confirms already enforced by CPP) |
| `offer_ready_to_freeze` | `pricing_status == V6_PRICED_DRY_RUN_READY` **and** `commercial_freeze_allowed(payload)` |
| `canonical_gate` | `ready` iff `pricing_status == V6_PRICED_DRY_RUN_READY`, else `blocked` |

## Distinctions preserved

- Product composition ≠ commercial composition ≠ job Product Truth freeze confirm
- `complete_offer_total` ≠ `commercial_totals`
- FE does not invent READY; it displays this read-model + existing dry-run fields
