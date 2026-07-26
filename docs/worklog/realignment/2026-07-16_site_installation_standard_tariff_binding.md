# WORKOS — SITE_INSTALLATION_STANDARD commercial tariff binding

**Date:** 2026-07-16  
**Task:** `WORKOS-SITE-INSTALLATION-STANDARD-TARIFF-BINDING-V1`  
**Owner decision:** M1/M2 base 200 EUR + VAT per job/location; travel out of Bucharest deferred.

## Scope

- Configure Pricing Registry operation `SITE_INSTALLATION_STANDARD` = **200 EUR**, `per_piece` (commercial unit: once per locatie/job).
- Bind CPP `montaj` / `MONTAJ_COMMERCIAL_RULE` via `registry_pricing_code`.
- Canonical company EUR→RON; fail closed if rate missing.
- **Not in this phase:** travel/distance, hourly install, per-letter/logo install, Quote/Order creation.

## Files changed

| File | Change |
|------|--------|
| `backend/data/commercial_rules_volumetric_v2.py` | Montaj rule → `SITE_INSTALLATION_STANDARD` mapping |
| `backend/services/commercial_price_proposal_service.py` | Async registry bind + EUR→RON for `registry_pricing_code` rules |
| `backend/seeds/seed_volumetric_workcenter_rates.py` | Idempotent seed for `SITE_INSTALLATION_STANDARD` |
| `backend/tests/test_commercial_price_proposal_site_installation_binding.py` | Characterization + dry-run contract |
| `backend/tests/test_commercial_price_proposal_logo_registry_binding.py` | Fail-closed montaj without registry row |
| `backend/tests/test_commercial_price_proposal_linked_logo.py` | Same fail-closed isolation |
| `backend/tests/test_commercial_price_proposal_preview.py` | Forbidden-hourly token boundary fixture |

## Commands / results

```text
pytest tests/test_commercial_price_proposal_site_installation_binding.py
  + logo/linked fail-closed + forbidden hourly
→ 9 passed
```

Live DB seed (dev.db):

```text
SITE_INSTALLATION_STANDARD INSERTED — 200 EUR / per_piece / active
```

Same-workspace dry-run `11891d68-c4c8-4719-acc5-f8fcb22a44af`:

| Check | Result |
|-------|--------|
| `pricing_status` | `V6_PRICED_DRY_RUN_READY` |
| Montaj lines | **1** (`code=montaj`, qty=1, unit=`locatie`) |
| Montaj net | **1000.00 RON** (200 EUR × 5.0) |
| Travel lines | **0** |
| Letter lines | unchanged (`debitare_fata` 529.1875, cant 635.025, spate 25.276) |
| Logo print/lam/app | unchanged (42.5 / 25 / 25 RON × 2 logos) |
| Totals | net **3513.56** (= prior 2513.56 + 1000), VAT 737.85, gross **4251.41** |
| `MONTAJ_COMMERCIAL_RULE` blocker | **gone** |
| Confirmare / handoff | Still blocked by **other** genuine gates (`operator_confirmation_missing` + dossier trigger warnings) — not montaj |

## Boundary

- No ACM, no packaging tariff, no travel commercial line.
- No Quote/Order write in this task.
- Included/excluded commercial copy lives in registry notes; operator commercial text for M1/M2 can be surfaced later.
