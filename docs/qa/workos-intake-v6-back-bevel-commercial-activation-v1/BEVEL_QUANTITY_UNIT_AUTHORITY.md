# BEVEL_QUANTITY_UNIT_AUTHORITY

```text
HEAD = 5cb792f8
STATUS = RESOLVED (planning)
```

## Technical op

`cnc_backing_bevel_forex_10mm` / `VOLUMETRIC_BACKING_BEVEL_RULE`

| Field | Value |
|-------|--------|
| basis_key | `backing_cnc_cutting_perimeter` |
| quantity | path perimeter |
| unit | `ml` |
| passes | `2` (`FOREX_10MM_BEVEL_PASSES_OWNER`) |
| equivalent | `ml × passes` → `ml-pass` |

Source: `backend/services/shared_cnc_operation_model.py`

## Candidates rejected / accepted

| Candidate | Verdict |
|-----------|---------|
| m² (like debitare_spate) | **Reject** — different basis; Owner forbids deriving area for bevel |
| piece count | **Reject** — not what CNC bevel rule uses |
| fixed/job | **Reject** — no canonical fixed job qty |
| machine time | **Reject** — not canonical sell qty here |
| perimeter ml | **Accept** — matches op rule |

```text
BEVEL_TECHNICAL_QUANTITY = backing CNC contour length
BEVEL_TECHNICAL_UNIT = ml
SOURCE = VOLUMETRIC_BACKING_BEVEL_RULE / material-breakdown operation_rows
BEVEL_COMMERCIAL_UNIT = ml
BEVEL_QUANTITY_SOURCE = backing_cnc_cutting_perimeter_ml for bevel-enabled groups only
```
