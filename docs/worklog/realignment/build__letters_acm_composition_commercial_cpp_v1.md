# Build — Letters↔ACM composition commercial CPP v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Track** | C — commercial wiring (not CostEngine BOM rewrite) |
| **Boundary** | CPP `CommercialPriceProposal` lines; suppress legacy sablon under composition |

## Delivered

- Helper: `backend/services/letters_acm_composition_commercial_v1.py` (composition gate + outbox qty)
- Rules: `LETTERS_ACM_COMPOSITION_CONNECTION_RULES` in `commercial_rules_volumetric_v2.py`
- Wired into Letters v2 + ACM boxed template rule catalogs
- Gate: `applied_content=letters` + ACM mounting payload
- Suppress: `sablon_montaj_*` when composition active
- Qty: `letters_layer_outbox_m2` preferred; fallback `mounting_template_area_m2` with honesty warning
- Pack min 15 EUR

## Rates (EUR)

| Line | Rate |
|------|------|
| Șablon process | 20 / mp |
| Forex fasten | 8 / mp |
| Electric + traf | 35 / buc |
| Cablu 5 m | 6 / buc |
| Test lumină | 8 / buc |
| Attach body | 12 / mp |
| Pack | 10 / mp (min 15) |

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_letters_acm_composition_commercial_v1.py -q
```

Result: 5 passed.

## Out of scope

CostEngine `MAT-SABLON-*` BOM rewrite · EIC mirror · Intake autofill of outbox field UI
