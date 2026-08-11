# CONFIRM_GATE_AUTHORITY_MAP

Task: `WORKOS_INTAKE_V6_CONFIRM_GATE_COMPLETE_OFFER_INTEGRITY_V1`  
Baseline HEAD: `9ad34e02`

## Authority chain

```text
operator finish_setup.confirmed + letter_group_finishes[].confirmed
  → Product Truth / workspace readiness (finish_setup_incomplete)
  → quote_input matrix (OR setup|group — looser; not commercial authority)
  → CPP Oracal 8500 width gate (REQUIRES per-group confirmed)
  → commercial_blockers (COMMERCIAL_CONFIGURATION_INCOMPLETE)
  → complete_offer_total null | valued  (product composition base)
  → dry-run blockers + pricing_status READY|BLOCKED
  → commercial_totals (official adjusted offer; empty when blocked)
  → offer_composition_readiness (derived read-model only; mirrors above)
  → Confirm UI (display) / priced-write / freeze
```

## Canonical READY/BLOCKED

| Surface | Authority |
|---------|-----------|
| Official Ofertă money | dry-run `pricing_status == V6_PRICED_DRY_RUN_READY` + non-null `commercial_totals` |
| Product composition base | CPP `complete_offer_total` |
| Freeze eligibility | dry-run READY **and** `commercial_freeze_allowed` (ConfirmJobProductTruth confirmed + pinned) |
| `offer_composition_readiness` | **Derived read-model only** — never a second authority |

## Parallel gates (inventory; not FE-invented READY)

1. `finish_setup.confirmed` / workspace `finish_setup_incomplete`
2. `letter_group_finishes[].confirmed` (Oracal 8500 commercial dependency)
3. `product_composition_confirmed`
4. Layer / offer-scope readiness
5. CPP `commercial_blockers` / `status`
6. ConfirmJobProductTruth freeze pin
7. FE checklist checkboxes (operator ack only — not money authority)

## Asymmetry (documented, unchanged)

quote_input matrix ORs `setup.confirmed` with group confirmed; CPP Oracal 8500 requires **per-group** `confirmed is True`. Commercial composition authority remains CPP.
